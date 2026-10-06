import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:printing/printing.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import 'rapor_pdf.dart';

enum _Aralik {
  bugun('Bugün'),
  hafta('Bu Hafta'),
  ay('Bu Ay'),
  gecenAy('Geçen Ay'),
  ozel('Özel');

  final String etiket;
  const _Aralik(this.etiket);
}

class RaporlarSayfasi extends StatefulWidget {
  const RaporlarSayfasi({super.key});

  @override
  State<RaporlarSayfasi> createState() => _RaporlarSayfasiState();
}

class _RaporlarSayfasiState extends State<RaporlarSayfasi> with VeriYukleyici<RaporlarSayfasi, RaporVerisi> {
  _Aralik _secim = _Aralik.ay;
  late DateTimeRange _aralik = _hesapla(_Aralik.ay);
  bool _pdfHazirlaniyor = false;

  static DateTimeRange _hesapla(_Aralik a) {
    final n = DateTime.now();
    final bugun = DateTime(n.year, n.month, n.day);
    return switch (a) {
      _Aralik.bugun => DateTimeRange(start: bugun, end: bugun),
      _Aralik.hafta => DateTimeRange(start: bugun.subtract(Duration(days: bugun.weekday - 1)), end: bugun),
      _Aralik.ay || _Aralik.ozel => DateTimeRange(start: DateTime(bugun.year, bugun.month, 1), end: bugun),
      _Aralik.gecenAy => DateTimeRange(
          start: DateTime(bugun.year, bugun.month - 1, 1),
          end: DateTime(bugun.year, bugun.month, 0),
        ),
    };
  }

  @override
  Future<RaporVerisi> getir() async {
    final bas = isoGun(_aralik.start);
    final bit = isoGun(_aralik.end);
    final r = await Future.wait([
      RaporApi.aralik(bas, bit),
      RaporApi.kirilim(bas, bit),
      RaporApi.enCokSatan(bas, bit),
    ]);
    return RaporVerisi(
      baslangic: _aralik.start,
      bitis: _aralik.end,
      ozet: r[0] as Json,
      kirilim: r[1] as List<Json>,
      enCok: r[2] as List<Json>,
    );
  }

  Future<void> _secimDegisti(_Aralik a) async {
    if (a == _Aralik.ozel) {
      final secilen = await showDateRangePicker(
        context: context,
        firstDate: DateTime(2020),
        lastDate: DateTime.now(),
        initialDateRange: _aralik,
        helpText: 'Rapor aralığı',
        saveText: 'Uygula',
      );
      if (secilen == null) return;
      _aralik = secilen;
    } else {
      _aralik = _hesapla(a);
    }
    setState(() => _secim = a);
    yenile();
  }

  Future<void> _pdf({required bool yazdir}) async {
    final v = veri;
    if (v == null) return;
    setState(() => _pdfHazirlaniyor = true);
    try {
      final bytes = await raporPdfOlustur(v);
      final ad = 'rapor_${isoGun(v.baslangic)}_${isoGun(v.bitis)}.pdf';
      if (yazdir) {
        await Printing.layoutPdf(onLayout: (_) async => bytes, name: ad);
      } else {
        await Printing.sharePdf(bytes: bytes, filename: ad);
      }
    } catch (e) {
      if (mounted) bildir(context, 'PDF oluşturulamadı: ${hataMesaji(e)}', hata: true);
    } finally {
      if (mounted) setState(() => _pdfHazirlaniyor = false);
    }
  }

