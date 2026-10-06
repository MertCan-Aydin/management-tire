import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../satis/satislar_sayfasi.dart';

class MusterilerSayfasi extends StatelessWidget {
  const MusterilerSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.person_2,
        liste: (ctx, sec, seciliId) => _MusteriListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, m) => MusteriDetay(musteri: m),
      );
}

class _MusteriListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _MusteriListesi({required this.sec, this.seciliId});

  @override
  State<_MusteriListesi> createState() => _MusteriListesiState();
}

class _MusteriListesiState extends State<_MusteriListesi> with VeriYukleyici<_MusteriListesi, List<Json>> {
  String _arama = '';

  @override
  Future<List<Json>> getir() => MusteriApi.liste(arama: _arama);

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      ListeUstu(
        baslik: 'Müşteriler',
        eylemler: [
          UstDugme(
            ikon: CupertinoIcons.add,
            ipucu: 'Yeni müşteri',
            onTap: () => musteriFormuAc(context),
          ),
        ],
        arama: AramaKutusu(
          ipucu: 'Ad, telefon veya plaka',
          degisti: (v) {
            _arama = v;
            yenile();
          },
        ),
      ),
      Expanded(
        child: durum((liste) {
          if (liste.isEmpty) {
            return BosDurum(
              ikon: CupertinoIcons.person_2,
              baslik: _arama.isEmpty ? 'Henüz müşteri yok' : 'Sonuç bulunamadı',
              eylem: _arama.isEmpty
                  ? CupertinoButton.filled(onPressed: () => musteriFormuAc(context), child: const Text('Müşteri Ekle'))
                  : null,
            );
          }
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Grup(
                girinti: 68,
                altNot: '${liste.length} müşteri',
                children: [
                  for (final m in liste)
                    Satir(
                      onde: _Avatar(m['ad_soyad'] as String? ?? ''),
                      baslik: m['ad_soyad'] as String? ?? '',
                      alt: [m['telefon'], m['arac_plakasi']].where((e) => e != null && '$e'.isNotEmpty).join('  ·  '),
                      secili: widget.seciliId == m['id'],
                      onTap: () => widget.sec(m),
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

class _Avatar extends StatelessWidget {
  final String ad;
  const _Avatar(this.ad);

  @override
  Widget build(BuildContext context) => CircleAvatar(
        radius: 20,
        backgroundColor: context.renk.ucuncul,
        child: Text(basHarfler(ad), style: const TextStyle(fontFamily: kFont, color: Colors.white, fontWeight: FontWeight.w600)),
      );
}

// ─── Detay ──────────────────────────────────────────────────────────────────

class MusteriDetay extends StatefulWidget {
  final Json musteri;
  const MusteriDetay({required this.musteri, super.key});

  @override
  State<MusteriDetay> createState() => _MusteriDetayState();
}

class _MusteriDetayState extends State<MusteriDetay> with VeriYukleyici<MusteriDetay, (Json, List<Json>)> {
  int get _id => tamSayi(widget.musteri['id']);

  @override
  (Json, List<Json>)? get ilkVeri => null;

  @override
  Future<(Json, List<Json>)> getir() async {
    final r = await Future.wait([MusteriApi.getir(_id), SatisApi.liste(musteriId: _id, limit: 50)]);
    return (r[0] as Json, r[1] as List<Json>);
  }

  Future<void> _sil(Json m) async {
    final onay = await onayla(context,
        baslik: 'Müşteriyi Sil', mesaj: '"${m['ad_soyad']}" silinecek. Bu işlem geri alınamaz.', onayMetni: 'Sil', yikici: true);
    if (!onay || !mounted) return;
    try {
      await MusteriApi.sil(_id);
      if (!mounted) return;
      bildir(context, 'Müşteri silindi');
      DetayKapsami.of(context).kapat();
      veriDegisti();
    } catch (e) {
      if (mounted) bildir(context, hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final m = veri?.$1 ?? widget.musteri;
    final satislar = veri?.$2;
    final r = context.renk;
    final toplam = satislar
        ?.where((s) => !dogruMu(s['iptal_mi']))
        .fold<double>(0, (t, s) => t + sayi(s['toplam_tutar']) - sayi(s['indirim']));

    return DetayIskeleti(
      baslik: m['ad_soyad'] as String? ?? 'Müşteri',
      yenile: yenile,
      eylemler: [UstDugme(metin: 'Düzenle', onTap: () => musteriFormuAc(context, mevcut: m))],
      children: [
        DetayKafa(
          harfler: basHarfler(m['ad_soyad'] as String? ?? ''),
          renk: const Color(0xFF8E8E93),
          baslik: m['ad_soyad'] as String? ?? '',
          alt: m['arac_plakasi'] as String?,
        ),
        Grup(children: [
          BilgiSatiri('Telefon', m['telefon'] as String?, degerRengi: r.ana),
          BilgiSatiri('Araç', m['arac_markasi'] as String?),
          BilgiSatiri('Plaka', m['arac_plakasi'] as String?),
        ]),
        if ((m['notlar'] as String?)?.isNotEmpty == true)
          Grup(baslik: 'Notlar', children: [
            Padding(padding: const EdgeInsets.all(16), child: Text(m['notlar'] as String, style: context.yazi.bodyLarge)),
          ]),
        if (satislar == null)
          const Padding(padding: EdgeInsets.all(24), child: Yukleniyor())
        else
          Grup(
            baslik: 'Satış Geçmişi',
            altNot: satislar.isEmpty ? null : '${satislar.length} satış · Toplam ${para(toplam)}',
            children: satislar.isEmpty
                ? [const BilgiSatiri('Henüz satış yok', '')]
                : [
                    for (final s in satislar)
                      Satir(
                        baslik: para(sayi(s['toplam_tutar']) - sayi(s['indirim'])),
                        alt: '${tarihSaat(s['tarih'])} · ${s['odeme_yontemi'] ?? ''}',
                        sag: dogruMu(s['iptal_mi']) ? Rozet('İptal', r.tehlike) : null,
                        onTap: () => satisDetayAc(context, s),
                      ),
                  ],
          ),
        Grup(children: [EylemSatiri('Müşteriyi Sil', yikici: true, onTap: () => _sil(m))]),
      ],
    );
  }
}

// ─── Form ───────────────────────────────────────────────────────────────────

/// Yeni müşteri ekler ya da [mevcut]'u düzenler. Eklenen müşteriyi döner.
Future<Json?> musteriFormuAc(BuildContext context, {Json? mevcut}) => formAc<Json>(context, (_) => _MusteriFormu(mevcut: mevcut));

class _MusteriFormu extends StatefulWidget {
  final Json? mevcut;
  const _MusteriFormu({this.mevcut});

  @override
  State<_MusteriFormu> createState() => _MusteriFormuState();
}

class _MusteriFormuState extends State<_MusteriFormu> {
  late final _ad = TextEditingController(text: widget.mevcut?['ad_soyad'] as String? ?? '');
  late final _tel = TextEditingController(text: widget.mevcut?['telefon'] as String? ?? '');
  late final _marka = TextEditingController(text: widget.mevcut?['arac_markasi'] as String? ?? '');
  late final _plaka = TextEditingController(text: widget.mevcut?['arac_plakasi'] as String? ?? '');
  late final _not = TextEditingController(text: widget.mevcut?['notlar'] as String? ?? '');
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    for (final c in [_ad, _tel, _marka, _plaka, _not]) {
      c.dispose();
    }
    super.dispose();
  }

  String? _bosNull(TextEditingController c) => c.text.trim().isEmpty ? null : c.text.trim();

  Future<void> _kaydet() async {
    if (_ad.text.trim().isEmpty || _tel.text.trim().isEmpty) {
      setState(() => _hata = 'Ad soyad ve telefon zorunludur');
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    final v = <String, dynamic>{
      'ad_soyad': _ad.text.trim(),
      'telefon': _tel.text.trim(),
      'arac_markasi': _bosNull(_marka),
      'arac_plakasi': _bosNull(_plaka)?.toUpperCase(),
      'notlar': _bosNull(_not),
    };
    try {
      if (widget.mevcut == null) {
        v['id'] = await MusteriApi.ekle(v);
      } else {
        v['id'] = widget.mevcut!['id'];
        await MusteriApi.guncelle(tamSayi(widget.mevcut!['id']), v);
      }
      veriDegisti();
      if (!mounted) return;
      bildir(context, widget.mevcut == null ? 'Müşteri eklendi' : 'Değişiklikler kaydedildi');
      Navigator.pop(context, v);
    } catch (e) {
      setState(() {
        _hata = hataMesaji(e);
        _kaydediliyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormIskeleti(
      baslik: widget.mevcut == null ? 'Yeni Müşteri' : 'Müşteriyi Düzenle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          MetinSatiri(etiket: 'Ad Soyad', kontrolcu: _ad, ipucu: 'Zorunlu', otomatikOdak: widget.mevcut == null),
          MetinSatiri(etiket: 'Telefon', kontrolcu: _tel, ipucu: 'Zorunlu', klavye: TextInputType.phone),
        ]),
        Grup(baslik: 'Araç', children: [
          MetinSatiri(etiket: 'Marka', kontrolcu: _marka, ipucu: 'Örn. Renault'),
          MetinSatiri(etiket: 'Plaka', kontrolcu: _plaka, ipucu: '34 ABC 123', buyukHarfli: true),
        ]),
        Grup(children: [MetinSatiri(etiket: 'Notlar', kontrolcu: _not, satir: 3)]),
      ],
    );
  }
}
