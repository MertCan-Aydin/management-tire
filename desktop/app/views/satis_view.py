from PyQt6.QtWidgets import QMessageBox
from ..core import api_client
from ._base_view import BaseListView
from ..dialogs.satis_dialog import SatisDialog


class SatisView(BaseListView):
    BASLIK = "Satışlar"
    API_PATH = "/api/satislar"
    SUTUNLAR = ["Tarih", "Müşteri", "Plaka", "Toplam (₺)", "İndirim (₺)", "Kâr (₺)", "Ödeme", "Durum"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            str(row.get("tarih", ""))[:16],
            row.get("musteri_adi", ""),
            row.get("arac_plakasi", "") or "",
            f"{row.get('toplam_tutar', 0):,.2f}",
            f"{row.get('indirim', 0):,.2f}",
            f"{row.get('kar', 0):,.2f}",
            row.get("odeme_yontemi", ""),
            "İptal" if row.get("iptal_mi") else "Aktif",
        ]

    def _ekle_dialogu(self):
        dlg = SatisDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        # Satış detayı — çift tıkla satış kalemlerini göster
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
        from ..core import api_client
        try:
            detay = api_client.get(f"/api/satislar/{row['id']}")
        except Exception:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Satış #{row['id']} Detayı")
        dlg.setMinimumWidth(500)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"Müşteri: {row.get('musteri_adi', '')}  |  {row.get('arac_plakasi', '')}"))
        lay.addWidget(QLabel(f"Tarih: {str(row.get('tarih', ''))[:16]}  |  Ödeme: {row.get('odeme_yontemi', '')}"))
        lay.addWidget(QLabel(f"Toplam: {row.get('toplam_tutar', 0):.2f} ₺  |  İndirim: {row.get('indirim', 0):.2f} ₺  |  Kâr: {row.get('kar', 0):.2f} ₺"))
        tablo = QTableWidget(0, 4)
        tablo.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim ₺", "Toplam ₺"])
        tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for k in detay.get("kalemler", []):
            r = tablo.rowCount()
            tablo.insertRow(r)
            tablo.setItem(r, 0, QTableWidgetItem(k.get("urun_adi_anlik", "")))
            tablo.setItem(r, 1, QTableWidgetItem(str(k.get("miktar", 0))))
            tablo.setItem(r, 2, QTableWidgetItem(f"{k.get('birim_fiyat', 0):.2f}"))
            tablo.setItem(r, 3, QTableWidgetItem(f"{k.get('toplam_fiyat', 0):.2f}"))
        lay.addWidget(tablo)
        dlg.exec()