  String get _aralikMetni {
    final f = DateFormat('d MMM y', 'tr_TR');
    if (_aralik.start == _aralik.end) return f.format(_aralik.start);
    return '${f.format(_aralik.start)} – ${f.format(_aralik.end)}';
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      ListeUstu(
        baslik: 'Raporlar',
        altBaslik: _aralikMetni,
        eylemler: [
          UstDugme(
            ikon: CupertinoIcons.printer,
            ipucu: 'Yazdır',
            yukleniyor: _pdfHazirlaniyor,
            onTap: veri == null ? null : () => _pdf(yazdir: true),
          ),
          UstDugme(
            ikon: CupertinoIcons.share,
            ipucu: 'PDF paylaş',
            onTap: veri == null || _pdfHazirlaniyor ? null : () => _pdf(yazdir: false),
          ),
        ],
        filtre: SizedBox(
          width: double.infinity,
          child: SegmentSecici<_Aralik>(
            secenekler: {for (final a in _Aralik.values) a: a.etiket},
            secili: _secim,
            degisti: _secimDegisti,
          ),
        ),
      ),
      Expanded(child: durum((v) => _icerik(context, v))),
    ]);
  }

  Widget _icerik(BuildContext context, RaporVerisi v) {
    final r = context.renk;
    final o = v.ozet;
    final kar = sayi(o['toplam_kar']);
    final gider = sayi(o['toplam_gider']);
    return LayoutBuilder(builder: (context, c) {
      final genis = c.maxWidth >= 900;
      final kartlar = KartIzgarasi(minGenislik: genis ? 190 : 160, maxSutun: 5, children: [
        IstatistikKarti(baslik: 'Ciro', deger: para(o['toplam_ciro']), ikon: CupertinoIcons.chart_bar_fill, renk: r.ana),
        IstatistikKarti(baslik: 'Kâr', deger: para(kar), ikon: CupertinoIcons.arrow_up_right, renk: r.basari),
        IstatistikKarti(
            baslik: 'Satış Adedi', deger: '${tamSayi(o['satis_adedi'])}', ikon: CupertinoIcons.cart_fill, renk: r.turuncu),
        IstatistikKarti(baslik: 'Gider', deger: para(gider), ikon: CupertinoIcons.creditcard_fill, renk: r.tehlike),
        IstatistikKarti(
          baslik: 'Net (Kâr − Gider)',
          deger: para(kar - gider),
          ikon: CupertinoIcons.equal_circle_fill,
          renk: kar - gider >= 0 ? r.basari : r.tehlike,
        ),
      ]);

      final grafik = Grup(
        baslik: 'Günlük Ciro ve Kâr',
        dis: EdgeInsets.zero,
        children: [
          if (v.kirilim.isEmpty)
            const Padding(padding: EdgeInsets.all(24), child: Center(child: Text('Bu aralıkta satış yok')))
          else ...[
            Padding(padding: const EdgeInsets.fromLTRB(16, 18, 16, 8), child: _GunlukGrafik(v.kirilim)),
            for (final g in v.kirilim.reversed)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
                child: Row(children: [
                  SizedBox(width: 100, child: Text(tarih(g['gun']), style: context.yazi.bodyMedium)),
                  Expanded(child: Text('${tamSayi(g['satis_adedi'])} satış', style: context.yazi.bodySmall)),
                  Text(para(g['ciro']), style: context.yazi.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                  SizedBox(
                    width: 110,
                    child: Text(para(g['kar']),
                        textAlign: TextAlign.right, style: context.yazi.bodyMedium?.copyWith(color: r.basari)),
                  ),
                ]),
              ),
          ],
        ],
      );

      final enCok = Grup(
        baslik: 'En Çok Satanlar',
        dis: EdgeInsets.zero,
        children: v.enCok.isEmpty
            ? [const Padding(padding: EdgeInsets.all(24), child: Center(child: Text('Veri yok')))]
            : [
                for (var i = 0; i < v.enCok.length; i++)
                  Satir(
                    onde: Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        color: i < 3 ? r.ana : r.dolgu,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text('${i + 1}',
                            style: TextStyle(
                              fontFamily: kFont,
                              fontWeight: FontWeight.w700,
                              fontSize: 13,
                              color: i < 3 ? Colors.white : r.metin,
                            )),
                      ),
                    ),
                    baslik: v.enCok[i]['urun_adi_anlik'] as String? ?? '',
                    alt: '${tamSayi(v.enCok[i]['toplam_adet'])} adet  ·  Kâr ${para(v.enCok[i]['toplam_kar'])}',
                    sag: Text(para(v.enCok[i]['toplam_ciro']), style: context.yazi.titleSmall),
                  ),
              ],
      );

      return YenilenebilirListe(
        yenile: yenile,
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
        children: [
          kartlar,
          const SizedBox(height: 24),
          if (genis)
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(flex: 3, child: grafik),
              const SizedBox(width: 20),
              Expanded(flex: 2, child: enCok),
            ])
          else ...[
            grafik,
            const SizedBox(height: 24),
            enCok,
          ],
        ],
      );
    });
  }
}

/// Günlük ciro (açık) ve kâr (koyu) çubukları.
class _GunlukGrafik extends StatelessWidget {
  final List<Json> gunler;
  const _GunlukGrafik(this.gunler);

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final enBuyuk = gunler.fold<double>(0, (m, g) => sayi(g['ciro']) > m ? sayi(g['ciro']) : m);
    return SizedBox(
      height: 170,
      child: LayoutBuilder(builder: (context, c) {
        final adet = gunler.length;
        final cubuk = ((c.maxWidth / adet) * 0.62).clamp(4.0, 34.0);
        final etiketAdimi = (adet / 8).ceil().clamp(1, 1000);
        return Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            for (var i = 0; i < adet; i++)
              Expanded(
                child: Tooltip(
                  message: '${tarih(gunler[i]['gun'])}\nCiro ${para(gunler[i]['ciro'])}\nKâr ${para(gunler[i]['kar'])}',
                  child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
                    Stack(alignment: Alignment.bottomCenter, children: [
                      Container(
                        width: cubuk,
                        height: enBuyuk <= 0 ? 2 : (140 * sayi(gunler[i]['ciro']) / enBuyuk).clamp(2.0, 140.0),
                        decoration: BoxDecoration(
                          color: r.ana.withValues(alpha: 0.25),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      Container(
                        width: cubuk,
                        height: enBuyuk <= 0
                            ? 0
                            : (140 * sayi(gunler[i]['kar']).clamp(0, double.infinity) / enBuyuk).clamp(0.0, 140.0),
                        decoration: BoxDecoration(color: r.ana, borderRadius: BorderRadius.circular(4)),
                      ),
                    ]),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 16,
                      child: i % etiketAdimi == 0
                          ? Text(
                              '${tarihOku(gunler[i]['gun'])?.day ?? ''}',
                              style: context.yazi.labelSmall,
                            )
                          : null,
                    ),
                  ]),
                ),
              ),
          ],
        );
      }),
    );
  }
}
