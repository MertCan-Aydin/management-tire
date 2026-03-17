import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QHBoxLayout, QPushButton, QStackedWidget,
                             QFrame, QMessageBox, QDialog, QGridLayout,
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from config import Config

from modules.suppliers import SuppliersModule
from modules.inventory import InventoryModule
from modules.sales import SalesModule
from modules.reports import ReportsModule
from modules.expenses import ExpensesModule
from modules.transactions import HistoryModule
from modules.customers import CustomersModule

# ── Temalar ───────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg_app":       "#313338",
        "bg_sidebar":   "#2b2d31",
        "bg_iconbar":   "#1e1f22",
        "bg_hover":     "#35373c",
        "bg_active":    "#404249",
        "bg_input":     "#1e1f22",
        "accent":       "#5865f2",
        "accent_h":     "#4752c4",
        "text_main":    "#f2f3f5",
        "text_sub":     "#b5bac1",
        "text_hint":    "#80848e",
        "divider":      "#3b3d43",
        "green":        "#23a55a",
        "red":          "#f23f42",
        "table_bg":     "#2b2d31",
        "header_bg":    "#313338",
        "scrollhandle": "#1a1b1e",
    },
    "light": {
        "bg_app":       "#ffffff",
        "bg_sidebar":   "#f2f3f5",
        "bg_iconbar":   "#e3e5e8",
        "bg_hover":     "#edeef0",
        "bg_active":    "#d9dbdd",
        "bg_input":     "#e9eaec",
        "accent":       "#5865f2",
        "accent_h":     "#4752c4",
        "text_main":    "#060607",
        "text_sub":     "#4e5058",
        "text_hint":    "#80848e",
        "divider":      "#d4d7dc",
        "green":        "#1e8a4a",
        "red":          "#da373c",
        "table_bg":     "#ffffff",
        "header_bg":    "#f2f3f5",
        "scrollhandle": "#c4c9d0",
    }
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"theme": "dark"}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

_current_theme = load_settings().get("theme", "dark")

def T(key):
    return THEMES[_current_theme][key]


def build_stylesheet():
    t = THEMES[_current_theme]
    return f"""
        * {{ border: none; outline: none; }}
        QMainWindow, QWidget {{
            background-color: {t['bg_app']};
            color: {t['text_main']};
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
        }}
        QLabel {{ color: {t['text_main']}; background: transparent; border: none; }}
        QDialog     {{ background-color: {t['bg_sidebar']}; }}
        QMessageBox {{ background-color: {t['bg_sidebar']}; }}

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {t['bg_input']};
            color: {t['text_main']};
            border: none;
            padding: 8px 10px;
            border-radius: 4px;
            font-size: 14px;
        }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            background: {t['bg_sidebar']};
            color: {t['text_main']};
            border: 1px solid {t['divider']};
            selection-background-color: {t['bg_active']};
        }}

        QPushButton {{
            background-color: {t['accent']};
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 14px;
        }}
        QPushButton:hover   {{ background-color: {t['accent_h']}; }}
        QPushButton:pressed {{ background-color: {t['accent_h']}; }}

        QTableWidget {{
            background-color: {t['table_bg']};
            color: {t['text_main']};
            gridline-color: {t['divider']};
            border: none;
            font-size: 14px;
        }}
        QHeaderView::section {{
            background-color: {t['header_bg']};
            color: {t['text_hint']};
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {t['divider']};
            font-weight: 700;
            font-size: 11px;
        }}
        QTableWidget::item {{
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {t['divider']};
        }}
        QTableWidget::item:selected {{
            background-color: {t['bg_active']};
            color: {t['text_main']};
        }}

        QTabWidget::pane {{ border: none; background-color: {t['bg_app']}; }}
        QTabBar::tab {{
            background: transparent;
            color: {t['text_hint']};
            padding: 8px 16px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 14px;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            color: {t['text_main']};
            border-bottom: 2px solid {t['accent']};
        }}
        QTabBar::tab:hover {{ color: {t['text_sub']}; }}

        QScrollBar:vertical {{
            background: transparent; width: 8px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['scrollhandle']};
            border-radius: 4px; min-height: 40px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: transparent; height: 8px;
        }}
        QScrollBar::handle:horizontal {{
            background: {t['scrollhandle']}; border-radius: 4px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

        QToolTip {{
            background-color: {t['bg_iconbar']};
            color: {t['text_main']};
            border: none; padding: 6px 10px;
            border-radius: 4px; font-size: 13px; font-weight: 600;
        }}
    """


