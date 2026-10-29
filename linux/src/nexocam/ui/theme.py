"""Tema nativo compartilhado entre o receptor e seus diálogos."""

from pathlib import Path

STYLESHEET = """
QWidget { color: #e7ecef; font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 13px; }
QMainWindow, QDialog, QMessageBox { background: #101417; }
QWidget#root { background: #101417; }
QFrame#panel, QFrame#videoCard { background: #191f23; border: 1px solid #2a3339; border-radius: 16px; }
QFrame#statusCard { background: #12181b; border: 1px solid #2a3339; border-radius: 10px; }
QLabel { background: transparent; border: none; }
QLabel#brand { font-size: 23px; font-weight: 700; letter-spacing: -0.5px; }
QLabel#subtitle, QLabel#muted { color: #98a7af; font-size: 12px; }
QLabel#sectionTitle { font-size: 17px; font-weight: 600; }
QLabel#eyebrow { color: #9aaab2; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
QLabel#statValue { font-size: 19px; font-weight: 600; }
QLabel#stateBadge { color: #a8b5bd; background: #20282d; border: 1px solid #344149; border-radius: 12px; padding: 5px 12px; font-size: 11px; }
QLabel#stateBadge[state="active"] { color: #8de6cf; background: #19342e; border-color: #295047; }
QLabel#stateBadge[state="error"] { color: #f2c48b; background: #362b1e; border-color: #654d2c; }
QLabel#preview { background: #0b0e10; color: #899aa5; border-radius: 10px; font-size: 16px; }
QLabel#qr { background: white; border-radius: 12px; padding: 12px; color: #20282d; }
QPushButton { background: #252e34; border: 1px solid #3a474f; border-radius: 9px; padding: 10px 16px; font-weight: 500; }
QPushButton:hover { background: #303c43; border-color: #5e737e; }
QPushButton:pressed { background: #1b242a; }
QPushButton:focus, QComboBox:focus, QLineEdit:focus { border: 1px solid #74d7bd; }
QPushButton#primary { background: #8be0c4; color: #10251e; border-color: #8be0c4; font-weight: 700; }
QPushButton#primary:hover { background: #a3edd5; border-color: #a3edd5; }
QPushButton#stop { color: #efb4b0; border-color: #64413e; background: #322321; }
QPushButton#stop:hover { background: #48302d; }
QPushButton#ghost { background: transparent; border-color: #344149; color: #b8c5cc; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#stop:disabled { background: #20272c; color: #687780; border-color: #2c363d; }
QComboBox { background: #12181c; border: 1px solid #38454d; border-radius: 8px; padding: 10px 28px 10px 12px; min-height: 18px; }
QComboBox:disabled { color: #788791; border-color: #2c363d; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow { image: url("CHEVRON_DOWN"); width: 12px; height: 12px; }
QComboBox QAbstractItemView { background: #20292f; color: #e7ecef; selection-background-color: #34564b; outline: none; padding: 6px; }
QLineEdit { background: #11181c; border: 1px solid #38454d; border-radius: 7px; padding: 9px; selection-background-color: #34564b; }
QToolTip { background: #253139; color: #e7ecef; border: 1px solid #4b606c; padding: 6px; }
QMenu { background: #20292f; border: 1px solid #38454d; padding: 6px; }
QMenu::item { padding: 8px 18px; border-radius: 5px; }
QMenu::item:selected { background: #34564b; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 7px; margin: 0; }
QScrollBar::handle:vertical { background: #3e4e58; border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""".replace("CHEVRON_DOWN", str(Path(__file__).parent / "assets/chevron-down.svg"))
