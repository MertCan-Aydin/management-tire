import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from config import Config

API   = Config.API_BASE_URL
HDRS  = {"Content-Type": "application/json", "X-API-Key": Config.API_KEY, "Connection": "close"}


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.setFixedSize(340, 460)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.token    = None
        self.username = "user"
        self._pin     = ""
        self._mode   = "login"   # "login" veya "setup"
        self._setup_mode = False
        self._confirm_pin = ""   # setup'ta ilk girilen PIN
        self._awaiting_confirm = False
        self._check_status()
        self._build_ui()

    def _check_status(self):
        try:
            r = requests.get(f"{API}/api/auth/status", headers=HDRS, timeout=5)
            self._setup_mode = not r.json().get("pin_set", True)
        except Exception:
            self._setup_mode = False

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)

        # Başlık
        title = QLabel(Config.APP_NAME)
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#89b4fa;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Yonetim Paneli")
        sub.setStyleSheet("font-size:11px;color:#a6adc8;margin-bottom:6px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#313244;"); layout.addWidget(line)

        # Durum etiketi
        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size:13px;color:#cdd6f4;margin:8px 0;")
        layout.addWidget(self.lbl_status)

        # PIN göstergesi (4 nokta)
        dots_row = QHBoxLayout()
        dots_row.setSpacing(16)
        dots_row.addStretch()
        self._dots = []
        for _ in range(4):
            d = QLabel("○")
            d.setStyleSheet("font-size:28px;color:#45475a;")
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._dots.append(d)
            dots_row.addWidget(d)
        dots_row.addStretch()
        layout.addLayout(dots_row)

        # Hata mesajı
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color:#f38ba8;font-size:11px;min-height:16px;")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_error)

        # Numpad
        numpad = QVBoxLayout(); numpad.setSpacing(8)
        keys = [["1","2","3"],["4","5","6"],["7","8","9"],["←","0","✓"]]
        for row_keys in keys:
            row = QHBoxLayout(); row.setSpacing(8)
            for k in row_keys:
                btn = QPushButton(k)
                btn.setFixedSize(70, 58)
                if k == "✓":
                    btn.setStyleSheet(
                        "background:#a6e3a1;color:#11111b;font-size:22px;"
                        "font-weight:bold;border-radius:8px;border:none;")
                elif k == "←":
                    btn.setStyleSheet(
                        "background:#f38ba8;color:#11111b;font-size:18px;"
                        "font-weight:bold;border-radius:8px;border:none;")
                else:
                    btn.setStyleSheet(
                        "background:#313244;color:#cdd6f4;font-size:20px;"
                        "font-weight:bold;border-radius:8px;border:none;")
                btn.clicked.connect(lambda _, key=k: self._key_pressed(key))
                row.addWidget(btn)
            numpad.addLayout(row)
        layout.addLayout(numpad)

        self._refresh_ui()

    def _refresh_ui(self):
        if self._setup_mode:
            if self._awaiting_confirm:
                self.lbl_status.setText("PIN'i tekrar girin\n(onaylayın)")
            else:
                self.lbl_status.setText("Yeni 4 haneli PIN\nbelirleyin")
        else:
            self.lbl_status.setText("PIN kodunuzu girin")
        self._update_dots()

    def _update_dots(self):
        n = len(self._pin)
        for i, d in enumerate(self._dots):
            if i < n:
                d.setText("●")
                d.setStyleSheet("font-size:28px;color:#89b4fa;")
            else:
                d.setText("○")
                d.setStyleSheet("font-size:28px;color:#45475a;")

    def keyPressEvent(self, event):
        key = event.text()
        if key.isdigit():
            self._key_pressed(key)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._key_pressed("✓")
        elif event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self._key_pressed("←")

    def _key_pressed(self, key):
        self.lbl_error.setText("")
        if key == "←":
            self._pin = self._pin[:-1]
            self._update_dots()
        elif key == "✓":
            self._submit()
        else:
            if len(self._pin) < 4:
                self._pin += key
                self._update_dots()
                if len(self._pin) == 4:
                    self._submit()

    def _submit(self):
        if len(self._pin) != 4:
            return

        if self._setup_mode:
            if not self._awaiting_confirm:
                # İlk giriş — onay için bekle
                self._confirm_pin = self._pin
                self._pin = ""
                self._awaiting_confirm = True
                self._refresh_ui()
            else:
                # Onay girişi
                if self._pin != self._confirm_pin:
                    self.lbl_error.setText("PIN'ler eşleşmiyor! Tekrar deneyin.")
                    self._pin = ""
                    self._confirm_pin = ""
                    self._awaiting_confirm = False
                    self._refresh_ui()
                    return
                # PIN'leri kaydet
                try:
                    r = requests.post(f"{API}/api/auth/setup",
                                      json={"pin": self._pin}, headers=HDRS, timeout=10)
                    if r.status_code == 200:
                        self.token = r.json()["access_token"]
                        self.accept()
                    else:
                        self.lbl_error.setText(r.json().get("detail","Hata"))
                        self._pin = ""
                        self._update_dots()
                except Exception:
                    self.lbl_error.setText("Sunucuya bağlanılamıyor!")
                    self._pin = ""
                    self._update_dots()
        else:
            # Normal login
            try:
                r = requests.post(f"{API}/api/auth/login",
                                  json={"pin": self._pin}, headers=HDRS, timeout=10)
                if r.status_code == 200:
                    self.token = r.json()["access_token"]
                    self.accept()
                elif r.status_code == 401:
                    self.lbl_error.setText("Hatalı PIN! Tekrar deneyin.")
                    self._pin = ""
                    self._update_dots()
                else:
                    self.lbl_error.setText(r.json().get("detail","Hata"))
                    self._pin = ""
                    self._update_dots()
            except Exception:
                self.lbl_error.setText("Sunucuya bağlanılamıyor!")
                self._pin = ""
                self._update_dots()