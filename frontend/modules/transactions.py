from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QTabWidget, QWidget, QPushButton,
                             QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from modules.base import BaseModule
from api_client import api, APIError

COLOR_CANCELLED = QColor("#3b1f1f"); COLOR_CANCEL_TEXT = QColor("#f38ba8")
COLOR_LOG_BG = QColor("#2a1f3b"); COLOR_LOG_TEXT = QColor("#cba6f7")

def _paint_row(table, row, bg, fg):
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(QBrush(bg)); item.setForeground(QBrush(fg))


class HistoryModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Alim ve Satim Gecmisi"); title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.tab_sales = QWidget(); self._setup_sales_tab(); self.tabs.addTab(self.tab_sales, "Satis Gecmisi")
        self.tab_purchases = QWidget(); self._setup_purchases_tab(); self.tabs.addTab(self.tab_purchases, "Alim Gecmisi")
        self.tab_logs = QWidget(); self._setup_logs_tab(); self.tabs.addTab(self.tab_logs, "Iptal Kayitlari")

    def _setup_sales_tab(self):
        layout = QVBoxLayout(self.tab_sales)
        btn_row = QHBoxLayout()
        self.btn_cancel_item = QPushButton("Secili Kalemi Iptal Et")
        self.btn_cancel_item.setStyleSheet("background-color: #e67e22; color: white; padding: 8px; font-weight: bold;")
        self.btn_cancel_item.clicked.connect(self._cancel_sale_item)
        self.btn_cancel_sale = QPushButton("Tum Satisi Iptal Et")
        self.btn_cancel_sale.setStyleSheet("background-color: #c0392b; color: white; padding: 8px; font-weight: bold;")
        self.btn_cancel_sale.clicked.connect(self._cancel_full_sale)
        btn_row.addWidget(self.btn_cancel_item); btn_row.addWidget(self.btn_cancel_sale); btn_row.addStretch()
        layout.addLayout(btn_row)
        self.sales_table = QTableWidget(); self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels(["Satis No", "Tarih", "Musteri", "Urun Adi", "Adet", "Birim Fiyat", "Toplam", "Durum"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sales_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sales_table)

    def _setup_purchases_tab(self):
        layout = QVBoxLayout(self.tab_purchases)
        btn_row = QHBoxLayout()
        self.btn_cancel_purchase = QPushButton("Secili Alimi Iptal Et")
        self.btn_cancel_purchase.setStyleSheet("background-color: #c0392b; color: white; padding: 8px; font-weight: bold;")
        self.btn_cancel_purchase.clicked.connect(self._cancel_purchase)
        btn_row.addWidget(self.btn_cancel_purchase); btn_row.addStretch()
        layout.addLayout(btn_row)
        self.purchases_table = QTableWidget(); self.purchases_table.setColumnCount(7)
        self.purchases_table.setHorizontalHeaderLabels(["Alim No", "Tarih", "Tedarikci", "Urun Adi", "Adet", "Birim Fiyat", "Durum"])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.purchases_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.purchases_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.purchases_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.purchases_table)

    def _setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        lbl = QLabel("Tum iptal islemlerinin kalici kaydi."); lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(lbl)
        self.logs_table = QTableWidget(); self.logs_table.setColumnCount(6)
        self.logs_table.setHorizontalHeaderLabels(["Iptal Tarihi", "Iptal Turu", "Kayit No", "Aciklama", "Iade Miktar", "Iade Tutar"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.logs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.logs_table)

    def refresh_data(self):
        self._load_sales_history(); self._load_purchases_history(); self._load_cancellation_logs()

    def _load_sales_history(self):
        try:
            sales = api.get_sales_history()
            self.sales_table.setRowCount(0)
            for sale in sales:
                for item in sale.get("items", []):
                    row = self.sales_table.rowCount(); self.sales_table.insertRow(row)
                    sale_cancelled = sale["is_cancelled"]; item_cancelled = item["is_cancelled"]
                    is_any = sale_cancelled or item_cancelled
                    if sale_cancelled: status = "Satis Iptal"
                    elif item_cancelled: status = "Kalem Iptal"
                    else: status = "Aktif"
                    cells = [f"SAT-{sale['id']}", sale["timestamp"][:16].replace("T", " "),
                             sale.get("customer_name") or "Genel", item.get("product_name") or "-",
                             str(item["quantity"]), f"{item['unit_price']:,.2f} TL",
                             f"{item['quantity'] * item['unit_price']:,.2f} TL", status]
                    for col, text in enumerate(cells):
                        cell = QTableWidgetItem(text)
                        if col in (4, 5, 6): cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        if col == 0: cell.setData(Qt.ItemDataRole.UserRole, sale["id"])
                        if col == 3: cell.setData(Qt.ItemDataRole.UserRole, item["id"])
                        self.sales_table.setItem(row, col, cell)
                    if is_any: _paint_row(self.sales_table, row, COLOR_CANCELLED, COLOR_CANCEL_TEXT)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_purchases_history(self):
        try:
            purchases = api.get_purchases_history()
            self.purchases_table.setRowCount(0)
            for purchase in purchases:
                for item in purchase.get("items", []):
                    row = self.purchases_table.rowCount(); self.purchases_table.insertRow(row)
                    status = "Iptal" if purchase["is_cancelled"] else "Aktif"
                    supp = purchase.get("supplier_name") or "Bilinmiyor"
                    cells = [f"ALIM-{purchase['id']}", purchase["timestamp"][:16].replace("T", " "),
                             supp, item.get("product_name") or "-",
                             str(item["quantity"]), f"{item['unit_price']:,.2f} TL", status]
                    for col, text in enumerate(cells):
                        cell = QTableWidgetItem(text)
                        if col in (4, 5): cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        if col == 0: cell.setData(Qt.ItemDataRole.UserRole, purchase["id"])
                        self.purchases_table.setItem(row, col, cell)
                    if purchase["is_cancelled"]: _paint_row(self.purchases_table, row, COLOR_CANCELLED, COLOR_CANCEL_TEXT)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_cancellation_logs(self):
        try:
            logs = api.get_cancellation_logs()
            self.logs_table.setRowCount(0)
            for row, log in enumerate(logs):
                self.logs_table.insertRow(row)
                cells = [log["timestamp"][:19].replace("T", " "), log["record_type"], str(log["record_id"]),
                         log.get("description", ""),
                         str(log["cancelled_qty"]) if log.get("cancelled_qty") else "-",
                         f"{log['refund_amount']:,.2f} TL" if log.get("refund_amount") else "-"]
                for col, text in enumerate(cells):
                    cell = QTableWidgetItem(text)
                    if col in (4, 5): cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    cell.setBackground(QBrush(COLOR_LOG_BG)); cell.setForeground(QBrush(COLOR_LOG_TEXT))
                    self.logs_table.setItem(row, col, cell)
        except APIError: pass

    def _get_selected_sale_info(self):
        selected = self.sales_table.selectedItems()
        if not selected: return None, None
        row = selected[0].row()
        sale_id = self.sales_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item_id = self.sales_table.item(row, 3).data(Qt.ItemDataRole.UserRole)
        return sale_id, item_id

    def _get_selected_purchase_id(self):
        selected = self.purchases_table.selectedItems()
        if not selected: return None
        return self.purchases_table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _cancel_sale_item(self):
        sale_id, item_id = self._get_selected_sale_info()
        if not item_id: QMessageBox.information(self, "Bilgi", "Iptal icin bir satis kalemi secin."); return
        reply = QMessageBox.question(self, "Kalem Iptali", "Bu kalem iptal edilecek, stok iade edilecek. Onayliyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.cancel_sale_item(sale_id, item_id)
            QMessageBox.information(self, "Basarili", "Kalem iptal edildi.")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_full_sale(self):
        sale_id, _ = self._get_selected_sale_info()
        if not sale_id: QMessageBox.information(self, "Bilgi", "Iptal icin bir satis secin."); return
        reply = QMessageBox.question(self, "Tum Satisi Iptal Et", f"SAT-{sale_id} tamamen iptal edilecek. Onayliyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.cancel_full_sale(sale_id)
            QMessageBox.information(self, "Basarili", "Satis iptal edildi.")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_purchase(self):
        purchase_id = self._get_selected_purchase_id()
        if not purchase_id: QMessageBox.information(self, "Bilgi", "Iptal icin bir alim secin."); return
        reply = QMessageBox.question(self, "Alim Iptali", f"ALIM-{purchase_id} iptal edilecek. Onayliyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.cancel_purchase(purchase_id)
            QMessageBox.information(self, "Basarili", "Alim iptal edildi.")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))
