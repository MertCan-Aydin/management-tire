from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from ..core import api_client
from ..core.token_store import save_tokens


class _LoginWorker(QThread):
    basarili = pyqtSignal(dict)
    hata = pyqtSignal(str)

    def __init__(self, pin: str, is_setup: bool = False):
        super().__init__()
        self._pin = pin
        self._is_setup = is_setup

    def run(self):
        try:
            if self._is_setup:
                data = api_client.setup_pin(self._pin)
            else:
                data = api_client.pin_login(self._pin)
            self.basarili.emit(data)
        except api_client.AuthError:
            self.hata.emit("Hatalı PIN.")
        except api_client.NetworkError as e:
            self.hata.emit(str(e))
        except Exception as e:
            self.hata.emit(f"Hata: {str(e)}")


class _SetupCheckWorker(QThread):
    sonuc = pyqtSignal(bool)
    hata = pyqtSignal(str)

    def run(self):
        try:
            kurulu_mu = api_client.get_setup_status()
            self.sonuc.emit(kurulu_mu)
        except Exception as e:
            self.hata.emit(str(e))


class LoginView(QWidget):
    giris_yapildi = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._setup_worker = None
        self._is_setup_mode = False
        self._build_ui()
        self._check_setup()

    def _build_ui(self):
        self.setWindowTitle("Dijital Lastik Servisi")
        self.setFixedSize(420, 540)
        self.setStyleSheet("background:#f7f9fb;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Merkezi kart — sadece QFrame#loginKart'a uygulansın diye objectName
        kart = QFrame()
        kart.setObjectName("loginKart")
        kart.setFixedWidth(360)
        kart.setStyleSheet("""
            QFrame#loginKart {
                background: #ffffff;
                border-radius: 16px;
                border: 1px solid #e0e3e5;
            }
        """)
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(32)
        eff.setOffset(0, 6)
        c = QColor("#003d9b")
        c.setAlpha(20)
        eff.setColor(c)
        kart.setGraphicsEffect(eff)

        kart_layout = QVBoxLayout(kart)
        kart_layout.setContentsMargins(36, 32, 36, 32)
        kart_layout.setSpacing(14)

        # Logo
        logo = QLabel("🔧")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(80, 80)
        logo.setStyleSheet(
            "font-size:38px; background:#eef2ff; border-radius:18px;"
            "border:none; color:#003d9b;"
        )
        logo_wrap = QHBoxLayout()
        logo_wrap.addStretch()
        logo_wrap.addWidget(logo)
        logo_wrap.addStretch()
        kart_layout.addLayout(logo_wrap)

        # Başlık
        self.baslik_lbl = QLabel("Hoş Geldiniz")
        self.baslik_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.baslik_lbl.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.baslik_lbl.setStyleSheet(
            "color:#191c1e; background:transparent; border:none;")
        kart_layout.addWidget(self.baslik_lbl)

        self.alt_baslik = QLabel("PIN kodunuzu girin")
        self.alt_baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alt_baslik.setStyleSheet(
            "color:#505f76; font-size:13px; background:transparent; border:none;")
        kart_layout.addWidget(self.alt_baslik)

        kart_layout.addSpacing(8)

        # PIN giriş — büyük, ortalanmış, kalın font
        self._pin_input = QLineEdit()
        self._pin_input.setPlaceholderText("• • • •")
        self._pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pin_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_input.setMaxLength(4)
        self._pin_input.setFixedHeight(54)
        self._pin_input.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        self._pin_input.setStyleSheet(
            "QLineEdit { background:#f7f9fb; border:1.5px solid #e0e3e5;"
            " border-radius:10px; color:#191c1e; letter-spacing:6px; }"
            "QLineEdit:focus { border-color:#003d9b; background:#ffffff; }"
        )
        self._pin_input.returnPressed.connect(self._giris)
        kart_layout.addWidget(self._pin_input)

        # PIN tekrar
        self._pin_tekrar_input = QLineEdit()
        self._pin_tekrar_input.setPlaceholderText("PIN Tekrar")
        self._pin_tekrar_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pin_tekrar_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_tekrar_input.setMaxLength(4)
        self._pin_tekrar_input.setFixedHeight(48)
        self._pin_tekrar_input.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self._pin_tekrar_input.setStyleSheet(
            "QLineEdit { background:#f7f9fb; border:1.5px solid #e0e3e5;"
            " border-radius:10px; color:#191c1e; letter-spacing:5px; }"
            "QLineEdit:focus { border-color:#003d9b; background:#ffffff; }"
        )
        self._pin_tekrar_input.setVisible(False)
        kart_layout.addWidget(self._pin_tekrar_input)

        # Giriş butonu
        self._giris_btn = QPushButton("Giriş Yap")
        self._giris_btn.setFixedHeight(48)
        self._giris_btn.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self._giris_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._giris_btn.setStyleSheet(
            "QPushButton { background-color:#003d9b; color:#ffffff;"
            " border:none; border-radius:10px; }"
            "QPushButton:hover { background-color:#1a52ae; }"
            "QPushButton:pressed { background-color:#002d7a; }"
            "QPushButton:disabled { background-color:#bcc4d3; color:#ffffff; }"
        )
        self._giris_btn.clicked.connect(self._giris)
        kart_layout.addWidget(self._giris_btn)

        # Hata etiketi
        self._hata_label = QLabel("")
        self._hata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hata_label.setWordWrap(True)
        self._hata_label.setStyleSheet(
            "color:#dc2626; background:#fee2e2; border-radius:8px;"
            "padding:8px 10px; font-size:12px; border:none;"
        )
        self._hata_label.hide()
        kart_layout.addWidget(self._hata_label)

        outer.addStretch()
        outer.addWidget(kart, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()

        alt = QLabel("Dijital Lastik Servisi")
        alt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt.setStyleSheet(
            "color:#737685; font-size:11px; background:transparent; border:none;")
        outer.addWidget(alt)

    def _check_setup(self):
        self._pin_input.setEnabled(False)
        self._giris_btn.setEnabled(False)
        self._hata_label.hide()
        self.alt_baslik.setText("Sistem durumu kontrol ediliyor…")

        self._setup_worker = _SetupCheckWorker()
        self._setup_worker.sonuc.connect(self._on_setup_check_success)
        self._setup_worker.hata.connect(self._on_setup_check_error)
        self._setup_worker.start()

    def _on_setup_check_success(self, kurulu_mu: bool):
        self._pin_input.setEnabled(True)
        self._giris_btn.setEnabled(True)
        self._hata_label.hide()

        if not kurulu_mu:
            self._is_setup_mode = True
            self.baslik_lbl.setText("İlk Kurulum")
            self.alt_baslik.setText("4 haneli yeni PIN belirleyin")
            self._pin_tekrar_input.setVisible(True)
            self._giris_btn.setText("PIN Oluştur")
            self.setFixedSize(420, 580)
        else:
            self._is_setup_mode = False
            self.baslik_lbl.setText("Hoş Geldiniz")
            self.alt_baslik.setText("PIN kodunuzu girin")
            self._pin_tekrar_input.setVisible(False)
            self._giris_btn.setText("Giriş Yap")
            self.setFixedSize(420, 520)

        self._pin_input.setFocus()

    def _on_setup_check_error(self, mesaj: str):
        self._hata_label.setText(f"Bağlantı hatası: {mesaj}")
        self._hata_label.show()
        self._giris_btn.setText("Tekrar Dene")
        self._giris_btn.setEnabled(True)
        self._giris_btn.clicked.disconnect()
        self._giris_btn.clicked.connect(self._check_setup)

    def _giris(self):
        pin = self._pin_input.text().strip()

        if not pin or len(pin) != 4 or not pin.isdigit():
            self._hata_label.setText("Lütfen 4 haneli sayısal bir PIN girin.")
            self._hata_label.show()
            return

        if self._is_setup_mode:
            pin_tekrar = self._pin_tekrar_input.text().strip()
            if pin != pin_tekrar:
                self._hata_label.setText("PIN kodları eşleşmiyor.")
                self._hata_label.show()
                return

        self._hata_label.hide()
        self._giris_btn.setEnabled(False)
        self._giris_btn.setText("İşlem yapılıyor…")

        self._worker = _LoginWorker(pin, is_setup=self._is_setup_mode)
        self._worker.basarili.connect(self._on_basarili)
        self._worker.hata.connect(self._on_hata)
        self._worker.start()

    def _on_basarili(self, data: dict):
        save_tokens(data["access_token"], data["refresh_token"])
        self.giris_yapildi.emit()

    def _on_hata(self, mesaj: str):
        self._hata_label.setText(mesaj)
        self._hata_label.show()
        self._giris_btn.setEnabled(True)
        self._giris_btn.setText(
            "PIN Oluştur" if self._is_setup_mode else "Giriş Yap")
        self._pin_input.clear()
        self._pin_tekrar_input.clear()
        self._pin_input.setFocus()
