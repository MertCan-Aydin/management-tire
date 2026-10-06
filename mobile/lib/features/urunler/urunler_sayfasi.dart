import 'package:flutter/cupertino.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../barkod/barkod_screen.dart';
import 'urun_secici.dart';

class UrunlerSayfasi extends StatelessWidget {
  const UrunlerSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.cube_box,
        liste: (ctx, sec, seciliId) => _UrunListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, u) => UrunDetay(urun: u),
      );
}

enum _StokFiltre { tumu, stokta, azalan, tukenen }

class _UrunListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _UrunListesi({required this.sec, this.seciliId});

  @override
  State<_UrunListesi> createState() => _UrunListesiState();
}

class _UrunListesiState extends State<_UrunListesi> with VeriYukleyici<_UrunListesi, List<Json>> {
  String _arama = '';
  _StokFiltre _filtre = _StokFiltre.tumu;
  final _aramaKontrol = TextEditingController();

  static const azalanEsik = 4; // 4'ten az lastik = takım tamamlanamaz

  @override
  void dispose() {
    _aramaKontrol.dispose();
    super.dispose();
  }

  @override
  Future<List<Json>> getir() => UrunApi.liste(arama: _arama);

  List<Json> _filtrele(List<Json> v) => switch (_filtre) {
        _StokFiltre.tumu => v,
        _StokFiltre.stokta => v.where((u) => tamSayi(u['stok']) > 0).toList(),
        _StokFiltre.azalan => v.where((u) => tamSayi(u['stok']) > 0 && tamSayi(u['stok']) < azalanEsik).toList(),
        _StokFiltre.tukenen => v.where((u) => tamSayi(u['stok']) <= 0).toList(),
      };

