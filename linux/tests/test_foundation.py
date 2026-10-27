import json
import stat
from threading import Event
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from nexocam.devices import v4l2
from nexocam.network.protocol import MAX_CONTROL_BYTES, ProtocolError, parse_control
from nexocam.video import stream, virtual_camera
from nexocam.video.pattern import neutral, pattern


@pytest.mark.parametrize(
    "value",
    [
        [],
        None,
        {},
        {"v": True, "type": "hello"},
        {"v": 2, "type": "hello"},
        {"v": 1, "type": []},
        {"v": 1, "type": "unknown"},
    ],
)
def test_invalid_control(value):
    with pytest.raises(ProtocolError):
        parse_control(json.dumps(value))


def test_protocol_limits_and_json():
    assert parse_control('{"v":1,"type":"hello"}')["v"] == 1
    for raw in ("{", "é" * MAX_CONTROL_BYTES, "[" * 2000):
        with pytest.raises(ProtocolError):
            parse_control(raw)


def test_pattern_colors_motion_and_memory():
    first, second = pattern(0), pattern(1)
    assert first.shape == (480, 640, 3)
    assert first.dtype == np.uint8 and first.flags.c_contiguous
    assert tuple(first[0, 0]) == (255, 255, 255)
    assert tuple(first[0, 480]) == (0, 0, 255)
    assert not np.array_equal(first, second)
    assert not np.shares_memory(first, second)
    assert np.all(neutral() == 24)
    with pytest.raises(ValueError):
        pattern(0, 1, 1)


def test_querycap_rejects_physical_camera_and_closes(monkeypatch):
    monkeypatch.setattr(v4l2.os, "stat", lambda _: SimpleNamespace(st_mode=stat.S_IFCHR))
    monkeypatch.setattr(v4l2.os, "open", lambda *_: 42)
    closed = []
    monkeypatch.setattr(v4l2.os, "close", closed.append)

    def ioctl(fd, request, data, mutate):
        data[:] = v4l2.CAPABILITY.pack(b"uvcvideo", b"Physical", b"", *([0] * 6))

    monkeypatch.setattr(v4l2.fcntl, "ioctl", ioctl)
    with pytest.raises(ValueError, match="físicas"):
        v4l2.inspect_device("/dev/video99")
    assert closed == [42]


def test_querycap_accepts_loopback(monkeypatch):
    monkeypatch.setattr(v4l2.os, "stat", lambda _: SimpleNamespace(st_mode=stat.S_IFCHR))
    monkeypatch.setattr(v4l2.os, "open", lambda *_: 42)
    monkeypatch.setattr(v4l2.os, "close", lambda _: None)
    monkeypatch.setattr(v4l2.os, "access", lambda *_: True)

    def ioctl(fd, request, data, mutate):
        data[:] = v4l2.CAPABILITY.pack(b"v4l2 loopback", b"NexoCam", b"", *([0] * 6))

    monkeypatch.setattr(v4l2.fcntl, "ioctl", ioctl)
    assert v4l2.inspect_device("/dev/video99").label == "NexoCam"


def test_virtual_camera_closes_on_failure(monkeypatch):
    import pyvirtualcam

    camera = MagicMock()
    monkeypatch.setattr(pyvirtualcam, "Camera", lambda **kwargs: camera)
    monkeypatch.setattr(virtual_camera, "inspect_device", lambda _: SimpleNamespace(writable=True))
    with pytest.raises(ValueError), virtual_camera.VirtualCameraManager("/dev/video99") as manager:
        manager.send(np.zeros((1, 1, 3), dtype=np.uint8))
    camera.close.assert_called_once()


def test_stream_cancel_neutral_and_cleanup(monkeypatch):
    stop = Event()
    output = []

    class Camera:
        closed = False

        def __init__(self, device):
            pass

        def __enter__(self):
            return self

        def send(self, frame):
            output.append(frame)

        def __exit__(self, *_):
            Camera.closed = True

    monkeypatch.setattr(stream, "VirtualCameraManager", Camera)
    stream.run_pattern(stop, "/dev/video99", lambda *_: stop.set())
    assert len(output) == 2
    assert np.array_equal(output[-1], neutral())
    assert Camera.closed


def test_no_output_after_cancel():
    stop = Event()
    stop.set()
    output = []
    stream.run_pattern(stop, publish=lambda *args: output.append(args))
    assert output == []
