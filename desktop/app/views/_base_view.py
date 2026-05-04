"""
Tüm modül view'larının temel sınıfı.
Liste + Ekle/Düzenle/Sil + API çağrısı pattern'ini standartlaştırır.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QHeaderView, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


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
        SUTUNLAR     : list[str]
        API_PATH     : str
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
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ── Başlık + araç çubuğu ──────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        baslik = QLabel(self.BASLIK)
        baslik.setFont(QFont("Inter", 17, QFont.Weight.Bold))
        baslik.setStyleSheet("color:#191c1e;")
        toolbar.addWidget(baslik)
        toolbar.addStretch()

        # Arama kutusu
        self._arama = QLineEdit()
        self._arama.setPlaceholderText("🔍  Ara…")
        self._arama.setFixedWidth(240)
        self._arama.setFixedHeight(36)
        self._arama.textChanged.connect(self._filtrele)
        toolbar.addWidget(self._arama)

        # Ekle butonu
        self._ekle_btn = QPushButton("+ Yeni")
        self._ekle_btn.setFixedHeight(36)
        self._ekle_btn.clicked.connect(self._ekle_dialogu)
        toolbar.addWidget(self._ekle_btn)

        layout.addLayout(toolbar)

        # ── Tablo kartı ───────────────────────────────────────────────────
        kart = QFrame()
        kart.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e3e5;
            }
        """)
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(18)
        eff.setOffset(0, 2)
        c = QColor("#003d9b")
        c.setAlpha(15)
        eff.setColor(c)
        kart.setGraphicsEffect(eff)

        kart_layout = QVBoxLayout(kart)
        kart_layout.setContentsMargins(0, 0, 0, 0)
        kart_layout.setSpacing(0)

        self._tablo = QTableWidget()
        self._tablo.setColumnCount(len(self.SUTUNLAR))
        self._tablo.setHorizontalHeaderLabels(self.SUTUNLAR)
        self._tablo.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._tablo.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._tablo.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._tablo.setAlternatingRowColors(True)
        self._tablo.setShowGrid(True)
        self._tablo.verticalHeader().setVisible(False)
        self._tablo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._tablo.doubleClicked.connect(self._satir_secildi)

        kart_layout.addWidget(self._tablo)
        layout.addWidget(kart)

        # ── Alt bilgi ─────────────────────────────────────────────────────
        self._bilgi_lbl = QLabel("")
        self._bilgi_lbl.setStyleSheet(
            "color:#737685; font-size:11px; background:transparent;")
        layout.addWidget(self._bilgi_lbl)

        self.yukle()

    def showEvent(self, event):
        """Sekmeye her geçişte veriyi tazele."""
        super().showEvent(event)
        # Önceki worker hâlâ çalışıyorsa yeni istek atma
        if self._worker and self._worker.isRunning():
            return
        self.yukle()

    def yukle(self):
        from ..core import api_client

        self._bilgi_lbl.setText("Yükleniyor…")

        def fetch():
            return api_client.get(self.API_PATH)

        self._worker = _ListeWorker(fetch)
        self._worker.veri_geldi.connect(self._veri_yukle)
        self._worker.hata.connect(self._yukle_hatasi)
        # Worker bitince buton her zaman aktif kalsın (sinyal gelmese bile)
        self._worker.finished.connect(lambda: self._ekle_btn.setEnabled(True))
        self._worker.start()
        self._ekle_btn.setEnabled(False)

    def _veri_yukle(self, rows: list):
        self._satirlar = rows
        self._tablo_doldur(rows)
        sayi = len(rows)
        self._bilgi_lbl.setText(
            f"{sayi} kayıt  •  Düzenlemek için çift tıklayın  •  Silmek için Delete")

    def _yukle_hatasi(self, msg: str):
        self._bilgi_lbl.setText(f"⚠ Hata: {msg}")

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
        self._bilgi_lbl.setText(f"{len(filtrelenmis)} / {len(self._satirlar)} kayıt")

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
