import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import 'satis_formu.dart';

class SatislarSayfasi extends StatelessWidget {
  const SatislarSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.cart,
        liste: (ctx, sec, seciliId) => _SatisListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, s) => SatisDetay(satis: s),
      );
}

/// Satışın indirim düşülmüş tutarı.
double satisNet(Json s) => sayi(s['toplam_tutar']) - sayi(s['indirim']);

/// Başka bir ekrandan (müşteri detayı vb.) satış detayını tam sayfa açar.
void satisDetayAc(BuildContext context, Json satis) {
  Navigator.of(context).push(CupertinoPageRoute(
    builder: (_) => Scaffold(
      body: SafeArea(
        bottom: false,
        child: Builder(
          builder: (ic) => DetayKapsami(
            tamSayfa: true,
            kapat: () => Navigator.of(ic).maybePop(),
            child: SatisDetay(satis: satis),
          ),
        ),
      ),
    ),
  ));
}

class _SatisListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _SatisListesi({required this.sec, this.seciliId});

  @override
  State<_SatisListesi> createState() => _SatisListesiState();
}

class _SatisListesiState extends State<_SatisListesi> with VeriYukleyici<_SatisListesi, List<Json>> {
  Donem _donem = Donem.bugun;

  @override
  Future<List<Json>> getir() => SatisApi.liste(donem: _donem.parametreler());

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      ListeUstu(
        baslik: 'Satışlar',
        eylemler: [
          CupertinoButton.filled(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            minimumSize: const Size(44, 36),
            onPressed: () => satisFormuAc(context),
            child: const Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(CupertinoIcons.add, size: 18, color: Colors.white),
              SizedBox(width: 4),
              Text('Yeni Satış', style: TextStyle(fontFamily: kFont, fontSize: 15, fontWeight: FontWeight.w600)),
            ]),
          ),
          const SizedBox(width: 6),
        ],
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
              ikon: CupertinoIcons.cart,
              baslik: 'Bu dönemde satış yok',
              eylem: CupertinoButton.filled(onPressed: () => satisFormuAc(context), child: const Text('Yeni Satış')),
            );
          }
          final aktif = liste.where((s) => !dogruMu(s['iptal_mi']));
          final ciro = aktif.fold<double>(0, (t, s) => t + satisNet(s));
          final kar = aktif.fold<double>(0, (t, s) => t + sayi(s['kar']));
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
                child: Row(children: [
                  Expanded(child: _OzetHapi('Ciro', para(ciro), r.ana)),
                  const SizedBox(width: 10),
                  Expanded(child: _OzetHapi('Kâr', para(kar), r.basari)),
                  const SizedBox(width: 10),
                  Expanded(child: _OzetHapi('Adet', '${aktif.length}', r.turuncu)),
                ]),
              ),
              Grup(
                girinti: 60,
                children: [
                  for (final s in liste)
                    Satir(
                      onde: IkonKutusu(
                        _odemeIkonu(s['odeme_yontemi'] as String?),
                        dogruMu(s['iptal_mi']) ? r.ucuncul : r.basari,
                        boyut: 32,
                      ),
                      baslik: s['musteri_adi'] as String? ?? '',
                      alt: '${tarihSaat(s['tarih'])}  ·  ${s['odeme_yontemi'] ?? ''}',
                      sag: dogruMu(s['iptal_mi'])
                          ? Rozet('İptal', r.tehlike)
                          : Text(para(satisNet(s)), style: context.yazi.titleSmall),
                      secili: widget.seciliId == s['id'],
                      onTap: () => widget.sec(s),
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

IconData _odemeIkonu(String? y) => switch (y) {
      'Kredi Kartı' => CupertinoIcons.creditcard_fill,
      'Havale' => CupertinoIcons.arrow_right_arrow_left,
      _ => CupertinoIcons.money_dollar,
    };

class _OzetHapi extends StatelessWidget {
  final String etiket;
  final String deger;
  final Color renk;
  const _OzetHapi(this.etiket, this.deger, this.renk);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(color: context.renk.kart, borderRadius: BorderRadius.circular(12)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(etiket, style: context.yazi.labelMedium),
          const SizedBox(height: 2),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(deger, style: context.yazi.titleMedium?.copyWith(color: renk)),
          ),
        ]),
      );
}

