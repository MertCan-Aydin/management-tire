
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../../core/config.dart';
import '../../core/format.dart';

class RaporVerisi {
  final DateTime baslangic;
  final DateTime bitis;
  final Json ozet;
  final List<Json> kirilim;
  final List<Json> enCok;

  const RaporVerisi(
      {required this.baslangic, required this.bitis, required this.ozet, required this.kirilim, required this.enCok});
}

const _lacivert = PdfColor.fromInt(0xFF003D9B);
const _gri = PdfColor.fromInt(0xFF737685);
const _cizgi = PdfColor.fromInt(0xFFE0E3E5);
const _yesil = PdfColor.fromInt(0xFF16A34A);
const _kirmizi = PdfColor.fromInt(0xFFDC2626);

/// Masaüstü rapor PDF'inin karşılığı: özet + günlük kırılım + en çok satanlar.
Future<Uint8List> raporPdfOlustur(RaporVerisi v) async {
  // Türkçe karakterler için gömülü Inter yazı tipi
  final normal = pw.Font.ttf(await rootBundle.load('assets/fonts/Inter-Regular.ttf'));
  final kalin = pw.Font.ttf(await rootBundle.load('assets/fonts/Inter-Bold.ttf'));
  final tema = pw.ThemeData.withFont(base: normal, bold: kalin);

  final f = DateFormat('dd.MM.yyyy', 'tr_TR');
  final aralik = '${f.format(v.baslangic)} – ${f.format(v.bitis)}';
  final o = v.ozet;
  final kar = sayi(o['toplam_kar']);
  final gider = sayi(o['toplam_gider']);

  pw.Widget kart(String baslik, String deger, PdfColor renk) => pw.Expanded(
        child: pw.Container(
          padding: const pw.EdgeInsets.all(10),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: _cizgi),
            borderRadius: pw.BorderRadius.circular(6),
          ),
          child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
            pw.Text(baslik, style: const pw.TextStyle(fontSize: 9, color: _gri)),
            pw.SizedBox(height: 4),
            pw.Text(deger, style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: renk)),
          ]),
        ),
      );

  pw.Widget tablo(List<String> basliklar, List<List<String>> satirlar) => pw.TableHelper.fromTextArray(
        headers: basliklar,
        data: satirlar,
        border: pw.TableBorder.all(color: _cizgi, width: 0.6),
        headerStyle: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold, color: PdfColors.white),
        headerDecoration: const pw.BoxDecoration(color: _lacivert),
        cellStyle: const pw.TextStyle(fontSize: 9),
        cellPadding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
        cellAlignments: {for (var i = 1; i < basliklar.length; i++) i: pw.Alignment.centerRight},
        oddRowDecoration: const pw.BoxDecoration(color: PdfColor.fromInt(0xFFF7F8FA)),
      );

  final doc = pw.Document(theme: tema, title: 'Rapor $aralik', author: kAppName);
  doc.addPage(pw.MultiPage(
    pageFormat: PdfPageFormat.a4,
    margin: const pw.EdgeInsets.all(36),
    header: (ctx) => pw.Container(
      padding: const pw.EdgeInsets.only(bottom: 10),
      margin: const pw.EdgeInsets.only(bottom: 14),
      decoration: const pw.BoxDecoration(border: pw.Border(bottom: pw.BorderSide(color: _lacivert, width: 2))),
      child: pw.Row(mainAxisAlignment: pw.MainAxisAlignment.spaceBetween, children: [
        pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Text(kAppName, style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold, color: _lacivert)),
          pw.Text('Dönem Raporu  ·  $aralik', style: const pw.TextStyle(fontSize: 10, color: _gri)),
        ]),
        pw.Text('Oluşturma: ${DateFormat('dd.MM.yyyy HH:mm', 'tr_TR').format(DateTime.now())}',
            style: const pw.TextStyle(fontSize: 8, color: _gri)),
      ]),
    ),
    footer: (ctx) => pw.Align(
      alignment: pw.Alignment.centerRight,
      child: pw.Text('Sayfa ${ctx.pageNumber} / ${ctx.pagesCount}', style: const pw.TextStyle(fontSize: 8, color: _gri)),
    ),
    build: (ctx) => [
      pw.Row(children: [
        kart('CİRO', para(o['toplam_ciro']), _lacivert),
        pw.SizedBox(width: 8),
        kart('KÂR', para(kar), _yesil),
        pw.SizedBox(width: 8),
        kart('SATIŞ', '${tamSayi(o['satis_adedi'])} adet', PdfColors.orange800),
        pw.SizedBox(width: 8),
        kart('GİDER', para(gider), _kirmizi),
        pw.SizedBox(width: 8),
        kart('NET', para(kar - gider), kar - gider >= 0 ? _yesil : _kirmizi),
      ]),
      pw.SizedBox(height: 20),
      pw.Text('Günlük Kırılım', style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 6),
      if (v.kirilim.isEmpty)
        pw.Text('Bu aralıkta satış yok.', style: const pw.TextStyle(fontSize: 10, color: _gri))
      else
        tablo([
          'Gün',
          'Satış',
          'Ciro',
          'Kâr'
        ], [
          for (final g in v.kirilim) [tarih(g['gun']), '${tamSayi(g['satis_adedi'])}', para(g['ciro']), para(g['kar'])],
        ]),
      pw.SizedBox(height: 20),
      pw.Text('En Çok Satanlar', style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 6),
      if (v.enCok.isEmpty)
        pw.Text('Veri yok.', style: const pw.TextStyle(fontSize: 10, color: _gri))
      else
        tablo([
          'Ürün',
          'Adet',
          'Ciro',
          'Kâr'
        ], [
          for (final u in v.enCok)
            [
              u['urun_adi_anlik']?.toString() ?? '',
              '${tamSayi(u['toplam_adet'])}',
              para(u['toplam_ciro']),
              para(u['toplam_kar'])
            ],
        ]),
    ],
  ));
  return doc.save();
}
