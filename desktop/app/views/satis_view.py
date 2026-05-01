from PyQt6.QtWidgets import QMessageBox
from ..core import api_client
from ..core.utils import tr_para
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
            tr_para(row.get('toplam_tutar', 0)),
            tr_para(row.get('indirim', 0)),
            tr_para(row.get('kar', 0)),
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
        from ..core.utils import tr_para as _p
        lay.addWidget(QLabel(f"Toplam: {_p(row.get('toplam_tutar', 0))} ₺  |  İndirim: {_p(row.get('indirim', 0))} ₺  |  Kâr: {_p(row.get('kar', 0))} ₺"))
        tablo = QTableWidget(0, 4)
        tablo.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim ₺", "Toplam ₺"])
        tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for k in detay.get("kalemler", []):
            r = tablo.rowCount()
            tablo.insertRow(r)
            tablo.setItem(r, 0, QTableWidgetItem(k.get("urun_adi_anlik", "")))
            tablo.setItem(r, 1, QTableWidgetItem(str(k.get("miktar", 0))))
            tablo.setItem(r, 2, QTableWidgetItem(_p(k.get('birim_fiyat', 0))))
            tablo.setItem(r, 3, QTableWidgetItem(_p(k.get('toplam_fiyat', 0))))
        lay.addWidget(tablo)
        dlg.exec()
