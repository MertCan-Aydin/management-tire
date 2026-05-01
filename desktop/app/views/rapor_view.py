from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..core import api_client
from ..core.utils import tr_para


class _RaporWorker(QThread):
    veri_geldi = pyqtSignal(dict)
    hata = pyqtSignal(str)

    def __init__(self, baslangic: str, bitis: str):
        super().__init__()
        self._bas = baslangic
        self._bit = bitis

    def run(self):
        try:
            aralik = api_client.get("/api/raporlar/aralik", params={"baslangic": self._bas, "bitis": self._bit})
            kirilim = api_client.get("/api/raporlar/kirilim", params={"baslangic": self._bas, "bitis": self._bit})
            en_cok = api_client.get("/api/raporlar/en-cok-satan", params={"baslangic": self._bas, "bitis": self._bit, "limit": 10})
            self.veri_geldi.emit({"aralik": aralik, "kirilim": kirilim, "en_cok": en_cok})
        except Exception as e:
            self.hata.emit(str(e))


class RaporView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        baslik = QLabel("Raporlar")
        baslik.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(baslik)

        # Tarih seçimi
        tarih_row = QHBoxLayout()
        tarih_row.addWidget(QLabel("Başlangıç:"))
        self._bas_tarih = QDateEdit(QDate.currentDate().addDays(-30))
        self._bas_tarih.setCalendarPopup(True)
        self._bas_tarih.setDisplayFormat("yyyy-MM-dd")
        tarih_row.addWidget(self._bas_tarih)
        tarih_row.addWidget(QLabel("Bitiş:"))
        self._bit_tarih = QDateEdit(QDate.currentDate())
        self._bit_tarih.setCalendarPopup(True)
        self._bit_tarih.setDisplayFormat("yyyy-MM-dd")
        tarih_row.addWidget(self._bit_tarih)
        goster_btn = QPushButton("Göster")
        goster_btn.clicked.connect(self._yukle)
        tarih_row.addWidget(goster_btn)
        tarih_row.addStretch()
        layout.addLayout(tarih_row)

        # Özet kartlar
        ozet_row = QHBoxLayout()
        self._lbl_ciro = self._kart("Ciro (₺)", "—")
        self._lbl_kar = self._kart("Kâr (₺)", "—")
        self._lbl_satis = self._kart("Satış", "—")
        self._lbl_gider = self._kart("Gider (₺)", "—")
        for w in (self._lbl_ciro, self._lbl_kar, self._lbl_satis, self._lbl_gider):
            ozet_row.addWidget(w)
        layout.addLayout(ozet_row)

        # Tab: günlük kırılım + en çok satanlar
        self._tabs = QTabWidget()
        self._kirilim_tablo = self._tablo(["Gün", "Satış Adedi", "Ciro (₺)", "Kâr (₺)"])
        self._en_cok_tablo = self._tablo(["Ürün", "Adet", "Ciro (₺)", "Kâr (₺)"])
        self._tabs.addTab(self._kirilim_tablo, "Günlük Kırılım")
        self._tabs.addTab(self._en_cok_tablo, "En Çok Satanlar")
        layout.addWidget(self._tabs)

        self._yukle()

    def _kart(self, baslik: str, deger: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        lb = QLabel(baslik)
        lb.setFont(QFont("Segoe UI", 8))
        val = QLabel(deger)
        val.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        val.setObjectName("val")
        v.addWidget(lb)
        v.addWidget(val)
        return w

    def _tablo(self, sutunlar: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(sutunlar))
        t.setHorizontalHeaderLabels(sutunlar)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        return t

    def _yukle(self):
        self._worker = _RaporWorker(
            self._bas_tarih.date().toString("yyyy-MM-dd"),
            self._bit_tarih.date().toString("yyyy-MM-dd"),
        )
        self._worker.veri_geldi.connect(self._guncelle)
        self._worker.start()

    def _guncelle(self, data: dict):
        aralik = data.get("aralik") or {}
        kirilim = data.get("kirilim") or []
        en_cok = data.get("en_cok") or []

        def _fmt(v): return tr_para(float(v or 0))

        self._lbl_ciro.findChild(QLabel, "val").setText(_fmt(aralik.get("toplam_ciro", 0)))
        self._lbl_kar.findChild(QLabel, "val").setText(_fmt(aralik.get("toplam_kar", 0)))
        self._lbl_satis.findChild(QLabel, "val").setText(str(aralik.get("satis_adedi", 0)))
        self._lbl_gider.findChild(QLabel, "val").setText(_fmt(aralik.get("toplam_gider", 0)))

        self._kirilim_tablo.setRowCount(0)
        for row in kirilim:
            r = self._kirilim_tablo.rowCount()
            self._kirilim_tablo.insertRow(r)
            for c, v in enumerate([row.get("gun"), row.get("satis_adedi"), _fmt(row.get("ciro")), _fmt(row.get("kar"))]):
                self._kirilim_tablo.setItem(r, c, QTableWidgetItem(str(v)))

        self._en_cok_tablo.setRowCount(0)
        for row in en_cok:
            r = self._en_cok_tablo.rowCount()
            self._en_cok_tablo.insertRow(r)
            for c, v in enumerate([row.get("urun_adi_anlik"), row.get("toplam_adet"), _fmt(row.get("toplam_ciro")), _fmt(row.get("toplam_kar"))]):
                self._en_cok_tablo.setItem(r, c, QTableWidgetItem(str(v)))
