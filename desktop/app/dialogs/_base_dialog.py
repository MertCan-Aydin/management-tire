"""
Tüm form diyaloglarının temel sınıfı.
Kaydet/İptal butonlarını ve hata gösterimini standartlaştırır.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class _SaveWorker(QThread):
    basarili = pyqtSignal()
    hata = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self._fn()
            self.basarili.emit()
        except Exception as e:
            self.hata.emit(str(e))


class BaseFormDialog(QDialog):
    """
    Alt sınıflar şunları uygular:
        BASLIK : str
        _form_alanlari()  -> QFormLayout (form_layout'u doldurmak için)
        _kaydet_fn()      -> callable (API çağrısı yapan lambda/fn)
    """
    BASLIK = "Form"

    def __init__(self, parent=None, duzenleme: dict = None):
        super().__init__(parent)
        self._duzenleme = duzenleme   # None ise yeni kayıt, dict ise düzenleme
        self._worker = None
        self.setWindowTitle(self.BASLIK if not duzenleme else f"{self.BASLIK} — Düzenle")
        self.setMinimumWidth(420)
        self._build_ui()
        if duzenleme:
            self._form_doldur(duzenleme)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        baslik = QLabel(self.windowTitle())
        baslik.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        root.addWidget(baslik)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self._form_alanlari()
        root.addLayout(self.form_layout)

        self._hata_label = QLabel("")
        self._hata_label.setStyleSheet("color: #c0392b;")
        self._hata_label.setWordWrap(True)
        root.addWidget(self._hata_label)

        buton_row = QHBoxLayout()
        buton_row.addStretch()
        self._iptal_btn = QPushButton("İptal")
        self._iptal_btn.clicked.connect(self.reject)
        buton_row.addWidget(self._iptal_btn)
        self._kaydet_btn = QPushButton("Kaydet")
        self._kaydet_btn.setDefault(True)
        self._kaydet_btn.clicked.connect(self._kaydet)
        buton_row.addWidget(self._kaydet_btn)
        root.addLayout(buton_row)

    def _form_alanlari(self):
        """Alt sınıf form alanlarını self.form_layout'a ekler."""
        pass

    def _form_doldur(self, data: dict):
        """Düzenleme modunda alanları mevcut veriyle doldurur."""
        pass

    def _kaydet_fn(self):
        """API çağrısını yapan callable. Alt sınıf uygular."""
        raise NotImplementedError

    def _dogrula(self) -> bool:
        """Kaydetmeden önce doğrulama. False dönerse kayıt durur."""
        return True

    def _kaydet(self):
        self._hata_label.setText("")
        if not self._dogrula():
            return
        self._kaydet_btn.setEnabled(False)
        self._kaydet_btn.setText("Kaydediliyor…")
        self._worker = _SaveWorker(self._kaydet_fn())
        self._worker.basarili.connect(self.accept)
        self._worker.hata.connect(self._on_hata)
        self._worker.start()

    def _on_hata(self, mesaj: str):
        self._hata_label.setText(mesaj)
        self._kaydet_btn.setEnabled(True)
        self._kaydet_btn.setText("Kaydet")
