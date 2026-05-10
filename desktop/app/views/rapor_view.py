from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QFileDialog, QMessageBox,
    QGraphicsDropShadowEffect, QSizePolicy,
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextDocument, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from ..core import api_client
from ..core.utils import tr_para


class _RaporWorker(QThread):
    veri_geldi = pyqtSignal(dict)
    hata = pyqtSignal(str)

    def __init__(self, baslangic: str, bitis: str):
        super().__init__()
        self._bas = baslangic
        self._bit = bitis

    def run(self):
        try:
            aralik = api_client.get("/api/raporlar/aralik",
                                     params={"baslangic": self._bas, "bitis": self._bit})
            kirilim = api_client.get("/api/raporlar/kirilim",
                                      params={"baslangic": self._bas, "bitis": self._bit})
            en_cok = api_client.get("/api/raporlar/en-cok-satan",
                                     params={"baslangic": self._bas, "bitis": self._bit, "limit": 10})
            self.veri_geldi.emit({"aralik": aralik, "kirilim": kirilim, "en_cok": en_cok})
        except Exception as e:
            self.hata.emit(str(e))


class RaporView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._son_veri: dict = {}
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Başlık + dışa aktarma butonları
        ust = QHBoxLayout()
        baslik = QLabel("Raporlar")
        baslik.setFont(QFont("Inter", 17, QFont.Weight.Bold))
        baslik.setStyleSheet("color:#191c1e;")
        ust.addWidget(baslik)
        ust.addStretch()

        self._pdf_btn = QPushButton("📄  PDF Kaydet")
        self._pdf_btn.setObjectName("flat")
        self._pdf_btn.setFixedHeight(36)
        self._pdf_btn.clicked.connect(self._pdf_kaydet)
        ust.addWidget(self._pdf_btn)

        self._yazdir_btn = QPushButton("🖨  Yazdır")
        self._yazdir_btn.setFixedHeight(36)
        self._yazdir_btn.clicked.connect(self._yazdir)
        ust.addWidget(self._yazdir_btn)

        layout.addLayout(ust)

        # Tarih seçim çubuğu
        tarih_row = QHBoxLayout()
        tarih_row.setSpacing(8)
        tarih_row.addWidget(self._mini_lbl("Başlangıç"))
        self._bas_tarih = QDateEdit(QDate.currentDate().addDays(-30))
        self._bas_tarih.setCalendarPopup(True)
        self._bas_tarih.setDisplayFormat("dd.MM.yyyy")
        self._bas_tarih.setFixedHeight(36)
        tarih_row.addWidget(self._bas_tarih)

        tarih_row.addSpacing(8)
        tarih_row.addWidget(self._mini_lbl("Bitiş"))
        self._bit_tarih = QDateEdit(QDate.currentDate())
        self._bit_tarih.setCalendarPopup(True)
        self._bit_tarih.setDisplayFormat("dd.MM.yyyy")
        self._bit_tarih.setFixedHeight(36)
        tarih_row.addWidget(self._bit_tarih)

        goster_btn = QPushButton("Göster")
        goster_btn.setFixedHeight(36)
        goster_btn.clicked.connect(self._yukle)
        tarih_row.addWidget(goster_btn)
        tarih_row.addStretch()
        layout.addLayout(tarih_row)

        # Özet kartlar
        ozet_row = QHBoxLayout()
        ozet_row.setSpacing(12)
        self._lbl_ciro  = self._kart("CİRO",       "₺ 0", "#003d9b", "#eef2ff")
        self._lbl_kar   = self._kart("KÂR",        "₺ 0", "#16a34a", "#dcfce7")
        self._lbl_satis = self._kart("SATIŞ",      "0",   "#d97706", "#fef3c7")
        self._lbl_gider = self._kart("GİDER",      "₺ 0", "#dc2626", "#fee2e2")
        for w in (self._lbl_ciro, self._lbl_kar, self._lbl_satis, self._lbl_gider):
            ozet_row.addWidget(w)
        layout.addLayout(ozet_row)

        # Sekmeli tablolar
        self._tabs = QTabWidget()
        self._kirilim_tablo = self._tablo(["Tarih", "Satış Adedi", "Ciro (₺)", "Kâr (₺)"])
        self._en_cok_tablo = self._tablo(["Ürün", "Adet", "Ciro (₺)", "Kâr (₺)"])
        self._tabs.addTab(self._kirilim_tablo, "Günlük Kırılım")
        self._tabs.addTab(self._en_cok_tablo, "En Çok Satanlar")
        layout.addWidget(self._tabs)

        self._yukle()

    def _mini_lbl(self, txt: str) -> QLabel:
        l = QLabel(txt)
        l.setStyleSheet("color:#505f76; font-size:12px; background:transparent;")
        return l

    def _kart(self, baslik: str, deger: str, aksan: str, aksan_bg: str) -> QFrame:
        kart = QFrame()
        kart.setObjectName("rapKart")
        kart.setFixedHeight(96)
        kart.setStyleSheet("""
            QFrame#rapKart {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e3e5;
            }
        """)
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(16)
        eff.setOffset(0, 2)
        c = QColor(aksan); c.setAlpha(20)
        eff.setColor(c)
        kart.setGraphicsEffect(eff)

        v = QVBoxLayout(kart)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)

        lb = QLabel(baslik)
        lb.setStyleSheet(
            f"color:#505f76; font-size:11px; font-weight:600;"
            f"letter-spacing:0.5px; background:transparent; border:none;"
        )
        val = QLabel(deger)
        val.setObjectName("val")
        val.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        val.setStyleSheet(f"color:{aksan}; background:transparent; border:none;")

        v.addWidget(lb)
        v.addWidget(val)
        v.addStretch()
        return kart

    def _tablo(self, sutunlar: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(sutunlar))
        t.setHorizontalHeaderLabels(sutunlar)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        return t

    # ── Veri yükleme ──────────────────────────────────────────────────────
    def _yukle(self):
        self._worker = _RaporWorker(
            self._bas_tarih.date().toString("yyyy-MM-dd"),
            self._bit_tarih.date().toString("yyyy-MM-dd"),
        )
        self._worker.veri_geldi.connect(self._guncelle)
        self._worker.start()

    def _guncelle(self, data: dict):
        self._son_veri = data
        aralik = data.get("aralik") or {}
        kirilim = data.get("kirilim") or []
        en_cok = data.get("en_cok") or []

        def _fmt(v): return tr_para(float(v or 0))

        self._lbl_ciro.findChild(QLabel, "val").setText(f"₺ {_fmt(aralik.get('toplam_ciro', 0))}")
        self._lbl_kar.findChild(QLabel, "val").setText(f"₺ {_fmt(aralik.get('toplam_kar', 0))}")
        self._lbl_satis.findChild(QLabel, "val").setText(str(aralik.get("satis_adedi", 0)))
        self._lbl_gider.findChild(QLabel, "val").setText(f"₺ {_fmt(aralik.get('toplam_gider', 0))}")

        self._kirilim_tablo.setRowCount(0)
        for row in kirilim:
            r = self._kirilim_tablo.rowCount()
            self._kirilim_tablo.insertRow(r)
            for c, v in enumerate([
                str(row.get("gun", ""))[:10],
                row.get("satis_adedi"),
                _fmt(row.get("ciro")),
                _fmt(row.get("kar"))
            ]):
                self._kirilim_tablo.setItem(r, c, QTableWidgetItem(str(v)))

        self._en_cok_tablo.setRowCount(0)
        for row in en_cok:
            r = self._en_cok_tablo.rowCount()
            self._en_cok_tablo.insertRow(r)
            for c, v in enumerate([
                row.get("urun_adi_anlik"),
                row.get("toplam_adet"),
                _fmt(row.get("toplam_ciro")),
                _fmt(row.get("toplam_kar"))
            ]):
                self._en_cok_tablo.setItem(r, c, QTableWidgetItem(str(v)))

    # ── Rapor HTML üretimi ────────────────────────────────────────────────
    def _rapor_html(self) -> str:
        aralik = self._son_veri.get("aralik") or {}
        kirilim = self._son_veri.get("kirilim") or []
        en_cok = self._son_veri.get("en_cok") or []

        bas = self._bas_tarih.date().toString("dd.MM.yyyy")
        bit = self._bit_tarih.date().toString("dd.MM.yyyy")
        bugun = date.today().strftime("%d.%m.%Y")

        def f(v): return tr_para(float(v or 0))

        kirilim_satir = "\n".join(
            f"<tr><td>{str(r.get('gun',''))[:10]}</td>"
            f"<td style='text-align:right'>{r.get('satis_adedi','')}</td>"
            f"<td style='text-align:right'>{f(r.get('ciro'))} ₺</td>"
            f"<td style='text-align:right'>{f(r.get('kar'))} ₺</td></tr>"
            for r in kirilim
        ) or "<tr><td colspan='4' style='text-align:center; color:#999'>Veri yok</td></tr>"

        en_cok_satir = "\n".join(
            f"<tr><td>{r.get('urun_adi_anlik','')}</td>"
            f"<td style='text-align:right'>{r.get('toplam_adet','')}</td>"
            f"<td style='text-align:right'>{f(r.get('toplam_ciro'))} ₺</td>"
            f"<td style='text-align:right'>{f(r.get('toplam_kar'))} ₺</td></tr>"
            for r in en_cok
        ) or "<tr><td colspan='4' style='text-align:center; color:#999'>Veri yok</td></tr>"

        return f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; color:#191c1e; margin:24px;">

            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
                <tr>
                    <td><h1 style="color:#003d9b; margin:0; font-size:22px;">Dijital Lastik Servisi</h1>
                        <div style="color:#505f76; font-size:12px;">Dönem Raporu</div></td>
                    <td style="text-align:right; color:#505f76; font-size:11px;">
                        Rapor Tarihi: {bugun}
                    </td>
                </tr>
            </table>
            <hr style="border:none; border-top:2px solid #003d9b; margin:0 0 16px 0;">

            <h2 style="font-size:14px; margin:8px 0;">Tarih Aralığı: {bas} — {bit}</h2>

            <h3 style="font-size:13px; margin-top:18px; color:#003d9b;">ÖZET</h3>
            <table width="100%" cellpadding="8" cellspacing="0"
                   style="border:1px solid #e0e3e5; border-collapse:collapse; font-size:12px;">
                <tr style="background:#f7f9fb;">
                    <th style="text-align:left; border:1px solid #e0e3e5;">Toplam Ciro</th>
                    <th style="text-align:left; border:1px solid #e0e3e5;">Toplam Kâr</th>
                    <th style="text-align:left; border:1px solid #e0e3e5;">Satış Adedi</th>
                    <th style="text-align:left; border:1px solid #e0e3e5;">Toplam Gider</th>
                </tr>
                <tr>
                    <td style="border:1px solid #e0e3e5;"><b>{f(aralik.get('toplam_ciro'))} ₺</b></td>
                    <td style="border:1px solid #e0e3e5; color:#16a34a;"><b>{f(aralik.get('toplam_kar'))} ₺</b></td>
                    <td style="border:1px solid #e0e3e5;"><b>{aralik.get('satis_adedi', 0)}</b></td>
                    <td style="border:1px solid #e0e3e5; color:#dc2626;"><b>{f(aralik.get('toplam_gider'))} ₺</b></td>
                </tr>
            </table>

            <h3 style="font-size:13px; margin-top:24px; color:#003d9b;">GÜNLÜK KIRILIM</h3>
            <table width="100%" cellpadding="6" cellspacing="0"
                   style="border:1px solid #e0e3e5; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="background:#f7f9fb;">
                        <th style="text-align:left; border:1px solid #e0e3e5;">Tarih</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Satış Adedi</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Ciro</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Kâr</th>
                    </tr>
                </thead>
                <tbody>{kirilim_satir}</tbody>
            </table>

            <h3 style="font-size:13px; margin-top:24px; color:#003d9b;">EN ÇOK SATAN ÜRÜNLER</h3>
            <table width="100%" cellpadding="6" cellspacing="0"
                   style="border:1px solid #e0e3e5; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="background:#f7f9fb;">
                        <th style="text-align:left; border:1px solid #e0e3e5;">Ürün</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Adet</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Ciro</th>
                        <th style="text-align:right; border:1px solid #e0e3e5;">Kâr</th>
                    </tr>
                </thead>
                <tbody>{en_cok_satir}</tbody>
            </table>

            <p style="text-align:center; color:#737685; font-size:10px; margin-top:32px;
                       border-top:1px solid #e0e3e5; padding-top:8px;">
                Dijital Lastik Servisi · Otomatik üretilmiş rapor · {bugun}
            </p>
        </body>
        </html>
        """

    # ── PDF kaydetme ──────────────────────────────────────────────────────
    def _pdf_kaydet(self):
        if not self._son_veri:
            QMessageBox.information(self, "Bilgi", "Önce 'Göster' ile rapor verilerini yükleyin.")
            return

        bugun = date.today().strftime("%Y-%m-%d")
        varsayilan = f"rapor_{bugun}.pdf"
        yol, _ = QFileDialog.getSaveFileName(
            self, "PDF Olarak Kaydet", varsayilan, "PDF (*.pdf)")
        if not yol:
            return
        if not yol.lower().endswith(".pdf"):
            yol += ".pdf"

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(yol)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            doc = QTextDocument()
            doc.setHtml(self._rapor_html())
            doc.print(printer)

            QMessageBox.information(self, "Başarılı", f"PDF kaydedildi:\n{yol}")
            try:
                self.window().statusBar().showMessage("PDF rapor kaydedildi ✓", 3000)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"PDF oluşturulamadı: {e}")

    # ── Yazdırma ──────────────────────────────────────────────────────────
    def _yazdir(self):
        if not self._son_veri:
            QMessageBox.information(self, "Bilgi", "Önce 'Göster' ile rapor verilerini yükleyin.")
            return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QPrintDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setHtml(self._rapor_html())
                doc.print(printer)
                try:
                    self.window().statusBar().showMessage("Rapor yazdırıldı ✓", 3000)
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yazdırma başarısız: {e}")
