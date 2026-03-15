from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QInputDialog)
from PyQt6.QtCore import Qt
from modules.base import BaseModule
from api_client import api, APIError


class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Tedarikci Ekle" if not supplier else "Tedarikci Duzenle")
        self.setFixedSize(400, 200)
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        if supplier:
            self.name_input.setText(supplier.get("name", ""))
            self.contact_input.setText(supplier.get("contact_info") or "")
        layout.addRow("Firma Adi:", self.name_input)
        layout.addRow("Iletisim:", self.contact_input)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("Iptal")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {"name": self.name_input.text().strip(), "contact_info": self.contact_input.text().strip()}


class SuppliersModule(BaseModule):
    def __init__(self, parent=None):
        self._last_payment_id = None
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        title = QLabel("Tedarikci Yonetimi")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_add = QPushButton("Yeni Tedarikci Ekle")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_supplier)
        controls.addWidget(title); controls.addStretch(); controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Firma Adi", "Iletisim", "Guncel Borc (TL)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_edit = QPushButton("Secili Olani Duzenle")
        self.btn_delete = QPushButton("Secili Olani Sil")
        self.btn_pay = QPushButton("Borc Ode")
        self.btn_undo = QPushButton("Son Odemeyi Geri Al")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
        self.btn_pay.setStyleSheet("background-color: #f39c12; color: white; padding: 5px; font-weight: bold;")
        self.btn_undo.setStyleSheet("background-color: #e67e22; color: white; padding: 5px; font-weight: bold;")
        self.btn_undo.setEnabled(False)
        self.btn_edit.clicked.connect(self.edit_supplier)
        self.btn_delete.clicked.connect(self.delete_supplier)
        self.btn_pay.clicked.connect(self.pay_debt)
        self.btn_undo.clicked.connect(self.undo_last_payment)
        actions.addWidget(self.btn_edit); actions.addWidget(self.btn_pay)
        actions.addWidget(self.btn_undo); actions.addWidget(self.btn_delete); actions.addStretch()
        layout.addLayout(actions)

    def refresh_data(self):
        self.load_suppliers()

    def load_suppliers(self):
        try:
            suppliers = api.get_suppliers()
            self.table.setRowCount(0)
            for row, s in enumerate(suppliers):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(s["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(s.get("contact_info") or ""))
                debt_item = QTableWidgetItem(f"{s['current_debt']:,.2f}")
                debt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, debt_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items: return None
        return int(self.table.item(items[0].row(), 0).text())

    def add_supplier(self):
        dlg = SupplierDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Hata", "Firma adi bos olamaz!"); return
            try:
                api.create_supplier(data)
                self.load_suppliers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def edit_supplier(self):
        sid = self.get_selected_id()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Duzenlemek icin bir tedarikci secin."); return
        try:
            suppliers = api.get_suppliers()
            supplier = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier: return
            dlg = SupplierDialog(self, supplier)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]:
                    QMessageBox.warning(self, "Hata", "Firma adi bos olamaz!"); return
                api.update_supplier(sid, data)
                self.load_suppliers()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_supplier(self):
        sid = self.get_selected_id()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Silmek icin bir tedarikci secin."); return
        reply = QMessageBox.question(self, "Onay", "Bu tedarkciyi silmek istediginize emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_supplier(sid)
                self.load_suppliers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def pay_debt(self):
        sid = self.get_selected_id()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Borc odemek icin bir tedarikci secin."); return
        try:
            suppliers = api.get_suppliers()
            supplier = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier or supplier["current_debt"] <= 0:
                QMessageBox.information(self, "Bilgi", "Bu firmanin odenmemis borcu yok."); return
            amount, ok = QInputDialog.getDouble(
                self, "Borc Odeme",
                f"Odenecek Tutar (TL):\n(Mevcut Borc: {supplier['current_debt']:,.2f} TL)",
                decimals=2, min=0.01, max=supplier["current_debt"]
            )
            if not (ok and amount > 0): return
            result = api.pay_supplier_debt(sid, amount)
            self._last_payment_id = result["id"]
            self.btn_undo.setEnabled(True)
            QMessageBox.information(self, "Basarili", f"{amount:,.2f} TL odeme islendi.")
            self.load_suppliers()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def undo_last_payment(self):
        if not self._last_payment_id:
            QMessageBox.information(self, "Bilgi", "Geri alinacak odeme bulunamadi."); return
        reply = QMessageBox.question(self, "Son Odemeyi Geri Al",
                                     "Son tedarikci odemesi geri alinacak. Onayliyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.undo_supplier_payment(sid, self._last_payment_id)
            self._last_payment_id = None
            self.btn_undo.setEnabled(False)
            QMessageBox.information(self, "Basarili", "Odeme geri alindi.")
            self.load_suppliers()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))