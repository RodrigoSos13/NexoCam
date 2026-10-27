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
