import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QPushButton, QWidget

from nexocam.ui.window import Window, Worker


def test_mailbox_replaces_old_frame():
    worker = Worker()
    worker.publish("old", 1, 15)
    worker.publish("new", 2, 15)
    assert worker.take() == ("new", 2, 15)
    assert worker.take() is None


@pytest.fixture(scope="session")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    instance.processEvents()


def test_ui_preview_start_stop(app):
    window = Window()
    window.show()
    window.mode.setCurrentIndex(1)
    assert window.output_resolution.text() == "—"
    window.begin()
    assert window.output_resolution.text() == "640 × 480"
    from time import monotonic, sleep

    deadline = monotonic() + 5
    while monotonic() < deadline:
        app.processEvents()
        if window.worker and window.worker.latest is not None:
            window.refresh()
            break
        sleep(0.01)
    assert window.preview.pixmap() is not None
    window.end()
    while window.worker is not None and monotonic() < deadline:
        app.processEvents()
        sleep(0.01)
    assert window.worker is None
    assert window.output_resolution.text() == "—"
    window.close()
    while window.checker is not None and monotonic() < deadline:
        app.processEvents()
        sleep(0.01)
    assert window.checker is None
    app.processEvents()

    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


@pytest.mark.parametrize("usb_error", [False, True])
def test_ui_receiver_start_stop(app, tmp_path, monkeypatch, usb_error):
    from time import monotonic, sleep

    from nexocam.security.identity import Identity
    from nexocam.ui import window as window_module

    class FakeTunnel:
        connected = False
        closed = False
        attempts = 0

        def __init__(self, port):
            assert port > 0

        def connect(self):
            FakeTunnel.attempts += 1
            if usb_error and FakeTunnel.attempts == 1:
                raise window_module.UsbError("Autorize a depuração USB no celular.")
            FakeTunnel.connected = True

        def close(self):
            FakeTunnel.closed = True

    monkeypatch.setattr(window_module, "UsbTunnel", FakeTunnel)
    from nexocam.security import qr

    qr_hosts = []
    original_payload = qr.payload

    def capture_payload(host, *args):
        qr_hosts.append(host)
        return original_payload(host, *args)

    monkeypatch.setattr(qr, "payload", capture_payload)
    firewall_calls = []
    original_which = window_module.shutil.which
    monkeypatch.setattr(
        window_module.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in ("ufw", "pkexec") else original_which(name),
    )
    monkeypatch.setattr(
        window_module.QProcess,
        "start",
        lambda self, program, arguments: firewall_calls.append((program, arguments)),
    )
    monkeypatch.setattr(window_module, "default_identity", lambda: Identity(tmp_path / "identity"))
    # Porta efêmera evita depender de uma instância do usuário já aberta em 8765.
    original = window_module.StreamServer
    monkeypatch.setattr(
        window_module,
        "StreamServer",
        lambda *args, **kwargs: original(*args, **kwargs, host="127.0.0.1", port=0),
    )
    window = Window()
    window.show()
    window.begin()
    deadline = monotonic() + 5
    try:
        while window.pairing_info is None and monotonic() < deadline:
            app.processEvents()
            sleep(0.01)
        assert window.pairing_info is not None
        assert window.output_resolution.text() == "1920 × 1080"
        assert window.pairing_button.isEnabled()
        assert window.report_dialog.isVisible()
        assert not window.findChild(QWidget, "advancedSettings").isVisible()
        assert not window.findChild(QWidget, "videoStats").isVisible()
        assert firewall_calls == []
        transport = window.report_dialog.findChild(QComboBox, "pairingTransport")
        assert transport.currentData() is True
        while window.usb_busy and monotonic() < deadline:
            app.processEvents()
            sleep(0.01)
        if usb_error:
            assert not window.usb_active
            assert "Autorize" in window.usb_message
            assert not qr_hosts
            usb_button = next(
                button
                for button in window.report_dialog.findChildren(QPushButton)
                if button.text() == "Verificar cabo novamente"
            )
            usb_button.click()
            while not window.usb_active and monotonic() < deadline:
                app.processEvents()
                sleep(0.01)
        assert window.usb_active
        assert FakeTunnel.connected
        assert qr_hosts[-1] == "127.0.0.1"
        qr_widget = window.report_dialog.findChild(QLabel, "qr")
        qr_image = qr_widget.grab().toImage()
        assert any(
            qr_image.pixelColor(x, y).lightness() < 32
            for y in range(24, qr_image.height() - 24, 4)
            for x in range(24, qr_image.width() - 24, 4)
        )  # O QR deve estar desenhado, não apenas uma área branca.
        transport = window.report_dialog.findChild(QComboBox, "pairingTransport")
        transport.setCurrentIndex(transport.findData(False))
        firewall_button = next(
            button
            for button in window.report_dialog.findChildren(QPushButton)
            if button.text() == "Liberar acesso no firewall…"
        )
        assert not firewall_button.isVisible()
        wifi_help = next(
            button
            for button in window.report_dialog.findChildren(QPushButton)
            if button.text() == "Problemas com o Wi-Fi?"
        )
        wifi_help.click()
        assert firewall_button.isVisible()
        if firewall_button.isEnabled():
            firewall_button.click()
            assert len(firewall_calls) == 1
            program, arguments = firewall_calls[0]
            assert program == "/usr/bin/pkexec"
            assert arguments[:2] == ["/usr/bin/ufw", "allow"]
            assert "/" in arguments[arguments.index("from") + 1]
        transport = window.report_dialog.findChild(QComboBox, "pairingTransport")
        transport.setCurrentIndex(transport.findData(True))
        assert not firewall_button.isVisible()
        assert qr_hosts[-1] == "127.0.0.1"
        window.worker.pairing_confirmed.emit()
        app.processEvents()
        assert not window.report_dialog.isVisible()
        window.show_pairing()
        assert window.report_dialog.isVisible()
        assert window.report_dialog.findChild(QComboBox, "pairingTransport").currentData() is True
        transport = window.report_dialog.findChild(QComboBox, "pairingTransport")
        transport.setCurrentIndex(transport.findData(False))
        window.show_pairing()
        assert window.report_dialog.findChild(QComboBox, "pairingTransport").currentData() is False
    finally:
        window.close()
        while (window.worker is not None or window.checker is not None) and monotonic() < deadline:
            app.processEvents()
            sleep(0.01)
        assert window.worker is None
        assert FakeTunnel.closed
        assert window.pairing_info is None
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
