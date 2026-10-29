"""Acomoda o quadro sem deformar ou reabrir a webcam virtual durante a sessão."""

import cv2
import numpy as np


def fit_output(frame, width=640, height=480):
    if frame.shape == (height, width, 3):
        return frame
    scale = min(width / frame.shape[1], height / frame.shape[0])
    w, h = round(frame.shape[1] * scale), round(frame.shape[0] * scale)
    resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
    output = np.zeros((height, width, 3), dtype=np.uint8)
    x, y = (width - w) // 2, (height - h) // 2
    output[y : y + h, x : x + w] = resized
    return output
