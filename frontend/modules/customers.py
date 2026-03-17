import re
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt
from modules.base import BaseModule
from api_client import api, APIError


def format_phone(raw: str) -> str:
    digits = re.sub(r'[^0-9]', '', raw)
    if len(digits) == 10 and digits[0] == '5':
        digits = '0' + digits
    if len(digits) == 11 and digits[:2] == '05':
        return f"{digits[0:4]} {digits[4:7]} {digits[7:9]} {digits[9:11]}"
    return raw

def format_plate(raw: str) -> str:
    cleaned = re.sub(r'\s+', ' ', raw.upper().strip())
    if re.match(r'^\d{2} [A-Z]+ \d+$', cleaned):
        return cleaned
    m = re.match(r'^(\d{2})([A-Z]+)(\d+)$', re.sub(r'\s', '', cleaned))
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    return cleaned

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()))


class PhoneLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("0532 123 45 67")
        self.setMaxLength(14)
        self.textEdited.connect(self._on_edit)

    def _on_edit(self, text):
        digits = re.sub(r'[^0-9]', '', text)
        if not digits: return
        fmt = digits[:4]
        if len(digits) >= 5: fmt += ' ' + digits[4:7]
        if len(digits) >= 8: fmt += ' ' + digits[7:9]
        if len(digits) >= 10: fmt += ' ' + digits[9:11]
        self.blockSignals(True)
        self.setText(fmt)
        self.setCursorPosition(len(fmt))
        self.blockSignals(False)

    def get_formatted(self): return format_phone(self.text())


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.setWindowTitle("Musteri Ekle" if not customer else "Musteri Duzenle")
        self.setFixedSize(400, 400)
        layout = QFormLayout(self)
        self.name_input      = QLineEdit()
        self.phone_input     = PhoneLineEdit()
        self.car_brand_input = QLineEdit()
        self.car_plate_input = QLineEdit()
        self.car_plate_input.setPlaceholderText("34 ABC 123")
        self.car_plate_input.setMaxLength(12)
        self.notes_input = QTextEdit(); self.notes_input.setMaximumHeight(80)
        if customer:
            self.name_input.setText(customer.get("name", ""))
            self.phone_input.setText(customer.get("phone") or "")
            self.car_brand_input.setText(customer.get("car_brand") or "")
            self.car_plate_input.setText(customer.get("car_plate") or "")
            self.notes_input.setText(customer.get("notes") or "")
        layout.addRow("Ad Soyad:", self.name_input)
        layout.addRow("Telefon:", self.phone_input)
        layout.addRow("Arac Marka/Model:", self.car_brand_input)
        layout.addRow("Plaka:", self.car_plate_input)
        layout.addRow("Notlar:", self.notes_input)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet"); cancel_btn = QPushButton("Iptal")
        save_btn.clicked.connect(self.accept); cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn); btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "name":      self.name_input.text().strip(),
            "phone":     self.phone_input.get_formatted() or None,
            "car_brand": self.car_brand_input.text().strip() or None,
            "car_plate": format_plate(self.car_plate_input.text()) if self.car_plate_input.text().strip() else None,
            "notes":     self.notes_input.toPlainText().strip() or None,
        }


class CustomerHistoryDialog(QDialog):
    def __init__(self, parent, customer_id):
        super().__init__(parent)
        self.setWindowTitle("Musteri Siparis Gecmisi"); self.setFixedSize(700, 400)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Etiket No", "Tarih & Saat", "Odeme Yontemi", "Indirim", "Toplam Tutar"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        try:
            sales = api.get_customer_sales(customer_id)
            for row, sale in enumerate(sales):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(f"SAT-{sale['id']}"))
                self.table.setItem(row, 1, QTableWidgetItem(sale["timestamp"][:19].replace("T", " ")))
                self.table.setItem(row, 2, QTableWidgetItem(sale["payment_method"]))
                disc = f"{sale['discount']:,.2f} TL" if sale['discount'] > 0 else "-"
                self.table.setItem(row, 3, QTableWidgetItem(disc))
                self.table.setItem(row, 4, QTableWidgetItem(f"{sale['total_amount']:,.2f} TL"))
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))


class CustomersModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        title = QLabel("Musteriler"); title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Isim, Telefon veya Plaka ile Ara...")
        self.search_input.textChanged.connect(self.filter_data)
        self.btn_add = QPushButton("Yeni Musteri Ekle")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_customer)
        controls.addWidget(title); controls.addWidget(self.search_input); controls.addStretch(); controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Telefon", "Arac Marka/Model", "Plaka"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_history = QPushButton("Gecmis Siparisleri Gor")
        self.btn_edit = QPushButton("Secili Olani Duzenle")
        self.btn_delete = QPushButton("Secili Olani Sil")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
        self.btn_history.clicked.connect(self.view_history)
        self.btn_edit.clicked.connect(self.edit_customer)
        self.btn_delete.clicked.connect(self.delete_customer)
        actions.addWidget(self.btn_history); actions.addWidget(self.btn_edit); actions.addWidget(self.btn_delete); actions.addStretch()
        layout.addLayout(actions)

    def refresh_data(self): self.load_customers()

    def load_customers(self, search=""):
        try:
            customers = api.get_customers(search)
            self.table.setRowCount(0)
            for row, c in enumerate(customers):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(c["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(c["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(c.get("phone") or ""))
                self.table.setItem(row, 3, QTableWidgetItem(c.get("car_brand") or ""))
                self.table.setItem(row, 4, QTableWidgetItem(c.get("car_plate") or ""))
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def filter_data(self, text): self.load_customers(text)

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items: return None
        return int(self.table.item(items[0].row(), 0).text())

    def view_history(self):
        cid = self.get_selected_id()
        if not cid: QMessageBox.information(self, "Bilgi", "Gecmis icin bir musteri secin."); return
        CustomerHistoryDialog(self, cid).exec()

    def add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]: QMessageBox.warning(self, "Hata", "Musteri adi bos olamaz!"); return
            try:
                api.create_customer(data); self.load_customers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def edit_customer(self):
        cid = self.get_selected_id()
        if not cid: QMessageBox.information(self, "Bilgi", "Duzenlemek icin bir musteri secin."); return
        try:
            customers = api.get_customers()
            customer = next((c for c in customers if c["id"] == cid), None)
            if not customer: return
            dlg = CustomerDialog(self, customer)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]: QMessageBox.warning(self, "Hata", "Ad bos olamaz!"); return
                api.update_customer(cid, data); self.load_customers()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_customer(self):
        cid = self.get_selected_id()
        if not cid: QMessageBox.information(self, "Bilgi", "Silmek icin bir musteri secin."); return
        reply = QMessageBox.question(self, "Onay", "Bu musteriyi silmek istediginize emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_customer(cid); self.load_customers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))