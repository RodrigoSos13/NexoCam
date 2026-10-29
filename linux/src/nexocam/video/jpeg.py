"""Inspeção do cabeçalho JPEG antes de alocar a imagem decodificada."""

import struct

import cv2
import numpy as np

from nexocam.network.protocol import MAX_FRAME_BYTES, ProtocolError

HEADER = struct.Struct("!4sBQQ")
SOF = {0xC0, 0xC1, 0xC2}


def jpeg_size(data: bytes) -> tuple[int, int]:
    if not data.startswith(b"\xff\xd8"):
        raise ProtocolError("Quadro não é JPEG.")
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            break
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9, 0xDA, 0x00}:
            break
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in SOF:
            if length < 8 or data[offset + 2] != 8:
                break
            height, width = struct.unpack("!HH", data[offset + 3 : offset + 7])
            return width, height
        offset += length
    raise ProtocolError("Cabeçalho JPEG inválido ou não suportado.")


def unpack_frame(data: bytes, previous: int, allowed_sizes=((640, 480),)) -> tuple[int, bytes]:
    if not HEADER.size < len(data) <= MAX_FRAME_BYTES:
        raise ProtocolError("Tamanho de quadro inválido.")
    magic, version, sequence, _timestamp = HEADER.unpack_from(data)
    if magic != b"NXCF" or version != 1:
        raise ProtocolError("Cabeçalho de quadro incompatível.")
    if sequence <= previous:
        raise ProtocolError("Sequência de quadro inválida.")
    jpeg = data[HEADER.size :]
    if jpeg_size(jpeg) not in allowed_sizes:
        raise ProtocolError("Dimensões do quadro não negociadas.")
    return sequence, jpeg


def decode(jpeg: bytes, allowed_sizes=((640, 480),)) -> np.ndarray:
    if jpeg_size(jpeg) not in allowed_sizes:
        raise ProtocolError("Dimensões JPEG incompatíveis.")
    try:
        image = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise ProtocolError("JPEG rejeitado pelo decodificador.") from exc
    if (
        image is None
        or (image.shape[1], image.shape[0]) not in allowed_sizes
        or image.shape[2] != 3
    ):
        raise ProtocolError("Não foi possível decodificar o JPEG.")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
