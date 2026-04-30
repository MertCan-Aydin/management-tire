"""
Global QSS stylesheet — Enterprise SaaS design system
Renkler, tipografi, spacing ve bileşen stilleri tek yerden yönetilir.
"""

# ── Renk Paleti ──────────────────────────────────────────────────────────────
C = {
    "bg":           "#f7f9fb",   # ana arka plan (off-white)
    "surface":      "#ffffff",   # kart / panel yüzeyleri
    "primary":      "#003d9b",   # ana aksan (koyu mavi)
    "primary_h":    "#1a52ae",   # primary hover
    "primary_p":    "#002d7a",   # primary pressed
    "primary_light":"#eef2ff",   # primary çok açık (seçili bg)
    "text_hi":      "#191c1e",   # yüksek kontrast metin
    "text_md":      "#505f76",   # orta metin / etiket
    "text_lo":      "#737685",   # düşük önem
    "border":       "#e0e3e5",   # ince kenarlık
    "bg2":          "#eceef0",   # ikincil zemin / konteynır
    "success":      "#16a34a",   # yeşil
    "success_bg":   "#dcfce7",
    "danger":       "#dc2626",   # kırmızı
    "danger_bg":    "#fee2e2",
    "warning":      "#d97706",   # amber
    "warning_bg":   "#fef3c7",
}

APP_STYLE = f"""
/* ── Genel ──────────────────────────────────────────────────────────────── */
* {{
    font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
    color: {C['text_hi']};
}}

QMainWindow, QWidget {{
    background-color: {C['bg']};
}}

QDialog {{
    background-color: {C['bg']};
}}

QLabel {{
    background: transparent;
    color: {C['text_hi']};
}}

/* ── Kenar çubuğu ───────────────────────────────────────────────────────── */
QListWidget#sidebar {{
    background-color: {C['surface']};
    border: none;
    border-right: 1px solid {C['border']};
    outline: none;
    padding: 6px 0;
}}

QListWidget#sidebar::item {{
    height: 42px;
    padding-left: 20px;
    border-radius: 8px;
    margin: 2px 8px;
    color: {C['text_md']};
    font-size: 13px;
}}

QListWidget#sidebar::item:selected {{
    background-color: {C['primary_light']};
    color: {C['primary']};
    font-weight: bold;
}}

QListWidget#sidebar::item:hover:!selected {{
    background-color: {C['bg']};
    color: {C['primary']};
}}

/* ── Butonlar ───────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {C['primary']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 34px;
}}

QPushButton:hover {{
    background-color: {C['primary_h']};
}}

QPushButton:pressed {{
    background-color: {C['primary_p']};
}}

QPushButton:disabled {{
    background-color: {C['bg2']};
    color: {C['text_lo']};
}}

QPushButton#flat, QPushButton[flat="true"] {{
    background-color: {C['bg2']};
    color: {C['text_md']};
    font-weight: 500;
}}

QPushButton#flat:hover, QPushButton[flat="true"]:hover {{
    background-color: {C['border']};
    color: {C['text_hi']};
}}

QPushButton#danger {{
    background-color: {C['danger']};
    color: #ffffff;
}}

QPushButton#danger:hover {{
    background-color: #b91c1c;
}}

/* ── Giriş alanları ─────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {C['surface']};
    border: 1.5px solid {C['border']};
    border-radius: 8px;
    padding: 7px 12px;
    color: {C['text_hi']};
    selection-background-color: #cdd9f5;
    min-height: 34px;
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {C['primary']};
}}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QTextEdit:disabled {{
    background-color: {C['bg']};
    color: {C['text_lo']};
    border-color: {C['bg2']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 18px;
    border: none;
    background: transparent;
}}

/* ── ComboBox ───────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {C['surface']};
    border: 1.5px solid {C['border']};
    border-radius: 8px;
    padding: 7px 12px;
    color: {C['text_hi']};
    min-height: 34px;
}}

QComboBox:focus {{
    border-color: {C['primary']};
}}

QComboBox:disabled {{
    background-color: {C['bg']};
    color: {C['text_lo']};
    border-color: {C['bg2']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}}

QComboBox QAbstractItemView {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    selection-background-color: {C['primary_light']};
    selection-color: {C['primary']};
    padding: 4px;
    outline: none;
}}

/* ── Tablo ──────────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {C['surface']};
    gridline-color: {C['bg2']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    alternate-background-color: #fafbfc;
    selection-background-color: {C['primary_light']};
    outline: none;
}}

QTableWidget::item {{
    padding: 6px 12px;
    border: none;
    color: {C['text_hi']};
}}

QTableWidget::item:selected {{
    background-color: {C['primary_light']};
    color: {C['primary']};
}}

QTableWidget::item:hover {{
    background-color: {C['bg']};
}}

QHeaderView::section {{
    background-color: {C['bg']};
    color: {C['text_md']};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {C['border']};
}}

QHeaderView {{
    background: {C['bg']};
    border: none;
}}

/* ── Durum çubuğu ───────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {C['surface']};
    border-top: 1px solid {C['border']};
    color: {C['text_md']};
    padding: 2px 8px;
}}

/* ── Kaydırma çubukları ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 7px;
    background: transparent;
    border-radius: 4px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #c8cdd6;
    border-radius: 4px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: #9aa3b0;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    height: 7px;
    background: transparent;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: #c8cdd6;
    border-radius: 4px;
    min-width: 28px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Onay kutusu ────────────────────────────────────────────────────────── */
QCheckBox {{
    color: {C['text_md']};
    spacing: 8px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border-radius: 4px;
    border: 1.5px solid {C['border']};
    background: {C['surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {C['primary']};
    border-color: {C['primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {C['primary']};
}}

/* ── Frame / Kart ───────────────────────────────────────────────────────── */
QFrame[role="card"] {{
    background-color: {C['surface']};
    border-radius: 12px;
    border: 1px solid {C['border']};
}}

/* ── Splitter ───────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {C['border']};
    width: 1px;
}}

/* ── MessageBox ─────────────────────────────────────────────────────────── */
QMessageBox {{
    background-color: {C['bg']};
}}

QMessageBox QLabel {{
    color: {C['text_hi']};
    font-size: 13px;
}}
"""
