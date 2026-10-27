"""Identidade TLS local; chaves nunca entram no repositório ou nos logs."""

import os
import ssl
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def private_write(path: Path, data: bytes):
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Identity:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)
        self.cert_path, self.key_path = directory / "identity.pem", directory / "identity.key"
        if not self.cert_path.exists() and not self.key_path.exists():
            key = ec.generate_private_key(ec.SECP256R1())
            now = datetime.now(UTC)
            subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "nexocam.local")])
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(minutes=5))
                .not_valid_after(now + timedelta(days=365))
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("nexocam.local")]), False)
                .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
                .sign(key, hashes.SHA256())
            )
            private_write(
                self.key_path,
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ),
            )
            private_write(self.cert_path, cert.public_bytes(serialization.Encoding.PEM))
        if not self.cert_path.exists() or not self.key_path.exists():
            raise ValueError("Identidade TLS incompleta. Restaure certificado e chave juntos.")
        self.key_path.chmod(0o600)
        self.cert_path.chmod(0o600)
        self.cert = x509.load_pem_x509_certificate(self.cert_path.read_bytes())
        if self.cert.not_valid_after_utc <= datetime.now(UTC):
            raise ValueError(
                "Certificado local expirou. Renove a identidade e refaça o pareamento."
            )
        self.fingerprint = self.cert.fingerprint(hashes.SHA256()).hex()

    def server_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(self.cert_path, self.key_path)
        return context


def default_identity() -> Identity:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return Identity(base / "nexocam" / "identity")
