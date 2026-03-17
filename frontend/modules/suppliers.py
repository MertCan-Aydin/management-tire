import re
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QInputDialog, QFrame,
                             QAbstractItemView, QTextEdit)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from modules.base import BaseModule
from api_client import api, APIError


# ── Format yardımcıları ───────────────────────────────────────────────────────

def format_phone(raw: str) -> str:
    """Ham telefon → '0532 123 45 67' formatı."""
    digits = re.sub(r'[^0-9]', '', raw)
    if len(digits) == 10 and digits[0] == '5':
        digits = '0' + digits
    if len(digits) == 11 and digits[:2] == '05':
        return f"{digits[0:4]} {digits[4:7]} {digits[7:9]} {digits[9:11]}"
    return raw  # Tanımlanamıyorsa olduğu gibi bırak

def format_plate(raw: str) -> str:
    """Ham plaka → '34 ABC 123' formatı."""
    cleaned = re.sub(r'\s+', ' ', raw.upper().strip())
    # Zaten formatlıysa dokunma
    if re.match(r'^\d{2} [A-Z]+ \d+$', cleaned):
        return cleaned
    # Ham: 34ABC123 → 34 ABC 123
    m = re.match(r'^(\d{2})([A-Z]+)(\d+)$', re.sub(r'\s', '', cleaned))
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    return cleaned

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()))

def fmt_dt(dt_str):
    if not dt_str: return "-"
    try:
        s = dt_str[:19].replace("T", " ")
        date, time = s.split(" ")
        y, m, d = date.split("-")
        return f"{d}.{m}.{y} {time}"
    except Exception:
        return dt_str[:16]


# ── Telefon input widget ──────────────────────────────────────────────────────

