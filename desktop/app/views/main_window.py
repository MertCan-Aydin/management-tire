from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QStatusBar, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

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


_MENU_OGELER = [
    ("🏠  Dashboard",    DashboardView),
    ("📦  Ürünler",      UrunView),
    ("🚚  Tedarikçiler", TedarikciView),
    ("👤  Müşteriler",   MusteriView),
    ("⬇️  Alımlar",      AlimView),
    ("💳  Satışlar",     SatisView),
    ("💸  Giderler",     GiderView),
    ("📊  Raporlar",     RaporView),
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

        # Navigasyon listesi
        self._menu = QListWidget()
        self._menu.setObjectName("sidebar")
        self._menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._menu.setFont(QFont("Inter", 12))

        self._stack = QStackedWidget()

        for baslik, ViewClass in _MENU_OGELER:
            item = QListWidgetItem(baslik)
            item.setSizeHint(QSize(204, 44))
            self._menu.addItem(item)
            self._stack.addWidget(ViewClass())

        self._menu.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._menu.setCurrentRow(0)
        sb_layout.addWidget(self._menu)
        sb_layout.addStretch()

        # Versiyon etiketi
        ver_lbl = QLabel("v1.0")
        ver_lbl.setStyleSheet(
            "color:#737685; font-size:11px; padding:8px 20px;"
            "background:#ffffff; border-top:1px solid #e0e3e5;"
        )
        sb_layout.addWidget(ver_lbl)

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

    def _cikis(self):
        raw_refresh = get_refresh_token()
        if raw_refresh:
            api_client.logout(raw_refresh)
        clear_tokens()
        self.close()
