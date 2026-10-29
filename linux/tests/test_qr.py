import json

import cv2
import pytest

from nexocam.security.qr import PREFIX, payload, pixels


@pytest.mark.parametrize("box_size", [4, 5])
def test_qr_can_be_decoded_and_contains_only_pairing_fields(box_size):
    value = payload("192.0.2.10", "a" * 64, "b" * 64)
    image = pixels(value, box_size=box_size)
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
    assert decoded == value
    data = json.loads(decoded.removeprefix(PREFIX))
    assert data == {
        "v": 1,
        "host": "192.0.2.10",
        "port": 8765,
        "fingerprint": "a" * 64,
        "token": "b" * 64,
    }


@pytest.mark.parametrize(
    "host,pin,token,port",
    [
        ("invalid", "a" * 64, "b" * 64, 8765),
        ("192.0.2.10", "short", "b" * 64, 8765),
        ("192.0.2.10", "a" * 64, "invalid", 8765),
        ("192.0.2.10", "a" * 64, "b" * 64, 0),
    ],
)
def test_invalid_pairing_not_encoded(host, pin, token, port):
    with pytest.raises(ValueError):
        payload(host, pin, token, port)
