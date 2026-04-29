from PyQt6.QtWidgets import (
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QCheckBox, QTextEdit, QLabel,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from ..core import api_client
from ._base_dialog import BaseFormDialog


class _KomboYukleyici(QThread):
    bitti = pyqtSignal(list)

    def __init__(self, path: str, params: dict = None):
        super().__init__()
        self._path = path
        self._params = params

    def run(self):
        try:
            self.bitti.emit(api_client.get(self._path, params=self._params) or [])
        except Exception:
            self.bitti.emit([])


class UrunDialog(BaseFormDialog):
    BASLIK = "Ürün"

    def _form_alanlari(self):
        # Barkod
        barkod_row = QLineEdit()
        self._barkod = barkod_row
        self._barkod.setPlaceholderText("Opsiyonel — QR koddan veya manuel")
        self.form_layout.addRow("Barkod / QR", self._barkod)

        # Ürün Adı
        self._ad = QLineEdit()
        self._ad.setPlaceholderText("Zorunlu")
        self.form_layout.addRow("Ürün Adı *", self._ad)

        # Ebat
        self._ebat = QLineEdit()
        self._ebat.setPlaceholderText("205/55 R16")
        self.form_layout.addRow("Ebat", self._ebat)

        # Tip → Marka → Model zinciri
        self._tip_combo = QComboBox()
        self._tip_combo.setPlaceholderText("Önce tip seçin…")
        self._tip_combo.currentIndexChanged.connect(self._tip_degisti)
        self.form_layout.addRow("Ürün Tipi *", self._tip_combo)

        self._marka_combo = QComboBox()
        self._marka_combo.setPlaceholderText("Tip seçildikten sonra…")
        self._marka_combo.setEnabled(False)
        self._marka_combo.currentIndexChanged.connect(self._marka_degisti)
        self.form_layout.addRow("Marka *", self._marka_combo)

        self._model_combo = QComboBox()
        self._model_combo.setPlaceholderText("Marka seçildikten sonra…")
        self._model_combo.setEnabled(False)
        self.form_layout.addRow("Model *", self._model_combo)

        # Fiyatlar
        self._satis_fiyati = QDoubleSpinBox()
        self._satis_fiyati.setRange(0.01, 999_999)
        self._satis_fiyati.setDecimals(2)
        self._satis_fiyati.setSuffix(" ₺")
        self.form_layout.addRow("Satış Fiyatı *", self._satis_fiyati)

        self._maliyet_fiyati = QDoubleSpinBox()
        self._maliyet_fiyati.setRange(0, 999_999)
        self._maliyet_fiyati.setDecimals(2)
        self._maliyet_fiyati.setSuffix(" ₺")
        self.form_layout.addRow("Maliyet Fiyatı", self._maliyet_fiyati)

        # Stok
        self._stok = QSpinBox()
        self._stok.setRange(0, 999_999)
        self.form_layout.addRow("Stok", self._stok)

        # Fiziksel ürün mü?
        self._fiziksel = QCheckBox("Fiziksel ürün (stok düşer)")
        self._fiziksel.setChecked(True)
        self.form_layout.addRow("", self._fiziksel)

        # Açıklama
        self._aciklama = QTextEdit()
        self._aciklama.setMaximumHeight(60)
        self.form_layout.addRow("Açıklama", self._aciklama)

        # Tipleri yükle
        self._tipler: list[dict] = []
        self._markalar: list[dict] = []
        self._modeller: list[dict] = []
        self._tipleri_yukle()

    def _tipleri_yukle(self):
        w = _KomboYukleyici("/api/urunler/tipler")
        w.bitti.connect(self._tipler_yuklendi)
        w.start()
        self._w_tip = w

    def _tipler_yuklendi(self, data: list):
        self._tipler = data
        self._tip_combo.clear()
        self._tip_combo.addItem("— Seçin —", None)
        for t in data:
            self._tip_combo.addItem(t["ad"], t["id"])
        # Düzenleme modunda seçili değeri geri yükle
        if self._duzenleme and self._duzenleme.get("urun_tipi_id"):
            self._set_combo_by_id(self._tip_combo, self._duzenleme["urun_tipi_id"])

    def _tip_degisti(self, idx: int):
        tip_id = self._tip_combo.currentData()
        self._marka_combo.clear()
        self._model_combo.clear()
        self._marka_combo.setEnabled(False)
        self._model_combo.setEnabled(False)
        if not tip_id:
            return
        w = _KomboYukleyici("/api/urunler/markalar", {"tip_id": tip_id})
        w.bitti.connect(self._markalar_yuklendi)
        w.start()
        self._w_marka = w

    def _markalar_yuklendi(self, data: list):
        self._markalar = data
        self._marka_combo.clear()
        self._marka_combo.addItem("— Seçin —", None)
        for m in data:
            self._marka_combo.addItem(m["ad"], m["id"])
        self._marka_combo.setEnabled(True)
        if self._duzenleme and self._duzenleme.get("marka_id"):
            self._set_combo_by_id(self._marka_combo, self._duzenleme["marka_id"])

    def _marka_degisti(self, idx: int):
        marka_id = self._marka_combo.currentData()
        self._model_combo.clear()
        self._model_combo.setEnabled(False)
        if not marka_id:
            return
        w = _KomboYukleyici("/api/urunler/modeller", {"marka_id": marka_id})
        w.bitti.connect(self._modeller_yuklendi)
        w.start()
        self._w_model = w

    def _modeller_yuklendi(self, data: list):
        self._modeller = data
        self._model_combo.clear()
        self._model_combo.addItem("— Seçin —", None)
        for m in data:
            etiket = m["ad"] + (f" ({m['mevsim']})" if m.get("mevsim") else "")
            self._model_combo.addItem(etiket, m["id"])
        self._model_combo.setEnabled(True)
        if self._duzenleme and self._duzenleme.get("marka_modeli_id"):
            self._set_combo_by_id(self._model_combo, self._duzenleme["marka_modeli_id"])

    def _set_combo_by_id(self, combo: QComboBox, target_id: int):
        for i in range(combo.count()):
            if combo.itemData(i) == target_id:
                combo.setCurrentIndex(i)
                return

    def _form_doldur(self, data: dict):
        self._barkod.setText(data.get("barkod_qr", "") or "")
        self._ad.setText(data.get("ad", ""))
        self._ebat.setText(data.get("ebat", "") or "")
        self._satis_fiyati.setValue(float(data.get("satis_fiyati", 0)))
        self._maliyet_fiyati.setValue(float(data.get("maliyet_fiyati", 0) or 0))
        self._stok.setValue(int(data.get("stok", 0)))
        self._fiziksel.setChecked(bool(data.get("fiziksel_urun_mu", True)))
        self._aciklama.setPlainText(data.get("aciklama", "") or "")

    def _dogrula(self) -> bool:
        if not self._ad.text().strip():
            self._hata_label.setText("Ürün adı zorunludur.")
            return False
        if not self._tip_combo.currentData():
            self._hata_label.setText("Ürün tipi seçmelisiniz.")
            return False
        if not self._marka_combo.currentData():
            self._hata_label.setText("Marka seçmelisiniz.")
            return False
        if not self._model_combo.currentData():
            self._hata_label.setText("Model seçmelisiniz.")
            return False
        if self._satis_fiyati.value() <= 0:
            self._hata_label.setText("Satış fiyatı 0'dan büyük olmalıdır.")
            return False
        return True

    def _kaydet_fn(self):
        payload = {
            "barkod_qr": self._barkod.text().strip() or None,
            "ad": self._ad.text().strip(),
            "ebat": self._ebat.text().strip() or None,
            "aciklama": self._aciklama.toPlainText().strip() or None,
            "satis_fiyati": self._satis_fiyati.value(),
            "maliyet_fiyati": self._maliyet_fiyati.value() or None,
            "stok": self._stok.value(),
            "fiziksel_urun_mu": self._fiziksel.isChecked(),
            "resim_yolu": None,
            "urun_tipi_id": self._tip_combo.currentData(),
            "marka_id": self._marka_combo.currentData(),
            "marka_modeli_id": self._model_combo.currentData(),
        }
        if self._duzenleme:
            uid = self._duzenleme["id"]
            payload["silindi_mi"] = False
            return lambda: api_client.put(f"/api/urunler/{uid}", json=payload)
        return lambda: api_client.post("/api/urunler", json=payload)
