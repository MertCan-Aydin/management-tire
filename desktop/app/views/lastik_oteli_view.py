from datetime import date
from PyQt6.QtWidgets import (
    QMessageBox, QPushButton, QDialog, QVBoxLayout,
    QLabel, QDateEdit, QHBoxLayout, QCheckBox,
)
from PyQt6.QtCore import QDate, Qt

from ..core import api_client
from ._base_view import BaseListView
from ..dialogs.lastik_oteli_dialog import LastikOteliDialog


class LastikOteliView(BaseListView):
    BASLIK = "Lastik Oteli"
    API_PATH = "/api/lastik-oteli"
    SUTUNLAR = ["Raf", "Müşteri", "Plaka", "Lastik Bilgisi", "Adet", "Sezon", "Giriş", "Durum"]

    def _satira_donustur(self, row: dict) -> list:
        durum = "Depoda" if row.get("aktif_mi") else "Teslim Edildi"
        giris = str(row.get("giris_tarihi", ""))[:10]
        return [
            row.get("raf_kodu", ""),
            row.get("musteri_adi", ""),
            row.get("arac_plakasi", "") or "",
            row.get("lastik_bilgisi", "") or "",
            str(row.get("lastik_adedi", "")),
            row.get("sezon", ""),
            giris,
            durum,
        ]

    def _build_ui(self):
        super()._build_ui()
        toolbar = self.layout().itemAt(0).layout()

        # Sadece aktif filtresi
        self._sadece_aktif = QCheckBox("Sadece depodakiler")
        self._sadece_aktif.setChecked(True)
        self._sadece_aktif.stateChanged.connect(self.yukle)
        toolbar.insertWidget(2, self._sadece_aktif)

        # Teslim Et butonu
        self._teslim_btn = QPushButton("✓ Teslim Et")
        self._teslim_btn.setObjectName("flat")
        self._teslim_btn.setFixedHeight(36)
        self._teslim_btn.clicked.connect(self._teslim_et)
        toolbar.insertWidget(toolbar.count() - 1, self._teslim_btn)

    def yukle(self):
        from ..core import api_client

        self._bilgi_lbl.setText("Yükleniyor…")
        sadece_aktif = self._sadece_aktif.isChecked() if hasattr(self, '_sadece_aktif') else True

        from ._base_view import _ListeWorker

        def fetch():
            return api_client.get(self.API_PATH, params={
                "sadece_aktif": sadece_aktif,
                "limit": 500,
            })

        self._worker = _ListeWorker(fetch)
        self._worker.veri_geldi.connect(self._veri_yukle)
        self._worker.hata.connect(self._yukle_hatasi)
        self._worker.finished.connect(lambda: self._ekle_btn.setEnabled(True))
        self._worker.start()
        self._ekle_btn.setEnabled(False)

    def _ekle_dialogu(self):
        dlg = LastikOteliDialog(self)
        if dlg.exec():
            self.yukle()

    def _duzenle_dialogu(self, row: dict):
        if not row.get("aktif_mi"):
            return  # Teslim edilmişlerde düzenleme yok
        dlg = LastikOteliDialog(self, duzenleme=row)
        if dlg.exec():
            self.yukle()

    def _teslim_et(self):
        row = self._secili_satir()
        if not row:
            QMessageBox.information(self, "Bilgi", "Önce bir kayıt seçin.")
            return
        if not row.get("aktif_mi"):
            QMessageBox.information(self, "Bilgi", "Bu kayıt zaten teslim edilmiş.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Teslim Et")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            f"<b>{row['raf_kodu']}</b>  —  {row['musteri_adi']}<br>"
            f"{row.get('lastik_bilgisi', '')}"))
        lay.addWidget(QLabel("Çıkış Tarihi:"))
        tarih = QDateEdit(QDate.currentDate())
        tarih.setCalendarPopup(True)
        tarih.setDisplayFormat("dd.MM.yyyy")
        lay.addWidget(tarih)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        iptal = QPushButton("İptal")
        iptal.setObjectName("flat")
        iptal.clicked.connect(dlg.reject)
        btn_row.addWidget(iptal)
        onayla = QPushButton("Teslim Et")
        onayla.clicked.connect(dlg.accept)
        btn_row.addWidget(onayla)
        lay.addLayout(btn_row)

        if dlg.exec():
            gd = tarih.date()
            cikis = f"{gd.year()}-{gd.month():02d}-{gd.day():02d}"
            try:
                api_client.put(
                    f"/api/lastik-oteli/{row['id']}/teslim",
                    json={"cikis_tarihi": cikis},
                )
                self.yukle()
            except Exception as e:
                QMessageBox.warning(self, "Hata", str(e))

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Delete:
            row = self._secili_satir()
            if row and QMessageBox.question(
                self, "Sil",
                f"'{row['raf_kodu']} — {row['musteri_adi']}' kaydını silmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.Yes:
                try:
                    api_client.delete(f"/api/lastik-oteli/{row['id']}")
                    self.yukle()
                except Exception as e:
                    QMessageBox.warning(self, "Hata", str(e))
        super().keyPressEvent(event)
