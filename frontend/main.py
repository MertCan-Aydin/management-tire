import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QHBoxLayout, QPushButton, QStackedWidget, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from config import Config

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
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        sidebar_layout.addStretch()
        self.lbl_cash_balance = QLabel("Net Bakiye:\n0.00 TL")
        self.lbl_cash_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #a6e3a1; margin-top: 20px; text-align: center;")
        self.lbl_cash_balance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.lbl_cash_balance)
        sidebar_layout.addStretch()

        # Modules
        self.stacked_widget = QStackedWidget()
        self.module_sales = SalesModule()
        self.module_inventory = InventoryModule()
        self.module_suppliers = SuppliersModule()
        self.module_reports = ReportsModule()
        self.module_expenses = ExpensesModule()
        self.module_history = HistoryModule()
        self.module_customers = CustomersModule()

        for module in [self.module_sales, self.module_inventory, self.module_suppliers,
                       self.module_customers, self.module_reports, self.module_expenses, self.module_history]:
            module.main_window = self

        for module in [self.module_sales, self.module_inventory, self.module_suppliers,
                       self.module_customers, self.module_reports, self.module_expenses, self.module_history]:
            self.stacked_widget.addWidget(module)

        # Nav buttons
        nav_buttons = [
            ("Satis (POS)", 0), ("Urunler & Stok", 1), ("Tedarkiciler", 2),
            ("Musteriler", 3), ("Giderler", 4), ("Alim-Satim Gecmisi", 5), ("Raporlar", 6)
        ]
        # Rearrange stacked indices to match
        for i, (label, idx) in enumerate(nav_buttons):
            btn = self.create_nav_button(label)
            btn.clicked.connect(lambda checked, i=idx: self.switch_module(i))
            sidebar_layout.insertWidget(i + 1, btn)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        self.update_cash_balance()

    def update_cash_balance(self):
        from api_client import api, APIError
        try:
            data = api.get_dashboard()
            net = data["net_balance"]
            if net < 0:
                self.lbl_cash_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #f38ba8; margin-top: 20px; text-align: center;")
                self.lbl_cash_balance.setText(f"Net Bakiye:\n{net:,.2f} TL")
            else:
                self.lbl_cash_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #a6e3a1; margin-top: 20px; text-align: center;")
                self.lbl_cash_balance.setText(f"Net Bakiye:\n{net:,.2f} TL")
        except APIError as e:
            self.lbl_cash_balance.setText("Baglanti Hatasi")
            self.lbl_cash_balance.setStyleSheet("font-size: 12px; color: #f38ba8; margin-top: 20px;")

    def create_nav_button(self, text):
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; color: white;
                          text-align: left; padding: 10px 15px; font-size: 14px; }
            QPushButton:hover { background-color: #34495e; border-radius: 5px; }
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
            background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 5px; border-radius: 4px; }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #89b4fa; }
        QPushButton { background-color: #89b4fa; color: #11111b; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
        QPushButton:hover { background-color: #b4befe; }
        QPushButton:pressed { background-color: #74c7ec; }
        QTableWidget { background-color: #181825; color: #cdd6f4; gridline-color: #313244; border: 1px solid #313244; border-radius: 4px; }
        QHeaderView::section { background-color: #313244; color: #cdd6f4; padding: 6px; border: 1px solid #45475a; font-weight: bold; }
        QTableWidget::item:selected { background-color: #45475a; color: #cdd6f4; }
        QTabWidget::pane { border: 1px solid #313244; border-radius: 4px; background-color: #1e1e2e; }
        QTabBar::tab { background: #313244; color: #a6adc8; padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
        QTabBar::tab:selected { background: #89b4fa; color: #11111b; font-weight: bold; }
    """)

    # API baglantisini kontrol et
    from api_client import api, APIError
    try:
        api.get_dashboard()
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Baglanti Hatasi",
                             f"API sunucusuna baglanillamiyor!\n\n{e}\n\n"
                             f"config.py dosyasindaki API_BASE_URL adresini kontrol edin.")
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()