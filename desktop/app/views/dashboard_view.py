from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFrame, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from ..core import api_client
from ..core.utils import tr_para, tr_sayi


class _DashboardWorker(QThread):
    veri_geldi = pyqtSignal(dict)
    hata = pyqtSignal(str)

    def run(self):
        try:
            data = api_client.get("/api/raporlar/dashboard")
            self.veri_geldi.emit(data or {})
        except Exception as e:
            self.hata.emit(str(e))


def _kart_golge(widget: QWidget, renk: str = "#003d9b", alpha: int = 18):
    """Karta hafif mavi gölge efekti ekler."""
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(24)
    eff.setOffset(0, 4)
    eff.setColor(QColor(renk))
    eff.color().setAlpha(alpha)
    widget.setGraphicsEffect(eff)


class _KartWidget(QFrame):
    """Modern metrik kart — ikon + etiket + büyük değer."""

    def __init__(self, baslik: str, ikon: str = "◼",
                 aksan: str = "#003d9b", aksan_bg: str = "#eef2ff",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("dashCard")
        self.setStyleSheet(f"""
            QFrame#dashCard {{
                background-color: #ffffff;
                border-radius: 14px;
                border: 1px solid #e0e3e5;
            }}
        """)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(130)

        # Gölge
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(20)
        eff.setOffset(0, 3)
        c = QColor(aksan)
        c.setAlpha(22)
        eff.setColor(c)
        self.setGraphicsEffect(eff)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Renkli ikon alanı
        icon_box = QLabel(ikon)
        icon_box.setFixedSize(48, 48)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet(f"""
            background-color: {aksan_bg};
            border-radius: 12px;
            font-size: 22px;
            color: {aksan};
        """)
        layout.addWidget(icon_box)

        # Metin alanı
        txt = QVBoxLayout()
        txt.setSpacing(4)

        self._baslik_lbl = QLabel(baslik)
        self._baslik_lbl.setStyleSheet(
            "color:#505f76; font-size:11px; font-weight:600;"
            "letter-spacing:0.4px; background:transparent;"
        )

        self._deger_lbl = QLabel("—")
        self._deger_lbl.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self._deger_lbl.setStyleSheet(f"color:{aksan}; background:transparent;")

        txt.addWidget(self._baslik_lbl)
        txt.addWidget(self._deger_lbl)
        txt.addStretch()
        layout.addLayout(txt)

    def set_deger(self, v: str):
        self._deger_lbl.setText(v)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Başlık satırı
        ust = QHBoxLayout()
        baslik = QLabel("Dashboard")
        baslik.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        baslik.setStyleSheet("color:#191c1e;")
        ust.addWidget(baslik)
        ust.addStretch()
        yenile_btn = QPushButton("↻  Yenile")
        yenile_btn.setObjectName("flat")
        yenile_btn.setFixedHeight(34)
        yenile_btn.clicked.connect(self.yukle)
        ust.addWidget(yenile_btn)
        layout.addLayout(ust)

        # Bölüm başlığı — Bugün
        self._bolum_baslik("Bugün", layout)
        grid1 = QGridLayout()
        grid1.setSpacing(14)

        self._kartlar = {
            "bugun_ciro": _KartWidget(
                "BUGÜN CİRO", "💰", "#003d9b", "#eef2ff"),
            "bugun_kar": _KartWidget(
                "BUGÜN KÂR", "📈", "#16a34a", "#dcfce7"),
            "bugun_satis_adedi": _KartWidget(
                "BUGÜN SATIŞ", "🛒", "#d97706", "#fef3c7"),
        }
        for i, k in enumerate(["bugun_ciro", "bugun_kar", "bugun_satis_adedi"]):
            grid1.addWidget(self._kartlar[k], 0, i)
        layout.addLayout(grid1)

        # Bu Ay
        self._bolum_baslik("Bu Ay", layout)
        grid2 = QGridLayout()
        grid2.setSpacing(14)

        ay_kartlar = {
            "bu_ay_ciro": _KartWidget(
                "AY CİROSU", "📅", "#003d9b", "#eef2ff"),
            "bu_ay_kar": _KartWidget(
                "AY KÂRI", "📈", "#16a34a", "#dcfce7"),
        }
        self._kartlar.update(ay_kartlar)
        for i, k in enumerate(["bu_ay_ciro", "bu_ay_kar"]):
            grid2.addWidget(self._kartlar[k], 0, i)
        layout.addLayout(grid2)

        # Genel
        self._bolum_baslik("Genel", layout)
        grid3 = QGridLayout()
        grid3.setSpacing(14)

        genel_kartlar = {
            "toplam_tedarikci_borcu": _KartWidget(
                "TEDARİKÇİ BORCU", "⚠️", "#dc2626", "#fee2e2"),
            "toplam_stok_degeri": _KartWidget(
                "STOK DEĞERİ", "📦", "#d97706", "#fef3c7"),
            "toplam_musteri": _KartWidget(
                "TOPLAM MÜŞTERİ", "👥", "#7c3aed", "#ede9fe"),
        }
        self._kartlar.update(genel_kartlar)
        for i, k in enumerate(["toplam_tedarikci_borcu", "toplam_stok_degeri", "toplam_musteri"]):
            grid3.addWidget(self._kartlar[k], 0, i)
        layout.addLayout(grid3)

        layout.addStretch()
        self.yukle()

    def _bolum_baslik(self, metin: str, layout: QVBoxLayout):
        lbl = QLabel(metin)
        lbl.setStyleSheet(
            "color:#505f76; font-size:11px; font-weight:700;"
            "letter-spacing:0.8px; padding-top:4px;"
        )
        layout.addWidget(lbl)

    def yukle(self):
        self._worker = _DashboardWorker()
        self._worker.veri_geldi.connect(self._guncelle)
        self._worker.start()

    def _guncelle(self, data: dict):
        para_anahtarlar = {
            "bugun_ciro", "bugun_kar", "bu_ay_ciro",
            "bu_ay_kar", "toplam_tedarikci_borcu", "toplam_stok_degeri",
        }
        for key, kart in self._kartlar.items():
            val = data.get(key, 0) or 0
            if key in para_anahtarlar:
                kart.set_deger(f"₺ {tr_sayi(val)}")
            else:
                kart.set_deger(str(val))

    def showEvent(self, event):
        super().showEvent(event)
        if self._worker and self._worker.isRunning():
            return
        self.yukle()