class PhoneLineEdit(QLineEdit):
    """Telefon girerken otomatik format uygular."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("0532 123 45 67")
        self.setMaxLength(14)
        self.textEdited.connect(self._on_edit)

    def _on_edit(self, text):
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) == 0:
            return
        # Formatı uygula
        fmt = ''
        if len(digits) >= 1:
            fmt = digits[:4]
        if len(digits) >= 5:
            fmt += ' ' + digits[4:7]
        if len(digits) >= 8:
            fmt += ' ' + digits[7:9]
        if len(digits) >= 10:
            fmt += ' ' + digits[9:11]
        # Cursor pozisyonunu koru
        self.blockSignals(True)
        self.setText(fmt)
        self.setCursorPosition(len(fmt))
        self.blockSignals(False)

    def get_formatted(self) -> str:
        return format_phone(self.text())


# ── Tedarikçi dialog ──────────────────────────────────────────────────────────

class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.setWindowTitle("Tedarikci Ekle" if not supplier else "Tedarikci Duzenle")
        self.setFixedSize(420, 220)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_input    = QLineEdit()
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Genel iletisim notu (opsiyonel)")

        if supplier:
            self.name_input.setText(supplier.get("name", ""))
            self.contact_input.setText(supplier.get("contact_info") or "")

        layout.addRow("Firma Adi *:", self.name_input)
        layout.addRow("Genel Not:",   self.contact_input)

        btn_layout = QHBoxLayout()
        save_btn   = QPushButton("Kaydet")
        cancel_btn = QPushButton("Iptal")
        cancel_btn.setStyleSheet("background-color: #555; color: white;")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "name":         self.name_input.text().strip(),
            "contact_info": self.contact_input.text().strip(),
        }


# ── Sorumlu Kişi Dialog ───────────────────────────────────────────────────────

class ContactDialog(QDialog):
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.setWindowTitle("Sorumlu Kisi Ekle" if not contact else "Sorumlu Kisi Duzenle")
        self.setFixedSize(440, 300)
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_input  = QLineEdit()
        self.name_input.setPlaceholderText("Ad Soyad *")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Satis Temsilcisi, Muhasebe vb.")

        self.phone_input = PhoneLineEdit()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@firma.com")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Opsiyonel not...")

        if contact:
            self.name_input.setText(contact.get("name", ""))
            self.title_input.setText(contact.get("title") or "")
            self.phone_input.setText(contact.get("phone") or "")
            self.email_input.setText(contact.get("email") or "")
            self.notes_input.setPlainText(contact.get("notes") or "")

        layout.addRow("Ad Soyad *:",   self.name_input)
        layout.addRow("Gorev/Unvan:",  self.title_input)
        layout.addRow("Telefon:",      self.phone_input)
        layout.addRow("E-posta:",      self.email_input)
        layout.addRow("Not:",          self.notes_input)

        btn_row = QHBoxLayout()
        ok_btn  = QPushButton("Kaydet")
        no_btn  = QPushButton("Iptal")
        no_btn.setStyleSheet("background-color: #555; color: white;")
        ok_btn.clicked.connect(self.accept)
        no_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(no_btn)
        layout.addRow(btn_row)

    def get_data(self):
        phone = self.phone_input.get_formatted()
        email = self.email_input.text().strip()
        return {
            "name":  self.name_input.text().strip(),
            "title": self.title_input.text().strip() or None,
            "phone": phone if phone else None,
            "email": email if email else None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

    def accept(self):
        email = self.email_input.text().strip()
        if email and not is_valid_email(email):
            QMessageBox.warning(self, "Gecersiz E-posta",
                                "Lutfen gecerli bir e-posta adresi girin.\nOrnek: isim@firma.com")
            return
        super().accept()


# ── Sorumlu Kişiler Dialog ────────────────────────────────────────────────────

class ContactsDialog(QDialog):
    def __init__(self, parent, supplier):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle(f"Sorumlu Kisiler — {supplier['name']}")
        self.setMinimumSize(680, 420)
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel(f"{self.supplier['name']} — Sorumlu Kisiler")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Ad Soyad", "Gorev", "Telefon", "E-posta", "Not"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.btn_add  = QPushButton("+ Kisi Ekle")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 6px 14px;")
        self.btn_edit = QPushButton("Duzenle")
        self.btn_edit.setStyleSheet("background-color: #2980b9; color: white; padding: 6px 14px;")
        self.btn_del  = QPushButton("Sil")
        self.btn_del.setStyleSheet("background-color: #e74c3c; color: white; padding: 6px 14px;")
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("background-color: #555; color: white; padding: 6px 14px;")

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load(self):
        try:
            contacts = api.get_supplier_contacts(self.supplier["id"])
            self.table.setRowCount(0)
            for i, c in enumerate(contacts):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(c["name"]))
                self.table.setItem(i, 1, QTableWidgetItem(c.get("title") or "-"))
                self.table.setItem(i, 2, QTableWidgetItem(c.get("phone") or "-"))
                self.table.setItem(i, 3, QTableWidgetItem(c.get("email") or "-"))
                self.table.setItem(i, 4, QTableWidgetItem(c.get("notes") or ""))
                # ID'yi hidden data olarak sakla
                self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, c["id"])
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.information(self, "Bilgi", "Lutfen bir kisi secin.")
            return None
        return self.table.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _add(self):
        dlg = ContactDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Hata", "Ad Soyad bos olamaz!")
                return
            try:
                api.create_supplier_contact(self.supplier["id"], data)
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _edit(self):
        cid = self._get_selected_id()
        if not cid: return
        try:
            contacts = api.get_supplier_contacts(self.supplier["id"])
            contact  = next((c for c in contacts if c["id"] == cid), None)
            if not contact: return
            dlg = ContactDialog(self, contact)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]:
                    QMessageBox.warning(self, "Hata", "Ad Soyad bos olamaz!")
                    return
                api.update_supplier_contact(self.supplier["id"], cid, data)
                self._load()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _delete(self):
        cid = self._get_selected_id()
        if not cid: return
        reply = QMessageBox.question(
            self, "Onay", "Bu kisiyi silmek istediginize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_supplier_contact(self.supplier["id"], cid)
                self._load()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))


# ── Ödeme Geçmişi Dialog ──────────────────────────────────────────────────────

class PaymentHistoryDialog(QDialog):
    def __init__(self, parent, supplier):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle(f"Odeme Gecmisi — {supplier['name']}")
        self.setMinimumSize(560, 400)
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel(f"{self.supplier['name']} — Tum Odemeler")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tarih & Saat", "Tutar (TL)", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.lbl_total = QLabel("Toplam odeme: 0,00 TL")
        self.lbl_total.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(self.lbl_total)

        btn_row = QHBoxLayout()
        self.btn_undo = QPushButton("Secili Odemeyi Geri Al")
        self.btn_undo.setStyleSheet("background-color: #e67e22; color: white; padding: 6px 14px;")
        self.btn_undo.clicked.connect(self._undo)
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("background-color: #555; color: white; padding: 6px 14px;")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_undo)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load(self):
        try:
            payments = api.get_supplier_payments(self.supplier["id"])
            self.table.setRowCount(0)
            total = 0.0
            for i, p in enumerate(payments):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(fmt_dt(p.get("timestamp"))))
                amt = QTableWidgetItem(f"{p['amount']:,.2f} TL")
                amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, 1, amt)
                self.table.setItem(i, 2, QTableWidgetItem(str(p["id"])))
                total += p["amount"]
            self.lbl_total.setText(f"Toplam odeme: {total:,.2f} TL")
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _undo(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.information(self, "Bilgi", "Lutfen bir odeme secin.")
            return
        row        = items[0].row()
        payment_id = int(self.table.item(row, 2).text())
        amount_txt = self.table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Onay",
            f"{amount_txt} tutarindaki odemeyi geri almak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.undo_supplier_payment(self.supplier["id"], payment_id)
                self._load()
                if hasattr(self.parent(), "load_suppliers"):
                    self.parent().load_suppliers()
                if hasattr(self.parent(), "main_window"):
                    self.parent().main_window.update_cash_balance()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))


# ── Suppliers modülü ──────────────────────────────────────────────────────────

class SuppliersModule(BaseModule):
    def __init__(self, parent=None):
        self._last_payment_id  = None
        self._last_payment_sid = None
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        title = QLabel("Tedarikci Yonetimi")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_add = QPushButton("+ Yeni Tedarikci")
        self.btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 14px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_supplier)
        controls.addWidget(title)
        controls.addStretch()
        controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Firma Adi", "Genel Not", "Son Odeme", "Guncel Borc (TL)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_edit     = QPushButton("Duzenle")
        self.btn_contacts = QPushButton("Sorumlu Kisiler")
        self.btn_pay      = QPushButton("Borc Ode")
        self.btn_history  = QPushButton("Odeme Gecmisi")
        self.btn_undo     = QPushButton("Son Odemeyi Geri Al")
        self.btn_delete   = QPushButton("Sil")

        self.btn_contacts.setStyleSheet("background-color: #8e44ad; color: white; padding: 5px 12px;")
        self.btn_pay.setStyleSheet("background-color: #f39c12; color: white; padding: 5px 12px; font-weight: bold;")
        self.btn_history.setStyleSheet("background-color: #2980b9; color: white; padding: 5px 12px;")
        self.btn_undo.setStyleSheet("background-color: #e67e22; color: white; padding: 5px 12px;")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 12px;")
        self.btn_undo.setEnabled(False)

        self.btn_edit.clicked.connect(self.edit_supplier)
        self.btn_contacts.clicked.connect(self.show_contacts)
        self.btn_pay.clicked.connect(self.pay_debt)
        self.btn_history.clicked.connect(self.show_payment_history)
        self.btn_undo.clicked.connect(self.undo_last_payment)
        self.btn_delete.clicked.connect(self.delete_supplier)

        for btn in [self.btn_edit, self.btn_contacts, self.btn_pay,
                    self.btn_history, self.btn_undo, self.btn_delete]:
            actions.addWidget(btn)
        actions.addStretch()
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

                last_pay  = s.get("last_payment_date")
                last_item = QTableWidgetItem(fmt_dt(last_pay) if last_pay else "Odeme Yok")
                last_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, last_item)

                debt_item = QTableWidgetItem(f"{s['current_debt']:,.2f}")
                debt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, debt_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def _get_selected(self):
        items = self.table.selectedItems()
        if not items: return None, None
        row = items[0].row()
        sid  = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        return sid, name

    def add_supplier(self):
        dlg = SupplierDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Hata", "Firma adi bos olamaz!")
                return
            try:
                api.create_supplier(data)
                self.load_suppliers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def edit_supplier(self):
        sid, _ = self._get_selected()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Duzenlemek icin bir tedarikci secin.")
            return
        try:
            suppliers = api.get_suppliers()
            supplier  = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier: return
            dlg = SupplierDialog(self, supplier)
            if dlg.exec():
                data = dlg.get_data()
                if not data["name"]:
                    QMessageBox.warning(self, "Hata", "Firma adi bos olamaz!")
                    return
                api.update_supplier(sid, data)
                self.load_suppliers()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def show_contacts(self):
        sid, _ = self._get_selected()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Sorumlu kisiler icin bir tedarikci secin.")
            return
        try:
            suppliers = api.get_suppliers()
            supplier  = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier: return
            dlg = ContactsDialog(self, supplier)
            dlg.exec()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_supplier(self):
        sid, name = self._get_selected()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Silmek icin bir tedarikci secin.")
            return
        reply = QMessageBox.question(
            self, "Onay", f"'{name}' firmasini silmek istediginize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_supplier(sid)
                self.load_suppliers()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def pay_debt(self):
        sid, _ = self._get_selected()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Borc odemek icin bir tedarikci secin.")
            return
        try:
            suppliers = api.get_suppliers()
            supplier  = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier or supplier["current_debt"] <= 0:
                QMessageBox.information(self, "Bilgi", "Bu firmanin odenmemis borcu yok.")
                return
            amount, ok = QInputDialog.getDouble(
                self, "Borc Odeme",
                f"Odenecek Tutar (TL):\n(Mevcut Borc: {supplier['current_debt']:,.2f} TL)",
                decimals=2, min=0.01, max=supplier["current_debt"]
            )
            if not (ok and amount > 0): return
            result = api.pay_supplier(sid, amount)
            self._last_payment_id  = result["id"]
            self._last_payment_sid = sid
            self.btn_undo.setEnabled(True)
            QMessageBox.information(self, "Basarili", f"{amount:,.2f} TL odeme islendi.")
            self.load_suppliers()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def show_payment_history(self):
        sid, _ = self._get_selected()
        if not sid:
            QMessageBox.information(self, "Bilgi", "Gecmis icin bir tedarikci secin.")
            return
        try:
            suppliers = api.get_suppliers()
            supplier  = next((s for s in suppliers if s["id"] == sid), None)
            if not supplier: return
            dlg = PaymentHistoryDialog(self, supplier)
            dlg.exec()
            self.load_suppliers()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def undo_last_payment(self):
        if not self._last_payment_id:
            QMessageBox.information(self, "Bilgi", "Geri alinacak odeme bulunamadi.")
            return
        reply = QMessageBox.question(
            self, "Son Odemeyi Geri Al",
            "Son tedarikci odemesi geri alinacak. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.undo_supplier_payment(self._last_payment_sid, self._last_payment_id)
            self._last_payment_id  = None
            self._last_payment_sid = None
            self.btn_undo.setEnabled(False)
            QMessageBox.information(self, "Basarili", "Odeme geri alindi.")
            self.load_suppliers()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))