import numpy as np

from nexocam.devices.v4l2 import inspect_device


class VirtualCameraManager:
    """Um único proprietário; abrir, enviar e fechar sempre no mesmo worker."""

    def __init__(self, device: str, width: int = 640, height: int = 480, fps: int = 15):
        self.device, self.width, self.height, self.fps = device, width, height, fps
        self._camera = None

    def __enter__(self):
        import pyvirtualcam

        info = inspect_device(self.device)
        if not info.writable:
            raise PermissionError("Sem permissão de leitura/escrita na webcam virtual.")
        self._camera = pyvirtualcam.Camera(
            width=self.width,
            height=self.height,
            fps=self.fps,
            device=self.device,
            backend="v4l2loopback",
            fmt=pyvirtualcam.PixelFormat.RGB,
        )
        return self

    def send(self, frame: np.ndarray):
        if self._camera is None:
            raise RuntimeError("A webcam virtual não está aberta.")
        if frame.shape != (self.height, self.width, 3) or frame.dtype != np.uint8:
            raise ValueError("Quadro RGB incompatível com a configuração da webcam.")
        self._camera.send(np.ascontiguousarray(frame))

    def __exit__(self, *_):
        if self._camera is not None:
            try:
                self._camera.close()
            finally:
                self._camera = None
