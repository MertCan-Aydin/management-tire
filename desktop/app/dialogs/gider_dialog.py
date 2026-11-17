from PyQt6.QtWidgets import (
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
)
from ..core import api_client
from ._base_dialog import BaseFormDialog

_KATEGORILER = ["", "Kira", "Fatura", "Personel", "Yakıt", "Vergi", "Ürün Alımı", "Diğer"]


class GiderDialog(BaseFormDialog):
    BASLIK = "Gider"

    def _form_alanlari(self):
        self._kategori = QComboBox()
        self._kategori.addItems(_KATEGORILER)
        self._kategori.setPlaceholderText("Kategori (opsiyonel)")
        self._kategori.currentTextChanged.connect(self._kategori_degisti)
        self.form_layout.addRow("Kategori", self._kategori)

        self._aciklama = QLineEdit()
        self._aciklama.setPlaceholderText("Kira, fatura, yakıt…")
        self.form_layout.addRow("Açıklama *", self._aciklama)

        self._tutar = QDoubleSpinBox()
        self._tutar.setRange(0.01, 9_999_999)
        self._tutar.setDecimals(2)
        self._tutar.setSuffix(" ₺")
        self.form_layout.addRow("Tutar *", self._tutar)

        self._urun_adi = QLineEdit()
        self._urun_adi.setPlaceholderText("Jant, Akü, Yağ…")
        self.form_layout.addRow("Ürün Adı", self._urun_adi)

        self._marka = QLineEdit()
        self.form_layout.addRow("Marka", self._marka)

        self._alis_fiyati = QDoubleSpinBox()
        self._alis_fiyati.setRange(0, 9_999_999)
        self._alis_fiyati.setDecimals(2)
        self._alis_fiyati.setSuffix(" ₺")
        self.form_layout.addRow("Alış Fiyatı", self._alis_fiyati)

        self._satis_fiyati = QDoubleSpinBox()
        self._satis_fiyati.setRange(0, 9_999_999)
        self._satis_fiyati.setDecimals(2)
        self._satis_fiyati.setSuffix(" ₺")
        self.form_layout.addRow("Satış Fiyatı", self._satis_fiyati)

        self._yil = QSpinBox()
        self._yil.setRange(0, 2099)
        self._yil.setSpecialValueText("—")
        self.form_layout.addRow("Yıl", self._yil)

        self._maliyet_bilinmiyor = QCheckBox("Alış fiyatı bilinmiyor")
        self.form_layout.addRow("", self._maliyet_bilinmiyor)

        self._urun_alanlari = [self._urun_adi, self._marka, self._alis_fiyati,
                               self._satis_fiyati, self._yil, self._maliyet_bilinmiyor]
        self._kategori_degisti(self._kategori.currentText())

    def _kategori_degisti(self, text: str):
        gorunsun = text == "Ürün Alımı"
        for w in self._urun_alanlari:
            label = self.form_layout.labelForField(w)
            w.setVisible(gorunsun)
            if label:
                label.setVisible(gorunsun)

    def _form_doldur(self, data: dict):
        kat = data.get("kategori", "") or ""
        idx = self._kategori.findText(kat)
        if idx >= 0:
            self._kategori.setCurrentIndex(idx)
        self._aciklama.setText(data.get("aciklama", ""))
        self._tutar.setValue(float(data.get("tutar", 0)))
        self._urun_adi.setText(data.get("urun_adi", "") or "")
        self._marka.setText(data.get("marka", "") or "")
        self._alis_fiyati.setValue(float(data.get("alis_fiyati", 0) or 0))
        self._satis_fiyati.setValue(float(data.get("satis_fiyati", 0) or 0))
        self._yil.setValue(int(data.get("yil", 0) or 0))
        self._maliyet_bilinmiyor.setChecked(bool(data.get("maliyet_bilinmiyor", False)))

    def _dogrula(self) -> bool:
        if not self._aciklama.text().strip():
            self._hata_label.setText("Açıklama zorunludur.")
            return False
        if self._tutar.value() <= 0:
            self._hata_label.setText("Tutar 0'dan büyük olmalıdır.")
            return False
        return True

    def _kaydet_fn(self):
        payload = {
            "aciklama": self._aciklama.text().strip(),
            "tutar": self._tutar.value(),
            "kategori": self._kategori.currentText() or None,
        }
        if self._kategori.currentText() == "Ürün Alımı":
            payload.update({
                "urun_adi": self._urun_adi.text().strip() or None,
                "marka": self._marka.text().strip() or None,
                "alis_fiyati": self._alis_fiyati.value() or None,
                "satis_fiyati": self._satis_fiyati.value() or None,
                "yil": self._yil.value() or None,
                "maliyet_bilinmiyor": self._maliyet_bilinmiyor.isChecked(),
            })
        if self._duzenleme:
            gid = self._duzenleme["id"]
            return lambda: api_client.put(f"/api/giderler/{gid}", json=payload)
        return lambda: api_client.post("/api/giderler", json=payload)
