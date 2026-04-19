from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QTabWidget, QWidget, QPushButton,
                             QMessageBox, QAbstractItemView, QFrame, QComboBox,
                             QDateEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont
from modules.base import BaseModule, parse_brand_model
from api_client import api, APIError
import datetime

SEASON_COLORS = {"Kislik": "#74c0fc", "Yazlik": "#ffd43b", "4 Mevsim": "#8ce99a"}


def _product_label(item, products_by_id):
    """Satir ogesi icin 'Urun · Model (Mevsim)' etiketi uretir."""
    base = item.get("product_name") or "-"
    pid = item.get("product_id")
    extras = []
    if pid and products_by_id:
        p = products_by_id.get(pid)
        if p:
            season, model = parse_brand_model(p.get("brand_model") or "")
            if model and model not in base:
                extras.append(model)
            if season:
                extras.append(f"({season})")
    if extras:
        return base + "  ·  " + " ".join(extras)
    return base

COLOR_CANCELLED  = QColor("#3b1f1f")
COLOR_CANCEL_FG  = QColor("#f38ba8")
COLOR_LOSS_BG    = QColor("#2d1a1a")
COLOR_LOSS_FG    = QColor("#f38ba8")
COLOR_PROFIT_FG  = QColor("#a6e3a1")
COLOR_LOG_BG     = QColor("#2a1f3b")
COLOR_LOG_FG     = QColor("#cba6f7")
COLOR_NEUTRAL_FG = QColor("#cdd6f4")


def fmt_dt(dt_str):
    """ISO → 'GG.AA.YYYY SS:DD:SN' formatı."""
    if not dt_str:
        return "-"
    try:
        s = dt_str[:19].replace("T", " ")
        date, time = s.split(" ")
        y, m, d = date.split("-")
        return f"{d}.{m}.{y} {time}"
    except Exception:
        return dt_str[:19]


def _paint_row(table, row, bg, fg):
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(QBrush(bg))
            item.setForeground(QBrush(fg))


def _right(text):
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return item


def _center(text):
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
    return item


class DateFilterBar(QWidget):
    """Hızlı tarih filtresi — Bugün / Bu Hafta / Bu Ay / Tümü / Özel."""

    def __init__(self, on_change, parent=None):
        super().__init__(parent)
        self.on_change = on_change
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)

        lay.addWidget(QLabel("Dönem:"))

        self.combo = QComboBox()
        self.combo.addItems(["Bugün", "Bu Hafta", "Bu Ay", "Bu Yıl", "Tümü", "Özel Aralık"])
        self.combo.setFixedWidth(130)
        self.combo.currentIndexChanged.connect(self._on_combo)
        lay.addWidget(self.combo)

        self.lbl_from = QLabel("Başlangıç:")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setFixedWidth(110)

        self.lbl_to = QLabel("Bitiş:")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(110)

        self.btn_apply = QPushButton("Uygula")
        self.btn_apply.setFixedWidth(70)
        self.btn_apply.clicked.connect(lambda: self.on_change(*self.get_range()))

        for w in [self.lbl_from, self.date_from, self.lbl_to, self.date_to, self.btn_apply]:
            lay.addWidget(w)
            w.setVisible(False)

        lay.addStretch()

        # Kayıt sayısı
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size: 11px; color: #80848e;")
        lay.addWidget(self.lbl_count)

    def _on_combo(self, idx):
        is_custom = (idx == 5)
        for w in [self.lbl_from, self.date_from, self.lbl_to, self.date_to, self.btn_apply]:
            w.setVisible(is_custom)
        if not is_custom:
            self.on_change(*self.get_range())

    def get_range(self):
        """(start_dt, end_dt) veya (None, None) döner."""
        idx = self.combo.currentIndex()
        today = datetime.date.today()
        if idx == 0:   # Bugün
            return datetime.datetime(today.year, today.month, today.day, 0, 0, 0), \
                   datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        elif idx == 1: # Bu Hafta
            start = today - datetime.timedelta(days=today.weekday())
            return datetime.datetime.combine(start, datetime.time.min), \
                   datetime.datetime.combine(today, datetime.time.max)
        elif idx == 2: # Bu Ay
            start = today.replace(day=1)
            return datetime.datetime.combine(start, datetime.time.min), \
                   datetime.datetime.combine(today, datetime.time.max)
        elif idx == 3: # Bu Yıl
            start = today.replace(month=1, day=1)
            return datetime.datetime.combine(start, datetime.time.min), \
                   datetime.datetime.combine(today, datetime.time.max)
        elif idx == 4: # Tümü
            return None, None
        else:          # Özel
            qf = self.date_from.date(); qt = self.date_to.date()
            return datetime.datetime(qf.year(), qf.month(), qf.day(), 0, 0, 0), \
                   datetime.datetime(qt.year(), qt.month(), qt.day(), 23, 59, 59)

    def set_count(self, n, total):
        if total == n:
            self.lbl_count.setText(f"{n} kayıt")
        else:
            self.lbl_count.setText(f"{n} / {total} kayıt gösteriliyor")


