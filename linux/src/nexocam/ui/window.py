import asyncio
import json
import sys
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from nexocam.diagnostics.environment import report
from nexocam.network.server import StreamServer
from nexocam.security.identity import default_identity
from nexocam.ui.theme import STYLESHEET
from nexocam.video.stream import run_pattern


class Worker(QThread):
    failed = Signal(str)
    diagnostic = Signal(object)
    status_changed = Signal(str)
    pairing_ready = Signal(str, str, int)
    pairing_confirmed = Signal()

    def __init__(self, device=None, diagnostics=False, receive=False):
        super().__init__()
        self.stop = Event()
        self.portrait = Event()
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
                    paired=self.pairing_confirmed.emit,
                    portrait=self.portrait.is_set,
                )
                asyncio.run(server.run(self.stop))
            else:
                run_pattern(self.stop, self.device, self.publish)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(f"Não foi possível concluir a operação: {exc}")


def label(text, name="muted"):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


def app_icon():
    for path in (
        Path(__file__).resolve().parents[3] / "resources/nexocam.svg",
        Path(sys.prefix) / "share/icons/hicolor/scalable/apps/nexocam.svg",
    ):
        if path.exists():
            return QIcon(str(path))
    return QIcon.fromTheme("camera-web")


class VideoPreview(QLabel):
    """Redimensiona só a apresentação, preservando os pixels usados na saída V4L2."""

    def __init__(self):
        super().__init__()
        self.source = None
        self.setObjectName("preview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)

    def setPixmap(self, pixmap):
        self.source = pixmap
        self.render_frame()

    def setText(self, text):
        self.source = None
        super().setText(text)

    def render_frame(self):
        if self.source is not None:
            super().setPixmap(
                self.source.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_frame()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexoCam")
        self.resize(1160, 760)
        self.setMinimumSize(900, 600)
        self.setWindowIcon(app_icon())
        self.setStyleSheet(STYLESHEET)
        self.worker = None
        self.checker = None
        self.closing = False
        self.show_report = False
        self.report_dialog = None
        self.status = label("Inicie uma sessão para conectar seu Android.", "statusText")
        self.status.setWordWrap(True)
        self.preview = VideoPreview()
        self.preview.setText(
            "Sua câmera começa aqui.\n\nInicie uma sessão e escaneie o QR Code no Android."
        )
        self.devices = QComboBox()
        self.devices.addItem("Somente prévia", None)
        self.devices.setToolTip(
            "Selecione uma webcam virtual para disponibilizar vídeo no OBS e em outros aplicativos."
        )
        self.mode = QComboBox()
        self.mode.addItem("Receber do Android", True)
        self.mode.addItem("Teste de imagem", False)
        self.orientation = QComboBox()
        self.orientation.addItem("Horizontal", False)
        self.orientation.addItem("Vertical", True)
        self.orientation.setToolTip(
            "Troca ao vivo. Na webcam virtual 640×480, o vídeo vertical tem barras laterais."
        )
        self.orientation.currentIndexChanged.connect(self.update_orientation)
        self.mode.currentIndexChanged.connect(
            lambda: self.orientation.setEnabled(bool(self.mode.currentData()))
        )
        self.start = QPushButton("Iniciar sessão")
        self.start.setObjectName("primary")
        self.start.clicked.connect(self.begin)
        self.stop = QPushButton("Encerrar sessão")
        self.stop.setObjectName("stop")
        self.stop.setEnabled(False)
        self.stop.setVisible(False)
        self.stop.clicked.connect(self.end)
        self.diagnostics = QPushButton("Diagnósticos")
        self.diagnostics.setObjectName("ghost")
        self.diagnostics.clicked.connect(lambda: self.check(show_report=True))
        self.pairing_info = None
        self.pairing_button = QPushButton("Conectar celular · QR Code")
        self.pairing_button.setEnabled(False)
        self.pairing_button.clicked.connect(self.show_pairing)
        self.metrics = label("FPS de saída · aguardando sessão")
        self.fps_value = label("—", "statValue")
        self.frames_value = label("0", "statValue")
        self.device_hint = label("Escolha uma saída para usar no OBS.")
        self.device_hint.setWordWrap(True)
        self.devices.currentIndexChanged.connect(self.update_output_hint)
        self.badge = label("Pronto para iniciar", "stateBadge")
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 18)
        layout.setSpacing(22)
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(42, 42))
        header.addWidget(logo)
        brand = QVBoxLayout()
        brand.setSpacing(1)
        brand.addWidget(label("NexoCam", "brand"))
        brand.addWidget(label("Seu Android. Sua webcam.", "subtitle"))
        header.addLayout(brand)
        header.addStretch()
        header.addWidget(self.badge)
        header.addSpacing(12)
        header.addWidget(self.diagnostics)
        layout.addLayout(header)
        content = QHBoxLayout()
        content.setSpacing(20)
        video_card = QFrame()
        video_card.setObjectName("videoCard")
        video_layout = QVBoxLayout(video_card)
        video_layout.setContentsMargins(18, 18, 18, 18)
        video_layout.setSpacing(14)
        video_header = QHBoxLayout()
        video_header.addWidget(label("Prévia da câmera", "sectionTitle"))
        video_header.addStretch()
        self.frame_format = label("640 × 480", "eyebrow")
        video_header.addWidget(self.frame_format)
        video_layout.addLayout(video_header)
        video_layout.addWidget(self.preview, 1)
        stats = QHBoxLayout()
        for title, value in (
            ("RESOLUÇÃO DE SAÍDA", label("640 × 480", "statValue")),
            ("FPS DE SAÍDA", self.fps_value),
            ("QUADROS DE SAÍDA", self.frames_value),
        ):
            stat = QVBoxLayout()
            stat.setSpacing(4)
            stat.addWidget(label(title, "eyebrow"))
            stat.addWidget(value)
            stats.addLayout(stat, 1)
        video_layout.addLayout(stats)
        video_layout.addWidget(self.metrics)
        content.addWidget(video_card, 1)
        panel = QFrame()
        panel.setObjectName("panel")
        controls = QVBoxLayout(panel)
        controls.setContentsMargins(22, 22, 22, 22)
        controls.setSpacing(12)
        controls.addWidget(label("Conexão", "sectionTitle"))
        controls.addWidget(label("Origem do vídeo", "eyebrow"))
        controls.addWidget(self.mode)
        controls.addWidget(label("Saída de vídeo", "eyebrow"))
        controls.addWidget(self.devices)
        controls.addWidget(self.device_hint)
        controls.addWidget(label("Formato", "eyebrow"))
        controls.addWidget(self.orientation)
        controls.addSpacing(8)
        controls.addWidget(self.start)
        controls.addWidget(self.stop)
        controls.addWidget(self.pairing_button)
        controls.addStretch()
        status_card = QFrame()
        status_card.setObjectName("statusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(14, 14, 14, 14)
        status_layout.addWidget(label("ESTADO DA SESSÃO", "eyebrow"))
        status_layout.addWidget(self.status)
        controls.addWidget(status_card)
        side = QScrollArea()
        side.setWidgetResizable(True)
        side.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.setMinimumWidth(310)
        side.setMaximumWidth(340)
        side.setWidget(panel)
        content.addWidget(side)
        layout.addLayout(content, 1)
        footer = QHBoxLayout()

        footer.addStretch()
        self.setToolTip("Minimizar mantém a sessão ativa. Fechar encerra a transmissão.")
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

    def update_orientation(self):
        if self.worker:
            if self.orientation.currentData():
                self.worker.portrait.set()
            else:
                self.worker.portrait.clear()

    def update_output_hint(self):
        self.device_hint.setText("Para usar no OBS, selecione uma webcam virtual.")
        self.device_hint.setVisible(self.devices.currentData() is None)

    def set_badge(self, text, state="idle"):
        self.badge.setText(text)
        self.badge.setProperty("state", state)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

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
        selected = self.devices.currentData()
        self.devices.clear()
        self.devices.addItem("Somente prévia", None)
        for device in result["devices"]:
            if device["writable"]:
                self.devices.addItem(f"{device['label']} ({device['path']})", device["path"])
        index = self.devices.findData(selected)
        if index >= 0:
            self.devices.setCurrentIndex(index)
        self.update_output_hint()
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
        self.update_orientation()
        self.worker.status_changed.connect(self.status.setText)
        self.worker.pairing_ready.connect(self.paired)
        self.worker.pairing_confirmed.connect(self.close_pairing)
        self.mode.setEnabled(False)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.finished)
        self.start.setEnabled(False)
        self.start.setVisible(False)
        self.stop.setVisible(True)
        self.devices.setEnabled(False)
        self.stop.setEnabled(True)
        self.diagnostics.setEnabled(False)
        self.status.setText(
            "Preparando servidor TLS..."
            if receiving
            else "Teste sintético em execução" + (" • webcam virtual" if device else " • prévia")
        )
        self.set_badge("Sessão em execução", "active")
        self.worker.start()

    def paired(self, fingerprint, token, port):
        self.pairing_info = (fingerprint, token, port)
        self.pairing_button.setEnabled(True)
        self.show_pairing()

    def close_pairing(self):
        if self.report_dialog and self.report_dialog.windowTitle() == "Pareamento local seguro":
            self.report_dialog.close()

    def show_pairing(self):
        if not self.pairing_info or self.closing:
            return
        from PySide6.QtWidgets import QDialog

        if self.report_dialog:
            self.report_dialog.close()
        fingerprint, token, port = self.pairing_info
        dialog = QDialog(self)
        dialog.setWindowTitle("Pareamento local seguro")
        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        scroll.setWidget(body)
        outer.addWidget(scroll)
        dialog.setMinimumWidth(370)
        dialog.resize(390, min(740, self.screen().availableGeometry().height() - 60))
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(label("CONECTAR DISPOSITIVO", "eyebrow"))
        layout.addWidget(label("Conecte seu Android", "sectionTitle"))
        instructions = label(
            "No NexoCam Android, toque em Escanear QR Code.\n"
            "A conexão de vídeo começa quando você confirmar no celular."
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
        layout.addWidget(label("REDE DO COMPUTADOR", "eyebrow"))
        address_picker = QComboBox()
        for name, address in addresses:
            address_picker.addItem(f"{name} — {address}", address)
        layout.addWidget(address_picker)
        qr_label = QLabel()
        qr_label.setObjectName("qr")
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
            data = pixels(payload(host, fingerprint, token, port), box_size=4)
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
        security_note = label(
            "Válido por 5 minutos para novas conexões.\nEste código contém seu segredo de acesso; não compartilhe."
        )
        security_note.setWordWrap(True)
        layout.addWidget(security_note)
        toggle = QPushButton("Preencher manualmente")
        toggle.setObjectName("ghost")
        toggle.clicked.connect(lambda: manual.setVisible(not manual.isVisible()))
        layout.addWidget(toggle)
        layout.addWidget(manual)
        for field_label, value in (
            ("Impressão digital TLS", fingerprint),
            ("Segredo temporário", token),
        ):
            manual_layout.addWidget(QLabel(field_label))
            field = QLineEdit(value)
            field.setReadOnly(True)
            field.setMinimumWidth(260)
            manual_layout.addWidget(field)
        done = QPushButton("Concluir")
        done.setObjectName("primary")
        done.clicked.connect(dialog.close)
        layout.addWidget(done)
        self.report_dialog = dialog
        dialog.show()

    def end(self):
        if self.worker:
            self.worker.stop.set()
            self.stop.setEnabled(False)
            self.status.setText("Encerrando e liberando a webcam...")
            self.set_badge("Encerrando")

    def finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.mode.setEnabled(True)
        self.pairing_info = None
        self.pairing_button.setEnabled(False)
        if self.report_dialog:
            self.report_dialog.close()
            self.report_dialog = None
        self.preview.setText(
            "Sessão encerrada.\n\nSua câmera estará aqui quando você conectar novamente."
        )
        self.fps_value.setText("—")
        self.metrics.setText("Saída de vídeo interrompida")
        if self.badge.property("state") != "error":
            self.set_badge("Pronto para iniciar")
            self.status.setText("Sessão encerrada. Você pode iniciar uma nova conexão.")
        self.start.setEnabled(True)
        self.start.setVisible(True)
        self.stop.setVisible(False)
        self.devices.setEnabled(True)
        self.diagnostics.setEnabled(self.checker is None)
        self.stop.setEnabled(False)
        if self.closing:
            self.close()

    def error(self, message):
        self.status.setText(message)
        self.set_badge("Atenção", "error")

    def refresh(self):
        value = self.worker.take() if self.worker else None
        if value is None:
            return
        frame, count, fps = value
        height, width = frame.shape[:2]
        image = QImage(
            frame.data, width, height, frame.strides[0], QImage.Format.Format_RGB888
        ).copy()
        self.frame_format.setText(f"{width} × {height}")
        self.preview.setPixmap(QPixmap.fromImage(image))
        self.fps_value.setText(f"{fps:.1f}")
        self.frames_value.setText(f"{count:,}".replace(",", "."))
        self.metrics.setText("Saída · meta de 15 FPS")

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
    window = Window()
    window.show()
    return app.exec()
