from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QWidget,
                             QLabel, QDoubleSpinBox, QAbstractItemView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon
from modules.base import BaseModule
from api_client import api, APIError


class InlinePriceWidget(QWidget):
    """Tablo hücresine gömülü fiyat düzenleme widget'ı."""

    def __init__(self, product, on_save, parent=None):
        super().__init__(parent)
        self.product = product
        self.on_save = on_save
        self._editing = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(6)

        # Fiyat etiketi
        self.price_lbl = QLabel()
        self.price_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._update_label()
        lay.addWidget(self.price_lbl, stretch=1)

        # Fiyat input (gizli başlar)
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(1_000_000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" TL")
        self.price_input.setFixedWidth(130)
        self.price_input.setValue(product.get("price") or 0.0)
        self.price_input.setVisible(False)
        lay.addWidget(self.price_input)

        # Kalem butonu
        self.btn_edit = QPushButton("✏")
        self.btn_edit.setFixedSize(28, 28)
        self.btn_edit.setToolTip("Fiyat Duzenle")
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #80848e;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #404249;
                color: #f2f3f5;
            }
        """)
        self.btn_edit.clicked.connect(self._toggle_edit)
        lay.addWidget(self.btn_edit)

        # Kaydet butonu (gizli başlar)
        self.btn_save = QPushButton("✓")
        self.btn_save.setFixedSize(28, 28)
        self.btn_save.setToolTip("Kaydet")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #23a55a;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton:hover { background-color: #1e8a4a; }
        """)
        self.btn_save.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        lay.addWidget(self.btn_save)

        # İptal butonu (gizli başlar)
        self.btn_cancel = QPushButton("✕")
        self.btn_cancel.setFixedSize(28, 28)
        self.btn_cancel.setToolTip("Iptal")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:hover { background-color: #f23f42; }
        """)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel)
        lay.addWidget(self.btn_cancel)

    def _update_label(self):
        price = self.product.get("price") or 0.0
        cost  = self.product.get("cost_price") or 0.0
        if price == 0:
            self.price_lbl.setText("Girilmedi")
            self.price_lbl.setStyleSheet("color: #f0b232; font-size: 13px;")
        elif cost > 0 and price < cost:
            self.price_lbl.setText(f"{price:,.2f} TL")
            self.price_lbl.setStyleSheet("color: #f38ba8; font-size: 13px;")
        else:
            self.price_lbl.setText(f"{price:,.2f} TL")
            self.price_lbl.setStyleSheet("color: #a6e3a1; font-size: 13px; font-weight: 600;")

    def _toggle_edit(self):
        self._editing = True
        self.price_lbl.setVisible(False)
        self.price_input.setVisible(True)
        self.btn_edit.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)
        self.price_input.setFocus()
        self.price_input.selectAll()

    def _save(self):
        self.on_save(self.product["id"], self.price_input.value())
        self.product["price"] = self.price_input.value()
        self._close_edit()

    def _cancel(self):
        self.price_input.setValue(self.product.get("price") or 0.0)
        self._close_edit()

    def _close_edit(self):
        self._editing = False
        self.price_input.setVisible(False)
        self.price_lbl.setVisible(True)
        self.btn_edit.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self._update_label()


class PricingModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Başlık
        controls = QHBoxLayout()
        title = QLabel("Fiyatlandirma")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        hint = QLabel("Satış fiyatı girmek için ✏ ikonuna tıklayın")
        hint.setStyleSheet("font-size: 12px; color: #80848e;")
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self.load_products)
        controls.addWidget(title)
        controls.addWidget(hint)
        controls.addStretch()
        controls.addWidget(btn_refresh)
        layout.addLayout(controls)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Urun Adi", "Tedarikci", "Maliyet (TL)", "Stok", "Satis Fiyati"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.table)

        # Alt istatistik
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 12px; color: #80848e;")
        layout.addWidget(self.lbl_stats)

    def refresh_data(self):
        self.load_products()

    def load_products(self):
        try:
            products = api.get_products()
            self.table.setRowCount(0)

            no_price = 0
            for row, p in enumerate(products):
                self.table.insertRow(row)

                # Ürün adı
                name_item = QTableWidgetItem(p["name"])
                name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 0, name_item)

                # Tedarikçi
                sup_item = QTableWidgetItem(p.get("supplier_name") or "-")
                sup_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                sup_item.setForeground(QColor("#80848e"))
                self.table.setItem(row, 1, sup_item)

                # Maliyet
                cost_item = QTableWidgetItem(f"{p['cost_price']:,.2f} TL")
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 2, cost_item)

                # Stok
                stock_item = QTableWidgetItem(str(p["stock"]))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                stock_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if p["stock"] <= 0:
                    stock_item.setForeground(QColor("#f38ba8"))
                self.table.setItem(row, 3, stock_item)

                # Fiyat — inline widget
                widget = InlinePriceWidget(p, self._save_price)
                self.table.setCellWidget(row, 4, widget)

                if (p.get("price") or 0) == 0:
                    no_price += 1

            total = self.table.rowCount()
            self.lbl_stats.setText(
                f"Toplam {total} ürün  •  "
                f"{total - no_price} fiyatlandırılmış  •  "
                f"{no_price} fiyat girilmemiş"
            )
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _save_price(self, product_id, price):
        try:
            api.update_product_price(product_id, price)
        except APIError as e:
            QMessageBox.critical(self, "Kaydetme Hatasi", str(e))