// ─── Detay ──────────────────────────────────────────────────────────────────

class SatisDetay extends StatefulWidget {
  final Json satis;
  const SatisDetay({required this.satis, super.key});

  @override
  State<SatisDetay> createState() => _SatisDetayState();
}

class _SatisDetayState extends State<SatisDetay> with VeriYukleyici<SatisDetay, Json> {
  int get _id => tamSayi(widget.satis['id']);

  @override
  Future<Json> getir() => SatisApi.getir(_id);

  Future<void> _iptal() async {
    // null → vazgeçildi, true → stoğa geri ekle, false → stoğa dokunma
    final stogaEkle = await showCupertinoDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => CupertinoAlertDialog(
        title: const Text('Satışı İptal Et'),
        content: const Padding(
          padding: EdgeInsets.only(top: 4),
          child: Text('Satış ciro ve kâr hesaplarından çıkarılacak. Bu işlem geri alınamaz.\n\n'
              'Ürünler kullanılmadıysa stoğa geri ekleyin. Takıldıysa veya satılamayacak durumdaysa eklemeyin.'),
        ),
        actions: [
          CupertinoDialogAction(
            isDefaultAction: true,
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('İptal Et, Stoğa Geri Ekle'),
          ),
          CupertinoDialogAction(
            isDestructiveAction: true,
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('İptal Et, Stoğa Ekleme'),
          ),
          CupertinoDialogAction(onPressed: () => Navigator.pop(ctx), child: const Text('Vazgeç')),
        ],
      ),
    );
    if (stogaEkle == null || !mounted) return;
    try {
      await SatisApi.iptal(_id, stogaEkle: stogaEkle);
      veriDegisti();
      if (mounted) bildir(context, 'Satış iptal edildi');
    } catch (e) {
      if (mounted) bildir(context, hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = {...widget.satis, ...?veri};
    final kalemler = (veri?['kalemler'] as List?)?.cast<Json>();
    final iptal = dogruMu(s['iptal_mi']);
    final r = context.renk;

    return DetayIskeleti(
      baslik: 'Satış #${s['id']}',
      yenile: yenile,
      children: [
        DetayKafa(
          ikon: CupertinoIcons.cart_fill,
          renk: iptal ? r.ikincil : r.basari,
          baslik: s['musteri_adi'] as String? ?? '',
          alt: tarihSaat(s['tarih']),
          buyukDeger: para(satisNet(s)),
          rozet: iptal ? Rozet('İptal Edildi', r.tehlike) : null,
        ),
        Grup(children: [
          BilgiSatiri('Müşteri', s['musteri_adi'] as String?),
          BilgiSatiri('Plaka', s['arac_plakasi'] as String?),
          BilgiSatiri('Ödeme', s['odeme_yontemi'] as String?),
          BilgiSatiri('Tarih', tarihSaat(s['tarih'])),
        ]),
        if (kalemler == null && hata == null)
          const Padding(padding: EdgeInsets.all(24), child: Yukleniyor())
        else if (kalemler != null)
          Grup(baslik: 'Ürünler', children: [
            for (final k in kalemler)
              Satir(
                baslik: k['urun_adi_anlik'] as String? ?? '',
                alt: '${tamSayi(k['miktar'])} × ${para(k['birim_fiyat'])}',
                sag:
                    Text(para(k['toplam_fiyat'] ?? tamSayi(k['miktar']) * sayi(k['birim_fiyat'])), style: context.yazi.bodyLarge),
              ),
          ]),
        Grup(baslik: 'Özet', children: [
          BilgiSatiri('Ara Toplam', para(s['toplam_tutar'])),
          BilgiSatiri('İndirim', para(s['indirim'])),
          BilgiSatiri('Net Tutar', para(satisNet(s)), kalin: true, degerRengi: r.metin),
          if (s['toplam_maliyet'] != null) BilgiSatiri('Maliyet', para(s['toplam_maliyet'])),
          BilgiSatiri('Kâr', para(s['kar']), degerRengi: r.basari, kalin: true),
        ]),
        if (!iptal) Grup(children: [EylemSatiri('Satışı İptal Et', yikici: true, onTap: _iptal)]),
      ],
    );
  }
}
