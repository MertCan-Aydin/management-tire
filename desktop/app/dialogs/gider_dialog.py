from PyQt6.QtWidgets import QLineEdit, QDoubleSpinBox
from ..core import api_client
from ._base_dialog import BaseFormDialog


class GiderDialog(BaseFormDialog):
    BASLIK = "Gider"

    def _form_alanlari(self):
        self._aciklama = QLineEdit()
        self._aciklama.setPlaceholderText("Kira, fatura, yakıt…")
        self.form_layout.addRow("Açıklama *", self._aciklama)

        self._tutar = QDoubleSpinBox()
        self._tutar.setRange(0.01, 9_999_999)
        self._tutar.setDecimals(2)
        self._tutar.setSuffix(" ₺")
        self.form_layout.addRow("Tutar *", self._tutar)

    def _form_doldur(self, data: dict):
        self._aciklama.setText(data.get("aciklama", ""))
        self._tutar.setValue(float(data.get("tutar", 0)))

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
        }
        if self._duzenleme:
            gid = self._duzenleme["id"]
            return lambda: api_client.put(f"/api/giderler/{gid}", json=payload)
        return lambda: api_client.post("/api/giderler", json=payload)
