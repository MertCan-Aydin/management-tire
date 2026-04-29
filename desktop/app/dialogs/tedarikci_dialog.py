from PyQt6.QtWidgets import QLineEdit, QDoubleSpinBox
from ..core import api_client
from ._base_dialog import BaseFormDialog


class TedarikciDialog(BaseFormDialog):
    BASLIK = "Tedarikçi"

    def _form_alanlari(self):
        self._ad = QLineEdit()
        self._ad.setPlaceholderText("Zorunlu")
        self.form_layout.addRow("Firma Adı *", self._ad)

        self._iletisim = QLineEdit()
        self._iletisim.setPlaceholderText("Telefon / E-posta / Adres")
        self.form_layout.addRow("İletişim", self._iletisim)

        self._borc = QDoubleSpinBox()
        self._borc.setRange(0, 9_999_999)
        self._borc.setDecimals(2)
        self._borc.setSuffix(" ₺")
        self.form_layout.addRow("Güncel Borç", self._borc)

    def _form_doldur(self, data: dict):
        self._ad.setText(data.get("ad", ""))
        self._iletisim.setText(data.get("iletisim_bilgisi", "") or "")
        self._borc.setValue(float(data.get("guncel_borc", 0)))

    def _dogrula(self) -> bool:
        if not self._ad.text().strip():
            self._hata_label.setText("Firma adı zorunludur.")
            return False
        return True

    def _kaydet_fn(self):
        payload = {
            "ad": self._ad.text().strip(),
            "iletisim_bilgisi": self._iletisim.text().strip() or None,
            "guncel_borc": self._borc.value(),
        }
        if self._duzenleme:
            tid = self._duzenleme["id"]
            payload["silindi_mi"] = False
            return lambda: api_client.put(f"/api/tedarikciler/{tid}", json=payload)
        return lambda: api_client.post("/api/tedarikciler", json=payload)


class TedarikciOdemeDialog(BaseFormDialog):
    BASLIK = "Tedarikçiye Ödeme"

    def __init__(self, parent=None, tedarikci_id: int = None, tedarikci_adi: str = ""):
        self._tedarikci_id = tedarikci_id
        self._tedarikci_adi = tedarikci_adi
        super().__init__(parent)

    def _form_alanlari(self):
        from PyQt6.QtWidgets import QLabel
        self.form_layout.addRow("Tedarikçi", QLabel(self._tedarikci_adi))

        self._tutar = QDoubleSpinBox()
        self._tutar.setRange(0.01, 9_999_999)
        self._tutar.setDecimals(2)
        self._tutar.setSuffix(" ₺")
        self.form_layout.addRow("Ödeme Tutarı *", self._tutar)

    def _dogrula(self) -> bool:
        if self._tutar.value() <= 0:
            self._hata_label.setText("Tutar 0'dan büyük olmalıdır.")
            return False
        return True

    def _kaydet_fn(self):
        payload = {"tedarikci_id": self._tedarikci_id, "tutar": self._tutar.value()}
        return lambda: api_client.post("/api/tedarikciler/odemeler", json=payload)
