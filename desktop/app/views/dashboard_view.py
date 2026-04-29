from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QPushButton
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..core import api_client


class _DashboardWorker(QThread):
    veri_geldi = pyqtSignal(dict)
    hata = pyqtSignal(str)

    def run(self):
        try:
            data = api_client.get("/api/raporlar/dashboard")
            self.veri_geldi.emit(data or {})
        except Exception as e:
            self.hata.emit(str(e))


class _KartWidget(QFrame):
    def __init__(self, baslik: str, deger: str = "—", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(180, 100)
        layout = QVBoxLayout(self)
        self._baslik = QLabel(baslik)
        self._baslik.setFont(QFont("Segoe UI", 9))
        self._deger = QLabel(deger)
        self._deger.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._deger.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._baslik)
        layout.addWidget(self._deger)

    def set_deger(self, v: str):
        self._deger.setText(v)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        baslik = QLabel("Dashboard")
        baslik.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(12)

        self._kartlar = {
            "bugun_ciro":           _KartWidget("Bugün Ciro (₺)"),
            "bugun_kar":            _KartWidget("Bugün Kâr (₺)"),
            "bugun_satis_adedi":    _KartWidget("Bugün Satış"),
            "bu_ay_ciro":           _KartWidget("Bu Ay Ciro (₺)"),
            "bu_ay_kar":            _KartWidget("Bu Ay Kâr (₺)"),
            "toplam_tedarikci_borcu": _KartWidget("Tedarikçi Borcu (₺)"),
            "toplam_stok_degeri":   _KartWidget("Stok Değeri (₺)"),
            "toplam_musteri":       _KartWidget("Toplam Müşteri"),
        }

        pozisyonlar = list(self._kartlar.values())
        for i, kart in enumerate(pozisyonlar):
            grid.addWidget(kart, i // 4, i % 4)

        layout.addLayout(grid)

        yenile_btn = QPushButton("Yenile")
        yenile_btn.clicked.connect(self.yukle)
        layout.addWidget(yenile_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

        self.yukle()

    def yukle(self):
        self._worker = _DashboardWorker()
        self._worker.veri_geldi.connect(self._guncelle)
        self._worker.start()

    def _guncelle(self, data: dict):
        for key, kart in self._kartlar.items():
            val = data.get(key, 0)
            if isinstance(val, float):
                kart.set_deger(f"{val:,.2f}")
            else:
                kart.set_deger(str(val))

    def showEvent(self, event):
        super().showEvent(event)
        self.yukle()
