from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
                             QListWidgetItem, QMessageBox, QDialog, QLabel,
                             QLineEdit, QFormLayout, QComboBox, QWidget, QFrame,
                             QInputDialog, QSizePolicy, QToolButton, QButtonGroup)
from PyQt6.QtCore import Qt, QSize
from modules.base import BaseModule
from api_client import api, APIError


# ── Yardımcı: modern panel kartı ──────────────────────────────────────────────
class CatalogPanel(QFrame):
    """Başlıklı, sağ üstte + butonu olan modern bir panel kartı."""
    def __init__(self, title, add_text="+ Ekle", accent="#5865f2", parent=None):
        super().__init__(parent)
        self.setObjectName("catalogPanel")
        self.setStyleSheet(f"""
            QFrame#catalogPanel {{
                background-color: rgba(255,255,255,0.02);
                border: 1px solid rgba(127,127,127,0.22);
                border-radius: 10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)

        # Başlık satırı
        head = QHBoxLayout()
        head.setSpacing(8)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 700; letter-spacing: 0.4px; border: none;"
        )
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            "font-size: 11px; color: #80848e; border: none; padding-left: 6px;"
        )
        head.addWidget(self.title_lbl)
        head.addWidget(self.count_lbl)
        head.addStretch()

        self.add_btn = QToolButton()
        self.add_btn.setText(add_text)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {accent};
                color: white;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                border: none;
            }}
            QToolButton:hover   {{ background-color: rgba(88,101,242,0.85); }}
            QToolButton:disabled {{ background-color: rgba(127,127,127,0.25); color: #80848e; }}
        """)
        head.addWidget(self.add_btn)
        root.addLayout(head)

        # Alt başlık / context bilgisi
        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet(
            "font-size: 11px; color: #80848e; border: none;"
        )
        self.sub_lbl.setWordWrap(True)
        root.addWidget(self.sub_lbl)

        # İçerik alanı (dışarıdan eklenecek)
        self.body_lay = QVBoxLayout()
        self.body_lay.setSpacing(6)
        root.addLayout(self.body_lay, 1)

    def set_subtitle(self, text):
        self.sub_lbl.setText(text)
        self.sub_lbl.setVisible(bool(text))

    def set_count(self, n):
        self.count_lbl.setText(f"· {n}" if n else "")


