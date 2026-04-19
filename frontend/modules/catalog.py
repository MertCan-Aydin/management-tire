from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
                             QListWidgetItem, QMessageBox, QDialog, QLabel,
                             QLineEdit, QFormLayout, QComboBox, QSplitter,
                             QWidget, QFrame)
from PyQt6.QtCore import Qt
from modules.base import BaseModule
from api_client import api, APIError


class CatalogModule(BaseModule):
    """Ürün Tipi / Marka / Model yönetimi."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Katalog Yonetimi")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel("Urun tiplerini, markalarini ve modellerini buradan ekleyip yonetebilirsiniz.")
        hint.setStyleSheet("font-size: 12px; color: #80848e;")
        layout.addWidget(hint)

        # 3 sütunlu splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ── Sol: Tipler ──────────────────────────────────────────────────────
        type_frame = self._make_panel("Urun Tipleri")
        type_inner = type_frame.findChild(QVBoxLayout)

        self.type_list = QListWidget()
        self.type_list.currentItemChanged.connect(self._on_type_selected)
        type_inner.addWidget(self.type_list)

        type_btns = QHBoxLayout()
        self.btn_add_type = QPushButton("+ Tip Ekle")
        self.btn_add_type.setStyleSheet("background-color: #27ae60; color: white; padding: 5px 10px;")
        self.btn_del_type = QPushButton("Sil")
        self.btn_del_type.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px;")
        self.btn_add_type.clicked.connect(self._add_type)
        self.btn_del_type.clicked.connect(self._del_type)
        type_btns.addWidget(self.btn_add_type)
        type_btns.addWidget(self.btn_del_type)
        type_inner.addLayout(type_btns)
        splitter.addWidget(type_frame)

        # ── Orta: Markalar ───────────────────────────────────────────────────
        brand_frame = self._make_panel("Markalar")
        brand_inner = brand_frame.findChild(QVBoxLayout)

        self.brand_lbl = QLabel("Tip secin")
        self.brand_lbl.setStyleSheet("font-size: 11px; color: #80848e;")
        brand_inner.addWidget(self.brand_lbl)

        self.brand_list = QListWidget()
        self.brand_list.currentItemChanged.connect(self._on_brand_selected)
        brand_inner.addWidget(self.brand_list)

        brand_btns = QHBoxLayout()
        self.btn_add_brand = QPushButton("+ Marka Ekle")
        self.btn_add_brand.setStyleSheet("background-color: #2980b9; color: white; padding: 5px 10px;")
        self.btn_del_brand = QPushButton("Sil")
        self.btn_del_brand.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px;")
        self.btn_add_brand.setEnabled(False)
        self.btn_del_brand.setEnabled(False)
        self.btn_add_brand.clicked.connect(self._add_brand)
        self.btn_del_brand.clicked.connect(self._del_brand)
        brand_btns.addWidget(self.btn_add_brand)
        brand_btns.addWidget(self.btn_del_brand)
        brand_inner.addLayout(brand_btns)
        splitter.addWidget(brand_frame)

        # ── Sağ: Modeller ────────────────────────────────────────────────────
        model_frame = self._make_panel("Modeller")
        model_inner = model_frame.findChild(QVBoxLayout)

        self.model_lbl = QLabel("Marka secin")
        self.model_lbl.setStyleSheet("font-size: 11px; color: #80848e;")
        model_inner.addWidget(self.model_lbl)

        self.model_note = QLabel("")
        self.model_note.setStyleSheet("font-size: 11px; color: #f0b232;")
        self.model_note.setWordWrap(True)
        model_inner.addWidget(self.model_note)

        # Mevsim filtresi (sadece Lastik tipinde görünür)
        season_row = QHBoxLayout()
        self.season_lbl = QLabel("Mevsim:")
        self.season_lbl.setStyleSheet("font-size: 11px; border: none;")
        self.season_combo = QComboBox()
        self.season_combo.addItem("Tumu", None)
        for s in ("Kislik", "Yazlik", "4 Mevsim"):
            self.season_combo.addItem(s, s)
        self.season_combo.currentIndexChanged.connect(self._on_season_changed)
        season_row.addWidget(self.season_lbl)
        season_row.addWidget(self.season_combo, 1)
        self.season_row_widget = QWidget()
        self.season_row_widget.setLayout(season_row)
        self.season_row_widget.setVisible(False)
        model_inner.addWidget(self.season_row_widget)

        self.model_list = QListWidget()
        model_inner.addWidget(self.model_list)

        model_btns = QHBoxLayout()
        self.btn_add_model = QPushButton("+ Model Ekle")
        self.btn_add_model.setStyleSheet("background-color: #8e44ad; color: white; padding: 5px 10px;")
        self.btn_del_model = QPushButton("Sil")
        self.btn_del_model.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 10px;")
        self.btn_add_model.setEnabled(False)
        self.btn_del_model.setEnabled(False)
        self.btn_add_model.clicked.connect(self._add_model)
        self.btn_del_model.clicked.connect(self._del_model)
        model_btns.addWidget(self.btn_add_model)
        model_btns.addWidget(self.btn_del_model)
        model_inner.addLayout(model_btns)
        splitter.addWidget(model_frame)

        splitter.setSizes([200, 250, 250])

        self._selected_type_id  = None
        self._selected_brand_id = None
        self._selected_type_name = ""

    def _make_panel(self, title):
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #3b3d43; border-radius: 6px; }")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 13px; font-weight: 700; border: none;")
        lay.addWidget(lbl)
        return frame

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
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _on_type_selected(self, item):
        if not item:
            self._selected_type_id = None
            self.brand_list.clear()
            self.btn_add_brand.setEnabled(False)
            return
        self._selected_type_id   = item.data(Qt.ItemDataRole.UserRole)
        self._selected_type_name = item.text()
        self.brand_lbl.setText(f"{item.text()} markalari")
        self.btn_add_brand.setEnabled(True)
        self._load_brands()

        # Lastik ise mevsim filtresi görünür
        is_tire = (self._selected_type_name == "Lastik")
        self.season_row_widget.setVisible(is_tire)
        if is_tire:
            self.model_note.setText("Lastik modelleri mevsime göre eklenir (Kışlık/Yazlık/4 Mevsim).")
        else:
            self.model_note.setText("")

    def _load_brands(self):
        if not self._selected_type_id: return
        try:
            brands = api.get_product_brands(self._selected_type_id)
            self.brand_list.clear()
            self.model_list.clear()
            self.btn_del_brand.setEnabled(False)
            self.btn_add_model.setEnabled(False)
            self.btn_del_model.setEnabled(False)
            for b in brands:
                item = QListWidgetItem(b["name"])
                item.setData(Qt.ItemDataRole.UserRole, b["id"])
                self.brand_list.addItem(item)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _on_brand_selected(self, item):
        if not item:
            self._selected_brand_id = None
            self.model_list.clear()
            self.btn_del_brand.setEnabled(False)
            self.btn_add_model.setEnabled(False)
            return
        self._selected_brand_id = item.data(Qt.ItemDataRole.UserRole)
        self.model_lbl.setText(f"{item.text()} modelleri")
        self.btn_del_brand.setEnabled(True)

        # Artik Lastik dahil tum tiplerde model secmeli
        self.btn_add_model.setEnabled(True)
        self._load_models()

    def _load_models(self):
        if not self._selected_brand_id: return
        try:
            is_tire = (self._selected_type_name == "Lastik")
            season  = self.season_combo.currentData() if is_tire else None
            models = api.get_product_models(self._selected_brand_id, season=season)
            self.model_list.clear()
            self.btn_del_model.setEnabled(False)
            for m in models:
                label = m["name"]
                if is_tire and m.get("season"):
                    label = f"[{m['season']}] {m['name']}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, m["id"])
                self.model_list.addItem(item)
            self.model_list.itemClicked.connect(lambda: self.btn_del_model.setEnabled(True))
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _on_season_changed(self, _):
        if self._selected_brand_id and self._selected_type_name == "Lastik":
            self._load_models()

    # ── Tip işlemleri ─────────────────────────────────────────────────────────
    def _add_type(self):
        name, ok = self._ask("Yeni Tip", "Tip adi:")
        if not (ok and name): return
        try:
            api.create_product_type(name)
            self._load_types()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_type(self):
        item = self.type_list.currentItem()
        if not item: QMessageBox.information(self, "Bilgi", "Lutfen bir tip secin."); return
        reply = QMessageBox.question(self, "Onay", f"'{item.text()}' tipini silmek istiyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product_type(item.data(Qt.ItemDataRole.UserRole))
                self._load_types()
                self.brand_list.clear(); self.model_list.clear()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    # ── Marka işlemleri ───────────────────────────────────────────────────────
    def _add_brand(self):
        if not self._selected_type_id: return
        name, ok = self._ask("Yeni Marka", "Marka adi:")
        if not (ok and name): return
        try:
            api.create_product_brand(self._selected_type_id, name)
            self._load_brands()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_brand(self):
        item = self.brand_list.currentItem()
        if not item: return
        reply = QMessageBox.question(self, "Onay", f"'{item.text()}' markasini silmek istiyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product_brand(item.data(Qt.ItemDataRole.UserRole))
                self._load_brands()
                self.model_list.clear()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    # ── Model işlemleri ───────────────────────────────────────────────────────
    def _add_model(self):
        if not self._selected_brand_id: return
        is_tire = (self._selected_type_name == "Lastik")
        season  = None
        if is_tire:
            from PyQt6.QtWidgets import QInputDialog
            options = ["Kislik", "Yazlik", "4 Mevsim"]
            season, ok = QInputDialog.getItem(self, "Mevsim Secin",
                                              "Bu model hangi mevsim icin?",
                                              options, 0, False)
            if not ok: return
        name, ok = self._ask("Yeni Model", "Model adi:")
        if not (ok and name): return
        try:
            api.create_product_model(self._selected_brand_id, name, season=season)
            self._load_models()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _del_model(self):
        item = self.model_list.currentItem()
        if not item: return
        reply = QMessageBox.question(self, "Onay", f"'{item.text()}' modelini silmek istiyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product_model(item.data(Qt.ItemDataRole.UserRole))
                self._load_models()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _ask(self, title, label):
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, title, label)
