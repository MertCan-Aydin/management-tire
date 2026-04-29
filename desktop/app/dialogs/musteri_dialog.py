from PyQt6.QtWidgets import QLineEdit
from ..core import api_client
from ._base_dialog import BaseFormDialog


class MusteriDialog(BaseFormDialog):
    BASLIK = "Müşteri"

    def _form_alanlari(self):
        self._ad_soyad = QLineEdit()
        self._ad_soyad.setPlaceholderText("Zorunlu")
        self.form_layout.addRow("Ad Soyad *", self._ad_soyad)

        self._telefon = QLineEdit()
        self._telefon.setPlaceholderText("05xxxxxxxxx — Zorunlu, tekil")
        self.form_layout.addRow("Telefon *", self._telefon)

        self._arac_markasi = QLineEdit()
        self._arac_markasi.setPlaceholderText("Toyota, Ford…")
        self.form_layout.addRow("Araç Markası", self._arac_markasi)

        self._arac_plakasi = QLineEdit()
        self._arac_plakasi.setPlaceholderText("34 ABC 123")
        self._arac_plakasi.setMaxLength(20)
        self.form_layout.addRow("Plaka", self._arac_plakasi)

        self._notlar = QLineEdit()
        self.form_layout.addRow("Notlar", self._notlar)

    def _form_doldur(self, data: dict):
        self._ad_soyad.setText(data.get("ad_soyad", ""))
        self._telefon.setText(data.get("telefon", ""))
        self._arac_markasi.setText(data.get("arac_markasi", "") or "")
        self._arac_plakasi.setText(data.get("arac_plakasi", "") or "")
        self._notlar.setText(data.get("notlar", "") or "")

    def _dogrula(self) -> bool:
        if not self._ad_soyad.text().strip():
            self._hata_label.setText("Ad soyad zorunludur.")
            return False
        if not self._telefon.text().strip():
            self._hata_label.setText("Telefon zorunludur.")
            return False
        return True

    def _kaydet_fn(self):
        payload = {
            "ad_soyad": self._ad_soyad.text().strip(),
            "telefon": self._telefon.text().strip(),
            "arac_markasi": self._arac_markasi.text().strip() or None,
            "arac_plakasi": self._arac_plakasi.text().strip().upper() or None,
            "notlar": self._notlar.text().strip() or None,
        }
        if self._duzenleme:
            mid = self._duzenleme["id"]
            return lambda: api_client.put(f"/api/musteriler/{mid}", json=payload)
        return lambda: api_client.post("/api/musteriler", json=payload)