# ── Nav butonu ────────────────────────────────────────────────────────────────
class NavButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, icon, label, parent=None):
        super().__init__(parent)
        self._active  = False
        self._hovered = False
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFixedWidth(20)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_lbl = QLabel(label)

        lay.addWidget(self.icon_lbl)
        lay.addWidget(self.text_lbl)
        lay.addStretch()

        self._refresh()

    def set_active(self, v):
        self._active = v
        self._refresh()

    def _refresh(self):
        if self._active:
            bg    = T("bg_active")
            color = T("text_main")
            fw    = "700"
            bl    = f"border-left: 3px solid {T('accent')};"
            pl    = "padding-left: 9px;"
        elif self._hovered:
            bg    = T("bg_hover")
            color = T("text_sub")
            fw    = "500"
            bl    = "border-left: 3px solid transparent;"
            pl    = "padding-left: 9px;"
        else:
            bg    = "transparent"
            color = T("text_hint")
            fw    = "500"
            bl    = "border-left: 3px solid transparent;"
            pl    = "padding-left: 9px;"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border-radius: 4px;
                {bl}
                {pl}
                border-top: none; border-right: none; border-bottom: none;
            }}
        """)
        self.icon_lbl.setStyleSheet(f"font-size: 16px; color: {color}; background: transparent; border: none;")
        self.text_lbl.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: {fw}; background: transparent; border: none;")

    def enterEvent(self, e):
        self._hovered = True;  self._refresh(); super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False; self._refresh(); super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ── İstatistik satırı ─────────────────────────────────────────────────────────
class StatRow(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 3, 12, 3)
        lay.setSpacing(0)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {T('text_hint')}; background: transparent; border: none; letter-spacing: 0.5px;")

        self.val = QLabel("0,00 TL")
        self.val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.val.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {T('text_main')}; background: transparent; border: none;")

        lay.addWidget(self.lbl)
        lay.addStretch()
        lay.addWidget(self.val)

    def set_value(self, text, color=None):
        c = color or T("text_main")
        self.val.setText(text)
        self.val.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {c}; background: transparent; border: none;")


# ── Responsive home ───────────────────────────────────────────────────────────
class HomeCard(QWidget):
    def __init__(self, icon, title, subtitle, color, callback, parent=None):
        super().__init__(parent)
        self._callback = callback
        self._color    = color
        self._hovered  = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(180, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._refresh_style()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(5)

        self.icon_lbl  = QLabel(icon)
        self.icon_lbl.setStyleSheet(f"font-size: 24px; color: {color}; background: transparent; border: none;")
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T('text_main')}; background: transparent; border: none;")
        self.sub_lbl   = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {T('text_hint')}; background: transparent; border: none;")

        lay.addWidget(self.icon_lbl)
        lay.addWidget(self.title_lbl)
        lay.addWidget(self.sub_lbl)
        lay.addStretch()

    def _refresh_style(self):
        bg = T("bg_hover") if self._hovered else T("bg_sidebar")
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border-radius: 10px;
                border-left: 3px solid {self._color};
                border-top: none; border-right: none; border-bottom: none;
            }}
        """)

    def enterEvent(self, e):
        self._hovered = True;  self._refresh_style(); super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False; self._refresh_style(); super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._callback()


