import asyncio
import json
import sys
from threading import Event, Lock

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from nexocam.diagnostics.environment import report
from nexocam.network.server import StreamServer
from nexocam.security.identity import default_identity
from nexocam.video.stream import run_pattern


class Worker(QThread):
    failed = Signal(str)
    diagnostic = Signal(object)
    status_changed = Signal(str)
    pairing_ready = Signal(str, str, int)

    def __init__(self, device=None, diagnostics=False, receive=False):
        super().__init__()
        self.stop = Event()
        self.device = device
        self.diagnostics = diagnostics
        self.receive = receive
        self.lock = Lock()
        self.latest = None

    def publish(self, frame, count, fps):
        with self.lock:
            self.latest = (frame, count, fps)

    def take(self):
        with self.lock:
            latest, self.latest = self.latest, None
            return latest

    def run(self):
        try:
            if self.diagnostics:
                self.diagnostic.emit(report())
            elif self.receive:
                server = StreamServer(
                    default_identity(),
                    self.device,
                    publish=self.publish,
                    status=self.status_changed.emit,
                    ready=self.pairing_ready.emit,
                )
                asyncio.run(server.run(self.stop))
            else:
                run_pattern(self.stop, self.device, self.publish)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(f"Não foi possível concluir a operação: {exc}")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexoCam")
        self.resize(900, 720)
        self.worker = None
        self.checker = None
        self.closing = False
        self.show_report = False
        self.report_dialog = None
        self.status = QLabel("NexoCam • receptor Android e teste local")
        self.preview = QLabel("Inicie a prévia para verificar a imagem.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(640, 480)
        self.devices = QComboBox()
        self.devices.addItem("Somente prévia — sem webcam virtual", None)
        self.mode = QComboBox()
        self.mode.addItem("Receber do Android • TLS / JPEG", True)
        self.mode.addItem("Teste sintético local", False)
        self.start = QPushButton("Iniciar")
        self.start.clicked.connect(self.begin)
        self.stop = QPushButton("Interromper")
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.end)
        self.diagnostics = QPushButton("Diagnósticos / atualizar dispositivos")
        self.diagnostics.clicked.connect(lambda: self.check(show_report=True))
        self.pairing_info = None
        self.pairing_button = QPushButton("Dados de pareamento")
        self.pairing_button.setEnabled(False)
        self.pairing_button.clicked.connect(self.show_pairing)
        self.metrics = QLabel("640 × 480 • meta: 15 FPS • RGB")
        title = QLabel("NexoCam")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #58d6c7")
        root = QWidget()
        layout = QVBoxLayout(root)
        for widget in (title, self.status, self.mode, self.preview, self.metrics, self.devices):
            layout.addWidget(widget)
        buttons = QHBoxLayout()
        for button in (self.start, self.stop, self.pairing_button, self.diagnostics):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.setCentralWidget(root)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(66)
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
            self.tray = QSystemTrayIcon(icon, self)
            menu = QMenu(self)
            show = QAction("Mostrar NexoCam", self)
            show.triggered.connect(self.showNormal)
            quit_action = QAction("Encerrar", self)
            quit_action.triggered.connect(self.close)
            menu.addAction(show)
            menu.addAction(quit_action)
            self.tray.setContextMenu(menu)
            self.tray.setToolTip("NexoCam")
            self.tray.show()
        QTimer.singleShot(0, self.check)

    def check(self, show_report=False):
        if self.checker is not None:
            return
        self.show_report = show_report
        self.diagnostics.setEnabled(False)
        self.checker = Worker(diagnostics=True)
        self.checker.diagnostic.connect(self.checked)
        self.checker.failed.connect(self.error)
        self.checker.finished.connect(self.checked_finished)
        self.checker.start()

    def checked(self, result):
        self.devices.clear()
        self.devices.addItem("Somente prévia — sem webcam virtual", None)
        for device in result["devices"]:
            if device["writable"]:
                self.devices.addItem(f"{device['label']} ({device['path']})", device["path"])
        self.diagnostics.setToolTip(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ready"] and self.worker is None:
            self.status.setText("Webcam virtual indisponível. A prévia local está disponível.")
        if self.show_report and not self.closing:
            message = (
                "Dispositivo virtual detectado. Selecione-o e inicie o teste."
                if result["ready"]
                else "Nenhuma webcam virtual com acesso foi encontrada. "
                "Consulte docs/installation-linux.md para preparar o módulo "
                "v4l2loopback e as permissões. A prévia não exige o driver."
            )
            self.report_dialog = QMessageBox(self)
            self.report_dialog.setWindowTitle("Diagnósticos NexoCam")
            self.report_dialog.setText(message)
            self.report_dialog.setDetailedText(json.dumps(result, ensure_ascii=False, indent=2))
            self.report_dialog.open()

    def checked_finished(self):
        self.checker.deleteLater()
        self.checker = None
        self.diagnostics.setEnabled(self.worker is None)
        if self.closing:
            self.close()

    def begin(self):
        if self.worker is not None:
            return
        device = self.devices.currentData()
        receiving = self.mode.currentData()
        self.worker = Worker(device, receive=receiving)
        self.worker.status_changed.connect(self.status.setText)
        self.worker.pairing_ready.connect(self.paired)
        self.mode.setEnabled(False)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.finished)
        self.start.setEnabled(False)
        self.devices.setEnabled(False)
        self.stop.setEnabled(True)
        self.diagnostics.setEnabled(False)
        self.status.setText(
            "Preparando servidor TLS..."
            if receiving
            else "Teste sintético em execução" + (" • webcam virtual" if device else " • prévia")
        )
        self.worker.start()

    def paired(self, fingerprint, token, port):
        self.pairing_info = (fingerprint, token, port)
        self.pairing_button.setEnabled(True)
        self.show_pairing()

    def show_pairing(self):
        if not self.pairing_info or self.closing:
            return
        from PySide6.QtWidgets import QDialog

        if self.report_dialog:
            self.report_dialog.close()
        fingerprint, token, port = self.pairing_info
        dialog = QDialog(self)
        dialog.setWindowTitle("Pareamento local seguro")
        layout = QVBoxLayout(dialog)
        instructions = QLabel(
            f"No Android, toque em Escanear QR Code e aponte para esta tela. Porta {port}.\n"
            "Use uma rede local confiável. O segredo vale 5 minutos para novas conexões.\n"
            "Para revogar ou gerar outro segredo, interrompa e reinicie o receptor.\n"
            "Não compartilhe fotos desta tela ou o segredo de pareamento."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        from PySide6.QtNetwork import QAbstractSocket, QNetworkInterface

        interfaces = [
            interface
            for interface in QNetworkInterface.allInterfaces()
            if interface.flags() & QNetworkInterface.InterfaceFlag.IsUp
            and not interface.flags() & QNetworkInterface.InterfaceFlag.IsLoopBack
        ]
        addresses = [
            (interface.humanReadableName(), entry.ip().toString())
            for interface in interfaces
            for entry in interface.addressEntries()
            if entry.ip().protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol
        ]
        # Wi-Fi/Ethernet primeiro; bridges/VPN continuam selecionáveis explicitamente.
        addresses.sort(
            key=lambda item: (item[0].startswith(("docker", "br-", "veth", "virbr")), item[0])
        )
        layout.addWidget(QLabel("Endereço da rede conectada ao celular:"))
        address_picker = QComboBox()
        for name, address in addresses:
            address_picker.addItem(f"{name} — {address}", address)
        layout.addWidget(address_picker)
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_label)
        from nexocam.security.qr import payload, pixels

        def update_qr():
            host = address_picker.currentData()
            if not host:
                qr_label.setText(
                    "Nenhum IPv4 ativo encontrado. Conecte o computador à rede e reabra o pareamento."
                )
                return
            data = pixels(payload(host, fingerprint, token, port))
            image = QImage(
                data.data,
                data.shape[1],
                data.shape[0],
                data.strides[0],
                QImage.Format.Format_Grayscale8,
            ).copy()
            qr_label.setPixmap(QPixmap.fromImage(image))

        address_picker.currentIndexChanged.connect(update_qr)
        update_qr()
        manual = QWidget()
        manual_layout = QVBoxLayout(manual)
        manual.setVisible(False)
        toggle = QPushButton("Mostrar / ocultar dados para preenchimento manual")
        toggle.clicked.connect(lambda: manual.setVisible(not manual.isVisible()))
        layout.addWidget(toggle)
        layout.addWidget(manual)
        for label, value in (
            ("Impressão digital TLS", fingerprint),
            ("Segredo temporário", token),
        ):
            manual_layout.addWidget(QLabel(label))
            field = QLineEdit(value)
            field.setReadOnly(True)
            field.setMinimumWidth(560)
            manual_layout.addWidget(field)
        done = QPushButton("Fechar")
        done.clicked.connect(dialog.close)
        layout.addWidget(done)
        self.report_dialog = dialog
        dialog.show()

    def end(self):
        if self.worker:
            self.worker.stop.set()
            self.stop.setEnabled(False)
            self.status.setText("Encerrando e liberando a webcam...")

    def finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.mode.setEnabled(True)
        self.pairing_info = None
        self.pairing_button.setEnabled(False)
        if self.report_dialog:
            self.report_dialog.close()
            self.report_dialog = None
        self.preview.setText("Transmissão interrompida.")
        self.start.setEnabled(True)
        self.devices.setEnabled(True)
        self.diagnostics.setEnabled(self.checker is None)
        self.stop.setEnabled(False)
        if self.closing:
            self.close()

    def error(self, message):
        self.status.setText(message)

    def refresh(self):
        value = self.worker.take() if self.worker else None
        if value is None:
            return
        frame, count, fps = value
        image = QImage(frame.data, 640, 480, frame.strides[0], QImage.Format.Format_RGB888).copy()
        self.preview.setPixmap(QPixmap.fromImage(image))
        self.metrics.setText(f"640 × 480 • {fps:.1f} FPS de saída • {count} quadros")

    def closeEvent(self, event: QCloseEvent):
        self.closing = True
        if self.worker or self.checker:
            self.end()
            event.ignore()
            return
        if self.tray:
            self.tray.hide()
        event.accept()


def launch():
    app = QApplication(sys.argv)
    app.setApplicationName("NexoCam")
    app.setStyle("Fusion")
    app.setStyleSheet(
        "QWidget { background: #171e29; color: #e8eef6; font-size: 14px; }"
        "QPushButton, QComboBox { padding: 10px; background: #29384b; }"
        "QPushButton:disabled { color: #8190a3; }"
    )
    window = Window()
    window.show()
    return app.exec()
