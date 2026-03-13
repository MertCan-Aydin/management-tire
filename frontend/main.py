import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QHBoxLayout, QPushButton, QStackedWidget,
                             QFrame, QMessageBox, QDialog)
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
    def __init__(self, username=""):
        super().__init__()
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION} — {username}")
        self.setGeometry(100, 100, 1280, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)

        title_label = QLabel(Config.APP_NAME)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # Nav butonları
        nav_buttons = [
            ("Satis (POS)",           0),
            ("Urunler & Stok",        1),
            ("Tedarkiciler",          2),
            ("Musteriler",            3),
            ("Raporlar",              4),
            ("Giderler",              5),
            ("Alim-Satim Gecmisi",    6),
        ]
        for label, idx in nav_buttons:
            btn = self._create_nav_button(label)
            btn.clicked.connect(lambda checked, i=idx: self.switch_module(i))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # ── Finansal özet kartları ────────────────────────────────
        sidebar_layout.addWidget(self._divider())

        self.lbl_net_balance  = self._stat_label("Kasa", "0.00 TL", "#a6e3a1")
        self.lbl_gross_profit = self._stat_label("Brut Kar", "0.00 TL", "#89b4fa")
        self.lbl_net_profit   = self._stat_label("Net Kar", "0.00 TL", "#89dceb")
        self.lbl_cash_card    = self._small_label("Nakit: 0.00  |  Kart: 0.00")

        for w in [self.lbl_net_balance, self.lbl_gross_profit,
                  self.lbl_net_profit, self.lbl_cash_card]:
            sidebar_layout.addWidget(w)

        sidebar_layout.addWidget(self._divider())
        sidebar_layout.addStretch()

        # ── Modüller ──────────────────────────────────────────────
        self.stacked_widget   = QStackedWidget()
        self.module_sales     = SalesModule()
        self.module_inventory = InventoryModule()
        self.module_suppliers = SuppliersModule()
        self.module_reports   = ReportsModule()
        self.module_expenses  = ExpensesModule()
        self.module_history   = HistoryModule()
        self.module_customers = CustomersModule()

        modules = [
            self.module_sales, self.module_inventory, self.module_suppliers,
            self.module_customers, self.module_reports, self.module_expenses,
            self.module_history,
        ]
        for m in modules:
            m.main_window = self
            self.stacked_widget.addWidget(m)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        self.update_cash_balance()

    # ── Yardımcı widget'lar ───────────────────────────────────────
    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #3d5166;")
        return line

    def _stat_label(self, title, value, color):
        lbl = QLabel(f"{title}:\n{value}")
        lbl.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {color}; "
            f"padding: 4px 0; text-align: center;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _small_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 10px; color: #a6adc8; padding: 2px 0;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; border: none; color: white;
                text-align: left; padding: 10px 15px; font-size: 13px;
            }
            QPushButton:hover { background-color: #34495e; border-radius: 5px; }
        """)
        return btn

    # ── Dashboard güncelle ────────────────────────────────────────
    def update_cash_balance(self):
        from api_client import api, APIError
        try:
            d = api.get_dashboard()

            net_balance  = d.get("net_balance",  0.0)
            gross_profit = d.get("gross_profit", 0.0)
            net_profit   = d.get("net_profit",   0.0)
            cash_sales   = d.get("cash_sales",   0.0)
            card_sales   = d.get("card_sales",   0.0)

            # Kasa rengi
            kasa_color = "#a6e3a1" if net_balance >= 0 else "#f38ba8"
            self.lbl_net_balance.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {kasa_color}; padding: 4px 0; text-align: center;"
            )
            self.lbl_net_balance.setText(f"Kasa:\n{net_balance:,.2f} TL")

            # Brüt kar rengi
            gp_color = "#89b4fa" if gross_profit >= 0 else "#f38ba8"
            self.lbl_gross_profit.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {gp_color}; padding: 4px 0; text-align: center;"
            )
            self.lbl_gross_profit.setText(f"Brut Kar:\n{gross_profit:,.2f} TL")

            # Net kar rengi
            np_color = "#89dceb" if net_profit >= 0 else "#f38ba8"
            self.lbl_net_profit.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {np_color}; padding: 4px 0; text-align: center;"
            )
            self.lbl_net_profit.setText(f"Net Kar:\n{net_profit:,.2f} TL")

            self.lbl_cash_card.setText(
                f"Nakit: {cash_sales:,.0f} TL  |  Kart: {card_sales:,.0f} TL"
            )

        except APIError:
            for lbl in [self.lbl_net_balance, self.lbl_gross_profit, self.lbl_net_profit]:
                lbl.setText("Baglanti Hatasi")
                lbl.setStyleSheet("font-size: 11px; color: #f38ba8; padding: 2px 0;")

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
        QLabel  { color: #cdd6f4; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #313244; color: #cdd6f4;
            border: 1px solid #45475a; padding: 5px; border-radius: 4px; }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 1px solid #89b4fa; }
        QPushButton {
            background-color: #89b4fa; color: #11111b;
            border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
        QPushButton:hover   { background-color: #b4befe; }
        QPushButton:pressed { background-color: #74c7ec; }
        QTableWidget {
            background-color: #181825; color: #cdd6f4;
            gridline-color: #313244; border: 1px solid #313244; border-radius: 4px; }
        QHeaderView::section {
            background-color: #313244; color: #cdd6f4;
            padding: 6px; border: 1px solid #45475a; font-weight: bold; }
        QTableWidget::item:selected { background-color: #45475a; color: #cdd6f4; }
        QTabWidget::pane { border: 1px solid #313244; border-radius: 4px; background-color: #1e1e2e; }
        QTabBar::tab {
            background: #313244; color: #a6adc8;
            padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px;
            margin-right: 2px; }
        QTabBar::tab:selected { background: #89b4fa; color: #11111b; font-weight: bold; }
    """)

    from api_client import api, APIError
    try:
        api.get_dashboard()
    except Exception as e:
        QMessageBox.critical(None, "Baglanti Hatasi",
                             f"API sunucusuna baglanillamiyor!\n\n{e}\n\n"
                             f"config.py dosyasindaki API_BASE_URL adresini kontrol edin.")
        sys.exit(1)

    # Login ekranı
    from login import LoginDialog
    login_dialog = LoginDialog()
    login_dialog.setStyleSheet(app.styleSheet())
    if login_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # Token'ı api_client'a aktar
    api.set_token(login_dialog.token)

    window = MainWindow(username=login_dialog.username)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