  Future<void> _barkodOkut() async {
    final u = await Navigator.of(context).push<Json>(CupertinoPageRoute(builder: (_) => const BarkodScreen()));
    if (u == null || !mounted) return;
    widget.sec(u);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      ListeUstu(
        baslik: 'Ürünler',
        eylemler: [
          UstDugme(ikon: CupertinoIcons.qrcode_viewfinder, ipucu: 'Barkod okut', onTap: _barkodOkut),
          UstDugme(ikon: CupertinoIcons.add, ipucu: 'Yeni ürün', onTap: () => urunFormuAc(context)),
        ],
        arama: AramaKutusu(
          kontrolcu: _aramaKontrol,
          ipucu: 'Ürün adı, barkod veya ebat',
          degisti: (v) {
            _arama = v;
            yenile();
          },
        ),
        filtre: SizedBox(
          width: double.infinity,
          child: SegmentSecici<_StokFiltre>(
            secenekler: const {
              _StokFiltre.tumu: 'Tümü',
              _StokFiltre.stokta: 'Stokta',
              _StokFiltre.azalan: 'Azalan',
              _StokFiltre.tukenen: 'Tükenen',
            },
            secili: _filtre,
            degisti: (f) => setState(() => _filtre = f),
          ),
        ),
      ),
      Expanded(
        child: durum((hepsi) {
          final liste = _filtrele(hepsi);
          if (liste.isEmpty) {
            return BosDurum(
              ikon: CupertinoIcons.cube_box,
              baslik: hepsi.isEmpty && _arama.isEmpty ? 'Henüz ürün yok' : 'Ürün bulunamadı',
              eylem: hepsi.isEmpty && _arama.isEmpty
                  ? CupertinoButton.filled(onPressed: () => urunFormuAc(context), child: const Text('Ürün Ekle'))
                  : null,
            );
          }
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Grup(
                girinti: 66,
                altNot: '${liste.length} ürün${hepsi.length >= 200 ? ' (ilk 200 — aramayı daraltın)' : ''}',
                children: [
                  for (final u in liste)
                    Satir(
                      onde: _StokRozeti(tamSayi(u['stok'])),
                      baslik: u['ad'] as String? ?? '',
                      alt: urunAlt(u),
                      sag: Text(para(u['satis_fiyati']), style: context.yazi.titleSmall?.copyWith(color: r.metin)),
                      secili: widget.seciliId == u['id'],
                      onTap: () => widget.sec(u),
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

class _StokRozeti extends StatelessWidget {
  final int stok;
  const _StokRozeti(this.stok);

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final renk = stok <= 0 ? r.tehlike : (stok < _UrunListesiState.azalanEsik ? r.uyari : r.basari);
    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(color: renk.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(10)),
      child: Center(
        child: Text('$stok', style: TextStyle(fontFamily: kFont, fontWeight: FontWeight.w700, fontSize: 15, color: renk)),
      ),
    );
  }
}

// ─── Detay ──────────────────────────────────────────────────────────────────

class UrunDetay extends StatefulWidget {
  final Json urun;
  const UrunDetay({required this.urun, super.key});

  @override
  State<UrunDetay> createState() => _UrunDetayState();
}

class _UrunDetayState extends State<UrunDetay> with VeriYukleyici<UrunDetay, Json> {
  int get _id => tamSayi(widget.urun['id']);

  @override
  Json? get ilkVeri => widget.urun;

  @override
  Future<Json> getir() => UrunApi.getir(_id);

  Future<void> _sil(Json u) async {
    final onay = await onayla(context, baslik: 'Ürünü Sil', mesaj: '"${u['ad']}" silinecek.', onayMetni: 'Sil', yikici: true);
    if (!onay || !mounted) return;
    try {
      await UrunApi.sil(_id);
      if (!mounted) return;
      bildir(context, 'Ürün silindi');
      DetayKapsami.of(context).kapat();
      veriDegisti();
    } catch (e) {
      if (mounted) bildir(context, hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return durum((u) {
      final r = context.renk;
      final stok = tamSayi(u['stok']);
      final satis = sayi(u['satis_fiyati']);
      final maliyet = sayi(u['maliyet_fiyati']);
      final marj = satis > 0 && maliyet > 0 ? (satis - maliyet) / satis * 100 : null;
      return DetayIskeleti(
        baslik: u['ad'] as String? ?? 'Ürün',
        yenile: yenile,
        eylemler: [UstDugme(metin: 'Düzenle', onTap: () => urunFormuAc(context, mevcut: u))],
        children: [
          DetayKafa(
            ikon: CupertinoIcons.cube_box_fill,
            renk: r.turuncu,
            baslik: u['ad'] as String? ?? '',
            alt: urunAlt(u),
            buyukDeger: para(satis),
            rozet: Rozet(stok <= 0 ? 'Stokta yok' : 'Stok: $stok adet', stok <= 0 ? r.tehlike : r.basari),
          ),
          Grup(baslik: 'Ürün', children: [
            BilgiSatiri('Tip', u['tip_adi'] as String?),
            BilgiSatiri('Marka', u['marka_adi'] as String?),
            BilgiSatiri('Model', u['model_adi'] as String?),
            BilgiSatiri('Ebat', u['ebat'] as String?),
            BilgiSatiri('Mevsim', u['mevsim'] as String?),
            BilgiSatiri('Barkod / QR', u['barkod_qr'] as String?),
          ]),
          Grup(baslik: 'Fiyat ve Stok', children: [
            BilgiSatiri('Satış Fiyatı', para(satis), degerRengi: r.metin, kalin: true),
            BilgiSatiri('Maliyet', maliyet > 0 ? para(maliyet) : null),
            BilgiSatiri('Birim Kâr', maliyet > 0 ? para(satis - maliyet) : null, degerRengi: r.basari),
            BilgiSatiri('Kâr Marjı', marj == null ? null : '%${marj.toStringAsFixed(1).replaceAll('.', ',')}'),
            BilgiSatiri('Stok', '$stok adet'),
            BilgiSatiri('Stok Değeri', maliyet > 0 ? para(maliyet * stok) : null),
            BilgiSatiri('Fiziksel Ürün', dogruMu(u['fiziksel_urun_mu'] ?? true) ? 'Evet' : 'Hayır (hizmet)'),
          ]),
          if ((u['aciklama'] as String?)?.isNotEmpty == true)
            Grup(baslik: 'Açıklama', children: [
              Padding(padding: const EdgeInsets.all(16), child: Text(u['aciklama'] as String, style: context.yazi.bodyLarge)),
            ]),
          Grup(children: [EylemSatiri('Ürünü Sil', yikici: true, onTap: () => _sil(u))]),
        ],
      );
    });
  }
}

// ─── Form ───────────────────────────────────────────────────────────────────

Future<void> urunFormuAc(BuildContext context, {Json? mevcut}) => formAc(context, (_) => _UrunFormu(mevcut: mevcut));

class _UrunFormu extends StatefulWidget {
  final Json? mevcut;
  const _UrunFormu({this.mevcut});

  @override
  State<_UrunFormu> createState() => _UrunFormuState();
}

class _UrunFormuState extends State<_UrunFormu> {
  late final Json m = widget.mevcut ?? {};
  late final _barkod = TextEditingController(text: m['barkod_qr'] as String? ?? '');
  late final _ad = TextEditingController(text: m['ad'] as String? ?? '');
  late final _ebat = TextEditingController(text: m['ebat'] as String? ?? '');
  late final _satis = TextEditingController(text: m['satis_fiyati'] == null ? '' : paraSade(m['satis_fiyati']));
  late final _maliyet = TextEditingController(text: sayi(m['maliyet_fiyati']) > 0 ? paraSade(m['maliyet_fiyati']) : '');
  late final _aciklama = TextEditingController(text: m['aciklama'] as String? ?? '');
  late int _stok = tamSayi(m['stok']);
  late bool _fiziksel = dogruMu(m['fiziksel_urun_mu'] ?? true);

  // (id, ad) çiftleri
  late (int, String)? _tip = _cift(m['urun_tipi_id'], m['tip_adi']);
  late (int, String)? _marka = _cift(m['marka_id'], m['marka_adi']);
  late (int, String)? _model = _cift(m['marka_modeli_id'], m['model_adi']);

  bool _kaydediliyor = false;
  String? _hata;

  static (int, String)? _cift(dynamic id, dynamic ad) => id == null ? null : (tamSayi(id), ad?.toString() ?? '#$id');

  @override
  void dispose() {
    for (final c in [_barkod, _ad, _ebat, _satis, _maliyet, _aciklama]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<(int, String)?> _sec(String baslik, Future<List<Json>> Function() yukle, {bool mevsimli = false}) async {
    final s = await aramaliSec(
      context,
      baslik: baslik,
      yerelFiltre: true,
      yukle: (_) => yukle(),
      satirBaslik: (e) => e['ad'] as String? ?? '',
      satirAlt: mevsimli ? (e) => e['mevsim'] as String? : null,
    );
    return s == null ? null : (tamSayi(s['id']), s['ad'] as String? ?? '');
  }

  Future<void> _barkodOkut() async {
    final s = await Navigator.of(context).push<Json>(
      CupertinoPageRoute(builder: (_) => const BarkodScreen(hamDeger: true)),
    );
    final v = s?['rawValue'] as String?;
    if (v != null) setState(() => _barkod.text = v);
  }

  Future<void> _kaydet() async {
    final satis = sayiOku(_satis.text);
    String? hata;
    if (_ad.text.trim().isEmpty) {
      hata = 'Ürün adı zorunludur';
    } else if (_tip == null || _marka == null || _model == null) {
      hata = 'Tip, marka ve model seçin';
    } else if (satis == null || satis <= 0) {
      hata = 'Satış fiyatı 0\'dan büyük olmalıdır';
    }
    if (hata != null) {
      setState(() => _hata = hata);
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    String? bosNull(TextEditingController c) => c.text.trim().isEmpty ? null : c.text.trim();
    final v = <String, dynamic>{
      'barkod_qr': bosNull(_barkod),
      'ad': _ad.text.trim(),
      'ebat': bosNull(_ebat),
      'aciklama': bosNull(_aciklama),
      'satis_fiyati': satis,
      'maliyet_fiyati': sayiOku(_maliyet.text),
      'stok': _stok,
      'fiziksel_urun_mu': _fiziksel,
      'resim_yolu': m['resim_yolu'],
      'urun_tipi_id': _tip!.$1,
      'marka_id': _marka!.$1,
      'marka_modeli_id': _model!.$1,
    };
    try {
      if (widget.mevcut == null) {
        await UrunApi.ekle(v);
      } else {
        await UrunApi.guncelle(tamSayi(m['id']), {...v, 'silindi_mi': false});
      }
      veriDegisti();
      if (!mounted) return;
      bildir(context, widget.mevcut == null ? 'Ürün eklendi' : 'Değişiklikler kaydedildi');
      Navigator.pop(context);
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
      baslik: widget.mevcut == null ? 'Yeni Ürün' : 'Ürünü Düzenle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          MetinSatiri(etiket: 'Ürün Adı', kontrolcu: _ad, ipucu: 'Zorunlu'),
          MetinSatiri(etiket: 'Ebat', kontrolcu: _ebat, ipucu: '205/55 R16', buyukHarfli: true),
          MetinSatiri(
            etiket: 'Barkod / QR',
            kontrolcu: _barkod,
            ipucu: 'İsteğe bağlı',
            sag: UstDugme(ikon: CupertinoIcons.qrcode_viewfinder, ipucu: 'Okut', onTap: _barkodOkut),
          ),
        ]),
        Grup(baslik: 'Sınıflandırma', children: [
          SecimSatiri(
            etiket: 'Tip',
            deger: _tip?.$2,
            onTap: () async {
              final s = await _sec('Ürün Tipi', UrunApi.tipler);
              if (s != null && s.$1 != _tip?.$1) {
                setState(() {
                  _tip = s;
                  _marka = null;
                  _model = null;
                });
              }
            },
          ),
          SecimSatiri(
            etiket: 'Marka',
            deger: _marka?.$2,
            ipucu: _tip == null ? 'Önce tip seçin' : 'Seçin',
            onTap: _tip == null
                ? null
                : () async {
                    final s = await _sec('Marka', () => UrunApi.markalar(_tip!.$1));
                    if (s != null && s.$1 != _marka?.$1) {
                      setState(() {
                        _marka = s;
                        _model = null;
                      });
                    }
                  },
          ),
          SecimSatiri(
            etiket: 'Model',
            deger: _model?.$2,
            ipucu: _marka == null ? 'Önce marka seçin' : 'Seçin',
            onTap: _marka == null
                ? null
                : () async {
                    final s = await _sec('Model', () => UrunApi.modeller(_marka!.$1), mevsimli: true);
                    if (s != null) setState(() => _model = s);
                  },
          ),
        ]),
        Grup(baslik: 'Fiyat ve Stok', children: [
          MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satis),
          MetinSatiri.para(etiket: 'Maliyet', kontrolcu: _maliyet),
          AdimSatiri(etiket: 'Stok', deger: _stok, min: 0, degisti: (v) => setState(() => _stok = v)),
          AnahtarSatiri(etiket: 'Fiziksel ürün (stok düşer)', deger: _fiziksel, degisti: (v) => setState(() => _fiziksel = v)),
        ]),
        Grup(children: [MetinSatiri(etiket: 'Açıklama', kontrolcu: _aciklama, satir: 3)]),
      ],
    );
  }
}
