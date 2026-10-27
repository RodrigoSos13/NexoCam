"""Emissor de integração TLS; nunca imprime ou recebe segredo pela linha de comando."""

import argparse
import asyncio
import getpass
import json
import ssl
import time
from pathlib import Path

import cv2
from nexocam.network.server import control
from nexocam.video.jpeg import HEADER
from nexocam.video.pattern import pattern
from websockets.asyncio.client import connect


async def transmit(args, token):
    # Confiança restrita ao certificado local fornecido, com validação do nome TLS.
    context = ssl.create_default_context(cafile=str(args.certificate))
    async with connect(
        f"wss://{args.host}:8765",
        ssl=context,
        server_hostname="nexocam.local",
        proxy=None,
        compression=None,
    ) as ws:
        await ws.send(control("hello", device="Emissor sintético de integração"))
        assert json.loads(await ws.recv())["type"] == "hello"
        await ws.send(control("authenticate", token=token))
        assert json.loads(await ws.recv())["state"] == "authenticated"
        await ws.send(control("configure", width=640, height=480, fps=15, codec="jpeg"))
        assert json.loads(await ws.recv())["type"] == "configure"
        await ws.send(control("start"))
        assert json.loads(await ws.recv())["state"] == "streaming"
        started = time.monotonic()
        sequence = 0
        while time.monotonic() - started < args.seconds:
            tick = time.monotonic()
            sequence += 1
            _, jpeg = cv2.imencode(
                ".jpg", cv2.cvtColor(pattern(sequence), cv2.COLOR_RGB2BGR)
            )
            await ws.send(
                HEADER.pack(b"NXCF", 1, sequence, time.monotonic_ns() // 1000)
                + jpeg.tobytes()
            )
            reply = json.loads(await asyncio.wait_for(ws.recv(), 20))
            assert reply.get("state") == "frame" and reply.get("sequence") == sequence
            await asyncio.sleep(max(0, 1 / 15 - (time.monotonic() - tick)))
        await ws.send(control("stop"))
        print(f"{sequence} quadros confirmados pelo receptor.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if not 0 < args.seconds <= 3600:
        parser.error("Duração deve estar entre 0 e 3600 segundos.")
    token = getpass.getpass("Segredo temporário exibido no NexoCam: ").strip()
    try:
        asyncio.run(transmit(args, token))
    except (OSError, ValueError, AssertionError, TimeoutError):
        parser.exit(
            1, "Falha no teste. Confira certificado, segredo e servidor ativo.\n"
        )


if __name__ == "__main__":
    main()
