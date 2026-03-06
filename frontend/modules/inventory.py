from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QComboBox,
                             QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.base import BaseModule
from api_client import api, APIError

LOW_STOCK_THRESHOLD = 3


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None, suppliers=None):
        super().__init__(parent)
        self.product = product
        self.suppliers = suppliers or []
        self.setWindowTitle("Urun Ekle" if not product else "Urun Duzenle")
        self.setFixedSize(500, 400)
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.desc_input = QLineEdit()
        self.cost_input = QDoubleSpinBox(); self.cost_input.setMaximum(1000000.0); self.cost_input.setDecimals(2)
        self.price_input = QDoubleSpinBox(); self.price_input.setMaximum(1000000.0); self.price_input.setDecimals(2)
        self.price_input.valueChanged.connect(self._check_price)
        self.stock_input = QSpinBox(); self.stock_input.setMaximum(100000)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- Tedarikci Secin --", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(s["name"], s["id"])
        self.lbl_warning = QLabel(""); self.lbl_warning.setStyleSheet("color: #fab387; font-weight: bold;")

        if product:
            self.name_input.setText(product.get("name", ""))
            self.desc_input.setText(product.get("description") or "")
            self.cost_input.setValue(product.get("cost_price") or 0.0)
            self.price_input.setValue(product.get("price", 0.0))
            self.stock_input.setValue(product.get("stock", 0))
            idx = self.supplier_combo.findData(product.get("supplier_id"))
            if idx >= 0: self.supplier_combo.setCurrentIndex(idx)

        layout.addRow("Urun Adi:", self.name_input)
        layout.addRow("Aciklama:", self.desc_input)
        layout.addRow("Alis / Maliyet (TL):", self.cost_input)
        layout.addRow("Satis Fiyati (TL):", self.price_input)
        layout.addRow("", self.lbl_warning)
        layout.addRow("Stok Adedi:", self.stock_input)
        layout.addRow("Tedarikci:", self.supplier_combo)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet"); cancel_btn = QPushButton("Iptal")
        save_btn.clicked.connect(self.accept); cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn); btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _check_price(self):
        cost = self.cost_input.value(); price = self.price_input.value()
        if cost > 0 and price < cost:
            self.lbl_warning.setText(f"ZARAR: Satis fiyati alis fiyatindan ({cost:,.2f} TL) dusuk!")
        else:
            self.lbl_warning.setText("")

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
            "cost_price": self.cost_input.value(),
            "price": self.price_input.value(),
            "stock": self.stock_input.value(),
            "supplier_id": self.supplier_combo.currentData(),
        }


class InventoryModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        title = QLabel("Urun ve Stok Yonetimi"); title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_add = QPushButton("Yeni Urun Ekle")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_product)
        controls.addWidget(title); controls.addStretch(); controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Urun Adi", "Tedarikci", "Alis(TL)", "Satis(TL)", "Stok"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_edit = QPushButton("Secili Olani Duzenle / Stok Ekle")
        self.btn_delete = QPushButton("Secili Olani Sil")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
        self.btn_edit.clicked.connect(self.edit_product); self.btn_delete.clicked.connect(self.delete_product)
        actions.addWidget(self.btn_edit); actions.addWidget(self.btn_delete); actions.addStretch()
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
                self.table.setItem(row, 2, QTableWidgetItem(p.get("supplier_name") or "-"))
                cost_item = QTableWidgetItem(f"{p['cost_price']:,.2f}")
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, cost_item)
                price_item = QTableWidgetItem(f"{p['price']:,.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if p["cost_price"] > 0 and p["price"] < p["cost_price"]:
                    price_item.setForeground(QColor("#f38ba8"))
                self.table.setItem(row, 4, price_item)
                stock_item = QTableWidgetItem(str(p["stock"]))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if p["stock"] <= 0: stock_item.setForeground(QColor("#f38ba8"))
                elif p["stock"] <= LOW_STOCK_THRESHOLD: stock_item.setForeground(QColor("#fab387"))
                self.table.setItem(row, 5, stock_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items: return None
        return int(self.table.item(items[0].row(), 0).text())

    def add_product(self):
        try:
            suppliers = api.get_suppliers()
            dlg = ProductDialog(self, suppliers=suppliers)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]: QMessageBox.warning(self, "Hata", "Urun adi bos olamaz!"); return
                api.create_product(data)
                self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def edit_product(self):
        pid = self.get_selected_id()
        if not pid: QMessageBox.information(self, "Bilgi", "Duzenlemek icin bir urun secin."); return
        try:
            products = api.get_products()
            product = next((p for p in products if p["id"] == pid), None)
            if not product: return
            suppliers = api.get_suppliers()
            dlg = ProductDialog(self, product, suppliers)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]: QMessageBox.warning(self, "Hata", "Urun adi bos olamaz!"); return
                api.update_product(pid, data)
                self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_product(self):
        pid = self.get_selected_id()
        if not pid: QMessageBox.information(self, "Bilgi", "Silmek icin bir urun secin."); return
        reply = QMessageBox.question(self, "Onay", "Bu urunu silmek istediginize emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_product(pid)
                self.load_products()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))
