from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from ..core import api_client


class _AraWorker(QThread):
    bitti = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.bitti.emit(self._fn())
        except Exception:
            self.bitti.emit(None)


class SatisDialog(QDialog):
    """
    Satış diyalogu — kalem bazlı.
    Akış: müşteri seç → ürün barkod/adla ara → kalem ekle → kaydet.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Satış")
        self.setMinimumSize(720, 580)
        self._kalemler: list[dict] = []
        self._secili_musteri: dict | None = None
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        baslik = QLabel("Yeni Satış")
        baslik.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        root.addWidget(baslik)

        # ── Müşteri Seçimi ───────────────────────────────
        musteri_frame = QFrame()
        musteri_frame.setFrameShape(QFrame.Shape.StyledPanel)
        mf_lay = QHBoxLayout(musteri_frame)

        self._musteri_ara = QLineEdit()
        self._musteri_ara.setPlaceholderText("Telefon veya plaka ile ara…")
        self._musteri_ara.setMinimumWidth(220)
        self._musteri_ara_btn = QPushButton("Ara")
        self._musteri_ara_btn.clicked.connect(self._musteri_ara_et)
        self._musteri_ara.returnPressed.connect(self._musteri_ara_et)

        self._musteri_combo = QComboBox()
        self._musteri_combo.setMinimumWidth(240)
        self._musteri_combo.currentIndexChanged.connect(self._musteri_secildi)

        mf_lay.addWidget(QLabel("Müşteri:"))
        mf_lay.addWidget(self._musteri_ara)
        mf_lay.addWidget(self._musteri_ara_btn)
        mf_lay.addWidget(self._musteri_combo)
        mf_lay.addStretch()
        root.addWidget(musteri_frame)

        self._musteri_bilgi = QLabel("Müşteri seçilmedi")
        self._musteri_bilgi.setStyleSheet("color: #7f8c8d; font-style: italic;")
        root.addWidget(self._musteri_bilgi)

        # ── Ürün Arama / Kalem Ekleme ───────────────────
        urun_frame = QFrame()
        urun_frame.setFrameShape(QFrame.Shape.StyledPanel)
        uf_lay = QFormLayout(urun_frame)

        urun_ara_row = QHBoxLayout()
        self._urun_ara = QLineEdit()
        self._urun_ara.setPlaceholderText("Barkod veya ürün adı…")
        self._urun_ara_btn = QPushButton("Ara")
        self._urun_ara_btn.clicked.connect(self._urun_ara_et)
        self._urun_ara.returnPressed.connect(self._urun_ara_et)
        urun_ara_row.addWidget(self._urun_ara)
        urun_ara_row.addWidget(self._urun_ara_btn)
        uf_lay.addRow("Ürün *", urun_ara_row)

        self._urun_combo = QComboBox()
        self._urun_combo.setMinimumWidth(300)
        uf_lay.addRow("Bulunanlar", self._urun_combo)

        self._birim_fiyat = QDoubleSpinBox()
        self._birim_fiyat.setRange(0.01, 999_999)
        self._birim_fiyat.setDecimals(2)
        self._birim_fiyat.setSuffix(" ₺")
        uf_lay.addRow("Birim Fiyat *", self._birim_fiyat)

        self._miktar = QSpinBox()
        self._miktar.setRange(1, 9999)
        self._miktar.setValue(1)
        uf_lay.addRow("Miktar", self._miktar)

        ekle_btn = QPushButton("+ Kaleme Ekle")
        ekle_btn.clicked.connect(self._kalem_ekle)
        uf_lay.addRow("", ekle_btn)

        root.addWidget(urun_frame)

        # ── Kalem Tablosu ────────────────────────────────
        self._tablo = QTableWidget(0, 5)
        self._tablo.setHorizontalHeaderLabels(["Ürün", "Miktar", "Birim ₺", "Maliyet ₺", "Toplam ₺"])
        self._tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tablo.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tablo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self._tablo)

        # ── Özet + Ödeme ─────────────────────────────────
        ozet_lay = QFormLayout()
        self._indirim = QDoubleSpinBox()
        self._indirim.setRange(0, 999_999)
        self._indirim.setDecimals(2)
        self._indirim.setSuffix(" ₺")
        self._indirim.valueChanged.connect(self._ozet_guncelle)
        ozet_lay.addRow("İndirim", self._indirim)

        self._odeme_combo = QComboBox()
        self._odeme_combo.addItems(["Nakit", "Kredi Kartı", "Havale"])
        ozet_lay.addRow("Ödeme Yöntemi *", self._odeme_combo)

        self._ozet_label = QLabel("Toplam: 0,00 ₺  |  Kâr: 0,00 ₺")
        self._ozet_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ozet_lay.addRow("Özet", self._ozet_label)
        root.addLayout(ozet_lay)

        # ── Hata + Butonlar ──────────────────────────────
        self._hata = QLabel("")
        self._hata.setStyleSheet("color: #c0392b;")
        root.addWidget(self._hata)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._kalem_sil_btn = QPushButton("Seçili Kalemi Sil")
        self._kalem_sil_btn.clicked.connect(self._kalem_sil)
        btn_row.addWidget(self._kalem_sil_btn)
        self._iptal_btn = QPushButton("İptal")
        self._iptal_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._iptal_btn)
        self._kaydet_btn = QPushButton("Satışı Kaydet")
        self._kaydet_btn.setDefault(True)
        self._kaydet_btn.clicked.connect(self._kaydet)
        btn_row.addWidget(self._kaydet_btn)
        root.addLayout(btn_row)

    # ── Müşteri ─────────────────────────────────────────

    def _musteri_ara_et(self):
        q = self._musteri_ara.text().strip()
        if not q:
            return
        self._musteri_ara_btn.setEnabled(False)
        w = _AraWorker(lambda: api_client.get("/api/musteriler", params={"arama": q, "limit": 20}))
        w.bitti.connect(self._musteri_sonuclari)
        w.start()
        self._worker = w

    def _musteri_sonuclari(self, data):
        self._musteri_ara_btn.setEnabled(True)
        self._musteri_combo.clear()
        if not data:
            self._musteri_bilgi.setText("Müşteri bulunamadı.")
            return
        for m in data:
            etiket = f"{m['ad_soyad']} — {m.get('arac_plakasi', '')} ({m['telefon']})"
            self._musteri_combo.addItem(etiket, m)

    def _musteri_secildi(self, idx: int):
        musteri = self._musteri_combo.currentData()
        if musteri:
            self._secili_musteri = musteri
            self._musteri_bilgi.setText(
                f"✓ {musteri['ad_soyad']}  |  {musteri.get('arac_plakasi', '—')}  |  {musteri['telefon']}"
            )
            self._musteri_bilgi.setStyleSheet("color: #27ae60; font-style: normal;")

    # ── Ürün Arama ──────────────────────────────────────

    def _urun_ara_et(self):
        q = self._urun_ara.text().strip()
        if not q:
            return
        self._urun_ara_btn.setEnabled(False)
        # Önce barkodla dene, sonra ada göre listele
        w = _AraWorker(lambda: api_client.get("/api/urunler", params={"arama": q, "sadece_stoklu": True, "limit": 30}))
        w.bitti.connect(self._urun_sonuclari)
        w.start()
        self._urun_w = w

    def _urun_sonuclari(self, data):
        self._urun_ara_btn.setEnabled(True)
        self._urun_combo.clear()
        if not data:
            self._hata.setText("Ürün bulunamadı.")
            return
        self._hata.setText("")
        for u in data:
            etiket = f"{u['ad']}  {u.get('ebat', '')}  (Stok: {u['stok']})  — {u['satis_fiyati']:.2f} ₺"
            self._urun_combo.addItem(etiket, u)
        # Satış fiyatını otomatik doldur
        self._urun_combo.currentIndexChanged.connect(self._urun_secildi)
        self._urun_secildi(0)

    def _urun_secildi(self, idx: int):
        u = self._urun_combo.currentData()
        if u:
            self._birim_fiyat.setValue(float(u.get("satis_fiyati", 0)))

    # ── Kalem İşlemleri ─────────────────────────────────

    def _kalem_ekle(self):
        urun = self._urun_combo.currentData()
        if not urun:
            self._hata.setText("Önce ürün arayın ve seçin.")
            return
        miktar = self._miktar.value()
        birim = self._birim_fiyat.value()
        maliyet = float(urun.get("maliyet_fiyati") or 0)

        kalem = {
            "urun_id": urun["id"],
            "urun_adi_anlik": urun["ad"],
            "miktar": miktar,
            "birim_fiyat": birim,
            "birim_maliyet": maliyet,
        }
        self._kalemler.append(kalem)
        r = self._tablo.rowCount()
        self._tablo.insertRow(r)
        self._tablo.setItem(r, 0, QTableWidgetItem(urun["ad"]))
        self._tablo.setItem(r, 1, QTableWidgetItem(str(miktar)))
        self._tablo.setItem(r, 2, QTableWidgetItem(f"{birim:.2f}"))
        self._tablo.setItem(r, 3, QTableWidgetItem(f"{maliyet:.2f}"))
        self._tablo.setItem(r, 4, QTableWidgetItem(f"{miktar * birim:.2f}"))
        self._ozet_guncelle()
        self._hata.setText("")

    def _kalem_sil(self):
        row = self._tablo.currentRow()
        if row < 0:
            return
        self._tablo.removeRow(row)
        self._kalemler.pop(row)
        self._ozet_guncelle()

    def _ozet_guncelle(self):
        toplam = sum(k["miktar"] * k["birim_fiyat"] for k in self._kalemler)
        maliyet = sum(k["miktar"] * k["birim_maliyet"] for k in self._kalemler)
        indirim = self._indirim.value()
        kar = toplam - indirim - maliyet
        self._ozet_label.setText(
            f"Toplam: {toplam:.2f} ₺  |  İndirim: {indirim:.2f} ₺  |  Kâr: {kar:.2f} ₺"
        )

    # ── Kaydet ──────────────────────────────────────────

    def _kaydet(self):
        self._hata.setText("")
        if not self._secili_musteri:
            self._hata.setText("Müşteri seçmelisiniz.")
            return
        if not self._kalemler:
            self._hata.setText("En az bir kalem ekleyin.")
            return

        self._kaydet_btn.setEnabled(False)
        self._kaydet_btn.setText("Kaydediliyor…")

        payload = {
            "musteri_id": self._secili_musteri["id"],
            "odeme_yontemi": self._odeme_combo.currentText(),
            "indirim": self._indirim.value(),
            "kalemler": self._kalemler,
        }

        w = _AraWorker(lambda: api_client.post("/api/satislar", json=payload))
        w.bitti.connect(self._on_kayit_bitti)
        w.start()
        self._kaydet_w = w

    def _on_kayit_bitti(self, sonuc):
        if sonuc is None:
            self._hata.setText("Satış kaydedilemedi. Bağlantıyı kontrol edin.")
            self._kaydet_btn.setEnabled(True)
            self._kaydet_btn.setText("Satışı Kaydet")
        else:
            self.accept()
