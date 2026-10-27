import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

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
    window.begin()
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
    window.close()
    while window.checker is not None and monotonic() < deadline:
        app.processEvents()
        sleep(0.01)
    assert window.checker is None
    app.processEvents()

    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def test_ui_receiver_start_stop(app, tmp_path, monkeypatch):
    from time import monotonic, sleep

    from nexocam.security.identity import Identity
    from nexocam.ui import window as window_module

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
        assert window.pairing_button.isEnabled()
    finally:
        window.close()
        while (window.worker is not None or window.checker is not None) and monotonic() < deadline:
            app.processEvents()
            sleep(0.01)
        assert window.worker is None
        assert window.pairing_info is None
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