def _in_range(dt_str, start, end):
    """Tarih aralığı kontrolü. start/end None ise tümünü geçer."""
    if start is None:
        return True
    try:
        dt = datetime.datetime.fromisoformat(dt_str[:19])
        return start <= dt <= end
    except Exception:
        return True


class HistoryModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Alim ve Satim Gecmisi")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_sales     = QWidget(); self._setup_sales_tab()
        self.tab_purchases = QWidget(); self._setup_purchases_tab()
        self.tab_logs      = QWidget(); self._setup_logs_tab()

        self.tabs.addTab(self.tab_sales,     "Satis Gecmisi")
        self.tabs.addTab(self.tab_purchases, "Alim Gecmisi")
        self.tabs.addTab(self.tab_logs,      "Iptal Kayitlari")

        # Tüm verileri önbellekte tut
        self._all_sales     = []
        self._all_purchases = []
        self._all_logs      = []
        self._products_by_id = {}

    def _setup_sales_tab(self):
        layout = QVBoxLayout(self.tab_sales)

        # Filtre barı
        self.sales_filter = DateFilterBar(self._apply_sales_filter)
        layout.addWidget(self.sales_filter)

        self.sale_summary = QLabel("Toplam: —")
        self.sale_summary.setStyleSheet(
            "font-size: 12px; color: #a6adc8; padding: 4px 0; border-bottom: 1px solid #313244;"
        )
        layout.addWidget(self.sale_summary)

        btn_row = QHBoxLayout()
        self.btn_cancel_item = QPushButton("Secili Kalemi Iptal Et")
        self.btn_cancel_item.setStyleSheet(
            "background-color: #e67e22; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_item.clicked.connect(self._cancel_sale_item)
        self.btn_cancel_sale = QPushButton("Tum Satisi Iptal Et")
        self.btn_cancel_sale.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_sale.clicked.connect(self._cancel_full_sale)
        btn_row.addWidget(self.btn_cancel_item)
        btn_row.addWidget(self.btn_cancel_sale)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(11)
        self.sales_table.setHorizontalHeaderLabels([
            "Satis No", "Tarih & Saat", "Musteri", "Odeme",
            "Urun Adi", "Adet",
            "Birim Fiyat", "Maliyet/Adet", "Indirim Payi",
            "Kar/Zarar", "Durum"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sales_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sales_table)

    def _setup_purchases_tab(self):
        layout = QVBoxLayout(self.tab_purchases)

        self.purchases_filter = DateFilterBar(self._apply_purchases_filter)
        layout.addWidget(self.purchases_filter)

        self.purchase_summary = QLabel("Toplam: —")
        self.purchase_summary.setStyleSheet(
            "font-size: 12px; color: #a6adc8; padding: 4px 0; border-bottom: 1px solid #313244;"
        )
        layout.addWidget(self.purchase_summary)

        btn_row = QHBoxLayout()
        self.btn_cancel_purchase = QPushButton("Secili Alimi Iptal Et")
        self.btn_cancel_purchase.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_purchase.clicked.connect(self._cancel_purchase)
        btn_row.addWidget(self.btn_cancel_purchase)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(8)
        self.purchases_table.setHorizontalHeaderLabels([
            "Alim No", "Tarih & Saat", "Tedarikci",
            "Urun Adi", "Adet",
            "Birim Maliyet", "Toplam Tutar", "Durum"
        ])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.purchases_table.horizontalHeader().setStretchLastSection(True)
        self.purchases_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.purchases_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.purchases_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.purchases_table)

    def _setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)

        self.logs_filter = DateFilterBar(self._apply_logs_filter)
        layout.addWidget(self.logs_filter)

        lbl = QLabel("Tum iptal islemlerinin kalici kaydi — silinemez.")
        lbl.setStyleSheet("color: #a6adc8; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(lbl)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Iptal Tarihi & Saati", "Tur", "Kayit No",
            "Aciklama", "Iptal Adet",
            "Iade Tutar", "Maliyet Etkisi"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.logs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.logs_table)

    def refresh_data(self):
        self._load_products_cache()
        self._load_sales_history()
        self._load_purchases_history()
        self._load_cancellation_logs()

    def _load_products_cache(self):
        try:
            self._products_by_id = {p["id"]: p for p in api.get_products()}
        except APIError:
            self._products_by_id = {}

    # ── Veri yükleme ──────────────────────────────────────────────────────────
    def _load_sales_history(self):
        try:
            self._all_sales = api.get_sales()
            start, end = self.sales_filter.get_range()
            self._apply_sales_filter(start, end)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_purchases_history(self):
        try:
            self._all_purchases = api.get_purchases()
            start, end = self.purchases_filter.get_range()
            self._apply_purchases_filter(start, end)
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_cancellation_logs(self):
        try:
            self._all_logs = api.get_cancellation_logs()
            start, end = self.logs_filter.get_range()
            self._apply_logs_filter(start, end)
        except APIError:
            pass

    # ── Filtre uygulama ───────────────────────────────────────────────────────
    def _apply_sales_filter(self, start, end):
        sales = [s for s in self._all_sales if _in_range(s.get("timestamp", ""), start, end)]
        self._render_sales(sales)
        self.sales_filter.set_count(len(sales), len(self._all_sales))

    def _apply_purchases_filter(self, start, end):
        purchases = [p for p in self._all_purchases if _in_range(p.get("timestamp", ""), start, end)]
        self._render_purchases(purchases)
        self.purchases_filter.set_count(len(purchases), len(self._all_purchases))

    def _apply_logs_filter(self, start, end):
        logs = [l for l in self._all_logs if _in_range(l.get("timestamp", ""), start, end)]
        self._render_logs(logs)
        self.logs_filter.set_count(len(logs), len(self._all_logs))

    # ── Render ────────────────────────────────────────────────────────────────
    def _render_sales(self, sales):
        self.sales_table.setRowCount(0)
        total_satis = total_maliyet = total_kar = 0.0
        loss_count = 0

        for sale in sales:
            items        = sale.get("items", [])
            active_items = [i for i in items if not i.get("is_cancelled")]
            gross_total  = sum(i["quantity"] * i["unit_price"] for i in active_items)
            discount     = sale.get("discount", 0.0)

            for item in items:
                row = self.sales_table.rowCount()
                self.sales_table.insertRow(row)

                sale_cancelled   = sale["is_cancelled"]
                item_cancelled   = item["is_cancelled"]
                is_any_cancelled = sale_cancelled or item_cancelled

                if sale_cancelled:   status = "Satis Iptal"
                elif item_cancelled: status = "Kalem Iptal"
                else:                status = "Aktif"

                item_gross    = item["quantity"] * item["unit_price"]
                item_discount = discount * (item_gross / gross_total) if gross_total > 0 and not item_cancelled else 0.0
                item_net      = item_gross - item_discount
                item_cost     = item["quantity"] * item.get("unit_cost", 0.0)
                item_profit   = item_net - item_cost
                is_loss       = item_profit < 0 and not is_any_cancelled

                cells = [
                    QTableWidgetItem(f"SAT-{sale['id']}"),
                    QTableWidgetItem(fmt_dt(sale.get("timestamp"))),
                    QTableWidgetItem(sale.get("customer_name") or "Genel"),
                    QTableWidgetItem(sale.get("payment_method", "-")),
                    QTableWidgetItem(_product_label(item, self._products_by_id)),
                    _right(str(item["quantity"])),
                    _right(f"{item['unit_price']:,.2f} TL"),
                    _right(f"{item.get('unit_cost', 0):,.2f} TL"),
                    _right(f"{item_discount:,.2f} TL"),
                    _right(f"{item_profit:,.2f} TL"),
                    _center(status),
                ]

                for col, cell_item in enumerate(cells):
                    if col == 0: cell_item.setData(Qt.ItemDataRole.UserRole, sale["id"])
                    if col == 4: cell_item.setData(Qt.ItemDataRole.UserRole, item["id"])
                    self.sales_table.setItem(row, col, cell_item)

                if is_any_cancelled:
                    _paint_row(self.sales_table, row, COLOR_CANCELLED, COLOR_CANCEL_FG)
                elif is_loss:
                    _paint_row(self.sales_table, row, COLOR_LOSS_BG, COLOR_NEUTRAL_FG)
                    self.sales_table.item(row, 9).setForeground(QBrush(COLOR_LOSS_FG))
                else:
                    self.sales_table.item(row, 9).setForeground(QBrush(COLOR_PROFIT_FG))

                if not is_any_cancelled:
                    total_satis   += item_net
                    total_maliyet += item_cost
                    total_kar     += item_profit
                    if is_loss: loss_count += 1

        loss_text = f"  |  ⚠ {loss_count} zarali kalem" if loss_count > 0 else ""
        self.sale_summary.setText(
            f"Toplam Satis: {total_satis:,.2f} TL  |  "
            f"Maliyet: {total_maliyet:,.2f} TL  |  "
            f"Kar: {total_kar:,.2f} TL{loss_text}"
        )

    def _render_purchases(self, purchases):
        self.purchases_table.setRowCount(0)
        total_alim = aktif_count = iptal_count = 0

        for purchase in purchases:
            is_cancelled = purchase["is_cancelled"]
            for item in purchase.get("items", []):
                row = self.purchases_table.rowCount()
                self.purchases_table.insertRow(row)
                line_total = item["quantity"] * item["unit_price"]
                cells = [
                    QTableWidgetItem(f"ALIM-{purchase['id']}"),
                    QTableWidgetItem(fmt_dt(purchase.get("timestamp"))),
                    QTableWidgetItem(purchase.get("supplier_name") or "Bilinmiyor"),
                    QTableWidgetItem(_product_label(item, self._products_by_id)),
                    _right(str(item["quantity"])),
                    _right(f"{item['unit_price']:,.2f} TL"),
                    _right(f"{line_total:,.2f} TL"),
                    _center("Iptal" if is_cancelled else "Aktif"),
                ]
                for col, cell_item in enumerate(cells):
                    if col == 0: cell_item.setData(Qt.ItemDataRole.UserRole, purchase["id"])
                    self.purchases_table.setItem(row, col, cell_item)
                if is_cancelled:
                    _paint_row(self.purchases_table, row, COLOR_CANCELLED, COLOR_CANCEL_FG)
                    iptal_count += 1
                else:
                    total_alim += line_total
                    aktif_count += 1

        self.purchase_summary.setText(
            f"Toplam Alim: {total_alim:,.2f} TL  |  "
            f"Aktif Kalem: {aktif_count}  |  Iptal: {iptal_count}"
        )

    def _render_logs(self, logs):
        self.logs_table.setRowCount(0)
        for row, log in enumerate(logs):
            self.logs_table.insertRow(row)
            cells = [
                QTableWidgetItem(fmt_dt(log.get("timestamp"))),
                _center(log["record_type"]),
                _center(str(log["record_id"])),
                QTableWidgetItem(log.get("description", "")),
                _right(str(log["cancelled_qty"]) if log.get("cancelled_qty") else "-"),
                _right(f"{log['refund_amount']:,.2f} TL" if log.get("refund_amount") else "-"),
                _right(f"{log['cost_amount']:,.2f} TL"   if log.get("cost_amount")   else "-"),
            ]
            for col, cell_item in enumerate(cells):
                cell_item.setBackground(QBrush(COLOR_LOG_BG))
                cell_item.setForeground(QBrush(COLOR_LOG_FG))
                self.logs_table.setItem(row, col, cell_item)

    # ── Aksiyon ───────────────────────────────────────────────────────────────
    def _get_selected_sale_info(self):
        selected = self.sales_table.selectedItems()
        if not selected: return None, None
        row     = selected[0].row()
        sale_id = self.sales_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item_id = self.sales_table.item(row, 4).data(Qt.ItemDataRole.UserRole)
        return sale_id, item_id

    def _get_selected_purchase_id(self):
        selected = self.purchases_table.selectedItems()
        if not selected: return None
        return self.purchases_table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _cancel_sale_item(self):
        sale_id, item_id = self._get_selected_sale_info()
        if not item_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir satis kalemi secin.")
            return
        reply = QMessageBox.question(
            self, "Kalem Iptali",
            "Bu kalem iptal edilecek, stok iade edilecek. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            result = api.cancel_sale_item(sale_id, item_id)
            iade = result.get("refund_amount", 0)
            QMessageBox.information(self, "Basarili", f"Kalem iptal edildi. Iade: {iade:,.2f} TL")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_full_sale(self):
        sale_id, _ = self._get_selected_sale_info()
        if not sale_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir satis secin.")
            return
        reply = QMessageBox.question(
            self, "Tum Satisi Iptal Et",
            f"SAT-{sale_id} tamamen iptal edilecek. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            result = api.cancel_full_sale(sale_id)
            iade = result.get("refund_amount", 0)
            QMessageBox.information(self, "Basarili", f"Satis iptal edildi. Iade: {iade:,.2f} TL")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_purchase(self):
        purchase_id = self._get_selected_purchase_id()
        if not purchase_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir alim secin.")
            return
        reply = QMessageBox.question(
            self, "Alim Iptali",
            f"ALIM-{purchase_id} iptal edilecek. Stok ve borc geri alinacak. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            api.cancel_purchase(purchase_id)
            QMessageBox.information(self, "Basarili", "Alim iptal edildi.")
            self.refresh_data()
            if hasattr(self, "main_window"): self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))


COLOR_CANCELLED  = QColor("#3b1f1f")
COLOR_CANCEL_FG  = QColor("#f38ba8")
COLOR_LOSS_BG    = QColor("#2d1a1a")
COLOR_LOSS_FG    = QColor("#f38ba8")
COLOR_PROFIT_FG  = QColor("#a6e3a1")
COLOR_LOG_BG     = QColor("#2a1f3b")
COLOR_LOG_FG     = QColor("#cba6f7")
COLOR_NEUTRAL_FG = QColor("#cdd6f4")


def _paint_row(table, row, bg, fg):
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(QBrush(bg))
            item.setForeground(QBrush(fg))


def _right(text):
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return item


def _center(text):
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
    return item


class HistoryModule(BaseModule):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Alim ve Satim Gecmisi")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_sales     = QWidget(); self._setup_sales_tab()
        self.tab_purchases = QWidget(); self._setup_purchases_tab()
        self.tab_logs      = QWidget(); self._setup_logs_tab()

        self.tabs.addTab(self.tab_sales,     "Satis Gecmisi")
        self.tabs.addTab(self.tab_purchases, "Alim Gecmisi")
        self.tabs.addTab(self.tab_logs,      "Iptal Kayitlari")

    def _setup_sales_tab(self):
        layout = QVBoxLayout(self.tab_sales)

        self.sale_summary = QLabel("Toplam: —")
        self.sale_summary.setStyleSheet(
            "font-size: 12px; color: #a6adc8; padding: 4px 0; border-bottom: 1px solid #313244;"
        )
        layout.addWidget(self.sale_summary)

        btn_row = QHBoxLayout()
        self.btn_cancel_item = QPushButton("Secili Kalemi Iptal Et")
        self.btn_cancel_item.setStyleSheet(
            "background-color: #e67e22; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_item.clicked.connect(self._cancel_sale_item)
        self.btn_cancel_sale = QPushButton("Tum Satisi Iptal Et")
        self.btn_cancel_sale.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_sale.clicked.connect(self._cancel_full_sale)
        btn_row.addWidget(self.btn_cancel_item)
        btn_row.addWidget(self.btn_cancel_sale)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(11)
        self.sales_table.setHorizontalHeaderLabels([
            "Satis No", "Tarih", "Musteri", "Odeme",
            "Urun Adi", "Adet",
            "Birim Fiyat", "Maliyet/Adet", "Indirim Payi",
            "Kar/Zarar", "Durum"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sales_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sales_table)

    def _setup_purchases_tab(self):
        layout = QVBoxLayout(self.tab_purchases)

        self.purchase_summary = QLabel("Toplam: —")
        self.purchase_summary.setStyleSheet(
            "font-size: 12px; color: #a6adc8; padding: 4px 0; border-bottom: 1px solid #313244;"
        )
        layout.addWidget(self.purchase_summary)

        btn_row = QHBoxLayout()
        self.btn_cancel_purchase = QPushButton("Secili Alimi Iptal Et")
        self.btn_cancel_purchase.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_cancel_purchase.clicked.connect(self._cancel_purchase)
        btn_row.addWidget(self.btn_cancel_purchase)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(8)
        self.purchases_table.setHorizontalHeaderLabels([
            "Alim No", "Tarih", "Tedarikci",
            "Urun Adi", "Adet",
            "Birim Maliyet", "Toplam Tutar", "Durum"
        ])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.purchases_table.horizontalHeader().setStretchLastSection(True)
        self.purchases_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.purchases_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.purchases_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.purchases_table)

    def _setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        lbl = QLabel("Tum iptal islemlerinin kalici kaydi — silinemez.")
        lbl.setStyleSheet("color: #a6adc8; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(lbl)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Iptal Tarihi", "Tur", "Kayit No",
            "Aciklama", "Iptal Adet",
            "Iade Tutar", "Maliyet Etkisi"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.logs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.logs_table)

    def refresh_data(self):
        self._load_sales_history()
        self._load_purchases_history()
        self._load_cancellation_logs()

    def _load_sales_history(self):
        try:
            sales = api.get_sales()
            self.sales_table.setRowCount(0)

            total_satis   = 0.0
            total_maliyet = 0.0
            total_kar     = 0.0
            loss_count    = 0

            for sale in sales:
                items        = sale.get("items", [])
                active_items = [i for i in items if not i.get("is_cancelled")]
                gross_total  = sum(i["quantity"] * i["unit_price"] for i in active_items)
                discount     = sale.get("discount", 0.0)

                for item in items:
                    row = self.sales_table.rowCount()
                    self.sales_table.insertRow(row)

                    sale_cancelled = sale["is_cancelled"]
                    item_cancelled = item["is_cancelled"]
                    is_any_cancelled = sale_cancelled or item_cancelled

                    if sale_cancelled:   status = "Satis Iptal"
                    elif item_cancelled: status = "Kalem Iptal"
                    else:               status = "Aktif"

                    item_gross = item["quantity"] * item["unit_price"]
                    if gross_total > 0 and not item_cancelled:
                        item_discount = discount * (item_gross / gross_total)
                    else:
                        item_discount = 0.0

                    item_net    = item_gross - item_discount
                    item_cost   = item["quantity"] * item.get("unit_cost", 0.0)
                    item_profit = item_net - item_cost
                    is_loss     = item_profit < 0 and not is_any_cancelled

                    cells = [
                        QTableWidgetItem(f"SAT-{sale['id']}"),
                        QTableWidgetItem(sale["timestamp"][:16].replace("T", " ")),
                        QTableWidgetItem(sale.get("customer_name") or "Genel"),
                        QTableWidgetItem(sale.get("payment_method", "-")),
                        QTableWidgetItem(_product_label(item, getattr(self, "_products_by_id", {}))),
                        _right(str(item["quantity"])),
                        _right(f"{item['unit_price']:,.2f} TL"),
                        _right(f"{item.get('unit_cost', 0):,.2f} TL"),
                        _right(f"{item_discount:,.2f} TL"),
                        _right(f"{item_profit:,.2f} TL"),
                        _center(status),
                    ]

                    for col, cell_item in enumerate(cells):
                        if col == 0:
                            cell_item.setData(Qt.ItemDataRole.UserRole, sale["id"])
                        if col == 4:
                            cell_item.setData(Qt.ItemDataRole.UserRole, item["id"])
                        self.sales_table.setItem(row, col, cell_item)

                    if is_any_cancelled:
                        _paint_row(self.sales_table, row, COLOR_CANCELLED, COLOR_CANCEL_FG)
                    elif is_loss:
                        _paint_row(self.sales_table, row, COLOR_LOSS_BG, COLOR_NEUTRAL_FG)
                        self.sales_table.item(row, 9).setForeground(QBrush(COLOR_LOSS_FG))
                    else:
                        self.sales_table.item(row, 9).setForeground(QBrush(COLOR_PROFIT_FG))

                    if not is_any_cancelled:
                        total_satis   += item_net
                        total_maliyet += item_cost
                        total_kar     += item_profit
                        if is_loss:
                            loss_count += 1

            kar_color = "#a6e3a1" if total_kar >= 0 else "#f38ba8"
            loss_text = f"  |  ⚠ {loss_count} zarali kalem" if loss_count > 0 else ""
            self.sale_summary.setText(
                f"Toplam Satis: {total_satis:,.2f} TL  |  "
                f"Maliyet: {total_maliyet:,.2f} TL  |  "
                f"Kar: {total_kar:,.2f} TL"
                f"{loss_text}"
            )

        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_purchases_history(self):
        try:
            purchases = api.get_purchases()
            self.purchases_table.setRowCount(0)

            total_alim  = 0.0
            aktif_count = 0
            iptal_count = 0

            for purchase in purchases:
                is_cancelled = purchase["is_cancelled"]
                for item in purchase.get("items", []):
                    row = self.purchases_table.rowCount()
                    self.purchases_table.insertRow(row)

                    line_total = item["quantity"] * item["unit_price"]
                    status     = "Iptal" if is_cancelled else "Aktif"

                    cells = [
                        QTableWidgetItem(f"ALIM-{purchase['id']}"),
                        QTableWidgetItem(purchase["timestamp"][:16].replace("T", " ")),
                        QTableWidgetItem(purchase.get("supplier_name") or "Bilinmiyor"),
                        QTableWidgetItem(_product_label(item, getattr(self, "_products_by_id", {}))),
                        _right(str(item["quantity"])),
                        _right(f"{item['unit_price']:,.2f} TL"),
                        _right(f"{line_total:,.2f} TL"),
                        _center(status),
                    ]

                    for col, cell_item in enumerate(cells):
                        if col == 0:
                            cell_item.setData(Qt.ItemDataRole.UserRole, purchase["id"])
                        self.purchases_table.setItem(row, col, cell_item)

                    if is_cancelled:
                        _paint_row(self.purchases_table, row, COLOR_CANCELLED, COLOR_CANCEL_FG)
                        iptal_count += 1
                    else:
                        total_alim  += line_total
                        aktif_count += 1

            self.purchase_summary.setText(
                f"Toplam Alim: {total_alim:,.2f} TL  |  "
                f"Aktif Kalem: {aktif_count}  |  "
                f"Iptal Alim: {iptal_count}"
            )

        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _load_cancellation_logs(self):
        try:
            logs = api.get_cancellation_logs()
            self.logs_table.setRowCount(0)
            for row, log in enumerate(logs):
                self.logs_table.insertRow(row)
                cells = [
                    QTableWidgetItem(log["timestamp"][:19].replace("T", " ")),
                    _center(log["record_type"]),
                    _center(str(log["record_id"])),
                    QTableWidgetItem(log.get("description", "")),
                    _right(str(log["cancelled_qty"]) if log.get("cancelled_qty") else "-"),
                    _right(f"{log['refund_amount']:,.2f} TL" if log.get("refund_amount") else "-"),
                    _right(f"{log['cost_amount']:,.2f} TL"   if log.get("cost_amount")   else "-"),
                ]
                for col, cell_item in enumerate(cells):
                    cell_item.setBackground(QBrush(COLOR_LOG_BG))
                    cell_item.setForeground(QBrush(COLOR_LOG_FG))
                    self.logs_table.setItem(row, col, cell_item)
        except APIError:
            pass

    def _get_selected_sale_info(self):
        selected = self.sales_table.selectedItems()
        if not selected:
            return None, None
        row     = selected[0].row()
        sale_id = self.sales_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item_id = self.sales_table.item(row, 4).data(Qt.ItemDataRole.UserRole)
        return sale_id, item_id

    def _get_selected_purchase_id(self):
        selected = self.purchases_table.selectedItems()
        if not selected:
            return None
        return self.purchases_table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _cancel_sale_item(self):
        sale_id, item_id = self._get_selected_sale_info()
        if not item_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir satis kalemi secin.")
            return
        reply = QMessageBox.question(
            self, "Kalem Iptali",
            "Bu kalem iptal edilecek, stok iade edilecek. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            result = api.cancel_sale_item(sale_id, item_id)
            iade = result.get("refund_amount", 0)
            QMessageBox.information(self, "Basarili", f"Kalem iptal edildi. Iade: {iade:,.2f} TL")
            self.refresh_data()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_full_sale(self):
        sale_id, _ = self._get_selected_sale_info()
        if not sale_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir satis secin.")
            return
        reply = QMessageBox.question(
            self, "Tum Satisi Iptal Et",
            f"SAT-{sale_id} tamamen iptal edilecek. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            result = api.cancel_full_sale(sale_id)
            iade = result.get("refund_amount", 0)
            QMessageBox.information(self, "Basarili", f"Satis iptal edildi. Iade: {iade:,.2f} TL")
            self.refresh_data()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _cancel_purchase(self):
        purchase_id = self._get_selected_purchase_id()
        if not purchase_id:
            QMessageBox.information(self, "Bilgi", "Iptal icin bir alim secin.")
            return
        reply = QMessageBox.question(
            self, "Alim Iptali",
            f"ALIM-{purchase_id} iptal edilecek. Stok ve borc geri alinacak. Onayliyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            api.cancel_purchase(purchase_id)
            QMessageBox.information(self, "Basarili", "Alim iptal edildi.")
            self.refresh_data()
            if hasattr(self, "main_window"):
                self.main_window.update_cash_balance()
        except APIError as e:
            QMessageBox.critical(self, "Hata", str(e))