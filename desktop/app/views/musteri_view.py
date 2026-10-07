from typing import Optional
from PyQt6.QtWidgets import QMessageBox
from ..core import api_client
from ._base_view import BaseListView
from ..dialogs.musteri_dialog import MusteriDialog


class MusteriView(BaseListView):
    BASLIK = "Müşteriler"
    API_PATH = "/api/musteriler"
    SIL_IPUCU = "Silmek için Delete"
    SUTUNLAR = ["Ad Soyad", "Telefon", "Araç Markası", "Plaka", "Notlar"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            row.get("ad_soyad", ""),
            row.get("telefon", ""),
            row.get("arac_markasi", "") or "",
            row.get("arac_plakasi", "") or "",
            row.get("notlar", "") or "",
        ]

    def _ekle_dialogu(self):
        dlg = MusteriDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = MusteriDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()

    def _sil(self, row: dict):
        self._onayla_ve_sil(
            f"'{row['ad_soyad']}' müşterisini silmek istiyor musunuz?",
            f"/api/musteriler/{row['id']}", "Müşteri silindi")
