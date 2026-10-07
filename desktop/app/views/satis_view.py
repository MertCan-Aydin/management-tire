from PyQt6.QtWidgets import QMessageBox
from ..core import api_client
from ..core.utils import tr_para
from ._base_view import BaseListView
from ..dialogs.satis_dialog import SatisDialog


class SatisView(BaseListView):
    BASLIK = "Satışlar"
    API_PATH = "/api/satislar"
    SIL_IPUCU = "İptal için Delete"
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
        iptal_istendi = False
        if not row.get("iptal_mi"):
            from PyQt6.QtWidgets import QPushButton
            btn = QPushButton("Satışı İptal Et")
            btn.setObjectName("flat")
            btn.setStyleSheet("color:#dc2626;")

            def _iptal_tikla():
                nonlocal iptal_istendi
                iptal_istendi = True
                dlg.accept()

            btn.clicked.connect(_iptal_tikla)
            lay.addWidget(btn)
        dlg.exec()
        if iptal_istendi:
            self._sil(row)

    def _sil(self, row: dict):
        if row.get("iptal_mi"):
            QMessageBox.information(self, "Bilgi", "Bu satış zaten iptal edilmiş.")
            return
        kutu = QMessageBox(self)
        kutu.setIcon(QMessageBox.Icon.Warning)
        kutu.setWindowTitle("Satışı İptal Et")
        kutu.setText("Satış ciro ve kâr hesaplarından çıkarılacak. Bu işlem geri alınamaz.")
        kutu.setInformativeText(
            "Ürünler kullanılmadıysa stoğa geri ekleyin. "
            "Takıldıysa veya satılamayacak durumdaysa eklemeyin.")
        stoga_ekle = kutu.addButton("İptal Et, Stoğa Geri Ekle", QMessageBox.ButtonRole.AcceptRole)
        stoga_ekleme = kutu.addButton("İptal Et, Stoğa Ekleme", QMessageBox.ButtonRole.DestructiveRole)
        kutu.addButton("Vazgeç", QMessageBox.ButtonRole.RejectRole)
        kutu.setDefaultButton(stoga_ekle)
        kutu.exec()
        secilen = kutu.clickedButton()
        if secilen not in (stoga_ekle, stoga_ekleme):
            return
        try:
            api_client.delete(f"/api/satislar/{row['id']}",
                              params={"stoga_ekle": "true" if secilen is stoga_ekle else "false"})
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            return
        self._status_mesaj("Satış iptal edildi", 2500)
        self.yukle()
