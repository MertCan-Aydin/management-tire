"""
Tüm modül view'larının temel sınıfı.
Liste + Ekle/Düzenle/Sil + API çağrısı pattern'ini standartlaştırır.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class _ListeWorker(QThread):
    veri_geldi = pyqtSignal(list)
    hata = pyqtSignal(str)

    def __init__(self, fetch_fn):
        super().__init__()
        self._fn = fetch_fn

    def run(self):
        try:
            self.veri_geldi.emit(self._fn() or [])
        except Exception as e:
            self.hata.emit(str(e))


class BaseListView(QWidget):
    """
    Alt sınıflar şunları tanımlar:
        BASLIK       : str
        SUTUNLAR     : list[str]   — tablo başlıkları
        API_PATH     : str         — GET endpoint
        _satira_donustur(row: dict) -> list[str]
        _ekle_dialogu()  -> None
        _duzenle_dialogu(row: dict) -> None
    """
    BASLIK = "Modül"
    SUTUNLAR: list[str] = []
    API_PATH = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._satirlar: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Başlık + butonlar
        ust = QHBoxLayout()
        baslik = QLabel(self.BASLIK)
        baslik.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        ust.addWidget(baslik)
        ust.addStretch()

        self._arama = QLineEdit()
        self._arama.setPlaceholderText("Ara…")
        self._arama.setMaximumWidth(220)
        self._arama.textChanged.connect(self._filtrele)
        ust.addWidget(self._arama)

        self._ekle_btn = QPushButton("+ Yeni")
        self._ekle_btn.clicked.connect(self._ekle_dialogu)
        ust.addWidget(self._ekle_btn)

        self._yenile_btn = QPushButton("↻")
        self._yenile_btn.setToolTip("Yenile")
        self._yenile_btn.clicked.connect(self.yukle)
        ust.addWidget(self._yenile_btn)

        layout.addLayout(ust)

        # Tablo
        self._tablo = QTableWidget()
        self._tablo.setColumnCount(len(self.SUTUNLAR))
        self._tablo.setHorizontalHeaderLabels(self.SUTUNLAR)
        self._tablo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tablo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tablo.setAlternatingRowColors(True)
        self._tablo.doubleClicked.connect(self._satir_secildi)
        layout.addWidget(self._tablo)

        self.yukle()

    def yukle(self):
        from ..core import api_client

        def fetch():
            return api_client.get(self.API_PATH)

        self._worker = _ListeWorker(fetch)
        self._worker.veri_geldi.connect(self._veri_yukle)
        self._worker.hata.connect(lambda msg: QMessageBox.warning(self, "Hata", msg))
        self._worker.start()

    def _veri_yukle(self, rows: list):
        self._satirlar = rows
        self._tablo_doldur(rows)

    def _tablo_doldur(self, rows: list):
        self._tablo.setRowCount(0)
        for row in rows:
            r = self._tablo.rowCount()
            self._tablo.insertRow(r)
            for c, val in enumerate(self._satira_donustur(row)):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setData(Qt.ItemDataRole.UserRole, row)
                self._tablo.setItem(r, c, item)

    def _filtrele(self, metin: str):
        metin = metin.lower().strip()
        if not metin:
            self._tablo_doldur(self._satirlar)
            return
        filtrelenmis = [
            r for r in self._satirlar
            if any(metin in str(v).lower() for v in r.values())
        ]
        self._tablo_doldur(filtrelenmis)

    def _secili_satir(self) -> dict | None:
        idxs = self._tablo.selectedItems()
        if not idxs:
            return None
        return idxs[0].data(Qt.ItemDataRole.UserRole)

    def _satir_secildi(self):
        row = self._secili_satir()
        if row:
            self._duzenle_dialogu(row)

    def _satira_donustur(self, row: dict) -> list:
        return [str(v) for v in row.values()]

    def _ekle_dialogu(self):
        pass

    def _duzenle_dialogu(self, row: dict):
        pass
