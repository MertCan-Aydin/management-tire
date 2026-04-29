from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QStatusBar, QPushButton,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from ..core.config import APP_NAME
from ..core.token_store import get_refresh_token, clear_tokens
from ..core import api_client

# Modül view'ları (her biri kendi dosyasında geliştirilecek)
from .dashboard_view import DashboardView
from .urun_view import UrunView
from .tedarikci_view import TedarikciView
from .musteri_view import MusteriView
from .alim_view import AlimView
from .satis_view import SatisView
from .gider_view import GiderView
from .rapor_view import RaporView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 700)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sol menü
        self._menu = QListWidget()
        self._menu.setFixedWidth(180)
        self._menu.setFont(QFont("Segoe UI", 10))
        menü_ogeler = [
            ("Dashboard",   DashboardView),
            ("Ürünler",     UrunView),
            ("Tedarikçiler",TedarikciView),
            ("Müşteriler",  MusteriView),
            ("Alımlar",     AlimView),
            ("Satışlar",    SatisView),
            ("Giderler",    GiderView),
            ("Raporlar",    RaporView),
        ]

        self._stack = QStackedWidget()

        for i, (baslik, ViewClass) in enumerate(menü_ogeler):
            item = QListWidgetItem(baslik)
            item.setSizeHint(QSize(180, 44))
            self._menu.addItem(item)
            self._stack.addWidget(ViewClass())

        self._menu.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._menu.setCurrentRow(0)

        layout.addWidget(self._menu)
        layout.addWidget(self._stack)

        # Durum çubuğu + çıkış butonu
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        cikis_btn = QPushButton("Çıkış")
        cikis_btn.clicked.connect(self._cikis)
        status_bar.addPermanentWidget(cikis_btn)

    def _cikis(self):
        raw_refresh = get_refresh_token()
        if raw_refresh:
            api_client.logout(raw_refresh)
        clear_tokens()
        self.close()
