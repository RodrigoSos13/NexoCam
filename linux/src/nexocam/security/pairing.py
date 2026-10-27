import secrets
import time


class PairingManager:
    """Credencial efêmera em memória, válida por cinco minutos para novas conexões."""

    def __init__(self, lifetime=300):
        self.token = secrets.token_hex(32)
        self.deadline = time.monotonic() + lifetime

    def authenticate(self, token):
        return (
            isinstance(token, str)
            and len(token) == 64
            and time.monotonic() < self.deadline
            and secrets.compare_digest(token, self.token)
        )
