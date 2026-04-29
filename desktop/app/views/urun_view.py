from PyQt6.QtWidgets import QMessageBox
from ..core import api_client
from ._base_view import BaseListView
from ..dialogs.urun_dialog import UrunDialog


class UrunView(BaseListView):
    BASLIK = "Ürünler"
    API_PATH = "/api/urunler"
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
            f"{row.get('satis_fiyati', 0):,.2f}",
            f"{row.get('maliyet_fiyati', 0) or 0:,.2f}",
            str(row.get("stok", 0)),
        ]

    def _ekle_dialogu(self):
        dlg = UrunDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = UrunDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Delete:
            row = self._secili_satir()
            if row and QMessageBox.question(
                self, "Sil", f"'{row['ad']}' ürününü silmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                try:
                    api_client.delete(f"/api/urunler/{row['id']}")
                    self.yukle()
                except Exception as e:
                    QMessageBox.warning(self, "Hata", str(e))
        super().keyPressEvent(event)
