from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from ..core import api_client


class _W(QThread):
    bitti = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.bitti.emit(self._fn())
        except Exception:
            self.bitti.emit(None)


class AlimDialog(QDialog):
    """Tedarikçiden mal alımı — çok kalemli."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Alım")
        self.setMinimumSize(680, 520)
        self._kalemler: list[dict] = []
        self._tedarikciler: list[dict] = []
        self._build_ui()
        self._tedicarikcileri_yukle()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        baslik = QLabel("Yeni Alım Kaydı")
        baslik.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        root.addWidget(baslik)

        # ── Tedarikçi ────────────────────────────────────
        ted_row = QHBoxLayout()
        ted_row.addWidget(QLabel("Tedarikçi *:"))
        self._ted_combo = QComboBox()
        self._ted_combo.setMinimumWidth(260)
        ted_row.addWidget(self._ted_combo)
        ted_row.addStretch()
        root.addLayout(ted_row)

        # ── Ürün Arama ───────────────────────────────────
        urun_frame = QFrame()
        urun_frame.setFrameShape(QFrame.Shape.StyledPanel)
        uf = QFormLayout(urun_frame)

        ara_row = QHBoxLayout()
        self._urun_ara = QLineEdit()
        self._urun_ara.setPlaceholderText("Barkod veya ürün adı…")
        self._urun_ara_btn = QPushButton("Ara")
        self._urun_ara_btn.clicked.connect(self._urun_ara_et)
        self._urun_ara.returnPressed.connect(self._urun_ara_et)
        ara_row.addWidget(self._urun_ara)
        ara_row.addWidget(self._urun_ara_btn)
        uf.addRow("Ürün *", ara_row)

        self._urun_combo = QComboBox()
        self._urun_combo.setMinimumWidth(300)
        uf.addRow("Bulunanlar", self._urun_combo)

        self._miktar = QSpinBox()
        self._miktar.setRange(1, 9999)
        self._miktar.setValue(1)
        uf.addRow("Miktar", self._miktar)

        self._birim_fiyat = QDoubleSpinBox()
        self._birim_fiyat.setRange(0, 999_999)
        self._birim_fiyat.setDecimals(2)
        self._birim_fiyat.setSuffix(" ₺")
        uf.addRow("Birim Alış Fiyatı *", self._birim_fiyat)

        ekle_btn = QPushButton("+ Kaleme Ekle")
        ekle_btn.clicked.connect(self._kalem_ekle)
        uf.addRow("", ekle_btn)

        root.addWidget(urun_frame)

        # ── Kalem Tablosu ─────────────────────────────────
        self._tablo = QTableWidget(0, 4)
        self._tablo.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim ₺", "Toplam ₺"])
        self._tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tablo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self._tablo)

        self._ozet_label = QLabel("Toplam: 0,00 ₺")
        self._ozet_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        root.addWidget(self._ozet_label)

        self._hata = QLabel("")
        self._hata.setStyleSheet("color: #c0392b;")
        root.addWidget(self._hata)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        sil_btn = QPushButton("Seçili Kalemi Sil")
        sil_btn.clicked.connect(self._kalem_sil)
        btn_row.addWidget(sil_btn)
        iptal = QPushButton("İptal")
        iptal.clicked.connect(self.reject)
        btn_row.addWidget(iptal)
        self._kaydet_btn = QPushButton("Alımı Kaydet")
        self._kaydet_btn.setDefault(True)
        self._kaydet_btn.clicked.connect(self._kaydet)
        btn_row.addWidget(self._kaydet_btn)
        root.addLayout(btn_row)

    def _tedicarikcileri_yukle(self):
        w = _W(lambda: api_client.get("/api/tedarikciler"))
        w.bitti.connect(self._tedarikciler_yuklendi)
        w.start()
        self._tw = w

    def _tedarikciler_yuklendi(self, data):
        self._tedarikciler = data or []
        self._ted_combo.clear()
        self._ted_combo.addItem("— Seçin —", None)
        for t in self._tedarikciler:
            self._ted_combo.addItem(f"{t['ad']}  (Borç: {t['guncel_borc']:.2f} ₺)", t["id"])

    def _urun_ara_et(self):
        q = self._urun_ara.text().strip()
        if not q:
            return
        self._urun_ara_btn.setEnabled(False)
        w = _W(lambda: api_client.get("/api/urunler", params={"arama": q, "limit": 30}))
        w.bitti.connect(self._urun_sonuclari)
        w.start()
        self._uw = w

    def _urun_sonuclari(self, data):
        self._urun_ara_btn.setEnabled(True)
        self._urun_combo.clear()
        if not data:
            self._hata.setText("Ürün bulunamadı.")
            return
        self._hata.setText("")
        for u in data:
            etiket = f"{u['ad']}  {u.get('ebat', '')}  (Stok: {u['stok']})"
            self._urun_combo.addItem(etiket, u)
        self._urun_combo.currentIndexChanged.connect(self._urun_secildi)
        self._urun_secildi(0)

    def _urun_secildi(self, idx: int):
        u = self._urun_combo.currentData()
        if u and u.get("maliyet_fiyati"):
            self._birim_fiyat.setValue(float(u["maliyet_fiyati"]))

    def _kalem_ekle(self):
        urun = self._urun_combo.currentData()
        if not urun:
            self._hata.setText("Önce ürün arayın ve seçin.")
            return
        miktar = self._miktar.value()
        birim = self._birim_fiyat.value()
        kalem = {
            "urun_id": urun["id"],
            "urun_adi_anlik": urun["ad"],
            "miktar": miktar,
            "birim_fiyat": birim,
        }
        self._kalemler.append(kalem)
        r = self._tablo.rowCount()
        self._tablo.insertRow(r)
        self._tablo.setItem(r, 0, QTableWidgetItem(urun["ad"]))
        self._tablo.setItem(r, 1, QTableWidgetItem(str(miktar)))
        self._tablo.setItem(r, 2, QTableWidgetItem(f"{birim:.2f}"))
        self._tablo.setItem(r, 3, QTableWidgetItem(f"{miktar * birim:.2f}"))
        self._ozet_guncelle()

    def _kalem_sil(self):
        row = self._tablo.currentRow()
        if row < 0:
            return
        self._tablo.removeRow(row)
        self._kalemler.pop(row)
        self._ozet_guncelle()

    def _ozet_guncelle(self):
        toplam = sum(k["miktar"] * k["birim_fiyat"] for k in self._kalemler)
        from ..core.utils import tr_para
        self._ozet_label.setText(f"Toplam: {tr_para(toplam)} ₺")

    def _kaydet(self):
        self._hata.setText("")
        if not self._ted_combo.currentData():
            self._hata.setText("Tedarikçi seçmelisiniz.")
            return
        if not self._kalemler:
            self._hata.setText("En az bir kalem ekleyin.")
            return

        self._kaydet_btn.setEnabled(False)
        self._kaydet_btn.setText("Kaydediliyor…")
        payload = {
            "tedarikci_id": self._ted_combo.currentData(),
            "kalemler": self._kalemler,
        }
        w = _W(lambda: api_client.post("/api/alimlar", json=payload))
        w.bitti.connect(self._on_bitti)
        w.start()
        self._kw = w

    def _on_bitti(self, sonuc):
        if sonuc is None:
            self._hata.setText("Alım kaydedilemedi.")
            self._kaydet_btn.setEnabled(True)
            self._kaydet_btn.setText("Alımı Kaydet")
        else:
            self.accept()
