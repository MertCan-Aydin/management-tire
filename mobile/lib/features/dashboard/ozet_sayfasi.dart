import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../alim/alim_formu.dart';
import '../giderler/giderler_sayfasi.dart';
import '../lastik_oteli/lastik_oteli_sayfasi.dart';
import '../satis/satis_formu.dart';
import '../satis/satislar_sayfasi.dart';

class OzetSayfasi extends StatefulWidget {
  const OzetSayfasi({super.key});

  @override
  State<OzetSayfasi> createState() => _OzetSayfasiState();
}

typedef _OzetVeri = ({Json ozet, List<Json> sonSatislar});

class _OzetSayfasiState extends State<OzetSayfasi> with VeriYukleyici<OzetSayfasi, _OzetVeri> {
  @override
  Future<_OzetVeri> getir() async {
    final r = await Future.wait([
      RaporApi.dashboard(),
      SatisApi.liste(donem: Donem.bugun.parametreler(), limit: 8),
    ]);
    return (ozet: r[0] as Json, sonSatislar: r[1] as List<Json>);
  }

  @override
  Widget build(BuildContext context) {
    return durum((v) {
      final d = v.ozet;
      final r = context.renk;

      final hizli = _HizliIslemler(dugmeler: [
        (CupertinoIcons.cart_fill_badge_plus, 'Yeni Satış', r.basari, () => satisFormuAc(context)),
        (CupertinoIcons.arrow_down_doc_fill, 'Yeni Alım', r.mor, () => alimFormuAc(context)),
        (CupertinoIcons.archivebox_fill, 'Otel Kaydı', r.camgobegi, () => otelFormuAc(context)),
        (CupertinoIcons.creditcard_fill, 'Gider Ekle', r.tehlike, () => giderFormuAc(context)),
      ]);

      final istatistikler = [
        _bolum(context, 'Bugün', [
          IstatistikKarti(baslik: 'Ciro', deger: para(d['bugun_ciro']), ikon: CupertinoIcons.chart_bar_fill, renk: r.ana),
          IstatistikKarti(baslik: 'Kâr', deger: para(d['bugun_kar']), ikon: CupertinoIcons.arrow_up_right, renk: r.basari),
          IstatistikKarti(
              baslik: 'Satış Adedi',
              deger: '${tamSayi(d['bugun_satis_adedi'])}',
              ikon: CupertinoIcons.cart_fill,
              renk: r.turuncu),
        ]),
        _bolum(context, 'Bu Ay', [
          IstatistikKarti(baslik: 'Ciro', deger: para(d['bu_ay_ciro']), ikon: CupertinoIcons.calendar, renk: r.ana),
          IstatistikKarti(
              baslik: 'Kâr', deger: para(d['bu_ay_kar']), ikon: CupertinoIcons.money_dollar_circle_fill, renk: r.basari),
        ]),
        _bolum(context, 'Genel Durum', [
          IstatistikKarti(
              baslik: 'Tedarikçi Borcu',
              deger: para(d['toplam_tedarikci_borcu']),
              ikon: CupertinoIcons.exclamationmark_circle_fill,
              renk: r.tehlike),
          IstatistikKarti(
              baslik: 'Stok Değeri', deger: para(d['toplam_stok_degeri']), ikon: CupertinoIcons.cube_box_fill, renk: r.mor),
          IstatistikKarti(
              baslik: 'Müşteri',
              deger: '${tamSayi(d['toplam_musteri'])}',
              ikon: CupertinoIcons.person_2_fill,
              renk: const Color(0xFF5856D6)),
        ]),
      ];

      final sonSatislar = Grup(
        baslik: 'Bugünün Satışları',
        dis: EdgeInsets.zero,
        children: v.sonSatislar.isEmpty
            ? [
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Text('Bugün henüz satış yok',
                      textAlign: TextAlign.center, style: context.yazi.bodyMedium?.copyWith(color: r.ikincil)),
                ),
              ]
            : [
                for (final s in v.sonSatislar)
                  Satir(
                    baslik: s['musteri_adi'] as String? ?? '',
                    alt: '${tarihSaat(s['tarih']).split(' ').last}  ·  ${s['odeme_yontemi'] ?? ''}',
                    sag: Text(para(satisNet(s)), style: context.yazi.titleSmall),
                    onTap: () => satisDetayAc(context, s),
                  ),
              ],
      );

      return LayoutBuilder(builder: (context, c) {
        final genis = c.maxWidth >= 980;
        return YenilenebilirListe(
          yenile: yenile,
          padding: const EdgeInsets.only(bottom: 32),
          children: [
            BuyukBaslik('Özet', altBaslik: uzunTarih(DateTime.now())),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: genis
                  ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [hizli, const SizedBox(height: 20), ...istatistikler],
                        ),
                      ),
                      const SizedBox(width: 20),
                      SizedBox(width: 360, child: sonSatislar),
                    ])
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [hizli, const SizedBox(height: 20), ...istatistikler, sonSatislar],
                    ),
            ),
          ],
        );
      });
    });
  }

  Widget _bolum(BuildContext context, String baslik, List<Widget> kartlar) => Padding(
        padding: const EdgeInsets.only(bottom: 22),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.only(left: 4, bottom: 8),
            child: Text(baslik, style: context.yazi.titleLarge),
          ),
          KartIzgarasi(minGenislik: 200, children: kartlar),
        ]),
      );
}

class _HizliIslemler extends StatelessWidget {
  final List<(IconData, String, Color, VoidCallback)> dugmeler;
  const _HizliIslemler({required this.dugmeler});

  @override
  Widget build(BuildContext context) {
    return KartIzgarasi(
      minGenislik: 150,
      bosluk: 10,
      children: [
        for (final (ikon, metin, renk, onTap) in dugmeler)
          Material(
            color: context.renk.kart,
            borderRadius: BorderRadius.circular(14),
            child: InkWell(
              borderRadius: BorderRadius.circular(14),
              onTap: onTap,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                child: Row(children: [
                  IkonKutusu(ikon, renk, boyut: 36),
                  const SizedBox(width: 12),
                  Expanded(child: Text(metin, style: context.yazi.titleSmall, maxLines: 1, overflow: TextOverflow.ellipsis)),
                ]),
              ),
            ),
          ),
      ],
    );
  }
}
