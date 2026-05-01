from datetime import date
from PyQt6.QtWidgets import (
    QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QLabel, QDateEdit, QCompleter, QHBoxLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from ..core import api_client
from ._base_dialog import BaseFormDialog


class _MusteriAraWorker(QThread):
    bitti = pyqtSignal(list)

    def __init__(self, q: str):
        super().__init__()
        self._q = q

    def run(self):
        try:
            data = api_client.get("/api/musteriler", params={"arama": self._q, "limit": 20})
            self.bitti.emit(data or [])
        except Exception:
            self.bitti.emit([])


class LastikOteliDialog(BaseFormDialog):
    BASLIK = "Lastik Oteli"

    def _form_alanlari(self):
        # Müşteri arama
        self._musteri_input = QLineEdit()
        self._musteri_input.setPlaceholderText("Ad / telefon / plaka ile ara…")
        self._musteri_input.textChanged.connect(self._musteri_ara)
        self.form_layout.addRow("Müşteri *", self._musteri_input)

        self._musteri_id: int | None = None
        self._musteri_sonuc_lbl = QLabel("")
        self._musteri_sonuc_lbl.setStyleSheet(
            "color:#003d9b; font-size:11px; background:transparent;")
        self.form_layout.addRow("", self._musteri_sonuc_lbl)

        # Plaka (otomatik dolar, düzenlenebilir)
        self._plaka = QLineEdit()
        self._plaka.setPlaceholderText("34ABC123")
        self.form_layout.addRow("Araç Plakası", self._plaka)

        # Raf kodu
        self._raf_kodu = QLineEdit()
        self._raf_kodu.setPlaceholderText("A1, B12, C3 …")
        self._raf_kodu.setMaxLength(10)
        self.form_layout.addRow("Raf Kodu *", self._raf_kodu)

        # Lastik bilgisi
        self._lastik_bilgisi = QLineEdit()
        self._lastik_bilgisi.setPlaceholderText("205/55 R17 Michelin Kış")
        self.form_layout.addRow("Lastik Bilgisi", self._lastik_bilgisi)

        # Adet
        self._adet = QSpinBox()
        self._adet.setRange(1, 20)
        self._adet.setValue(4)
        self.form_layout.addRow("Adet", self._adet)

        # Sezon
        self._sezon = QComboBox()
        self._sezon.addItems(["Yaz", "Kış"])
        self.form_layout.addRow("Sezon *", self._sezon)

        # Giriş tarihi
        self._giris = QDateEdit(QDate.currentDate())
        self._giris.setCalendarPopup(True)
        self._giris.setDisplayFormat("dd.MM.yyyy")
        self.form_layout.addRow("Giriş Tarihi", self._giris)

        # Notlar
        self._notlar = QTextEdit()
        self._notlar.setMaximumHeight(60)
        self.form_layout.addRow("Notlar", self._notlar)

        self._musteriler: list[dict] = []
        self._ara_worker = None

    def _musteri_ara(self, metin: str):
        if len(metin) < 2:
            return
        self._ara_worker = _MusteriAraWorker(metin)
        self._ara_worker.bitti.connect(self._musteri_yuklendi)
        self._ara_worker.start()

    def _musteri_yuklendi(self, data: list):
        self._musteriler = data
        if not data:
            self._musteri_sonuc_lbl.setText("Müşteri bulunamadı")
            self._musteri_id = None
            return

        # İlk eşleşmeyi otomatik seç
        m = data[0]
        self._musteri_id = m["id"]
        self._musteri_sonuc_lbl.setText(
            f"✓  {m['ad_soyad']}  •  {m.get('arac_plakasi', '')}")
        if not self._plaka.text():
            self._plaka.setText(m.get("arac_plakasi", "") or "")

    def _form_doldur(self, data: dict):
        self._musteri_input.setText(data.get("musteri_adi", ""))
        self._musteri_id = data.get("musteri_id")
        self._plaka.setText(data.get("arac_plakasi", "") or "")
        self._raf_kodu.setText(data.get("raf_kodu", ""))
        self._lastik_bilgisi.setText(data.get("lastik_bilgisi", "") or "")
        self._adet.setValue(int(data.get("lastik_adedi", 4)))
        idx = self._sezon.findText(data.get("sezon", "Yaz"))
        if idx >= 0:
            self._sezon.setCurrentIndex(idx)
        if data.get("giris_tarihi"):
            gd = str(data["giris_tarihi"])[:10].split("-")
            self._giris.setDate(QDate(int(gd[0]), int(gd[1]), int(gd[2])))
        self._notlar.setPlainText(data.get("notlar", "") or "")

    def _dogrula(self) -> bool:
        if not self._musteri_input.text().strip():
            self._hata_label.setText("Müşteri adı zorunludur.")
            self._hata_label.show()
            return False
        if not self._raf_kodu.text().strip():
            self._hata_label.setText("Raf kodu zorunludur.")
            self._hata_label.show()
            return False
        return True

    def _kaydet_fn(self):
        musteri_adi = self._musteri_input.text().strip()
        gd = self._giris.date()
        payload = {
            "musteri_id":        self._musteri_id,
            "musteri_adi_anlik": musteri_adi,
            "arac_plakasi":      self._plaka.text().strip() or None,
            "raf_kodu":          self._raf_kodu.text().strip().upper(),
            "lastik_bilgisi":    self._lastik_bilgisi.text().strip() or None,
            "lastik_adedi":      self._adet.value(),
            "sezon":             self._sezon.currentText(),
            "giris_tarihi":      f"{gd.year()}-{gd.month():02d}-{gd.day():02d}",
            "notlar":            self._notlar.toPlainText().strip() or None,
        }
        if self._duzenleme:
            kid = self._duzenleme["id"]
            return lambda: api_client.put(f"/api/lastik-oteli/{kid}", json=payload)
        return lambda: api_client.post("/api/lastik-oteli", json=payload)
