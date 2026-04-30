"""
Tüm form diyaloglarının temel sınıfı.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


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
        _form_alanlari()  → form_layout'u doldurur
        _kaydet_fn()      → API çağrısı yapan callable
    """
    BASLIK = "Form"

    def __init__(self, parent=None, duzenleme: dict = None):
        super().__init__(parent)
        self._duzenleme = duzenleme
        self._worker = None
        mod = "Düzenle" if duzenleme else "Yeni"
        self.setWindowTitle(f"{self.BASLIK} — {mod}")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if duzenleme:
            self._form_doldur(duzenleme)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Başlık
        baslik = QLabel(self.windowTitle())
        baslik.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        baslik.setStyleSheet("color:#191c1e;")
        root.addWidget(baslik)

        # Ayırıcı
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border:none; border-top:1px solid #e0e3e5; margin:0;")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # Form alanları
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(10)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        self._form_alanlari()
        root.addLayout(self.form_layout)

        # Hata etiketi
        self._hata_label = QLabel("")
        self._hata_label.setWordWrap(True)
        self._hata_label.setStyleSheet(
            "color:#dc2626; background:#fee2e2; border-radius:6px;"
            "padding:6px 10px; font-size:12px;"
        )
        self._hata_label.hide()
        root.addWidget(self._hata_label)

        # Buton satırı
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("border:none; border-top:1px solid #e0e3e5;")
        sep2.setFixedHeight(1)
        root.addWidget(sep2)

        buton_row = QHBoxLayout()
        buton_row.setSpacing(10)
        buton_row.addStretch()

        self._iptal_btn = QPushButton("İptal")
        self._iptal_btn.setObjectName("flat")
        self._iptal_btn.setFixedHeight(36)
        self._iptal_btn.clicked.connect(self.reject)
        buton_row.addWidget(self._iptal_btn)

        self._kaydet_btn = QPushButton("Kaydet")
        self._kaydet_btn.setDefault(True)
        self._kaydet_btn.setFixedHeight(36)
        self._kaydet_btn.setMinimumWidth(100)
        self._kaydet_btn.clicked.connect(self._kaydet)
        buton_row.addWidget(self._kaydet_btn)

        root.addLayout(buton_row)

    def _form_alanlari(self):
        pass

    def _form_doldur(self, data: dict):
        pass

    def _kaydet_fn(self):
        raise NotImplementedError

    def _dogrula(self) -> bool:
        return True

    def _kaydet(self):
        self._hata_label.hide()
        if not self._dogrula():
            return
        self._kaydet_btn.setEnabled(False)
        self._kaydet_btn.setText("Kaydediliyor…")
        self._worker = _SaveWorker(self._kaydet_fn())
        self._worker.basarili.connect(self.accept)
        self._worker.hata.connect(self._on_hata)
        self._worker.start()

    def _on_hata(self, mesaj: str):
        self._hata_label.setText(f"⚠  {mesaj}")
        self._hata_label.show()
        self._kaydet_btn.setEnabled(True)
        self._kaydet_btn.setText("Kaydet")
