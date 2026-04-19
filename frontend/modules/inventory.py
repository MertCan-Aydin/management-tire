from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QComboBox,
                             QDoubleSpinBox, QSpinBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.base import BaseModule
from api_client import api, APIError

LOW_STOCK_THRESHOLD = 3


# ── Ürün Ekle / Düzenle Dialog ────────────────────────────────────────────────
class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None, suppliers=None):
        super().__init__(parent)
        self.product   = product
        self.suppliers = suppliers or []
        self.setWindowTitle("Urun Ekle" if not product else "Urun Duzenle")
        self.setMinimumWidth(500)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Temel alanlar
        self.name_input = QLineEdit()
        self.desc_input = QLineEdit()
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(1_000_000.0)
        self.cost_input.setDecimals(2)
        self.cost_input.setSuffix(" TL")
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(100_000)

        # Ürün tipi
        self.type_combo = QComboBox()
        self.type_combo.addItem("-- Tip Secin --", None)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        # Marka
        self.brand_combo = QComboBox()
        self.brand_combo.addItem("-- Marka Secin --", None)
        self.brand_combo.setEnabled(False)
        self.brand_combo.currentIndexChanged.connect(self._on_brand_changed)

        # Model (lastik → yazılabilir, diğer → seçmeli)
        self.model_combo = QComboBox()
        self.model_combo.addItem("-- Model Secin --", None)
        self.model_combo.setEnabled(False)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Lastik modeli (205/55R16 vb.)")
        self.model_input.setVisible(False)

        # Tedarikçi
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- Tedarikci Secin --", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(s["name"], s["id"])

        layout.addRow("Urun Adi *:", self.name_input)
        layout.addRow("Aciklama:", self.desc_input)
        layout.addRow("Urun Tipi:", self.type_combo)
        layout.addRow("Marka:", self.brand_combo)
        self.model_row_combo = QLabel("Model:")
        layout.addRow(self.model_row_combo, self.model_combo)
        self.model_row_input = QLabel("Model (yaziniz):")
        layout.addRow(self.model_row_input, self.model_input)
        self.model_row_input.setVisible(False)
        layout.addRow("Alis / Maliyet:", self.cost_input)
        layout.addRow("Baslangic Stok:", self.stock_input)
        layout.addRow("Tedarikci:", self.supplier_combo)

        btn_layout = QHBoxLayout()
        save_btn   = QPushButton("Kaydet")
        cancel_btn = QPushButton("Iptal")
        cancel_btn.setStyleSheet("background-color: #555; color: white;")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        # Düzenleme modunda mevcut değerleri doldur
        if product:
            self.name_input.setText(product.get("name", ""))
            self.desc_input.setText(product.get("description") or "")
            self.cost_input.setValue(product.get("cost_price") or 0.0)
            self.stock_input.setValue(product.get("stock", 0))
            idx = self.supplier_combo.findData(product.get("supplier_id"))
            if idx >= 0: self.supplier_combo.setCurrentIndex(idx)
            # Tip/marka/model sonradan doldurulacak (combo yüklendikten sonra)
            self._prefill_type = product.get("product_type_id")
            self._prefill_brand = product.get("brand_id")
            self._prefill_model_id = None  # model combo'da yok, text var
            self._prefill_model_text = product.get("brand_model") or ""
        else:
            self._prefill_type  = None
            self._prefill_brand = None
            self._prefill_model_text = ""

        # Tipleri yükle
        self._load_types()

    def _load_types(self):
        try:
            types = api.get_product_types()
            self.type_combo.clear()
            self.type_combo.addItem("-- Tip Secin --", None)
            for t in types:
                self.type_combo.addItem(t["name"], t["id"])
            # Prefill
            if self._prefill_type:
                idx = self.type_combo.findData(self._prefill_type)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
        except APIError:
            pass

    def _on_type_changed(self, _):
        type_id = self.type_combo.currentData()
        self.brand_combo.clear()
        self.brand_combo.addItem("-- Marka Secin --", None)
        self.model_combo.clear()
        self.model_combo.addItem("-- Model Secin --", None)
        self.model_combo.setEnabled(False)
        self.model_input.clear()

        if not type_id:
            self.brand_combo.setEnabled(False)
            self._set_model_mode(None)
            return

        self.brand_combo.setEnabled(True)
        try:
            brands = api.get_product_brands(type_id)
            for b in brands:
                self.brand_combo.addItem(b["name"], b["id"])
        except APIError:
            pass

        # Lastik mi → serbest model, değilse seçmeli
        type_name = self.type_combo.currentText()
        self._set_model_mode(type_name)

        # Prefill marka
        if self._prefill_brand:
            idx = self.brand_combo.findData(self._prefill_brand)
            if idx >= 0:
                self.brand_combo.setCurrentIndex(idx)
            self._prefill_brand = None

    def _on_brand_changed(self, _):
        brand_id  = self.brand_combo.currentData()
        type_name = self.type_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItem("-- Model Secin --", None)

        if not brand_id:
            self.model_combo.setEnabled(False)
            return

        # Lastik → serbest metin, model combo kapalı
        if type_name == "Lastik":
            self.model_combo.setEnabled(False)
            if self._prefill_model_text:
                self.model_input.setText(self._prefill_model_text)
                self._prefill_model_text = ""
            return

        # Diğer tiplerde modelleri yükle
        self.model_combo.setEnabled(True)
        try:
            models = api.get_product_models(brand_id)
            for m in models:
                self.model_combo.addItem(m["name"], m["id"])
            if self._prefill_model_text:
                idx = self.model_combo.findText(self._prefill_model_text)
                if idx >= 0:
                    self.model_combo.setCurrentIndex(idx)
                self._prefill_model_text = ""
        except APIError:
            pass

    def _set_model_mode(self, type_name):
        is_tire = (type_name == "Lastik")
        # Lastik: yazılabilir input, combo gizli
        self.model_input.setVisible(is_tire)
        self.model_row_input.setVisible(is_tire)
        self.model_combo.setVisible(not is_tire)
        self.model_row_combo.setVisible(not is_tire)

    def get_data(self):
        type_name   = self.type_combo.currentText()
        brand_model = None
        if type_name == "Lastik":
            brand_model = self.model_input.text().strip() or None
        else:
            # Seçmeli modelden metin al
            if self.model_combo.currentData():
                brand_model = self.model_combo.currentText()

        return {
            "name":            self.name_input.text().strip(),
            "description":     self.desc_input.text().strip() or None,
            "cost_price":      self.cost_input.value(),
            "price":           0.0,
            "stock":           self.stock_input.value(),
            "supplier_id":     self.supplier_combo.currentData(),
            "product_type_id": self.type_combo.currentData(),
            "brand_id":        self.brand_combo.currentData(),
            "brand_model":     brand_model,
        }


