from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QStatusBar, QPushButton, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QKeySequence

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
        # Menü çubuğu — Hafta 7
        self._menu_olustur()

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

        root.addWidget(sidebar_container)

        # ── İçerik alanı ──────────────────────────────────────────────────
        root.addWidget(self._stack)

        # ── Durum çubuğu — Hafta 7 (önce kurulur ki _nav_sec mesaj gönderebilsin) ─
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        kullanici_lbl = QLabel("👤  Admin")
        kullanici_lbl.setStyleSheet(
            "color:#505f76; padding:0 8px; font-size:12px; background:transparent;")
        status_bar.addWidget(kullanici_lbl)

        # Çıkış butonu — gri zemin, kırmızı hover (tasarım sistemi flat varyantı)
        cikis_btn = QPushButton("Çıkış Yap")
        cikis_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cikis_btn.setFixedSize(96, 30)
        cikis_btn.setStyleSheet("""
            QPushButton {
                background-color: #eceef0;
                color: #505f76;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                min-height: 0;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
        """)
        cikis_btn.clicked.connect(self._cikis)
        status_bar.addPermanentWidget(cikis_btn)

        status_bar.showMessage("Hazır", 3000)
        self._nav_sec(0)

    # ── Menü Çubuğu (QMenuBar + QAction) — Hafta 7 ────────────────────────
    def _menu_olustur(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e3e5;
                padding: 4px 8px;
                color: #191c1e;
                font-size: 12px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QMenuBar::item:selected {
                background-color: #eef2ff;
                color: #003d9b;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e0e3e5;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #eef2ff;
                color: #003d9b;
            }
        """)

        # Dosya menüsü
        dosya_menu = menubar.addMenu("&Dosya")

        yenile_action = QAction("Yenile", self)
        yenile_action.setShortcut(QKeySequence("F5"))
        yenile_action.triggered.connect(self._aktif_view_yenile)
        dosya_menu.addAction(yenile_action)

        dosya_menu.addSeparator()

        cikis_action = QAction("Çıkış", self)
        cikis_action.setShortcut(QKeySequence("Ctrl+Q"))
        cikis_action.triggered.connect(self._cikis)
        dosya_menu.addAction(cikis_action)

        # Görünüm menüsü
        gorunum_menu = menubar.addMenu("&Görünüm")
        for i, (baslik, _) in enumerate(_MENU_OGELER):
            act = QAction(baslik.strip(), self)
            act.setShortcut(QKeySequence(f"Ctrl+{i+1}"))
            act.triggered.connect(lambda checked=False, idx=i: self._nav_sec(idx))
            gorunum_menu.addAction(act)

        # Yardım menüsü
        yardim_menu = menubar.addMenu("&Yardım")

        hakkinda_action = QAction("Hakkında", self)
        hakkinda_action.triggered.connect(self._hakkinda_goster)
        yardim_menu.addAction(hakkinda_action)

    def _aktif_view_yenile(self):
        view = self._stack.currentWidget()
        if hasattr(view, "yukle"):
            view.yukle()
            self.statusBar().showMessage("Veriler yenilendi ✓", 2000)

    def _hakkinda_goster(self):
        QMessageBox.about(
            self,
            "Hakkında",
            "<h3>Dijital Lastik Servisi</h3>"
            "<p>Sürüm: <b>1.0</b></p>"
            "<p>Lastik satış ve servis işletmesi yönetim sistemi.</p>"
            "<p style='color:#737685;'>© 2026</p>",
        )

    def _nav_sec(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_butonlar):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._nav_btn_stili(i == idx))
        # statusBar mesajı — Hafta 7
        baslik = _MENU_OGELER[idx][0].strip()
        self.statusBar().showMessage(f"{baslik} açıldı", 2000)

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
