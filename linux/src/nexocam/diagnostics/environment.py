import importlib.util
import json
import platform
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

from nexocam.devices.v4l2 import discover


def report() -> dict:
    devices, errors = discover()
    modinfo = shutil.which("modinfo")
    available = False
    if modinfo:
        try:
            available = (
                subprocess.run(
                    [modinfo, "v4l2loopback"], capture_output=True, timeout=5, check=False
                ).returncode
                == 0
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {
        "python": platform.python_version(),
        "kernel": platform.release(),
        "distribution": platform.freedesktop_os_release().get("PRETTY_NAME", "Linux"),
        "module_available": available,
        "module_loaded": Path("/sys/module/v4l2loopback").exists(),
        "adb": shutil.which("adb") is not None,
        "dependencies": {
            name: importlib.util.find_spec(name) is not None
            for name in ("numpy", "PySide6", "pyvirtualcam")
        },
        "devices": [asdict(d) for d in devices],
        "device_errors": errors,
        "ready": any(d.writable for d in devices),
    }


def main():
    result = report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] else 1
