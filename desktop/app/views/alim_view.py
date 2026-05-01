from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from ..core import api_client
from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.alim_dialog import AlimDialog


class AlimView(BaseListView):
    BASLIK = "Alımlar"
    API_PATH = "/api/alimlar"
    SUTUNLAR = ["Tarih", "Tedarikçi", "Toplam (₺)", "Durum"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            str(row.get("tarih", ""))[:16],
            row.get("tedarikci_adi", ""),
            tr_para(row.get('toplam_tutar', 0)),
            "İptal" if row.get("iptal_mi") else "Aktif",
        ]

    def _ekle_dialogu(self):
        dlg = AlimDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        try:
            detay = api_client.get(f"/api/alimlar/{row['id']}")
        except Exception:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Alım #{row['id']} Detayı")
        dlg.setMinimumWidth(500)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"Tedarikçi: {row.get('tedarikci_adi', '')}"))
        lay.addWidget(QLabel(f"Tarih: {str(row.get('tarih', ''))[:16]}  |  Toplam: {tr_para(row.get('toplam_tutar', 0))} ₺"))
        tablo = QTableWidget(0, 4)
        tablo.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim ₺", "Toplam ₺"])
        tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for k in detay.get("kalemler", []):
            r = tablo.rowCount()
            tablo.insertRow(r)
            tablo.setItem(r, 0, QTableWidgetItem(k.get("urun_adi_anlik", "")))
            tablo.setItem(r, 1, QTableWidgetItem(str(k.get("miktar", 0))))
            tablo.setItem(r, 2, QTableWidgetItem(tr_para(k.get('birim_fiyat', 0))))
            tablo.setItem(r, 3, QTableWidgetItem(tr_para(k.get('toplam_fiyat', 0))))
        lay.addWidget(tablo)
        dlg.exec()
