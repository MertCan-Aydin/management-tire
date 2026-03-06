from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QWidget, QTabWidget)
from PyQt6.QtCore import Qt
from modules.base import BaseModule
from api_client import api, APIError


class ReportTab(QWidget):
    def __init__(self, endpoint_path, period_label):
        super().__init__()
        self.endpoint_path = endpoint_path
        layout = QVBoxLayout(self)
        self.lbl_total = QLabel(f"{period_label} Toplam Satis: 0.00 TL")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(self.lbl_total)
        self.table = QTableWidget(); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Satis ID", "Tarih & Saat", "Odeme Yontemi", "Tutar (TL)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load(self):
        try:
            data = api.get(self.endpoint_path)
            sales = data.get("sales", [])
            total = data.get("total", 0.0)
            self.table.setRowCount(0)
            for row, sale in enumerate(sales):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(sale["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(sale["timestamp"][:16].replace("T", " ")))
                self.table.setItem(row, 2, QTableWidgetItem(sale.get("payment_method", "-")))
                amount_item = QTableWidgetItem(f"{sale['total_amount']:,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, amount_item)
            self.lbl_total.setText(f"Toplam Satis: {total:,.2f} TL")
        except APIError as e:
            self.lbl_total.setText(f"Hata: {e}")


class ReportsModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Satis Raporlari"); title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        self.tab_daily = ReportTab("/reports/daily", "Gunluk")
        self.tab_weekly = ReportTab("/reports/weekly", "Haftalik")
        self.tab_monthly = ReportTab("/reports/monthly", "Aylik")
        self.tabs.addTab(self.tab_daily, "Gunluk Rapor")
        self.tabs.addTab(self.tab_weekly, "Haftalik Rapor")
        self.tabs.addTab(self.tab_monthly, "Aylik Rapor")
        layout.addWidget(self.tabs)

    def refresh_data(self):
        for tab in [self.tab_daily, self.tab_weekly, self.tab_monthly]:
            tab.load()
