import subprocess

import pytest

from nexocam.network import usb


@pytest.fixture
def adb(monkeypatch):
    class FakeAdb:
        def __init__(self):
            self.mappings = []
            self.calls = []
            self.error = None

        def run(self, command, **kwargs):
            args = command[1:]
            self.calls.append(args)
            assert kwargs["timeout"] == 8
            if self.error:
                return subprocess.CompletedProcess(command, 1, "", self.error)
            output = ""
            if args == ["-d", "get-serialno"]:
                output = "PHONE"
            elif args == ["-s", "PHONE", "get-state"]:
                output = "device"
            elif args[-2:] == ["reverse", "--list"]:
                output = "\n".join("UsbFfs " + " ".join(item) for item in self.mappings)
            elif "--no-rebind" in args:
                self.mappings.append(args[-2:])
            elif "--remove" in args:
                self.mappings = [item for item in self.mappings if item[0] != args[-1]]
            return subprocess.CompletedProcess(command, 0, output, "")

    fake = FakeAdb()
    monkeypatch.setattr(usb.subprocess, "run", fake.run)
    return fake


def test_usb_creates_and_removes_only_owned_mapping(adb):
    adb.mappings = [["tcp:9000", "tcp:9001"]]
    tunnel = usb.UsbTunnel(port=43210, adb="adb")
    tunnel.connect()
    assert tunnel.owned
    assert ["-s", "PHONE", "reverse", "--no-rebind", "tcp:8765", "tcp:43210"] in adb.calls
    tunnel.close()
    assert adb.mappings == [["tcp:9000", "tcp:9001"]]
    assert not tunnel.owned
    assert all("--remove-all" not in call for call in adb.calls)


def test_existing_matching_mapping_is_borrowed(adb):
    adb.mappings = [["tcp:8765", "tcp:8765"]]
    tunnel = usb.UsbTunnel(adb="adb")
    tunnel.connect()
    assert not tunnel.owned
    tunnel.close()
    assert adb.mappings == [["tcp:8765", "tcp:8765"]]
    assert not any("--remove" in call or "--no-rebind" in call for call in adb.calls)


def test_conflicting_mapping_is_preserved(adb):
    adb.mappings = [["tcp:8765", "tcp:9999"]]
    tunnel = usb.UsbTunnel(adb="adb")
    with pytest.raises(usb.UsbError, match="outro serviço"):
        tunnel.connect()
    tunnel.close()
    assert adb.mappings == [["tcp:8765", "tcp:9999"]]


def test_replaced_mapping_is_not_removed(adb):
    tunnel = usb.UsbTunnel(adb="adb")
    tunnel.connect()
    adb.mappings = [["tcp:8765", "tcp:1234"]]
    tunnel.close()
    assert adb.mappings == [["tcp:8765", "tcp:1234"]]


def test_reconnect_restores_mapping_lost_when_unplugged(adb):
    tunnel = usb.UsbTunnel(adb="adb")
    tunnel.connect()
    adb.mappings = []
    tunnel.connect()
    assert adb.mappings == [["tcp:8765", "tcp:8765"]]
    tunnel.close()
    assert not adb.mappings


@pytest.mark.parametrize(
    "error, message",
    [
        ("error: device unauthorized", "autorize"),
        ("error: no devices/emulators found", "cabo de dados"),
        ("error: more than one device/emulator", "somente um celular"),
        ("error: device offline", "offline"),
        ("error: insufficient permissions for device", "udev"),
    ],
)
def test_actionable_errors(adb, error, message):
    adb.error = error
    with pytest.raises(usb.UsbError, match=message):
        usb.UsbTunnel(adb="adb").connect()
    assert not any("--no-rebind" in call for call in adb.calls)


def test_timeout_is_reported_without_exposing_command(monkeypatch):
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 8)

    monkeypatch.setattr(usb.subprocess, "run", timeout)
    with pytest.raises(usb.UsbError, match="não respondeu"):
        usb.UsbTunnel(adb="adb").connect()
