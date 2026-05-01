from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QStatusBar, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..core.config import APP_NAME
from ..core.token_store import get_refresh_token, clear_tokens
from ..core import api_client

from .dashboard_view import DashboardView
from .urun_view import UrunView
from .tedarikci_view import TedarikciView
from .musteri_view import MusteriView
from .alim_view import AlimView
from .satis_view import SatisView
from .gider_view import GiderView
from .rapor_view import RaporView
from .lastik_oteli_view import LastikOteliView


_MENU_OGELER = [
    ("🏠  Dashboard",      DashboardView),
    ("📦  Ürünler",        UrunView),
    ("🚚  Tedarikçiler",   TedarikciView),
    ("👤  Müşteriler",     MusteriView),
    ("⬇️  Alımlar",        AlimView),
    ("💳  Satışlar",       SatisView),
    ("💸  Giderler",       GiderView),
    ("🏪  Lastik Oteli",   LastikOteliView),
    ("📊  Raporlar",       RaporView),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 740)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Kenar çubuğu ──────────────────────────────────────────────────
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(220)
        sidebar_container.setObjectName("sidebar_container")
        sidebar_container.setStyleSheet("background:#ffffff;")
        sb_layout = QVBoxLayout(sidebar_container)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Uygulama logosu / adı
        brand = QFrame()
        brand.setFixedHeight(60)
        brand.setStyleSheet("background:#ffffff; border-bottom:1px solid #e0e3e5;")
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(18, 0, 18, 0)
        brand_lbl = QLabel("🔧 Lastik Servisi")
        brand_lbl.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        brand_lbl.setStyleSheet("color:#003d9b; background:transparent;")
        brand_layout.addWidget(brand_lbl)
        sb_layout.addWidget(brand)

        # Navigasyon butonları
        self._stack = QStackedWidget()
        self._nav_butonlar: list[QPushButton] = []

        nav_container = QWidget()
        nav_container.setStyleSheet("background:#ffffff;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(2)

        for i, (baslik, ViewClass) in enumerate(_MENU_OGELER):
            btn = QPushButton(baslik)
            btn.setFixedHeight(42)
            btn.setCheckable(True)
            btn.setFont(QFont("Inter", 12))
            btn.setStyleSheet(self._nav_btn_stili(False))
            btn.clicked.connect(lambda checked, idx=i: self._nav_sec(idx))
            nav_layout.addWidget(btn)
            self._nav_butonlar.append(btn)
            self._stack.addWidget(ViewClass())

        nav_layout.addStretch()
        sb_layout.addWidget(nav_container)

        # Versiyon etiketi
        ver_lbl = QLabel("v1.0")
        ver_lbl.setStyleSheet(
            "color:#737685; font-size:11px; padding:8px 20px;"
            "background:#ffffff; border-top:1px solid #e0e3e5;"
        )
        sb_layout.addWidget(ver_lbl)

        self._nav_sec(0)

        root.addWidget(sidebar_container)

        # ── İçerik alanı ──────────────────────────────────────────────────
        root.addWidget(self._stack)

        # ── Durum çubuğu ──────────────────────────────────────────────────
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        kullanici_lbl = QLabel("👤 Admin")
        kullanici_lbl.setStyleSheet("color:#505f76; padding:0 8px;")
        status_bar.addWidget(kullanici_lbl)

        cikis_btn = QPushButton("Çıkış Yap")
        cikis_btn.setObjectName("flat")
        cikis_btn.setFixedHeight(28)
        cikis_btn.clicked.connect(self._cikis)
        status_bar.addPermanentWidget(cikis_btn)

    def _nav_sec(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_butonlar):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._nav_btn_stili(i == idx))

    @staticmethod
    def _nav_btn_stili(secili: bool) -> str:
        if secili:
            return """
                QPushButton {
                    background-color: #eef2ff;
                    color: #003d9b;
                    border: none;
                    border-radius: 8px;
                    padding-left: 16px;
                    text-align: left;
                    font-weight: bold;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                color: #505f76;
                border: none;
                border-radius: 8px;
                padding-left: 16px;
                text-align: left;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #f0f4ff;
                color: #003d9b;
            }
        """

    def _cikis(self):
        raw_refresh = get_refresh_token()
        if raw_refresh:
            api_client.logout(raw_refresh)
        clear_tokens()
        self.close()
