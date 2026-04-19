from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel,
                             QInputDialog, QWidget, QAbstractItemView, QComboBox,
                             QDoubleSpinBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from modules.base import BaseModule, parse_brand_model
from api_client import api, APIError

SEASON_COLORS = {"Kislik": "#74c0fc", "Yazlik": "#ffd43b", "4 Mevsim": "#8ce99a"}

LOW_STOCK_THRESHOLD = 3


class SalesModule(BaseModule):
    def __init__(self, parent=None):
        self._last_sale_id = None
        self._products_cache = {}   # id -> product dict (maliyet bilgisi için)
        super().__init__(parent)

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # ── Sol panel: Ürünler ────────────────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        lbl_products = QLabel("Urunler")
        lbl_products.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(lbl_products)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.setHorizontalHeaderLabels(["ID", "Urun", "Marka", "Mevsim", "Stok", "Fiyat (TL)"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        left_layout.addWidget(self.products_table)

        self.btn_add_cart = QPushButton("Sepete Ekle ->")
        self.btn_add_cart.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        self.btn_add_cart.clicked.connect(self.add_to_cart)
        left_layout.addWidget(self.btn_add_cart)

        # ── Sağ panel: Sepet ──────────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        lbl_cart = QLabel("Sepet")
        lbl_cart.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(lbl_cart)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.setHorizontalHeaderLabels(
            ["Urun ID", "Urun Adi", "Miktar", "Birim Fiyat", "Maliyet", "Toplam"]
        )
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        right_layout.addWidget(self.cart_table)

        self.btn_remove_cart = QPushButton("Secili Olani Sepetten Cikar")
        self.btn_remove_cart.clicked.connect(self.remove_from_cart)
        right_layout.addWidget(self.btn_remove_cart)

        # İndirim
        discount_layout = QHBoxLayout()
        discount_layout.addWidget(QLabel("Indirim Tipi:"))
        self.discount_type_combo = QComboBox()
        self.discount_type_combo.addItems(["Tutar (TL)", "Yuzde (%)"])
        self.discount_type_combo.currentIndexChanged.connect(self.update_cart_ui)
        discount_layout.addWidget(self.discount_type_combo)
        discount_layout.addWidget(QLabel("Indirim Degeri:"))
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMaximum(1000000.0)
        self.discount_input.setDecimals(2)
        self.discount_input.valueChanged.connect(self.update_cart_ui)
        discount_layout.addWidget(self.discount_input)
        right_layout.addLayout(discount_layout)

        # Müşteri & Ödeme
        details_layout = QFormLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Genel Musteri (Kayitsiz)", None)
        details_layout.addRow("Musteri:", self.customer_combo)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Nakit", "Kredi Karti", "Havale/EFT"])
        details_layout.addRow("Odeme Yontemi:", self.payment_combo)
        right_layout.addLayout(details_layout)

        self.lbl_subtotal = QLabel("Ara Toplam: 0.00 TL")
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(self.lbl_subtotal)

        # Kar/zarar göstergesi
        self.lbl_profit_preview = QLabel("")
        self.lbl_profit_preview.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_profit_preview.setStyleSheet("font-size: 12px; color: #89b4fa;")
        right_layout.addWidget(self.lbl_profit_preview)

        self.lbl_total = QLabel("Odenecek Tutar: 0.00 TL")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1; margin-top: 5px;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(self.lbl_total)

        btn_row = QHBoxLayout()
        self.btn_undo = QPushButton("Son Satisi Iptal Et")
        self.btn_undo.setStyleSheet("background-color: #e67e22; color: white; padding: 10px; font-weight: bold;")
        self.btn_undo.clicked.connect(self.undo_last_sale)
        self.btn_undo.setEnabled(False)
        self.btn_checkout = QPushButton("SAT (Odeme Al)")
        self.btn_checkout.setStyleSheet("background-color: #27ae60; color: white; padding: 15px; font-weight: bold; font-size: 16px;")
        self.btn_checkout.clicked.connect(self.checkout)
        btn_row.addWidget(self.btn_undo)
        btn_row.addWidget(self.btn_checkout)
        right_layout.addLayout(btn_row)

        layout.addWidget(left_widget, stretch=6)
        layout.addWidget(right_widget, stretch=4)

        self.cart_items = []
        self.current_total_amount = 0.0
        self.current_discount_amount = 0.0
        self.current_estimated_cost = 0.0

    def refresh_data(self):
        self.load_products()
        self.load_customers()
        self.btn_undo.setEnabled(self._last_sale_id is not None)

    def load_customers(self):
        try:
            customers = api.get_customers()
            self.customer_combo.clear()
            self.customer_combo.addItem("Genel Musteri (Kayitsiz)", None)
            for c in sorted(customers, key=lambda x: x["name"]):
                self.customer_combo.addItem(
                    f"{c['name']} ({c.get('car_plate') or 'Plaka Yok'})", c["id"]
                )
        except APIError:
            pass

    def load_products(self):
        try:
            products = api.get_products()
            self._products_cache = {p["id"]: p for p in products}
            self.products_table.setRowCount(0)
            for row, p in enumerate(products):
                self.products_table.insertRow(row)
                season, model = parse_brand_model(p.get("brand_model") or "")
                # Urun adi: "Urun Adi · Model" formatinda goster
                name_txt = p["name"]
                if model:
                    name_txt = f"{p['name']}  ·  {model}"
                self.products_table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
                self.products_table.setItem(row, 1, QTableWidgetItem(name_txt))
                self.products_table.setItem(row, 2, QTableWidgetItem(p.get("brand_name") or "-"))

                season_item = QTableWidgetItem(season or "-")
                season_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if season and season in SEASON_COLORS:
                    season_item.setForeground(QColor(SEASON_COLORS[season]))
                self.products_table.setItem(row, 3, season_item)

                stock_item = QTableWidgetItem(str(p["stock"]))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if p["stock"] <= 0:
                    stock_item.setForeground(QColor("#f38ba8"))
                elif p["stock"] <= LOW_STOCK_THRESHOLD:
                    stock_item.setForeground(QColor("#fab387"))
                self.products_table.setItem(row, 4, stock_item)
                price_item = QTableWidgetItem(f"{p['price']:,.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.products_table.setItem(row, 5, price_item)
        except APIError as e:
            QMessageBox.critical(self, "Baglanti Hatasi", str(e))

    def add_to_cart(self):
        selected = self.products_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Bilgi", "Sepete eklemek icin bir urun secin.")
            return
        row = selected[0].row()
        product_id      = int(self.products_table.item(row, 0).text())
        product_name    = self.products_table.item(row, 1).text()
        available_stock = int(self.products_table.item(row, 4).text())
        price           = float(self.products_table.item(row, 5).text().replace(",", ""))
        cost_price      = float(self._products_cache.get(product_id, {}).get("cost_price", 0))

        if available_stock <= 0:
            QMessageBox.warning(self, "Hata", "Bu urun stokta kalmamis!")
            return

        qty, ok = QInputDialog.getInt(
            self, "Miktar",
            f"{product_name} urununden kac adet satilacak?",
            1, 1, available_stock
        )
        if not (ok and qty > 0):
            return

        for item in self.cart_items:
            if item["product_id"] == product_id:
                if item["qty"] + qty > available_stock:
                    QMessageBox.warning(self, "Stok Yetersiz", "Stoktakinden fazla urun sepete eklenemez.")
                    return
                item["qty"] += qty
                self.update_cart_ui()
                return

        self.cart_items.append({
            "product_id": product_id,
            "name": product_name,
            "price": price,
            "cost_price": cost_price,
            "qty": qty
        })
        self.update_cart_ui()

    def remove_from_cart(self):
        selected = self.cart_table.selectedItems()
        if not selected:
            return
        del self.cart_items[selected[0].row()]
        self.update_cart_ui()

    def update_cart_ui(self):
        self.cart_table.setRowCount(0)
        subtotal   = 0.0
        total_cost = 0.0

        for row, item in enumerate(self.cart_items):
            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, QTableWidgetItem(str(item["product_id"])))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item["name"]))

            qty_item = QTableWidgetItem(str(item["qty"]))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.cart_table.setItem(row, 2, qty_item)

            price_item = QTableWidgetItem(f"{item['price']:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.cart_table.setItem(row, 3, price_item)

            cost_item = QTableWidgetItem(f"{item['cost_price']:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Maliyet > satış fiyatı ise kırmızı göster
            if item["cost_price"] > item["price"]:
                cost_item.setForeground(QColor("#f38ba8"))
            self.cart_table.setItem(row, 4, cost_item)

            line_total = item["qty"] * item["price"]
            subtotal  += line_total
            total_cost += item["qty"] * item["cost_price"]
            total_item = QTableWidgetItem(f"{line_total:,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.cart_table.setItem(row, 5, total_item)

        # İndirim hesapla
        discount_val = self.discount_input.value()
        discount_amount = 0.0
        if self.discount_type_combo.currentText() == "Yuzde (%)":
            if discount_val > 100.0:
                self.discount_input.blockSignals(True)
                self.discount_input.setValue(100.0)
                self.discount_input.blockSignals(False)
                discount_val = 100.0
            discount_amount = subtotal * (discount_val / 100.0)
        else:
            if subtotal > 0 and discount_val > subtotal:
                self.discount_input.blockSignals(True)
                self.discount_input.setValue(subtotal)
                self.discount_input.blockSignals(False)
                discount_val = subtotal
            discount_amount = discount_val

        final_total = max(0.0, subtotal - discount_amount)
        estimated_profit = final_total - total_cost

        self.lbl_subtotal.setText(
            f"Ara Toplam: {subtotal:,.2f} TL  (Indirim: {discount_amount:,.2f} TL)"
        )

        # Kar/zarar önizleme
        if self.cart_items:
            if estimated_profit < 0:
                self.lbl_profit_preview.setStyleSheet("font-size: 12px; color: #f38ba8; font-weight: bold;")
                self.lbl_profit_preview.setText(f"⚠ Tahmini Zarar: {estimated_profit:,.2f} TL")
            else:
                self.lbl_profit_preview.setStyleSheet("font-size: 12px; color: #a6e3a1;")
                self.lbl_profit_preview.setText(f"Tahmini Kar: {estimated_profit:,.2f} TL")
        else:
            self.lbl_profit_preview.setText("")

        self.lbl_total.setText(f"Odenecek Tutar: {final_total:,.2f} TL")
        self.current_total_amount   = final_total
        self.current_discount_amount = discount_amount
        self.current_estimated_cost  = total_cost

    def checkout(self):
        if not self.cart_items:
            QMessageBox.information(self, "Hata", "Sepetiniz bos!")
            return

        # Zararlı satış uyarısı
        estimated_profit = self.current_total_amount - self.current_estimated_cost
        if estimated_profit < 0:
            reply = QMessageBox.warning(
                self, "Zarar Uyarisi",
                f"Bu satis {abs(estimated_profit):,.2f} TL ZARARLI gozukuyor!\n\n"
                f"Satis tutari: {self.current_total_amount:,.2f} TL\n"
                f"Tahmini maliyet: {self.current_estimated_cost:,.2f} TL\n\n"
                f"Yine de devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        reply = QMessageBox.question(
            self, "Satis Onayi",
            f"Toplam {self.current_total_amount:,.2f} TL tutarindaki satisi onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            items = [
                {"product_id": i["product_id"], "quantity": i["qty"], "unit_price": i["price"]}
                for i in self.cart_items
            ]
            result = api.create_sale(
                items,
                self.current_discount_amount,
                self.payment_combo.currentText(),
                self.customer_combo.currentData()
            )
            self._last_sale_id = result["id"]
            self.btn_undo.setEnabled(True)

            # Sonuç mesajı — kar/zarar göster
            profit = result.get("profit", 0.0)
            profit_text = ""
            if profit < 0:
                profit_text = f"\nKar/Zarar: {profit:,.2f} TL (ZARAR)"
            else:
                profit_text = f"\nKar/Zarar: +{profit:,.2f} TL"

            QMessageBox.information(
                self, "Basarili",
                f"Satis tamamlandi!\nTutar: {result['total_amount']:,.2f} TL{profit_text}"
            )
            self.cart_items = []
            self.discount_input.setValue(0.0)
            self.update_cart_ui()
            self.load_products()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()

        except APIError as e:
            QMessageBox.critical(self, "Hata", "Satis tamamlanamadi:\n" + str(e))

    def undo_last_sale(self):
        if not self._last_sale_id:
            QMessageBox.information(self, "Bilgi", "Geri alinacak satis bulunamadi.")
            return
        reply = QMessageBox.question(
            self, "Son Satisi Iptal Et",
            f"Satis #{self._last_sale_id} geri alinacak. Stoklar iade edilecek. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            api.undo_sale(self._last_sale_id)
            self._last_sale_id = None
            self.btn_undo.setEnabled(False)
            QMessageBox.information(self, "Basarili", "Satis geri alindi.")
            self.load_products()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", "Geri alma basarisiz:\n" + str(e))