import asyncio
import json
import ssl
from threading import Event

import cv2
import numpy as np
import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from nexocam.network.protocol import MAX_FRAME_BYTES, ProtocolError
from nexocam.network.server import StreamServer, control
from nexocam.security.identity import Identity
from nexocam.security.pairing import PairingManager
from nexocam.video.jpeg import HEADER, decode, jpeg_size, unpack_frame
from nexocam.video.pattern import neutral, pattern


def make_packet(index=1, frame=None):
    frame = pattern(1) if frame is None else frame
    ok, encoded = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    assert ok
    return HEADER.pack(b"NXCF", 1, index, 100) + encoded.tobytes()


def test_identity_private_persistent_and_pairing(tmp_path):
    identity = Identity(tmp_path / "identity")
    assert Identity(tmp_path / "identity").fingerprint == identity.fingerprint
    assert identity.key_path.stat().st_mode & 0o777 == 0o600
    assert identity.key_path.parent.stat().st_mode & 0o777 == 0o700
    pairing = PairingManager()
    assert pairing.authenticate(pairing.token)
    assert not pairing.authenticate("x" * 64)
    assert not pairing.authenticate(None)
    pairing.deadline = 0
    assert not pairing.authenticate(pairing.token)


def test_jpeg_validation():
    packet = make_packet()
    sequence, jpeg = unpack_frame(packet, -1)
    assert sequence == 1 and jpeg_size(jpeg) == (640, 480)
    result = decode(jpeg)
    assert result.shape == (480, 640, 3) and result.dtype == np.uint8
    assert result[0, 500, 2] > 200  # RGB azul, não BGR.
    for invalid in (
        b"",
        b"other",
        packet[:20],
        b"XXXX" + packet[4:],
        packet + b"x" * MAX_FRAME_BYTES,
        make_packet(frame=np.zeros((100, 100, 3), dtype=np.uint8)),
    ):
        with pytest.raises(ProtocolError):
            unpack_frame(invalid, -1)
    with pytest.raises(ProtocolError):
        unpack_frame(packet, 1)
    with pytest.raises(ProtocolError):
        jpeg_size(b"\xff\xd8\xff\xc0\x00\x20")


async def wait_until(predicate):
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(0.01)


async def authenticate(ws, token):
    await ws.send(control("hello", device="Teste sem celular"))
    assert json.loads(await ws.recv())["type"] == "hello"
    await ws.send(control("authenticate", token=token))
    assert json.loads(await ws.recv())["state"] == "authenticated"
    await ws.send(control("configure", width=640, height=480, fps=15, codec="jpeg"))
    assert json.loads(await ws.recv())["type"] == "configure"
    await ws.send(control("start"))
    assert json.loads(await ws.recv())["state"] == "streaming"


def test_tls_authentication_frames_disconnect_and_reconnect(tmp_path):
    async def scenario():
        identity = Identity(tmp_path / "tls")
        stop = Event()
        output = []

        def publish(frame, *_):
            output[:] = [frame]

        server = StreamServer(identity, host="127.0.0.1", port=0, publish=publish)
        task = asyncio.create_task(server.run(stop))
        try:
            await wait_until(lambda: server.bound_port is not None or task.done())
            if task.done():
                await task
            context = ssl.create_default_context(cafile=str(identity.cert_path))
            uri = f"wss://127.0.0.1:{server.bound_port}"
            kwargs = {"ssl": context, "server_hostname": "nexocam.local", "proxy": None}
            with pytest.raises(ssl.SSLCertVerificationError):
                async with connect(uri, ssl=ssl.create_default_context(), proxy=None):
                    pytest.fail("Certificado desconhecido aceito")
            with pytest.raises(ssl.SSLCertVerificationError):
                async with connect(uri, ssl=context, server_hostname="other.local", proxy=None):
                    pytest.fail("Nome TLS incorreto aceito")
            async with connect(uri, **kwargs) as ws:
                await ws.send(control("hello", device="Teste"))
                await ws.recv()
                await ws.send(control("authenticate", token="0" * 64))
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            async with connect(uri, **kwargs) as ws:
                await ws.send(make_packet())
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            async with connect(uri, **kwargs) as ws:
                await ws.send("x" * 4097)
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            async with connect(uri, **kwargs) as ws:
                await ws.send(b"x" * (MAX_FRAME_BYTES + 1))
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            server.auth_timeout = 0.1
            async with connect(uri, **kwargs) as ws:
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            server.auth_timeout = 10
            for _ in range(2):
                async with connect(uri, **kwargs) as ws:
                    await authenticate(ws, server.pairing.token)
                    await ws.send(make_packet())
                    await wait_until(lambda: output and not np.array_equal(output[-1], neutral()))
                    assert server.active is not None
                    acknowledgement = json.loads(await ws.recv())
                    assert acknowledgement["state"] == "frame"
                    assert acknowledgement["sequence"] == 1
                    await wait_until(lambda: np.array_equal(output[-1], neutral()))
                    async with connect(uri, **kwargs) as other:
                        with pytest.raises(ConnectionClosed):
                            await other.recv()
                    await ws.send(control("stop"))
                await wait_until(lambda: server.active is None)
                await wait_until(lambda: output and np.array_equal(output[-1], neutral()))
            server.pairing.deadline = 0
            async with connect(uri, **kwargs) as ws:
                await ws.send(control("hello", device="Teste"))
                await ws.recv()
                await ws.send(control("authenticate", token=server.pairing.token))
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
        finally:
            stop.set()
            await asyncio.wait_for(task, 5)

    asyncio.run(scenario())


def test_decoder_failure_becomes_protocol_error(monkeypatch):
    jpeg = make_packet()[HEADER.size :]

    def fail(*_):
        raise cv2.error("invalid compressed data")

    monkeypatch.setattr(cv2, "imdecode", fail)
    with pytest.raises(ProtocolError):
        decode(jpeg)
