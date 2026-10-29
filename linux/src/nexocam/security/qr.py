"""QR de pareamento somente em memória; contém credencial temporária."""

import ipaddress
import json
import re

import numpy as np
import qrcode

PREFIX = "nexocam:pair:v1:"


def payload(host: str, fingerprint: str, token: str, port: int = 8765) -> str:
    ipaddress.IPv4Address(host)
    if not 1 <= port <= 65535 or not all(
        re.fullmatch("[0-9a-f]{64}", s) for s in (fingerprint, token)
    ):
        raise ValueError("Dados de pareamento inválidos.")
    return PREFIX + json.dumps(
        {"v": 1, "host": host, "port": port, "fingerprint": fingerprint, "token": token},
        separators=(",", ":"),
    )


def pixels(value: str) -> np.ndarray:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(value)
    qr.make(fit=True)
    matrix = np.asarray(qr.get_matrix(), dtype=np.uint8)
    return np.ascontiguousarray(np.repeat(np.repeat((1 - matrix) * 255, 5, axis=0), 5, axis=1))
