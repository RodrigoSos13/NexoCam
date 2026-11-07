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


async def authenticate(
    ws, token, orientation_control=False, before_start=None, fps=15, size=(640, 480)
):
    await ws.send(control("hello", device="Teste sem celular"))
    hello = json.loads(await ws.recv())
    assert hello["type"] == "hello"
    assert hello["max_in_flight"] == 2
    await ws.send(control("authenticate", token=token))
    assert json.loads(await ws.recv())["state"] == "authenticated"
    await ws.send(
        control(
            "configure",
            width=size[0],
            height=size[1],
            fps=fps,
            codec="jpeg",
            orientation_control=orientation_control,
        )
    )
    config = json.loads(await ws.recv())
    assert config["type"] == "configure" and config["fps"] == fps
    if before_start:
        await before_start()
    await ws.send(control("start"))
    assert json.loads(await ws.recv())["state"] == "streaming"


def test_tls_authentication_frames_disconnect_and_reconnect(tmp_path):
    async def scenario():
        identity = Identity(tmp_path / "tls")
        stop = Event()
        output = []

        def publish(frame, *_):
            output[:] = [frame]

        portrait_mode = Event()
        confirmations = []
        server = StreamServer(
            identity,
            host="127.0.0.1",
            port=0,
            publish=publish,
            paired=lambda: confirmations.append(True),
            portrait=portrait_mode.is_set,
        )
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
            assert not confirmations
            async with connect(uri, **kwargs) as ws:
                await ws.send(control("hello", device="Teste QR", purpose="pairing"))
                await ws.recv()
                await ws.send(control("authenticate", token=server.pairing.token))
                assert json.loads(await ws.recv())["state"] == "authenticated"
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
            assert confirmations == [True]
            assert server.active is None
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
            async with connect(uri, **kwargs) as ws:

                async def change_during_negotiation():
                    portrait_mode.set()
                    await asyncio.sleep(0.12)

                await authenticate(
                    ws,
                    server.pairing.token,
                    orientation_control=True,
                    before_start=change_during_negotiation,
                )
                for seq, portrait in ((1, False), (2, True)):
                    if portrait:
                        portrait_mode.set()
                    else:
                        portrait_mode.clear()
                    change = json.loads(await asyncio.wait_for(ws.recv(), 3))
                    assert change["state"] == "format" and change["portrait"] == portrait
                    frame = np.full(
                        (640, 480, 3) if portrait else (480, 640, 3), 180, dtype=np.uint8
                    )
                    await ws.send(make_packet(seq, frame))
                    ack = json.loads(await asyncio.wait_for(ws.recv(), 3))
                    assert ack["state"] == "frame" and ack["sequence"] == seq
                    await wait_until(
                        lambda expected=frame.shape: output and output[-1].shape == expected
                    )
                await ws.send(control("stop"))
            await wait_until(lambda: server.active is None)
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


def test_portrait_requires_negotiation_and_fits_virtual_output():
    from nexocam.video.layout import fit_output

    portrait = np.full((640, 480, 3), 200, dtype=np.uint8)
    packet = make_packet(frame=portrait)
    with pytest.raises(ProtocolError):
        unpack_frame(packet, -1)
    sizes = ((640, 480), (480, 640))
    _, jpeg = unpack_frame(packet, -1, sizes)
    decoded = decode(jpeg, sizes)
    assert decoded.shape == (640, 480, 3)
    output = fit_output(decoded)
    assert output.shape == (480, 640, 3)
    assert np.all(output[:, :140] == 0)
    assert np.all(output[:, 180:460] > 190)


def test_ack_does_not_wait_for_output_and_only_newest_frame_is_displayed(tmp_path):
    async def scenario():
        identity = Identity(tmp_path / "tls")
        stop = Event()
        release_output = asyncio.Event()
        published = []
        server = StreamServer(
            identity,
            host="127.0.0.1",
            port=0,
            publish=lambda frame, count, fps: published.append((frame, count, fps)),
        )
        original_output = server.output

        async def paused_output(camera):
            await release_output.wait()
            await original_output(camera)

        server.output = paused_output
        task = asyncio.create_task(server.run(stop))
        try:
            await wait_until(lambda: server.bound_port is not None or task.done())
            if task.done():
                await task
            context = ssl.create_default_context(cafile=str(identity.cert_path))
            async with connect(
                f"wss://127.0.0.1:{server.bound_port}",
                ssl=context,
                server_hostname="nexocam.local",
                proxy=None,
            ) as ws:
                await authenticate(ws, server.pairing.token)
                for batch in ((1, 2), (3,)):
                    for sequence in batch:
                        packet = make_packet(
                            sequence, np.full((480, 640, 3), sequence * 50, dtype=np.uint8)
                        )
                        await ws.send(packet)
                    for sequence in batch:
                        ack = json.loads(await asyncio.wait_for(ws.recv(), 1))
                        assert ack["state"] == "frame" and ack["sequence"] == sequence
                assert not published  # A saída está bloqueada, mas o emissor continua livre.
                assert server.received == 3 and server.dropped == 2
                release_output.set()
                await wait_until(lambda: bool(published))
                assert np.array_equal(published[0][0], decode(packet[HEADER.size :]))
                assert published[0][1:] == (1, 1.0)
                await wait_until(lambda: published[-1][2] == 0)
                assert published[-1][1] == 1  # Repetições não inflam a contagem/FPS.
                assert np.array_equal(published[-1][0], neutral())
        finally:
            stop.set()
            release_output.set()
            await asyncio.wait_for(task, 5)

    asyncio.run(scenario())


