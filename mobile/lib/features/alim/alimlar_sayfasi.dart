import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import 'alim_formu.dart';

class AlimlarSayfasi extends StatelessWidget {
  const AlimlarSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.arrow_down_doc,
        liste: (ctx, sec, seciliId) => _AlimListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, a) => AlimDetay(alim: a),
      );
}

/// Başka ekrandan (tedarikçi detayı) alım detayını tam sayfa açar.
void alimDetayAc(BuildContext context, Json alim) {
  Navigator.of(context).push(CupertinoPageRoute(
    builder: (_) => Scaffold(
      body: SafeArea(
        bottom: false,
        child: Builder(
          builder: (ic) => DetayKapsami(
            tamSayfa: true,
            kapat: () => Navigator.of(ic).maybePop(),
            child: AlimDetay(alim: alim),
          ),
        ),
      ),
    ),
  ));
}

class _AlimListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _AlimListesi({required this.sec, this.seciliId});

  @override
  State<_AlimListesi> createState() => _AlimListesiState();
}

class _AlimListesiState extends State<_AlimListesi> with VeriYukleyici<_AlimListesi, List<Json>> {
  Donem _donem = Donem.ay;

  @override
  Future<List<Json>> getir() => AlimApi.liste(donem: _donem.parametreler());

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      ListeUstu(
        baslik: 'Alımlar',
        eylemler: [UstDugme(ikon: CupertinoIcons.add, ipucu: 'Yeni alım', onTap: () => alimFormuAc(context))],
        filtre: SizedBox(
          width: double.infinity,
          child: SegmentSecici<Donem>(
            secenekler: {for (final d in Donem.values) d: d.etiket},
            secili: _donem,
            degisti: (d) {
              _donem = d;
              yenile();
            },
          ),
        ),
      ),
      Expanded(
        child: durum((liste) {
          if (liste.isEmpty) {
            return BosDurum(
              ikon: CupertinoIcons.arrow_down_doc,
              baslik: 'Bu dönemde alım yok',
              eylem: CupertinoButton.filled(onPressed: () => alimFormuAc(context), child: const Text('Yeni Alım')),
            );
          }
          final toplam = liste.where((a) => !dogruMu(a['iptal_mi'])).fold<double>(0, (t, a) => t + sayi(a['toplam_tutar']));
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Grup(
                girinti: 60,
                altNot: '${liste.length} alım · Toplam ${para(toplam)}',
                children: [
                  for (final a in liste)
                    Satir(
                      onde: IkonKutusu(CupertinoIcons.arrow_down_doc_fill, dogruMu(a['iptal_mi']) ? r.ucuncul : r.mor, boyut: 32),
                      baslik: a['tedarikci_adi'] as String? ?? '',
                      alt: tarihSaat(a['tarih']),
                      sag: dogruMu(a['iptal_mi'])
                          ? Rozet('İptal', r.tehlike)
                          : Text(para(a['toplam_tutar']), style: context.yazi.titleSmall),
                      secili: widget.seciliId == a['id'],
                      onTap: () => widget.sec(a),
                    ),
                ],
              ),
            ],
          );
        }),
      ),
    ]);
  }
}

class AlimDetay extends StatefulWidget {
  final Json alim;
  const AlimDetay({required this.alim, super.key});

  @override
  State<AlimDetay> createState() => _AlimDetayState();
}

class _AlimDetayState extends State<AlimDetay> with VeriYukleyici<AlimDetay, Json> {
  @override
  Future<Json> getir() => AlimApi.getir(tamSayi(widget.alim['id']));

  @override
  Widget build(BuildContext context) {
    final a = {...widget.alim, ...?veri};
    final kalemler = (veri?['kalemler'] as List?)?.cast<Json>();
    final r = context.renk;
    final iptal = dogruMu(a['iptal_mi']);
    return DetayIskeleti(
      baslik: 'Alım #${a['id']}',
      yenile: yenile,
      children: [
        DetayKafa(
          ikon: CupertinoIcons.arrow_down_doc_fill,
          renk: iptal ? r.ikincil : r.mor,
          baslik: a['tedarikci_adi'] as String? ?? '',
          alt: tarihSaat(a['tarih']),
          buyukDeger: para(a['toplam_tutar']),
          rozet: iptal ? Rozet('İptal Edildi', r.tehlike) : null,
        ),
        if (kalemler == null && hata == null)
          const Padding(padding: EdgeInsets.all(24), child: Yukleniyor())
        else if (kalemler != null)
          Grup(
            baslik: 'Ürünler',
            altNot: '${kalemler.fold<int>(0, (t, k) => t + tamSayi(k['miktar']))} adet ürün stoğa eklendi',
            children: [
              for (final k in kalemler)
                Satir(
                  baslik: k['urun_adi_anlik'] as String? ?? '',
                  alt: '${tamSayi(k['miktar'])} × ${para(k['birim_fiyat'])}',
                  sag: Text(para(k['toplam_fiyat'] ?? tamSayi(k['miktar']) * sayi(k['birim_fiyat'])),
                      style: context.yazi.bodyLarge),
                ),
            ],
          ),
        Grup(children: [
          BilgiSatiri('Tedarikçi', a['tedarikci_adi'] as String?),
          BilgiSatiri('Tarih', tarihSaat(a['tarih'])),
          BilgiSatiri('Toplam', para(a['toplam_tutar']), kalin: true, degerRengi: r.metin),
        ]),
      ],
    );
  }
}
