from ..core import api_client
from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.gider_dialog import GiderDialog


class GiderView(BaseListView):
    BASLIK = "Giderler"
    API_PATH = "/api/giderler"
    SIL_IPUCU = "Silmek için Delete"
    SUTUNLAR = ["Tarih", "Açıklama", "Tutar (₺)"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            str(row.get("tarih", ""))[:16],
            row.get("aciklama", ""),
            tr_para(row.get('tutar', 0)),
        ]

    def _ekle_dialogu(self):
        dlg = GiderDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = GiderDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()

    def _sil(self, row: dict):
        self._onayla_ve_sil(
            f"'{row['aciklama']}' giderini silmek istiyor musunuz?",
            f"/api/giderler/{row['id']}", "Gider silindi")
