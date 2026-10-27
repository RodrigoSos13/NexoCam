"""Padrão RGB: barras conhecidas e marcador móvel; não acessa câmeras."""

import numpy as np


def pattern(index: int, width: int = 640, height: int = 480) -> np.ndarray:
    if width < 16 or height < 16:
        raise ValueError("Dimensões devem ser pelo menos 16×16.")
    colors = np.array(
        [
            (255, 255, 255),
            (255, 255, 0),
            (0, 255, 255),
            (0, 255, 0),
            (255, 0, 255),
            (255, 0, 0),
            (0, 0, 255),
            (0, 0, 0),
        ],
        dtype=np.uint8,
    )
    row = colors[np.arange(width) * 8 // width]
    frame = np.repeat(row[None, :, :], height, axis=0)
    frame[-height // 8 :] = 32
    x = (index * 7) % (width - 8)
    frame[-height // 8 :, x : x + 8] = 255
    return np.ascontiguousarray(frame)


def neutral(width: int = 640, height: int = 480) -> np.ndarray:
    return np.full((height, width, 3), 24, dtype=np.uint8)
