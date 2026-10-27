"""Detecta o driver por VIDIOC_QUERYCAP, nunca pelo nome da câmera."""

import fcntl
import os
import stat
import struct
from dataclasses import dataclass
from pathlib import Path

QUERYCAP = 0x80685600
CAPABILITY = struct.Struct("16s32s32s6I")


@dataclass(frozen=True)
class Device:
    path: str
    label: str
    driver: str
    writable: bool


def inspect_device(path: str) -> Device:
    if not stat.S_ISCHR(os.stat(path).st_mode):
        raise ValueError("O caminho não é um dispositivo de vídeo.")
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        data = bytearray(CAPABILITY.size)
        fcntl.ioctl(fd, QUERYCAP, data, True)
        driver, label, *_ = CAPABILITY.unpack(data)
        driver = driver.split(b"\0", 1)[0].decode("ascii", errors="replace")
        if driver != "v4l2 loopback":
            raise ValueError(
                "Selecione um dispositivo v4l2loopback; câmeras físicas são recusadas."
            )
        return Device(
            path,
            label.split(b"\0", 1)[0].decode(errors="replace"),
            driver,
            os.access(path, os.R_OK | os.W_OK),
        )
    finally:
        os.close(fd)


def discover() -> tuple[list[Device], list[str]]:
    devices, errors = [], []
    for path in sorted(Path("/dev").glob("video*")):
        try:
            devices.append(inspect_device(str(path)))
        except ValueError:
            continue
        except OSError as exc:
            errors.append(f"{path}: não foi possível consultar o dispositivo ({exc.strerror}).")
    return devices, errors
