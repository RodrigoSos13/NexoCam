import time
from contextlib import nullcontext

from nexocam.video.pattern import neutral, pattern
from nexocam.video.virtual_camera import VirtualCameraManager


def run_pattern(stop, device=None, publish=lambda frame, count, fps: None, duration=None):
    """Não enfileira quadros: produz no máximo um por tick, sem recuperar ticks perdidos."""
    fps = 15
    context = VirtualCameraManager(device) if device else nullcontext(None)
    with context as camera:
        started = time.monotonic()
        count = 0
        try:
            while not stop.is_set():
                tick = time.monotonic()
                if duration is not None and tick - started >= duration:
                    break
                frame = pattern(count)
                if camera:
                    camera.send(frame)
                count += 1
                publish(frame, count, count / max(time.monotonic() - started, 1 / fps))
                stop.wait(max(0, 1 / fps - (time.monotonic() - tick)))
        finally:
            if camera:
                camera.send(neutral())
