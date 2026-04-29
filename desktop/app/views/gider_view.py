from ..core import api_client
from ._base_view import BaseListView
from ..dialogs.gider_dialog import GiderDialog


class GiderView(BaseListView):
    BASLIK = "Giderler"
    API_PATH = "/api/giderler"
    SUTUNLAR = ["Tarih", "Açıklama", "Tutar (₺)"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            str(row.get("tarih", ""))[:16],
            row.get("aciklama", ""),
            f"{row.get('tutar', 0):,.2f}",
        ]

    def _ekle_dialogu(self):
        dlg = GiderDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = GiderDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()