class HomeWidget(QWidget):
    CARD_MIN_W = 220
    GAP        = 14
    CARDS = [
        ("🛒", "Satış (POS)",     "Hızlı satış ve kasa",         "#5865f2", 0),
        ("📦", "Ürünler & Stok",  "Ürün ve stok yönetimi",        "#eb459e", 1),
        ("🚚", "Tedarikçiler",    "Tedarikçi ve borç takibi",     "#3ba55c", 2),
        ("👤", "Müşteriler",      "Müşteri kayıtları",            "#faa61a", 3),
        ("📊", "Raporlar",        "Satış ve kar raporları",       "#9b59b6", 4),
        ("💸", "Giderler",        "Gider takibi",                 "#ed4245", 5),
        ("🗂", "Geçmiş",          "Alım-satım geçmişi",          "#747f8d", 6),
    ]

    def __init__(self, switch_fn, parent=None):
        super().__init__(parent)
        self._switch_fn = switch_fn
        self._cols      = 3

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Başlık
        header = QWidget()
        header.setFixedHeight(72)
        header.setStyleSheet(f"background-color: {T('bg_app')}; border: none; border-bottom: 1px solid {T('divider')};")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 14, 28, 10)
        hl.setSpacing(2)
        title = QLabel("Ana Sayfa")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {T('text_main')}; background: transparent; border: none;")
        sub = QLabel("Bir modül seç")
        sub.setStyleSheet(f"font-size: 13px; color: {T('text_hint')}; background: transparent; border: none;")
        hl.addWidget(title)
        hl.addWidget(sub)
        outer.addWidget(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_w = QWidget()
        self._grid_w.setStyleSheet("background: transparent; border: none;")
        self._grid   = QGridLayout(self._grid_w)
        self._grid.setSpacing(self.GAP)
        self._grid.setContentsMargins(28, 24, 28, 24)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._cards = []
        for icon, ttl, subt, color, idx in self.CARDS:
            card = HomeCard(icon, ttl, subt, color, lambda i=idx: self._switch_fn(i))
            self._cards.append(card)

        self._place_cards(3)
        scroll.setWidget(self._grid_w)
        outer.addWidget(scroll)

    def _place_cards(self, cols):
        for card in self._cards:
            self._grid.removeWidget(card)
            card.setParent(self._grid_w)
        for i, card in enumerate(self._cards):
            self._grid.addWidget(card, i // cols, i % cols)
        self._cols = cols

    def resizeEvent(self, e):
        super().resizeEvent(e)
        avail = self.width() - 56
        cols  = max(1, avail // (self.CARD_MIN_W + self.GAP))
        cols  = min(cols, len(self.CARDS))
        if cols != self._cols:
            self._place_cards(cols)


# ── Ana pencere ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, username=""):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.setGeometry(100, 100, 1280, 800)
        self.setMinimumSize(1024, 680)
        self._nav_btns          = []   # [(idx, NavButton)]
        self._settings_visible  = False

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content())

        self.update_cash_balance()
        self._set_active(-1)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setStyleSheet(f"background-color: {T('bg_sidebar')}; border: none;")

        lay = QVBoxLayout(self.sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Başlık
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background-color: {T('bg_sidebar')}; border: none; border-bottom: 1px solid {T('divider')};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        name_lbl = QLabel(Config.APP_NAME)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T('text_main')}; background: transparent; border: none;")
        hl.addWidget(name_lbl)
        lay.addWidget(header)

        # ── Nav butonları
        nav_w = QWidget()
        nav_w.setStyleSheet("background: transparent; border: none;")
        nav_lay = QVBoxLayout(nav_w)
        nav_lay.setContentsMargins(8, 8, 8, 8)
        nav_lay.setSpacing(2)

        nav_items = [
            ("🏠", "Ana Sayfa",      -1),
            ("🛒", "Satış (POS)",     0),
            ("📦", "Ürünler & Stok",  1),
            ("🚚", "Tedarikçiler",    2),
            ("👤", "Müşteriler",      3),
            ("📊", "Raporlar",        4),
            ("💸", "Giderler",        5),
            ("🗂", "Geçmiş",          6),
        ]

        for icon, label, idx in nav_items:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda i=idx: self._set_active(i))
            nav_lay.addWidget(btn)
            self._nav_btns.append((idx, btn))

        nav_lay.addStretch()
        lay.addWidget(nav_w, stretch=1)

        # ── İstatistikler
        stats_w = QWidget()
        stats_w.setStyleSheet(f"background-color: {T('bg_iconbar')}; border: none; border-top: 1px solid {T('divider')};")
        sl = QVBoxLayout(stats_w)
        sl.setContentsMargins(0, 10, 0, 6)
        sl.setSpacing(2)

        self.stat_kasa = StatRow("KASA")
        self.stat_brut = StatRow("BRÜT KAR")
        self.stat_net  = StatRow("NET KAR")

        self.lbl_nakit = QLabel("Nakit: 0  |  Kart: 0")
        self.lbl_nakit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nakit.setStyleSheet(f"font-size: 10px; color: {T('text_hint')}; padding: 2px 0; background: transparent; border: none;")

        for w in [self.stat_kasa, self.stat_brut, self.stat_net, self.lbl_nakit]:
            sl.addWidget(w)

        lay.addWidget(stats_w)

        # ── Ayarlar (gizli panel)
        self.settings_w = self._build_settings()
        self.settings_w.setVisible(False)
        lay.addWidget(self.settings_w)

        # ── Ayarlar butonu (her zaman görünür)
        settings_btn_w = QWidget()
        settings_btn_w.setStyleSheet(f"background-color: {T('bg_iconbar')}; border: none; border-top: 1px solid {T('divider')};")
        sb_lay = QHBoxLayout(settings_btn_w)
        sb_lay.setContentsMargins(12, 8, 12, 8)

        self.settings_toggle_btn = QPushButton("⚙  Ayarlar")
        self.settings_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {T('text_hint')};
                border: none;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 0;
            }}
            QPushButton:hover {{ color: {T('text_sub')}; }}
        """)
        self.settings_toggle_btn.clicked.connect(self._toggle_settings)
        sb_lay.addWidget(self.settings_toggle_btn)
        sb_lay.addStretch()

        lay.addWidget(settings_btn_w)
        return self.sidebar

    def _build_settings(self):
        w = QWidget()
        w.setStyleSheet(f"background-color: {T('bg_iconbar')}; border: none;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        # Tema
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel("Tema")
        lbl.setStyleSheet(f"font-size: 12px; color: {T('text_sub')}; background: transparent; border: none;")
        row.addWidget(lbl)
        row.addStretch()

        self.btn_dark_t  = QPushButton("🌙 Koyu")
        self.btn_light_t = QPushButton("☀ Açık")
        for btn in [self.btn_dark_t, self.btn_light_t]:
            btn.setFixedHeight(26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {T('bg_active')};
                    color: {T('text_sub')};
                    border: none; border-radius: 4px;
                    font-size: 12px; padding: 0 10px;
                }}
                QPushButton:hover {{
                    background-color: {T('bg_hover')};
                    color: {T('text_main')};
                }}
            """)

        self.btn_dark_t.clicked.connect(lambda: self._apply_theme("dark"))
        self.btn_light_t.clicked.connect(lambda: self._apply_theme("light"))
        self._mark_active_theme()

        row.addWidget(self.btn_dark_t)
        row.addWidget(self.btn_light_t)
        lay.addLayout(row)
        return w

    def _mark_active_theme(self):
        a = f"""
            QPushButton {{
                background-color: {T('accent')};
                color: #ffffff; border: none;
                border-radius: 4px; font-size: 12px; padding: 0 10px;
            }}
        """
        b = f"""
            QPushButton {{
                background-color: {T('bg_active')};
                color: {T('text_sub')}; border: none;
                border-radius: 4px; font-size: 12px; padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {T('bg_hover')};
                color: {T('text_main')};
            }}
        """
        if _current_theme == "dark":
            self.btn_dark_t.setStyleSheet(a)
            self.btn_light_t.setStyleSheet(b)
        else:
            self.btn_light_t.setStyleSheet(a)
            self.btn_dark_t.setStyleSheet(b)

    def _toggle_settings(self):
        self._settings_visible = not self._settings_visible
        self.settings_w.setVisible(self._settings_visible)

    def _apply_theme(self, theme_name):
        global _current_theme
        _current_theme = theme_name
        save_settings({"theme": theme_name})
        QApplication.instance().setStyleSheet(build_stylesheet())
        self.sidebar.setStyleSheet(f"background-color: {T('bg_sidebar')}; border: none;")
        self.stacked.setStyleSheet(f"background-color: {T('bg_app')};")
        self._mark_active_theme()
        for _, btn in self._nav_btns:
            btn._refresh()

    # ── İçerik ────────────────────────────────────────────────────────────────
    def _build_content(self):
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f"background-color: {T('bg_app')};")

        self.home_module      = HomeWidget(self._set_active)
        self.module_sales     = SalesModule()
        self.module_inventory = InventoryModule()
        self.module_suppliers = SuppliersModule()
        self.module_customers = CustomersModule()
        self.module_reports   = ReportsModule()
        self.module_expenses  = ExpensesModule()
        self.module_history   = HistoryModule()

        all_mods = [
            self.home_module, self.module_sales, self.module_inventory,
            self.module_suppliers, self.module_customers, self.module_reports,
            self.module_expenses, self.module_history,
        ]
        for m in all_mods:
            self.stacked.addWidget(m)

        for m in [self.module_sales, self.module_inventory, self.module_suppliers,
                  self.module_customers, self.module_reports, self.module_expenses,
                  self.module_history]:
            m.main_window = self

        return self.stacked

    # ── Navigasyon ────────────────────────────────────────────────────────────
    def _set_active(self, idx):
        for nav_idx, btn in self._nav_btns:
            btn.set_active(nav_idx == idx)

        stack_idx = 0 if idx == -1 else idx + 1
        self.stacked.setCurrentIndex(stack_idx)

        if idx >= 0:
            w = self.stacked.currentWidget()
            if hasattr(w, "refresh_data"):
                w.refresh_data()

        self.update_cash_balance()

    def switch_module(self, index):
        self._set_active(index)

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def update_cash_balance(self):
        from api_client import api, APIError
        try:
            d    = api.get_dashboard()
            net  = d.get("net_balance",  0.0)
            brut = d.get("gross_profit", 0.0)
            netp = d.get("net_profit",   0.0)
            cash = d.get("cash_sales",   0.0)
            card = d.get("card_sales",   0.0)
            self.stat_kasa.set_value(f"{net:,.2f} TL",  T("green") if net  >= 0 else T("red"))
            self.stat_brut.set_value(f"{brut:,.2f} TL", T("accent") if brut >= 0 else T("red"))
            self.stat_net.set_value(f"{netp:,.2f} TL",  T("green") if netp >= 0 else T("red"))
            self.lbl_nakit.setText(f"Nakit: {cash:,.0f} TL  |  Kart: {card:,.0f} TL")
        except Exception:
            for s in [self.stat_kasa, self.stat_brut, self.stat_net]:
                s.set_value("—", T("text_hint"))


# ── Başlat ────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_stylesheet())

    from api_client import api, APIError
    try:
        api.get_dashboard()
    except Exception as e:
        QMessageBox.critical(None, "Bağlantı Hatası",
                             f"API sunucusuna bağlanılamıyor!\n\n{e}\n\n"
                             f"config.py dosyasındaki API_BASE_URL adresini kontrol edin.")
        sys.exit(1)

    from login import LoginDialog
    login_dialog = LoginDialog()
    login_dialog.setStyleSheet(app.styleSheet())
    if login_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    api.set_token(login_dialog.token)
    window = MainWindow(username=login_dialog.username)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()