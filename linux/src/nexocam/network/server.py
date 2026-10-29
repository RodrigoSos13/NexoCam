import asyncio
import json
import logging
import time
from contextlib import nullcontext

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from nexocam.network.protocol import MAX_FRAME_BYTES, ProtocolError, parse_control
from nexocam.security.pairing import PairingManager
from nexocam.video.jpeg import decode, unpack_frame
from nexocam.video.layout import fit_output
from nexocam.video.pattern import neutral
from nexocam.video.virtual_camera import VirtualCameraManager

# Sem traceback com conteúdo recebido. Nunca ativar logs de frames WebSocket.
LOGGER = logging.getLogger("nexocam.transport")
LOGGER.addHandler(logging.NullHandler())
LOGGER.propagate = False


def control(kind, **fields):
    return json.dumps({"v": 1, "type": kind, **fields})


class StreamServer:
    def __init__(
        self,
        identity,
        device=None,
        host="0.0.0.0",
        port=8765,
        publish=lambda *args: None,
        status=lambda message: None,
        ready=lambda *args: None,
        paired=lambda: None,
        portrait=lambda: False,
    ):
        self.identity, self.device, self.host, self.port = identity, device, host, port
        self.publish, self.status, self.ready = publish, status, ready
        self.paired = paired
        self.portrait = portrait
        self.format_control = False
        self.streaming = False
        self.sent_portrait = False
        self.allowed_sizes = ((640, 480),)
        self.pairing = PairingManager()
        self.active = None
        self.pending = 0
        self.latest = None
        self.last_frame = 0.0
        self.received = self.dropped = 0
        self.bound_port = None
        self.auth_timeout = 10

    async def expect(self, ws, kind):
        raw = await asyncio.wait_for(ws.recv(), self.auth_timeout)
        if not isinstance(raw, str):
            raise ProtocolError("Mensagem de controle esperada.")
        message = parse_control(raw)
        if message["type"] != kind:
            raise ProtocolError("Mensagem fora da ordem da sessão.")
        return message

    async def handle(self, ws):
        if self.pending >= 4 or self.active is not None:
            await ws.close(1013, "Receptor ocupado.")
            return
        self.pending += 1
        admitted = False
        try:
            hello = await self.expect(ws, "hello")
            name = hello.get("device", "Android")
            if not isinstance(name, str) or not 1 <= len(name) <= 80 or not name.isprintable():
                raise ProtocolError("Nome do dispositivo inválido.")
            purpose = hello.get("purpose", "stream")
            if purpose not in ("stream", "pairing"):
                raise ProtocolError("Finalidade inválida.")
            await ws.send(control("hello"))
            auth = await self.expect(ws, "authenticate")
            if not self.pairing.authenticate(auth.get("token")):
                await ws.close(1008, "Pareamento inválido ou expirado.")
                return
            self.paired()
            if purpose == "pairing":
                await ws.send(control("state", state="authenticated"))
                await ws.close(1000, "Leitura confirmada.")
                return
            # Não há await entre verificar e reservar a sessão.
            if self.active is not None:
                await ws.close(1013, "Receptor ocupado.")
                return
            self.active = ws
            admitted = True
            await ws.send(control("state", state="authenticated"))
            config = await self.expect(ws, "configure")
            if any(
                type(config.get(k)) is not int or config[k] != v
                for k, v in {"width": 640, "height": 480, "fps": 15}.items()
            ):
                raise ProtocolError("Configuração de vídeo não suportada.")
            if config.get("codec") != "jpeg":
                raise ProtocolError("Codec não suportado.")
            self.format_control = config.get("orientation_control") is True
            self.allowed_sizes = ((640, 480), (480, 640)) if self.format_control else ((640, 480),)
            await ws.send(control("configure", width=640, height=480, fps=15, codec="jpeg"))
            await self.expect(ws, "start")
            self.sent_portrait = self.portrait() if self.format_control else False
            await ws.send(control("state", state="streaming", portrait=self.sent_portrait))
            self.streaming = True
            self.status(f"Transmitindo • {name}")
            sequence = -1
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=20)
                if isinstance(raw, str):
                    if parse_control(raw)["type"] == "stop":
                        break
                    raise ProtocolError("Controle inesperado durante transmissão.")
                sequence, jpeg = unpack_frame(raw, sequence, self.allowed_sizes)
                if self.latest is not None:
                    self.dropped += 1
                self.latest = (ws, sequence, jpeg)
                self.last_frame = time.monotonic()
                self.received += 1
        except (ProtocolError, TimeoutError):
            await ws.close(1008, "Sessão inválida ou tempo esgotado.")
        except ConnectionClosed:
            pass
        finally:
            self.pending -= 1
            if admitted:
                self.streaming = False
                self.active = None
                self.latest = None
                self.last_frame = 0.0
                self.status("Celular desconectado. Aguardando conexão autenticada.")

    async def output(self, camera):
        count = 0
        started = time.monotonic()
        while True:
            tick = time.monotonic()
            if (
                self.active
                and self.streaming
                and self.format_control
                and self.portrait() != self.sent_portrait
            ):
                self.sent_portrait = self.portrait()
                try:
                    await self.active.send(
                        control("state", state="format", portrait=self.sent_portrait)
                    )
                except ConnectionClosed:
                    pass
            jpeg, self.latest = self.latest, None
            # Limita exibição da última imagem a 1 s, inclusive em conexão estagnada.
            if jpeg is not None:
                source, sequence, payload = jpeg
                try:
                    frame = decode(payload, self.allowed_sizes)
                except ProtocolError:
                    if self.active:
                        await self.active.close(1008, "JPEG inválido.")
                    frame = neutral()
                self.current = frame
                if source is self.active:
                    try:
                        await source.send(control("state", state="frame", sequence=sequence))
                    except ConnectionClosed:
                        pass
            elif self.active is None or tick - self.last_frame > 1:
                self.current = neutral()
            if camera:
                camera.send(fit_output(self.current))
            count += 1
            self.publish(self.current, count, count / max(time.monotonic() - started, 1 / 15))
            await asyncio.sleep(max(0, 1 / 15 - (time.monotonic() - tick)))

    async def run(self, stop):
        self.current = neutral()
        context = VirtualCameraManager(self.device) if self.device else nullcontext(None)
        with context as camera:
            output = None
            try:
                async with serve(
                    self.handle,
                    self.host,
                    self.port,
                    ssl=self.identity.server_context(),
                    max_size=MAX_FRAME_BYTES,
                    max_queue=1,
                    compression=None,
                    ping_interval=10,
                    ping_timeout=20,
                    close_timeout=2,
                    open_timeout=10,
                    origins=[None],
                    server_header=None,
                    logger=LOGGER,
                ) as server:
                    self.bound_port = server.sockets[0].getsockname()[1]
                    output = asyncio.create_task(self.output(camera))
                    self.ready(self.identity.fingerprint, self.pairing.token, self.bound_port)
                    self.status("Servidor TLS ativo. Aguardando pareamento do Android.")
                    while not stop.is_set():
                        if output.done():
                            await output
                        await asyncio.sleep(0.05)
            finally:
                if output:
                    output.cancel()
                    try:
                        await output
                    except asyncio.CancelledError:
                        pass
                if camera:
                    camera.send(neutral())
