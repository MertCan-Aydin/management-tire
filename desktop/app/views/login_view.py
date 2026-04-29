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

    def __init__(self, kullanici_adi: str, parola: str):
        super().__init__()
        self._kadi = kullanici_adi
        self._parola = parola

    def run(self):
        try:
            data = api_client.login(self._kadi, self._parola)
            self.basarili.emit(data)
        except api_client.AuthError:
            self.hata.emit("Kullanıcı adı veya parola hatalı.")
        except api_client.NetworkError as e:
            self.hata.emit(str(e))
        except Exception:
            self.hata.emit("Beklenmeyen hata oluştu.")


class LoginView(QWidget):
    giris_yapildi = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Giriş")
        self.setFixedSize(380, 320)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(12)
        root.setContentsMargins(48, 48, 48, 48)

        baslik = QLabel("Dijital Lastik Servisi")
        baslik.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(baslik)

        root.addSpacing(16)

        self._kadi_input = QLineEdit()
        self._kadi_input.setPlaceholderText("Kullanıcı adı")
        self._kadi_input.setMinimumHeight(36)
        root.addWidget(self._kadi_input)

        self._parola_input = QLineEdit()
        self._parola_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._parola_input.setPlaceholderText("Parola")
        self._parola_input.setMinimumHeight(36)
        self._parola_input.returnPressed.connect(self._giris)
        root.addWidget(self._parola_input)

        self._giris_btn = QPushButton("Giriş Yap")
        self._giris_btn.setMinimumHeight(40)
        self._giris_btn.clicked.connect(self._giris)
        root.addWidget(self._giris_btn)

        self._hata_label = QLabel("")
        self._hata_label.setStyleSheet("color: #c0392b;")
        self._hata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hata_label.setWordWrap(True)
        root.addWidget(self._hata_label)

    def _giris(self):
        kadi = self._kadi_input.text().strip()
        parola = self._parola_input.text()

        if not kadi or not parola:
            self._hata_label.setText("Kullanıcı adı ve parola gereklidir.")
            return

        self._hata_label.setText("")
        self._giris_btn.setEnabled(False)
        self._giris_btn.setText("Bağlanıyor…")

        self._worker = _LoginWorker(kadi, parola)
        self._worker.basarili.connect(self._on_basarili)
        self._worker.hata.connect(self._on_hata)
        self._worker.start()

    def _on_basarili(self, data: dict):
        save_tokens(data["access_token"], data["refresh_token"])
        self._giris_btn.setEnabled(True)
        self._giris_btn.setText("Giriş Yap")
        self.giris_yapildi.emit()

    def _on_hata(self, mesaj: str):
        self._hata_label.setText(mesaj)
        self._giris_btn.setEnabled(True)
        self._giris_btn.setText("Giriş Yap")
        self._parola_input.clear()
        self._parola_input.setFocus()
