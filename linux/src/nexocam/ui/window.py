import asyncio
import json
import shutil
import sys
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import QProcess, Qt, QThread, QTimer, Signal
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
from nexocam.network.usb import UsbError, UsbTunnel
from nexocam.security.identity import default_identity
from nexocam.ui.theme import STYLESHEET
from nexocam.video.stream import run_pattern


class Worker(QThread):
    failed = Signal(str)
    diagnostic = Signal(object)
    status_changed = Signal(str)
    pairing_ready = Signal(str, str, int)
    pairing_confirmed = Signal()
    usb_result = Signal(bool, str)

    def __init__(
        self,
        device=None,
        diagnostics=False,
        receive=False,
        video_size=(1920, 1080),
        quality=90,
        adaptive=True,
    ):
        super().__init__()
        self.stop = Event()
        self.portrait = Event()
        self.device = device
        self.diagnostics = diagnostics
        self.receive = receive
        self.video_size, self.quality, self.adaptive = video_size, quality, adaptive
        self.lock = Lock()
        self.latest = None
        self.usb_requested = Event()
        self.usb_tunnel = None

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
                    video_size=self.video_size,
                    quality=self.quality,
                    adaptive=self.adaptive,
                )
                asyncio.run(self.receive_stream(server))
            else:
                run_pattern(self.stop, self.device, self.publish)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(f"Não foi possível concluir a operação: {exc}")
        finally:
            if self.usb_tunnel:
                self.usb_tunnel.close()

    async def receive_stream(self, server):
        task = asyncio.create_task(server.run(self.stop))
        try:
            while not task.done():
                if self.usb_requested.is_set() and server.bound_port:
                    self.usb_requested.clear()
                    try:
                        if self.usb_tunnel is None:
                            self.usb_tunnel = UsbTunnel(server.bound_port)
                        await asyncio.to_thread(self.usb_tunnel.connect)
                        if not self.stop.is_set():
                            self.usb_result.emit(
                                True, "Cabo USB configurado. Escaneie o QR no celular."
                            )
                    except UsbError as error:
                        self.usb_result.emit(False, str(error))
                await asyncio.sleep(0.05)
            await task
        finally:
            self.stop.set()
            await task


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
        self.status = label("Conecte o cabo e clique em Conectar celular.", "statusText")
        self.status.setWordWrap(True)
        self.preview = VideoPreview()
        self.preview.setText(
            "Conecte seu celular por USB.\n\nClique em Conectar celular para começar."
        )
        self.devices = QComboBox()
        self.devices.addItem("Somente prévia", None)
        self.devices.setToolTip(
            "Selecione uma webcam virtual para disponibilizar vídeo no OBS e em outros aplicativos."
        )
        self.mode = QComboBox()
        self.mode.addItem("Receber do Android", True)
        self.mode.addItem("Teste de imagem", False)
        self.resolution = QComboBox()
        for title, size in [
            ("Full HD · 1920 × 1080", (1920, 1080)),
            ("HD · 1280 × 720", (1280, 720)),
            ("VGA · 640 × 480", (640, 480)),
        ]:
            self.resolution.addItem(title, size)
        self.quality = QComboBox()
        for title, value in [
            ("Qualidade automática", (90, True)),
            ("Máxima · JPEG 100", (100, False)),
            ("Alta · JPEG 90", (90, False)),
            ("Econômica · JPEG 75", (75, False)),
        ]:
            self.quality.addItem(title, value)
        self.orientation = QComboBox()
        self.orientation.addItem("Horizontal", False)
        self.orientation.addItem("Vertical", True)
        self.orientation.setToolTip(
            "Troca ao vivo. Na webcam virtual, o vídeo vertical tem barras laterais."
        )
        self.orientation.currentIndexChanged.connect(self.update_orientation)
        self.mode.currentIndexChanged.connect(
            lambda: self.orientation.setEnabled(bool(self.mode.currentData()))
        )
        self.start = QPushButton("Conectar celular")
        self.start.setObjectName("primary")
        self.start.clicked.connect(self.begin)
        self.stop = QPushButton("Desconectar")
        self.stop.setObjectName("stop")
        self.stop.setEnabled(False)
        self.stop.setVisible(False)
        self.stop.clicked.connect(self.end)
        self.diagnostics = QPushButton("Diagnósticos")
        self.diagnostics.setObjectName("ghost")
        self.diagnostics.clicked.connect(lambda: self.check(show_report=True))
        self.pairing_info = None
        self.usb_active = False
        self.pairing_usb = True
        self.usb_busy = False
        self.usb_message = ""
        self.pairing_button = QPushButton("Mostrar QR e instruções")
        self.pairing_button.setEnabled(False)
        self.pairing_button.setVisible(False)
        self.pairing_button.clicked.connect(self.show_pairing)
        self.metrics = label("Pronto para receber vídeo")
        self.output_resolution = label("—", "statValue")
        self.output_resolution.setToolTip(
            "Resolução da saída configurada. A resolução recebida aparece no canto da prévia."
        )
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
        stats_widget = QWidget()
        stats_widget.setObjectName("videoStats")
        stats = QHBoxLayout(stats_widget)
        stats.setContentsMargins(0, 0, 0, 0)
        for title, value in (
            ("RESOLUÇÃO DE SAÍDA", self.output_resolution),
            ("FPS DO VÍDEO", self.fps_value),
            ("QUADROS EXIBIDOS", self.frames_value),
        ):
            stat = QVBoxLayout()
            stat.setSpacing(4)
            stat.addWidget(label(title, "eyebrow"))
            stat.addWidget(value)
            stats.addLayout(stat, 1)
        stats_widget.setVisible(False)
        stats_toggle = QPushButton("Estatísticas")
        stats_toggle.setObjectName("ghost")
        stats_toggle.setCheckable(True)
        stats_toggle.toggled.connect(stats_widget.setVisible)
        video_layout.addWidget(stats_toggle, alignment=Qt.AlignmentFlag.AlignRight)
        video_layout.addWidget(stats_widget)
        video_layout.addWidget(self.metrics)
        content.addWidget(video_card, 1)
        panel = QFrame()
        panel.setObjectName("panel")
        controls = QVBoxLayout(panel)
        controls.setContentsMargins(22, 22, 22, 22)
        controls.setSpacing(12)
        controls.addWidget(label("Conecte seu celular", "sectionTitle"))
        connection_hint = label(
            "Conecte o cabo USB e autorize o computador no Android. Depois, leia o QR no NexoCam do celular."
        )
        connection_hint.setWordWrap(True)
        controls.addWidget(connection_hint)
        controls.addWidget(self.start)
        controls.addWidget(self.stop)
        controls.addWidget(self.pairing_button)
        controls.addSpacing(12)
        controls.addWidget(label("Usar imagem em", "eyebrow"))
        controls.addWidget(self.devices)
        controls.addWidget(self.device_hint)
        controls.addWidget(label("Formato", "eyebrow"))
        controls.addWidget(self.orientation)
        controls.addWidget(self.resolution)
        controls.addWidget(self.quality)
        advanced = QWidget()
        advanced.setObjectName("advancedSettings")
        advanced_layout = QVBoxLayout(advanced)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addWidget(label("Origem do vídeo", "eyebrow"))
        advanced_layout.addWidget(self.mode)
        advanced_layout.addWidget(self.diagnostics)
        advanced.setVisible(False)
        advanced_toggle = QPushButton("Opções avançadas")
        advanced_toggle.setObjectName("ghost")
        advanced_toggle.setCheckable(True)
        advanced_toggle.toggled.connect(advanced.setVisible)
        controls.addWidget(advanced_toggle)
        controls.addWidget(advanced)
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
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.refresh)
        # Consome a mailbox sem acrescentar outro ciclo inteiro de vídeo à espera.
        self.timer.start(16)
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
        self.worker = Worker(
            device,
            receive=receiving,
            video_size=self.resolution.currentData(),
            quality=self.quality.currentData()[0],
            adaptive=self.quality.currentData()[1],
        )
        width, height = self.worker.video_size if receiving else (640, 480)
        self.output_resolution.setText(f"{width} × {height}")
        self.update_orientation()
        self.worker.status_changed.connect(self.status.setText)
        self.worker.pairing_ready.connect(self.paired)
        self.worker.pairing_confirmed.connect(self.close_pairing)
        self.worker.usb_result.connect(self.usb_configured)
        self.resolution.setEnabled(False)
        self.quality.setEnabled(False)
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
        self.pairing_button.setVisible(True)
        if self.pairing_usb:
            self.usb_busy = True
            self.worker.usb_requested.set()
        self.show_pairing()

    def usb_configured(self, success, message):
        self.usb_busy = False
        self.usb_active = success
        self.usb_message = message
        if (
            self.worker
            and not self.worker.stop.is_set()
            and not self.closing
            and self.report_dialog
            and self.report_dialog.isVisible()
            and self.report_dialog.windowTitle() == "Pareamento local seguro"
        ):
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
        body.setObjectName("pairingBody")
        scroll.setWidget(body)
        outer.addWidget(scroll)
        dialog.setMinimumWidth(370)
        dialog.resize(460, min(740, self.screen().availableGeometry().height() - 60))
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(label("Conecte seu Android", "sectionTitle"))
        transport = QComboBox()
        transport.setObjectName("pairingTransport")
        transport.addItem("Cabo USB", True)
        transport.addItem("Wi-Fi", False)
        transport.setCurrentIndex(0 if self.pairing_usb else 1)
        layout.addWidget(transport)
        instructions = label("")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        usb_help = label(
            "No primeiro uso, ative Depuração USB nas opções do desenvolvedor do Android "
            "e autorize este computador. Use um cabo que transmita dados."
        )
        usb_help.setWordWrap(True)
        layout.addWidget(usb_help)
        usb_button = QPushButton("Verificar cabo novamente")
        usb_button.setObjectName("ghost")
        usb_button.setEnabled(not self.usb_busy)
        layout.addWidget(usb_button)
        usb_status = label("Preparando USB…" if self.usb_busy else self.usb_message)
        usb_status.setWordWrap(True)
        layout.addWidget(usb_status)

        def prepare_usb():
            if self.worker and not self.worker.stop.is_set():
                self.usb_busy = True
                usb_button.setEnabled(False)
                usb_status.setText("Verificando cabo e autorização do celular…")
                self.worker.usb_requested.set()

        usb_button.clicked.connect(prepare_usb)
        from PySide6.QtNetwork import QAbstractSocket, QNetworkInterface

        interfaces = [
            interface
            for interface in QNetworkInterface.allInterfaces()
            if interface.flags() & QNetworkInterface.InterfaceFlag.IsUp
            and not interface.flags() & QNetworkInterface.InterfaceFlag.IsLoopBack
        ]
        addresses = [
            (interface.name(), entry.ip().toString(), entry.netmask().toString())
            for interface in interfaces
            for entry in interface.addressEntries()
            if entry.ip().protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol
        ]
        # Wi-Fi/Ethernet primeiro; bridges/VPN continuam selecionáveis explicitamente.
        addresses.sort(
            key=lambda item: (item[0].startswith(("docker", "br-", "veth", "virbr")), item[0])
        )
        network_title = label("REDE DO COMPUTADOR", "eyebrow")
        layout.addWidget(network_title)
        address_picker = QComboBox()
        for name, address, netmask in addresses:
            address_picker.addItem(f"{name} — {address}", address)
        layout.addWidget(address_picker)
        network_help = label(
            "Use o mesmo Wi-Fi no celular e no computador. Se não conectar, "
            "libere o acesso à rede abaixo. Redes de convidados podem bloquear a conexão."
        )
        network_help.setWordWrap(True)
        wifi_details = QWidget()
        wifi_details_layout = QVBoxLayout(wifi_details)
        wifi_details_layout.setContentsMargins(0, 0, 0, 0)
        wifi_details_layout.addWidget(network_help)
        wifi_help = QPushButton("Problemas com o Wi-Fi?")
        wifi_help.setObjectName("ghost")
        wifi_help.setCheckable(True)
        wifi_help.toggled.connect(wifi_details.setVisible)
        layout.addWidget(wifi_help)
        wifi_details.setVisible(False)
        layout.addWidget(wifi_details)
        firewall_button = QPushButton("Liberar acesso no firewall…")
        wifi_details_layout.addWidget(firewall_button)
        firewall_status = label("")
        firewall_status.setWordWrap(True)
        wifi_details_layout.addWidget(firewall_status)
        ufw = shutil.which("ufw")
        pkexec = shutil.which("pkexec")
        firewall_button.setEnabled(bool(ufw and pkexec and addresses))
        if not ufw or not pkexec:
            firewall_status.setText(
                "Liberação automática disponível com UFW e PolicyKit. Em outros firewalls, "
                f"permita TCP {port} na rede local."
            )
        firewall_process = QProcess(self)

        def release_firewall():
            from nexocam.network.firewall import ufw_rule

            index = address_picker.currentIndex()
            if index < 0:
                return
            name, address, netmask = addresses[index]
            try:
                arguments = ufw_rule(name, address, netmask, port)
            except ValueError as error:
                firewall_status.setText(str(error))
                return
            firewall_button.setEnabled(False)
            address_picker.setEnabled(False)
            firewall_status.setText("Autorize a alteração na janela do sistema…")
            firewall_process.start(pkexec, [ufw, *arguments])

        def firewall_finished(code, exit_status):
            firewall_button.setEnabled(True)
            address_picker.setEnabled(True)
            firewall_status.setText(
                "Acesso liberado para esta rede, mesmo se o IP do celular mudar. "
                "Tente conectar novamente. Ao mudar de rede, repita esta liberação."
                if code == 0 and exit_status == QProcess.ExitStatus.NormalExit
                else "Não foi possível liberar o acesso. Confira a autorização do administrador."
            )

        def firewall_error(error):
            firewall_button.setEnabled(True)
            address_picker.setEnabled(True)
            firewall_status.setText("Não foi possível iniciar a autorização do firewall.")

        firewall_button.clicked.connect(release_firewall)
        firewall_process.finished.connect(firewall_finished)
        firewall_process.errorOccurred.connect(firewall_error)
        qr_label = QLabel()
        qr_label.setObjectName("qr")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_label)
        from nexocam.security.qr import payload, pixels

        manual_address = QLineEdit()
        manual_address.setReadOnly(True)

        def update_qr():
            self.pairing_usb = bool(transport.currentData())
            instructions.setText(
                "1. Conecte o cabo e autorize o computador.\n"
                "2. No celular, escaneie o QR abaixo.\n"
                "3. Toque em Conectar e transmitir no celular."
                if self.pairing_usb
                else "Conecte os dois dispositivos ao mesmo Wi-Fi. No celular, escaneie o QR "
                "e toque em Conectar e transmitir."
            )
            for widget in (usb_button, usb_status):
                widget.setVisible(self.pairing_usb)
            usb_help.setVisible(self.pairing_usb and not self.usb_active)
            for widget in (
                network_title,
                address_picker,
                wifi_help,
            ):
                widget.setVisible(not self.pairing_usb)
            wifi_details.setVisible(not self.pairing_usb and wifi_help.isChecked())
            qr_label.clear()
            host = "127.0.0.1" if self.pairing_usb else address_picker.currentData()
            manual_address.setText(host or "")
            if self.pairing_usb and not self.usb_active:
                qr_label.setText("O QR aparece quando o cabo estiver pronto.")
                return
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
            qr_label.setPixmap(QPixmap.fromImage(image.convertToFormat(QImage.Format.Format_RGB32)))

        address_picker.currentIndexChanged.connect(update_qr)
        transport.currentIndexChanged.connect(update_qr)
        manual = QWidget()
        manual_layout = QVBoxLayout(manual)
        manual.setVisible(False)
        security_note = label(
            "Válido por 5 minutos para novas conexões.\nEste código contém seu segredo de acesso; não compartilhe."
        )
        security_note.setWordWrap(True)
        layout.addWidget(security_note)
        toggle = QPushButton("Conexão manual")
        toggle.setObjectName("ghost")
        toggle.clicked.connect(lambda: manual.setVisible(not manual.isVisible()))
        layout.addWidget(toggle)
        layout.addWidget(manual)
        manual_layout.addWidget(QLabel("Endereço do computador"))
        manual_layout.addWidget(manual_address)
        for field_label, value in (
            ("Impressão digital TLS", fingerprint),
            ("Segredo temporário", token),
        ):
            manual_layout.addWidget(QLabel(field_label))
            field = QLineEdit(value)
            field.setReadOnly(True)
            field.setMinimumWidth(260)
            manual_layout.addWidget(field)
        done = QPushButton("Fechar")
        done.setObjectName("ghost")
        done.clicked.connect(dialog.close)
        layout.addWidget(done)
        self.report_dialog = dialog
        update_qr()
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
        self.resolution.setEnabled(True)
        self.quality.setEnabled(True)
        self.mode.setEnabled(True)
        self.pairing_info = None
        self.usb_active = self.usb_busy = False
        self.pairing_usb = True
        self.usb_message = ""
        self.pairing_button.setEnabled(False)
        self.pairing_button.setVisible(False)
        if self.report_dialog:
            self.report_dialog.close()
            self.report_dialog = None
        self.preview.setText(
            "Sessão encerrada.\n\nSua câmera estará aqui quando você conectar novamente."
        )
        self.output_resolution.setText("—")
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
        self.metrics.setText(
            "Vídeo recebido · últimos 1 s"
            if self.worker and self.worker.receive
            else "Saída · meta de 15 FPS"
        )

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