@pytest.mark.parametrize("fps", [15, 30])
def test_negotiated_rate_reaches_output_without_fifteen_fps_cap(tmp_path, monkeypatch, fps):
    from nexocam.network import server as server_module

    camera_rates = []

    class FakeCamera:
        def __init__(self, device, fps):
            camera_rates.append(fps)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def send(self, frame):
            assert frame.shape == (480, 640, 3)

    monkeypatch.setattr(server_module, "VirtualCameraManager", FakeCamera)

    async def scenario():
        identity = Identity(tmp_path / "tls")
        stop = Event()
        server = StreamServer(identity, device="test", host="127.0.0.1", port=0)
        task = asyncio.create_task(server.run(stop))
        try:
            await wait_until(lambda: server.bound_port is not None or task.done())
            if task.done():
                await task
            context = ssl.create_default_context(cafile=str(identity.cert_path))
            async with connect(
                f"wss://127.0.0.1:{server.bound_port}",
                ssl=context,
                server_hostname="nexocam.local",
                proxy=None,
            ) as ws:
                await authenticate(ws, server.pairing.token, fps=fps)
                assert server.fps == fps
                started = asyncio.get_running_loop().time()
                total = fps
                for sequence in range(1, total + 1):
                    deadline = started + (sequence - 1) / fps
                    await asyncio.sleep(max(0, deadline - asyncio.get_running_loop().time()))
                    await ws.send(make_packet(sequence))
                    ack = json.loads(await asyncio.wait_for(ws.recv(), 1))
                    assert ack["sequence"] == sequence
                await asyncio.sleep(1 / fps + 0.02)
                assert server.received == total
                assert server.displayed >= total * 0.7
                assert camera_rates == [30]
        finally:
            stop.set()
            await asyncio.wait_for(task, 5)

    asyncio.run(scenario())


def test_preview_wakes_on_frame_before_virtual_output_deadline():
    async def scenario():
        published = []
        server = StreamServer(None, publish=lambda frame, *_: published.append(frame))
        server.fps = 1  # Simula um próximo tick V4L2 distante para separar os relógios.
        server.current = neutral()
        server.active = object()
        server.last_frame = asyncio.get_running_loop().time()
        task = asyncio.create_task(server.output(None))
        try:
            await wait_until(lambda: bool(published))
            newest = np.full((480, 640, 3), 123, dtype=np.uint8)
            server.latest = newest
            server.frame_ready.set()
            await asyncio.wait_for(wait_until(lambda: published[-1] is newest), 0.5)
            assert server.displayed == 1
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())


@pytest.mark.parametrize("size", [(1280, 720), (1920, 1080)])
def test_high_resolution_negotiation_and_orientation(tmp_path, size):
    async def scenario():
        server = StreamServer(
            Identity(tmp_path / "tls"),
            host="127.0.0.1",
            port=0,
            video_size=size,
            quality=100,
            adaptive=False,
        )
        stop = Event()
        task = asyncio.create_task(server.run(stop))
        try:
            await wait_until(lambda: server.bound_port is not None or task.done())
            if task.done():
                await task
            context = ssl.create_default_context(cafile=str(server.identity.cert_path))
            async with connect(
                f"wss://127.0.0.1:{server.bound_port}",
                ssl=context,
                server_hostname="nexocam.local",
                proxy=None,
            ) as ws:
                await authenticate(ws, server.pairing.token, orientation_control=True, size=size)
                for sequence, dimensions in enumerate((size, size[::-1]), 1):
                    frame = np.full((dimensions[1], dimensions[0], 3), 120, dtype=np.uint8)
                    await ws.send(make_packet(sequence, frame))
                    ack = json.loads(await ws.recv())
                    assert ack["state"] == "frame" and ack["sequence"] == sequence
                # A different, unnegotiated resolution must still be rejected.
                await ws.send(make_packet(3))
                with pytest.raises(ConnectionClosed):
                    await ws.recv()
        finally:
            stop.set()
            await asyncio.wait_for(task, 5)

    asyncio.run(scenario())
