from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout
from ..core import api_client
from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.tedarikci_dialog import TedarikciDialog, TedarikciOdemeDialog


class TedarikciView(BaseListView):
    BASLIK = "Tedarikçiler"
    API_PATH = "/api/tedarikciler"
    SIL_IPUCU = "Silmek için Delete"
    SUTUNLAR = ["Tedarikçi Adı", "İletişim", "Güncel Borç (₺)"]

    def _satira_donustur(self, row: dict) -> list:
        return [
            row.get("ad", ""),
            row.get("iletisim_bilgisi", "") or "",
            tr_para(row.get('guncel_borc', 0)),
        ]

    def _build_ui(self):
        super()._build_ui()
        # Ödeme butonu — diğer butonlarla aynı yükseklik
        odeme_btn = QPushButton("Ödeme Yap")
        odeme_btn.setObjectName("flat")
        odeme_btn.setFixedHeight(36)
        odeme_btn.clicked.connect(self._odeme_yap)
        # Araç çubuğuna ekle: + Yeni butonundan hemen önce
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

    def _sil(self, row: dict):
        self._onayla_ve_sil(
            f"'{row['ad']}' tedarikçisini silmek istiyor musunuz?",
            f"/api/tedarikciler/{row['id']}", "Tedarikçi silindi")
