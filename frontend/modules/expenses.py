from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QLabel, QLineEdit, QFormLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from modules.base import BaseModule
from api_client import api, APIError


class ExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Gider Ekle"); self.setFixedSize(400, 200)
        layout = QFormLayout(self)
        self.desc_input = QLineEdit()
        self.amount_input = QDoubleSpinBox(); self.amount_input.setMaximum(1000000.0); self.amount_input.setDecimals(2)
        layout.addRow("Aciklama:", self.desc_input)
        layout.addRow("Tutar (TL):", self.amount_input)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet"); cancel_btn = QPushButton("Iptal")
        save_btn.clicked.connect(self.accept); cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn); btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {"description": self.desc_input.text().strip(), "amount": self.amount_input.value()}


class ExpensesModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        title = QLabel("Gider Yonetimi"); title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_add = QPushButton("Yeni Gider Ekle")
        self.btn_add.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 4px;")
        self.btn_add.clicked.connect(self.add_expense)
        controls.addWidget(title); controls.addStretch(); controls.addWidget(self.btn_add)
        layout.addLayout(controls)

        self.table = QTableWidget(); self.table.setColumnCount(4)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["ID", "Tarih & Saat", "Aciklama", "Tutar (TL)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.btn_delete = QPushButton("Secili Gideri Iptal Et (Sil)")
        self.btn_delete.setStyleSheet("background-color: #c0392b; color: white; padding: 5px;")
        self.btn_delete.clicked.connect(self.delete_expense)
        actions.addWidget(self.btn_delete); actions.addStretch()
        layout.addLayout(actions)

    def refresh_data(self): self.load_expenses()

    def load_expenses(self):
        try:
            expenses = api.get_expenses()
            self.table.setRowCount(0)
            for row, e in enumerate(expenses):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(e["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(e["timestamp"][:19].replace("T", " ")))
                self.table.setItem(row, 2, QTableWidgetItem(e["description"]))
                amount_item = QTableWidgetItem(f"{e['amount']:,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, amount_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["description"]: QMessageBox.warning(self, "Hata", "Aciklama bos olamaz!"); return
            if data["amount"] <= 0: QMessageBox.warning(self, "Hata", "Tutar sifirdan buyuk olmali!"); return
            try:
                api.create_expense(data["description"], data["amount"])
                self.load_expenses()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items: return None
        return int(self.table.item(items[0].row(), 0).text())

    def delete_expense(self):
        eid = self.get_selected_id()
        if not eid: QMessageBox.information(self, "Bilgi", "Silmek icin bir gider secin."); return
        reply = QMessageBox.question(self, "Onay", "Bu gider kaydini silmek istediginize emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                api.delete_expense(eid)
                self.load_expenses()
                if hasattr(self, "main_window"): self.main_window.update_cash_balance()
            except APIError as e:
                QMessageBox.critical(self, "Hata", str(e))