# ── Stok Düzenle Dialog ───────────────────────────────────────────────────────
class BatchEditDialog(QDialog):
    def __init__(self, parent, batch):
        super().__init__(parent)
        self.setWindowTitle("Partiyi Duzenle")
        self.setFixedSize(300, 160)
        layout = QFormLayout(self)
        layout.setSpacing(10)
        self.qty_input  = QSpinBox()
        self.qty_input.setMinimum(0); self.qty_input.setMaximum(100_000)
        self.qty_input.setValue(batch["quantity"])
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(1_000_000.0); self.cost_input.setDecimals(2)
        self.cost_input.setSuffix(" TL"); self.cost_input.setValue(batch["cost_price"])
        layout.addRow("Miktar:", self.qty_input)
        layout.addRow("Maliyet:", self.cost_input)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Kaydet"); no_btn = QPushButton("Iptal")
        no_btn.setStyleSheet("background-color: #555; color: white;")
        ok_btn.clicked.connect(self.accept); no_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn); btn_row.addWidget(no_btn)
        layout.addRow(btn_row)

    def get_data(self):
        return {"quantity": self.qty_input.value(), "cost_price": self.cost_input.value()}


class StockDialog(QDialog):
    def __init__(self, parent, product):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle(f"Stok Duzenle — {product['name']}")
        self.setMinimumSize(640, 460)
        self._build(); self._load()

    def _build(self):
        layout = QVBoxLayout(self); layout.setSpacing(10)
        title = QLabel(f"{self.product['name']} — Stok Partileri")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Eklenme Tarihi", "Miktar", "Maliyet (TL)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.lbl_total = QLabel("Toplam stok: 0 adet")
        self.lbl_total.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(self.lbl_total)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #444;"); layout.addWidget(line)
        add_title = QLabel("Yeni Parti Ekle")
        add_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(add_title)
        form = QHBoxLayout(); form.setSpacing(10)
        form.addWidget(QLabel("Miktar:"))
        self.new_qty = QSpinBox(); self.new_qty.setMinimum(1); self.new_qty.setMaximum(100_000); self.new_qty.setValue(1)
        form.addWidget(self.new_qty)
        form.addWidget(QLabel("Maliyet (TL):"))
        self.new_cost = QDoubleSpinBox(); self.new_cost.setMaximum(1_000_000.0); self.new_cost.setDecimals(2)
        self.new_cost.setValue(self.product.get("cost_price") or 0.0)
        form.addWidget(self.new_cost)
        self.btn_add_batch = QPushButton("+ Parti Ekle")
        self.btn_add_batch.setStyleSheet("background-color: #27ae60; color: white; padding: 6px 14px;")
        self.btn_add_batch.clicked.connect(self._add_batch)
        form.addWidget(self.btn_add_batch); form.addStretch()
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        self.btn_edit_b = QPushButton("Secili Partiyi Duzenle")
        self.btn_del_b  = QPushButton("Secili Partiyi Sil")
        self.btn_del_b.setStyleSheet("background-color: #e74c3c; color: white; padding: 6px 14px;")
        self.btn_edit_b.clicked.connect(self._edit_batch)
        self.btn_del_b.clicked.connect(self._delete_batch)
        btn_row.addWidget(self.btn_edit_b); btn_row.addWidget(self.btn_del_b); btn_row.addStretch()
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("background-color: #555; color: white; padding: 6px 14px;")
        close_btn.clicked.connect(self.accept); btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load(self):
        try:
            batches = api.get_product_batches(self.product["id"])
            self.table.setRowCount(0); total = 0
            for i, b in enumerate(batches):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(b["id"])))
                date_str = b.get("date_added", "")[:16].replace("T", " ") if b.get("date_added") else "-"
                self.table.setItem(i, 1, QTableWidgetItem(date_str))
                qty_item = QTableWidgetItem(str(b["quantity"]))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if b["quantity"] == 0: qty_item.setForeground(QColor("#888"))
                self.table.setItem(i, 2, qty_item)
                cost_item = QTableWidgetItem(f"{b['cost_price']:,.2f}")
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, 3, cost_item)
                total += b["quantity"]
            self.lbl_total.setText(f"Toplam stok: {total} adet")
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _get_selected(self):
        items = self.table.selectedItems()
        if not items: QMessageBox.information(self, "Bilgi", "Lutfen bir parti secin."); return None
        row = items[0].row()
        return {"id": int(self.table.item(row, 0).text()),
                "quantity": int(self.table.item(row, 2).text()),
                "cost_price": float(self.table.item(row, 3).text().replace(",", ""))}

    def _add_batch(self):
        cost = self.new_cost.value()
        if cost <= 0: QMessageBox.warning(self, "Hata", "Maliyet 0'dan buyuk olmali."); return
        try:
            api.add_product_batch(self.product["id"], {"quantity": self.new_qty.value(), "cost_price": cost})
            self._load()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _edit_batch(self):
        b = self._get_selected()
        if not b: return
        dlg = BatchEditDialog(self, b)
        if dlg.exec():
            try:
                api.update_product_batch(self.product["id"], b["id"], dlg.get_data())
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _delete_batch(self):
        b = self._get_selected()
        if not b: return
        reply = QMessageBox.question(self, "Onay",
            f"Bu partiyi silmek istediginize emin misiniz?\n({b['quantity']} adet, {b['cost_price']:,.2f} TL)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product_batch(self.product["id"], b["id"]); self._load()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))


# ── Inventory modülü ──────────────────────────────────────────────────────────
class InventoryModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(8)
        controls = QHBoxLayout()
        title = QLabel("Urun ve Stok Yonetimi")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_add = QPushButton("+ Yeni Urun Ekle")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 14px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_product)
        controls.addWidget(title); controls.addStretch(); controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Urun Adi", "Tip", "Marka", "Model", "Tedarikci", "Alis (TL)", "Stok"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_edit   = QPushButton("Urun Duzenle")
        self.btn_stock  = QPushButton("Stok Duzenle")
        self.btn_delete = QPushButton("Urunu Sil")
        self.btn_stock.setStyleSheet("background-color: #2980b9; color: white; padding: 5px 12px;")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 12px;")
        self.btn_edit.clicked.connect(self.edit_product)
        self.btn_stock.clicked.connect(self.manage_stock)
        self.btn_delete.clicked.connect(self.delete_product)
        actions.addWidget(self.btn_edit); actions.addWidget(self.btn_stock)
        actions.addWidget(self.btn_delete); actions.addStretch()
        layout.addLayout(actions)

    def refresh_data(self): self.load_products()

    def load_products(self):
        try:
            products = api.get_products()
            self.table.setRowCount(0)
            for row, p in enumerate(products):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(p["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(p.get("product_type_name") or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(p.get("brand_name") or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(p.get("brand_model") or "-"))
                self.table.setItem(row, 5, QTableWidgetItem(p.get("supplier_name") or "-"))
                cost_item = QTableWidgetItem(f"{p['cost_price']:,.2f}")
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 6, cost_item)
                stock_item = QTableWidgetItem(str(p["stock"]))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if p["stock"] <= 0: stock_item.setForeground(QColor("#f38ba8"))
                elif p["stock"] <= LOW_STOCK_THRESHOLD: stock_item.setForeground(QColor("#fab387"))
                self.table.setItem(row, 7, stock_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def get_selected_product(self):
        items = self.table.selectedItems()
        if not items: return None, None
        row = items[0].row()
        return int(self.table.item(row, 0).text()), self.table.item(row, 1).text()

    def add_product(self):
        try:
            suppliers = api.get_suppliers()
            dlg = ProductDialog(self, suppliers=suppliers)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]: QMessageBox.warning(self, "Hata", "Urun adi bos olamaz!"); return
                api.create_product(data); self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def edit_product(self):
        pid, _ = self.get_selected_product()
        if not pid: QMessageBox.information(self, "Bilgi", "Duzenlemek icin bir urun secin."); return
        try:
            products = api.get_products()
            product  = next((p for p in products if p["id"] == pid), None)
            if not product: return
            suppliers = api.get_suppliers()
            dlg = ProductDialog(self, product, suppliers)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]: QMessageBox.warning(self, "Hata", "Urun adi bos olamaz!"); return
                data["price"] = product["price"]
                api.update_product(pid, data); self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def manage_stock(self):
        pid, _ = self.get_selected_product()
        if not pid: QMessageBox.information(self, "Bilgi", "Stok duzenlemek icin bir urun secin."); return
        try:
            products = api.get_products()
            product  = next((p for p in products if p["id"] == pid), None)
            if not product: return
            dlg = StockDialog(self, product); dlg.exec()
            self.load_products()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_product(self):
        pid, name = self.get_selected_product()
        if not pid: QMessageBox.information(self, "Bilgi", "Silmek icin bir urun secin."); return
        reply = QMessageBox.question(self, "Onay", f"'{name}' urununu silmek istediginize emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product(pid); self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))