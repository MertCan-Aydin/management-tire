from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.urun_dialog import UrunDialog


class UrunView(BaseListView):
    BASLIK = "Ürünler"
    API_PATH = "/api/urunler"
    SIL_IPUCU = "Silmek için Delete"
    SUTUNLAR = ["Barkod/QR", "Ürün Adı", "Ebat", "Tip", "Marka", "Model", "Mevsim", "Satış ₺", "Maliyet ₺", "Stok"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            row.get("barkod_qr", "") or "",
            row.get("ad", ""),
            row.get("ebat", "") or "",
            row.get("tip_adi", ""),
            row.get("marka_adi", ""),
            row.get("model_adi", ""),
            row.get("mevsim", "") or "",
            tr_para(row.get('satis_fiyati', 0)),
            tr_para(row.get('maliyet_fiyati', 0) or 0),
            str(row.get("stok", 0)),
        ]

    def _ekle_dialogu(self):
        dlg = UrunDialog(self)
        if dlg.exec():
            self._status_mesaj("Yeni ürün eklendi ✓", 2500)
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = UrunDialog(self, duzenleme=row)
        if dlg.exec():
            self._status_mesaj(f"'{row['ad']}' güncellendi ✓", 2500)
            self.yukle()

    def _sil(self, row: dict):
        self._onayla_ve_sil(
            f"'{row['ad']}' ürününü silmek istiyor musunuz?",
            f"/api/urunler/{row['id']}", f"'{row['ad']}' silindi")
