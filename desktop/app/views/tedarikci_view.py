from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout
from ..core import api_client
from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.tedarikci_dialog import TedarikciDialog, TedarikciOdemeDialog


class TedarikciView(BaseListView):
    BASLIK = "Tedarikçiler"
    API_PATH = "/api/tedarikciler"
    SUTUNLAR = ["Tedarikçi Adı", "İletişim", "Güncel Borç (₺)"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            row.get("ad", ""),
            row.get("iletisim_bilgisi", "") or "",
            tr_para(row.get('guncel_borc', 0)),
        ]

    def _build_ui(self):
        super()._build_ui()
        # Ödeme butonu ekle
        odeme_btn = QPushButton("Ödeme Yap")
        odeme_btn.clicked.connect(self._odeme_yap)
        # Araç çubuğuna ekle (layout'un ilk çocuğu HBoxLayout)
        ust_lay = self.layout().itemAt(0).layout()
        ust_lay.insertWidget(ust_lay.count() - 1, odeme_btn)

    def _ekle_dialogu(self):
        dlg = TedarikciDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        dlg = TedarikciDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()

    def _odeme_yap(self):
        row = self._secili_satir()
        if not row:
            QMessageBox.information(self, "Bilgi", "Önce bir tedarikçi seçin.")
            return
        dlg = TedarikciOdemeDialog(self, tedarikci_id=row["id"], tedarikci_adi=row["ad"])
        if dlg.exec():
            self.yukle()
