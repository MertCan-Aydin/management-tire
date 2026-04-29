from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

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
        self.setWindowTitle("Dijital Lastik Servisi - Giriş")
        self.setFixedSize(380, 350)

        self.root = QVBoxLayout(self)
        self.root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root.setSpacing(15)
        self.root.setContentsMargins(40, 40, 40, 40)

        self.baslik = QLabel("Dijital Lastik Servisi")
        self.baslik.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root.addWidget(self.baslik)

        self.alt_baslik = QLabel("Lütfen PIN kodunuzu girin")
        self.alt_baslik.setStyleSheet("color: #7f8c8d;")
        self.alt_baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root.addWidget(self.alt_baslik)

        self.root.addSpacing(10)

        # PIN Giriş Alanı
        self._pin_input = QLineEdit()
        self._pin_input.setPlaceholderText("PIN (4 Hane)")
        self._pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pin_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_input.setMinimumHeight(45)
        self._pin_input.setMaxLength(4)
        self._pin_input.setFont(QFont("Segoe UI", 14))
        self._pin_input.returnPressed.connect(self._giris)
        self.root.addWidget(self._pin_input)

        # PIN Tekrar (Sadece kurulum modunda görünür)
        self._pin_tekrar_input = QLineEdit()
        self._pin_tekrar_input.setPlaceholderText("PIN Tekrar")
        self._pin_tekrar_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pin_tekrar_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_tekrar_input.setMinimumHeight(45)
        self._pin_tekrar_input.setMaxLength(4)
        self._pin_tekrar_input.setFont(QFont("Segoe UI", 14))
        self._pin_tekrar_input.setVisible(False)
        self.root.addWidget(self._pin_tekrar_input)

        self._giris_btn = QPushButton("Giriş Yap")
        self._giris_btn.setMinimumHeight(45)
        self._giris_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self._giris_btn.clicked.connect(self._giris)
        self.root.addWidget(self._giris_btn)

        self._hata_label = QLabel("")
        self._hata_label.setStyleSheet("color: #e74c3c;")
        self._hata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hata_label.setWordWrap(True)
        self.root.addWidget(self._hata_label)

    def _check_setup(self):
        self._pin_input.setEnabled(False)
        self._giris_btn.setEnabled(False)
        self._hata_label.setText("Sistem durumu kontrol ediliyor...")

        self._setup_worker = _SetupCheckWorker()
        self._setup_worker.sonuc.connect(self._on_setup_check_success)
        self._setup_worker.hata.connect(self._on_setup_check_error)
        self._setup_worker.start()

    def _on_setup_check_success(self, kurulu_mu: bool):
        self._pin_input.setEnabled(True)
        self._giris_btn.setEnabled(True)
        self._hata_label.setText("")

        if not kurulu_mu:
            self._is_setup_mode = True
            self.alt_baslik.setText("İlk Kurulum: Yeni PIN oluşturun")
            self._pin_tekrar_input.setVisible(True)
            self._giris_btn.setText("PIN Oluştur ve Giriş Yap")
            self.setFixedSize(380, 420)
        else:
            self._is_setup_mode = False
            self.alt_baslik.setText("Hoş geldiniz, PIN kodunuzu girin")
            self._pin_tekrar_input.setVisible(False)
            self._giris_btn.setText("Giriş Yap")
            self.setFixedSize(380, 350)
        
        self._pin_input.setFocus()

    def _on_setup_check_error(self, mesaj: str):
        self._hata_label.setText(f"Bağlantı hatası: {mesaj}")
        self._giris_btn.setText("Tekrar Dene")
        self._giris_btn.setEnabled(True)
        self._giris_btn.clicked.disconnect()
        self._giris_btn.clicked.connect(self._check_setup)

    def _giris(self):
        pin = self._pin_input.text().strip()
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            self._hata_label.setText("Lütfen 4 haneli bir PIN girin.")
            return

        if self._is_setup_mode:
            pin_tekrar = self._pin_tekrar_input.text().strip()
            if pin != pin_tekrar:
                self._hata_label.setText("PIN kodları eşleşmiyor.")
                return

        self._hata_label.setText("")
        self._giris_btn.setEnabled(False)
        self._giris_btn.setText("İşlem yapılıyor...")

        self._worker = _LoginWorker(pin, is_setup=self._is_setup_mode)
        self._worker.basarili.connect(self._on_basarili)
        self._worker.hata.connect(self._on_hata)
        self._worker.start()

    def _on_basarili(self, data: dict):
        save_tokens(data["access_token"], data["refresh_token"])
        self.giris_yapildi.emit()

    def _on_hata(self, mesaj: str):
        self._hata_label.setText(mesaj)
        self._giris_btn.setEnabled(True)
        self._giris_btn.setText("PIN Oluştur" if self._is_setup_mode else "Giriş Yap")
        self._pin_input.clear()
        self._pin_tekrar_input.clear()
        self._pin_input.setFocus()
