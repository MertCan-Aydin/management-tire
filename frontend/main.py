import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QHBoxLayout, QPushButton, QStackedWidget,
                             QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from config import Config
from api_client import api, APIError

from modules.suppliers import SuppliersModule
from modules.inventory import InventoryModule
from modules.sales import SalesModule
from modules.reports import ReportsModule
from modules.expenses import ExpensesModule
from modules.transactions import HistoryModule
from modules.customers import CustomersModule


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        title_label = QLabel(Config.APP_NAME)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        sidebar_layout.addStretch()

        self.lbl_cash_balance = QLabel("🟢 Net Kasa:\n0.00 ₺")
        self.lbl_cash_balance.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #a6e3a1; margin-top: 20px; text-align: center;"
        )
        self.lbl_cash_balance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.lbl_cash_balance)
        sidebar_layout.addStretch()

        self.stacked_widget = QStackedWidget()

        self.module_sales     = SalesModule()
        self.module_inventory = InventoryModule()
        self.module_suppliers = SuppliersModule()
        self.module_reports   = ReportsModule()
        self.module_expenses  = ExpensesModule()
        self.module_history   = HistoryModule()
        self.module_customers = CustomersModule()

        for module in [
            self.module_sales, self.module_inventory, self.module_suppliers,
            self.module_customers, self.module_reports, self.module_expenses,
            self.module_history
        ]:
            module.main_window = self

        for module in [
            self.module_sales, self.module_inventory, self.module_suppliers,
            self.module_customers, self.module_reports, self.module_expenses,
            self.module_history
        ]:
            self.stacked_widget.addWidget(module)

        self.btn_sales     = self.create_nav_button("Satış (POS)")
        self.btn_inventory = self.create_nav_button("Ürünler & Stok")
        self.btn_suppliers = self.create_nav_button("Tedarikçiler")
        self.btn_customers = self.create_nav_button("Müşteriler")
        self.btn_expenses  = self.create_nav_button("Giderler")
        self.btn_history   = self.create_nav_button("Alım-Satım Geçmişi")
        self.btn_reports   = self.create_nav_button("Raporlar")

        for i, btn in enumerate([
            self.btn_sales, self.btn_inventory, self.btn_suppliers,
            self.btn_customers, self.btn_expenses, self.btn_history, self.btn_reports
        ], start=1):
            sidebar_layout.insertWidget(i, btn)

        self.btn_sales.clicked.connect(lambda: self.switch_module(0))
        self.btn_inventory.clicked.connect(lambda: self.switch_module(1))
        self.btn_suppliers.clicked.connect(lambda: self.switch_module(2))
        self.btn_customers.clicked.connect(lambda: self.switch_module(3))
        self.btn_reports.clicked.connect(lambda: self.switch_module(4))
        self.btn_expenses.clicked.connect(lambda: self.switch_module(5))
        self.btn_history.clicked.connect(lambda: self.switch_module(6))

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)

        self.update_cash_balance()

    def update_cash_balance(self):
        try:
            data = api.get_dashboard()
            net = data.get("net_balance", 0.0)
            if net < 0:
                self.lbl_cash_balance.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #f38ba8; margin-top: 20px; text-align: center;"
                )
                self.lbl_cash_balance.setText(f"🔴 Net Bakiye:\n{net:,.2f} ₺")
            else:
                self.lbl_cash_balance.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #a6e3a1; margin-top: 20px; text-align: center;"
                )
                self.lbl_cash_balance.setText(f"🟢 Net Bakiye:\n{net:,.2f} ₺")
        except APIError as e:
            self.lbl_cash_balance.setText("⚠️ Bağlantı Hatası")

    def create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 10px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-radius: 5px;
            }
        """)
        return btn

    def switch_module(self, index):
        self.stacked_widget.setCurrentIndex(index)
        current_module = self.stacked_widget.currentWidget()
        if hasattr(current_module, "refresh_data"):
            current_module.refresh_data()
        self.update_cash_balance()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow, QDialog, QMessageBox { background-color: #1e1e2e; color: #cdd6f4; }
        QWidget { color: #cdd6f4; font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }
        QLabel { color: #cdd6f4; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #313244; color: #cdd6f4;
            border: 1px solid #45475a; padding: 5px; border-radius: 4px;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #89b4fa; }
        QPushButton {
            background-color: #89b4fa; color: #11111b;
            border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold;
        }
        QPushButton:hover { background-color: #b4befe; }
        QPushButton:pressed { background-color: #74c7ec; }
        QTableWidget {
            background-color: #181825; color: #cdd6f4;
            gridline-color: #313244; border: 1px solid #313244; border-radius: 4px;
        }
        QHeaderView::section {
            background-color: #313244; color: #cdd6f4;
            padding: 6px; border: 1px solid #45475a; font-weight: bold;
        }
        QTableWidget::item:selected { background-color: #45475a; color: #cdd6f4; }
        QTabWidget::pane { border: 1px solid #313244; border-radius: 4px; background-color: #1e1e2e; }
        QTabBar::tab {
            background: #313244; color: #a6adc8;
            padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;
        }
        QTabBar::tab:selected { background: #89b4fa; color: #11111b; font-weight: bold; }
    """)

    # Sunucu bağlantı testi
    try:
        api.get_dashboard()
    except APIError as e:
        msg = QMessageBox()
        msg.setWindowTitle("Sunucu Bağlantısı")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            f"⚠️ API sunucusuna bağlanılamadı!\n\n{str(e)}\n\n"
            f"Lütfen config.py dosyasında API_BASE_URL'yi VPS IP adresinizle güncelleyin.\n"
            f"Mevcut adres: {Config.API_BASE_URL}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Ignore)
        result = msg.exec()
        if result == QMessageBox.StandardButton.Ok:
            sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
