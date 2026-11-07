"""ADB Reverse USB, sem alterar encaminhamentos criados por outros aplicativos."""

import os
import shutil
import subprocess
from pathlib import Path


class UsbError(RuntimeError):
    pass


def find_adb():
    executable = shutil.which("adb")
    if executable:
        return executable
    roots = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT")]
    roots.append(Path(__file__).resolve().parents[4] / ".tools/sdk")
    for root in roots:
        if root:
            candidate = Path(root) / "platform-tools/adb"
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    raise UsbError("ADB não encontrado. Instale Android Platform Tools para usar o cabo USB.")


class UsbTunnel:
    def __init__(self, port=8765, adb=None):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Porta USB inválida.")
        self.adb = adb or find_adb()
        self.port = port
        self.serial = None
        self.owned = False

    def command(self, *arguments):
        try:
            result = subprocess.run(
                [self.adb, *arguments], capture_output=True, text=True, timeout=8, check=False
            )
        except subprocess.TimeoutExpired:
            raise UsbError(
                "O celular não respondeu ao ADB. Confira o cabo e tente novamente."
            ) from None
        except OSError:
            raise UsbError("Não foi possível executar o ADB. Confira sua instalação.") from None
        if result.returncode:
            error = result.stderr.lower()
            if "unauthorized" in error:
                message = "Desbloqueie o celular e autorize a depuração USB para este computador."
            elif "more than one" in error:
                message = "Conecte somente um celular USB para configurar a transmissão."
            elif "no permissions" in error or "insufficient permissions" in error:
                message = "Sem permissão USB. Configure as regras udev do Android no Linux."
            elif "no devices" in error or "device not found" in error:
                message = (
                    "Conecte um cabo de dados e ative a depuração USB nas opções do desenvolvedor."
                )
            elif "offline" in error:
                message = "Celular offline no ADB. Reconecte o cabo e desbloqueie o aparelho."
            else:
                message = "Falha ao configurar o USB. Confira a autorização, o cabo e a porta 8765."
            raise UsbError(message)
        return result.stdout.strip()

    def mappings(self):
        return [
            line.split()[-2:]
            for line in self.command("-s", self.serial, "reverse", "--list").splitlines()
            if len(line.split()) >= 2
        ]

    def connect(self):
        # -d seleciona exclusivamente USB, mesmo quando há ADB por Wi-Fi ativo.
        serial = self.command("-d", "get-serialno")
        if not serial or serial == "unknown":
            raise UsbError("Conecte e autorize um celular por cabo USB.")
        if self.serial and serial != self.serial:
            raise UsbError("Encerre a sessão antes de trocar o celular conectado por USB.")
        self.serial = serial
        if self.command("-s", serial, "get-state") != "device":
            raise UsbError("Desbloqueie o celular e confira a autorização de depuração USB.")
        remote, local = "tcp:8765", f"tcp:{self.port}"
        mappings = self.mappings()
        current = next((item for item in mappings if item[0] == remote), None)
        if current:
            if current != [remote, local]:
                raise UsbError(
                    "A porta USB 8765 já está encaminhada para outro serviço. Nada foi alterado."
                )
            return
        self.command("-s", serial, "reverse", "--no-rebind", remote, local)
        self.owned = True

    def close(self):
        if not self.owned:
            return
        try:
            # Não remove um encaminhamento que tenha sido substituído por outro programa.
            if ["tcp:8765", f"tcp:{self.port}"] in self.mappings():
                self.command("-s", self.serial, "reverse", "--remove", "tcp:8765")
        except UsbError:
            pass  # Desconectar o cabo também descarta os encaminhamentos no Android.
        finally:
            self.owned = False