# ── Ana modül ─────────────────────────────────────────────────────────────────
class CatalogModule(BaseModule):
    """Ürün Tipi / Marka / Model yönetimi — modern, sade."""

    LIST_STYLE = """
        QListWidget {
            background-color: transparent;
            border: 1px solid rgba(127,127,127,0.18);
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }
        QListWidget::item {
            padding: 9px 12px;
            border-radius: 6px;
            margin: 2px 2px;
        }
        QListWidget::item:hover    { background-color: rgba(127,127,127,0.10); }
        QListWidget::item:selected { background-color: rgba(88,101,242,0.22);
                                     color: palette(window-text); }
    """

    SEASONS = [("Tümü", None), ("Kışlık", "Kislik"),
               ("Yazlık", "Yazlik"), ("4 Mevsim", "4 Mevsim")]

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)

        # ── Header ───────────────────────────────────────────────────
        title = QLabel("Katalog Yönetimi")
        title.setStyleSheet("font-size: 22px; font-weight: 700; border: none;")
        layout.addWidget(title)

        hint = QLabel("Ürün tiplerini, markalarını ve modellerini buradan düzenleyin.")
        hint.setStyleSheet("font-size: 13px; color: #80848e; border: none;")
        layout.addWidget(hint)

        # ── Breadcrumb (aktif seçim göstergesi) ──────────────────────
        self.breadcrumb = QLabel("Tip seçilmedi")
        self.breadcrumb.setStyleSheet(
            "font-size: 12px; color: #80848e; border: none; padding: 4px 0;"
        )
        layout.addWidget(self.breadcrumb)

        # ── 3 Panel satırı ───────────────────────────────────────────
        panels_row = QHBoxLayout()
        panels_row.setSpacing(14)

        self.type_panel  = CatalogPanel("ÜRÜN TİPLERİ", "+ Yeni Tip",   "#27ae60")
        self.brand_panel = CatalogPanel("MARKALAR",     "+ Yeni Marka", "#2980b9")
        self.model_panel = CatalogPanel("MODELLER",     "+ Yeni Model", "#8e44ad")

        # Paneller eşit genişlikte
        for p in (self.type_panel, self.brand_panel, self.model_panel):
            panels_row.addWidget(p, 1)

        layout.addLayout(panels_row, 1)

        # ── Tip listesi ──────────────────────────────────────────────
        self.type_list = QListWidget()
        self.type_list.setStyleSheet(self.LIST_STYLE)
        self.type_list.currentItemChanged.connect(self._on_type_selected)
        self.type_panel.body_lay.addWidget(self.type_list, 1)
        self.type_panel.add_btn.clicked.connect(self._add_type)
        self._add_del_footer(self.type_panel, self._del_type)

        # ── Marka listesi ────────────────────────────────────────────
        self.brand_list = QListWidget()
        self.brand_list.setStyleSheet(self.LIST_STYLE)
        self.brand_list.currentItemChanged.connect(self._on_brand_selected)
        self.brand_panel.body_lay.addWidget(self.brand_list, 1)
        self.brand_panel.add_btn.clicked.connect(self._add_brand)
        self.brand_panel.add_btn.setEnabled(False)
        self._add_del_footer(self.brand_panel, self._del_brand, name="brand")
        self.brand_panel.set_subtitle("← Soldan bir tip seçin")

        # ── Model panel içeriği (mevsim segmentleri + liste) ────────
        # Mevsim segment butonları
        self.season_row = QWidget()
        season_lay = QHBoxLayout(self.season_row)
        season_lay.setContentsMargins(0, 0, 0, 0)
        season_lay.setSpacing(6)
        self.season_group = QButtonGroup(self.season_row)
        self.season_group.setExclusive(True)
        self._season_btns = []
        for i, (label, value) in enumerate(self.SEASONS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("season_value", value)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._season_btn_style())
            btn.clicked.connect(self._on_season_changed)
            self.season_group.addButton(btn, i)
            season_lay.addWidget(btn)
            self._season_btns.append(btn)
        season_lay.addStretch()
        self._season_btns[0].setChecked(True)
        self.season_row.setVisible(False)
        self.model_panel.body_lay.addWidget(self.season_row)

        self.model_list = QListWidget()
        self.model_list.setStyleSheet(self.LIST_STYLE)
        self.model_list.currentItemChanged.connect(self._on_model_selected)
        self.model_panel.body_lay.addWidget(self.model_list, 1)
        self.model_panel.add_btn.clicked.connect(self._add_model)
        self.model_panel.add_btn.setEnabled(False)
        self._add_del_footer(self.model_panel, self._del_model, name="model")
        self.model_panel.set_subtitle("← Önce tip ve marka seçin")

        # Durum
        self._selected_type_id    = None
        self._selected_type_name  = ""
        self._selected_brand_id   = None
        self._selected_brand_name = ""

    # ── Yardımcı UI ──────────────────────────────────────────────────
    def _add_del_footer(self, panel, del_callback, name=""):
        """Her panelin altına 'Sil' butonu ekler (seçim yapılınca aktifleşir)."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        btn = QPushButton("🗑  Seçiliyi Sil")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setEnabled(False)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e74c3c;
                border: 1px solid rgba(231,76,60,0.4);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(231,76,60,0.12); }
            QPushButton:disabled { color: #80848e; border: 1px solid rgba(127,127,127,0.2); }
        """)
        btn.clicked.connect(del_callback)
        row.addStretch()
        row.addWidget(btn)
        panel.body_lay.addLayout(row)

        # Panel başına referans tut
        setattr(self, f"_del_{name or 'type'}_btn", btn)

    def _season_btn_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #80848e;
                border: 1px solid rgba(127,127,127,0.25);
                border-radius: 14px;
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { color: palette(window-text);
                                border: 1px solid rgba(127,127,127,0.5); }
            QPushButton:checked {
                background-color: #8e44ad;
                color: white;
                border: 1px solid #8e44ad;
            }
        """

    # ── Yükleme ──────────────────────────────────────────────────────
    def refresh_data(self):
        self._load_types()

    def _load_types(self):
        try:
            types = api.get_product_types()
            self.type_list.clear()
            for t in types:
                item = QListWidgetItem(t["name"])
                item.setData(Qt.ItemDataRole.UserRole, t["id"])
                self.type_list.addItem(item)
            self.type_panel.set_count(len(types))
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _on_type_selected(self, item, _prev=None):
        if not item:
            self._selected_type_id = None
            self._selected_type_name = ""
            self.brand_list.clear()
            self.brand_panel.add_btn.setEnabled(False)
            self.brand_panel.set_subtitle("← Soldan bir tip seçin")
            self._del_type_btn.setEnabled(False)
            self._update_breadcrumb()
            return
        self._selected_type_id   = item.data(Qt.ItemDataRole.UserRole)
        self._selected_type_name = item.text()
        self._del_type_btn.setEnabled(True)

        self.brand_panel.add_btn.setEnabled(True)
        self.brand_panel.set_subtitle(f"'{item.text()}' için markalar")
        self._load_brands()

        # Model panel sıfırlama
        self.model_list.clear()
        self.model_panel.add_btn.setEnabled(False)
        self._del_model_btn.setEnabled(False)

        # Mevsim satırı sadece Lastik'te
        is_tire = ("lastik" in (self._selected_type_name or "").lower())
        self.season_row.setVisible(is_tire)
        if is_tire:
            self.model_panel.set_subtitle("Mevsim seçip model ekleyin (Kışlık/Yazlık/4 Mevsim)")
        else:
            self.model_panel.set_subtitle("← Bir marka seçin")

        self._update_breadcrumb()

    def _load_brands(self):
        if not self._selected_type_id: return
        try:
            brands = api.get_product_brands(self._selected_type_id)
            self.brand_list.clear()
            self.model_list.clear()
            self._del_brand_btn.setEnabled(False)
            self._del_model_btn.setEnabled(False)
            self.model_panel.add_btn.setEnabled(False)
            for b in brands:
                item = QListWidgetItem(b["name"])
                item.setData(Qt.ItemDataRole.UserRole, b["id"])
                self.brand_list.addItem(item)
            self.brand_panel.set_count(len(brands))
            self.model_panel.set_count(0)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _on_brand_selected(self, item, _prev=None):
        if not item:
            self._selected_brand_id   = None
            self._selected_brand_name = ""
            self.model_list.clear()
            self.model_panel.add_btn.setEnabled(False)
            self._del_brand_btn.setEnabled(False)
            self._update_breadcrumb()
            return
        self._selected_brand_id   = item.data(Qt.ItemDataRole.UserRole)
        self._selected_brand_name = item.text()
        self._del_brand_btn.setEnabled(True)
        self.model_panel.add_btn.setEnabled(True)
        self.model_panel.set_subtitle(f"'{item.text()}' modelleri")
        self._load_models()
        self._update_breadcrumb()

    def _on_model_selected(self, item, _prev=None):
        self._del_model_btn.setEnabled(bool(item))

    def _load_models(self):
        if not self._selected_brand_id:
            self.model_list.clear()
            return
        try:
            is_tire = ("lastik" in (self._selected_type_name or "").lower())
            season  = self._current_season() if is_tire else None
            models  = api.get_product_models(self._selected_brand_id, season=season)
            self.model_list.clear()
            self._del_model_btn.setEnabled(False)
            for m in models:
                label = m["name"]
                if is_tire and m.get("season"):
                    label = f"[{m['season']}]  {m['name']}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, m["id"])
                self.model_list.addItem(item)
            self.model_panel.set_count(len(models))
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _current_season(self):
        for btn in self._season_btns:
            if btn.isChecked():
                return btn.property("season_value")
        return None

    def _on_season_changed(self):
        if self._selected_brand_id and self._selected_type_name == "Lastik":
            self._load_models()

    def _update_breadcrumb(self):
        parts = []
        if self._selected_type_name:  parts.append(f"<b>{self._selected_type_name}</b>")
        if self._selected_brand_name: parts.append(f"<b>{self._selected_brand_name}</b>")
        if parts:
            self.breadcrumb.setText("  →  ".join(parts))
        else:
            self.breadcrumb.setText("Tip seçilmedi")

    # ── Tip işlemleri ────────────────────────────────────────────────
    def _add_type(self):
        name, ok = self._ask("Yeni Tip", "Tip adı:")
        if not (ok and name): return
        try:
            api.create_product_type(name); self._load_types()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_type(self):
        item = self.type_list.currentItem()
        if not item: return
        if QMessageBox.question(self, "Onay",
                                f"'{item.text()}' tipini silmek istiyor musunuz?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        try:
            api.delete_product_type(item.data(Qt.ItemDataRole.UserRole))
            self._load_types()
            self.brand_list.clear(); self.model_list.clear()
            self.brand_panel.set_count(0); self.model_panel.set_count(0)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    # ── Marka işlemleri ──────────────────────────────────────────────
    def _add_brand(self):
        if not self._selected_type_id: return
        name, ok = self._ask("Yeni Marka", "Marka adı:")
        if not (ok and name): return
        try:
            api.create_product_brand(self._selected_type_id, name)
            self._load_brands()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_brand(self):
        item = self.brand_list.currentItem()
        if not item: return
        if QMessageBox.question(self, "Onay",
                                f"'{item.text()}' markasını silmek istiyor musunuz?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        try:
            api.delete_product_brand(item.data(Qt.ItemDataRole.UserRole))
            self._load_brands(); self.model_list.clear()
            self.model_panel.set_count(0)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    # ── Model işlemleri ──────────────────────────────────────────────
    def _add_model(self):
        if not self._selected_brand_id: return
        is_tire = ("lastik" in (self._selected_type_name or "").lower())
        season  = None
        if is_tire:
            options = ["Kislik", "Yazlik", "4 Mevsim"]
            season, ok = QInputDialog.getItem(self, "Mevsim Seçin",
                                              "Bu model hangi mevsim için?",
                                              options, 0, False)
            if not ok: return
        name, ok = self._ask("Yeni Model", "Model adı:")
        if not (ok and name): return
        try:
            api.create_product_model(self._selected_brand_id, name, season=season)
            self._load_models()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_model(self):
        item = self.model_list.currentItem()
        if not item: return
        if QMessageBox.question(self, "Onay",
                                f"'{item.text()}' modelini silmek istiyor musunuz?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        try:
            api.delete_product_model(item.data(Qt.ItemDataRole.UserRole))
            self._load_models()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _ask(self, title, label):
        return QInputDialog.getText(self, title, label)
