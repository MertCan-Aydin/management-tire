import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/tema.dart';
import '../barkod/barkod_screen.dart';
import '../tedarikciler/tedarikciler_sayfasi.dart';
import '../urunler/urun_secici.dart';

Future<void> alimFormuAc(BuildContext context, {Json? tedarikci}) => Navigator.of(context).push(CupertinoPageRoute(
      fullscreenDialog: true,
      builder: (_) => Scaffold(body: SafeArea(child: _AlimFormu(tedarikci: tedarikci))),
    ));

class _Kalem {
  final int urunId;
  final String ad;
  final String alt;
  int miktar;
  double birimFiyat;

  _Kalem({required this.urunId, required this.ad, this.alt = '', this.miktar = 1, this.birimFiyat = 0});

  double get toplam => miktar * birimFiyat;

  Json json() => {'urun_id': urunId, 'urun_adi_anlik': ad, 'miktar': miktar, 'birim_fiyat': birimFiyat};
}

class _AlimFormu extends StatefulWidget {
  final Json? tedarikci;
  const _AlimFormu({this.tedarikci});

  @override
  State<_AlimFormu> createState() => _AlimFormuState();
}

class _AlimFormuState extends State<_AlimFormu> {
  late Json? _tedarikci = widget.tedarikci;
  final List<_Kalem> _kalemler = [];
  bool _kaydediliyor = false;
  String? _hata;

  double get _toplam => _kalemler.fold(0, (t, k) => t + k.toplam);

  void _urunEkle(Json u) {
    final id = tamSayi(u['id']);
    final mevcut = _kalemler.where((k) => k.urunId == id).firstOrNull;
    setState(() {
      if (mevcut != null) {
        mevcut.miktar++;
      } else {
        _kalemler.add(_Kalem(urunId: id, ad: u['ad'] as String? ?? '', alt: urunAlt(u), birimFiyat: sayi(u['maliyet_fiyati'])));
      }
    });
    HapticFeedback.selectionClick();
  }

  Future<void> _qrOkut() async {
    final s = await Navigator.of(context).push<Json>(
      CupertinoPageRoute(builder: (_) => const BarkodScreen(eprelDestekli: true)),
    );
    if (s == null || !mounted) return;
    if (s['tip'] == 'eprel') {
      await _eprelEkle(s);
    } else {
      _urunEkle(s);
    }
  }

  Future<void> _eprelEkle(Json eprel) async {
    final kalem = await formAc<_Kalem>(context, (_) => _EprelFormu(eprel: eprel));
    if (kalem == null || !mounted) return;
    setState(() => _kalemler.add(kalem));
  }

  Future<void> _urunListedenSec() async {
    final u = await urunSec(context, maliyetGoster: true);
    if (u != null && mounted) _urunEkle(u);
  }

  Future<void> _tedarikciSec() async {
    final t = await aramaliSec(
      context,
      baslik: 'Tedarikçi Seç',
      yerelFiltre: true,
      yukle: (_) => TedarikciApi.liste(),
      satirBaslik: (t) => t['ad'] as String? ?? '',
      satirAlt: (t) => t['iletisim_bilgisi'] as String?,
      satirSag: (t) => sayi(t['guncel_borc']) > 0 ? para(t['guncel_borc']) : null,
      yeniEkle: (ctx) => tedarikciFormuAc(ctx),
    );
    if (t != null) setState(() => _tedarikci = t);
  }

  Future<void> _fiyatDegistir(_Kalem k) async {
    final v = await sayiSor(context, baslik: 'Birim Alış Fiyatı', mesaj: k.ad, baslangic: k.birimFiyat);
    if (v != null && v >= 0) setState(() => k.birimFiyat = v);
  }

  Future<void> _vazgec() async {
    if (_kalemler.isEmpty) {
      Navigator.pop(context);
      return;
    }
    final onay = await onayla(context,
        baslik: 'Alımdan vazgeçilsin mi?', mesaj: 'Eklenen ürünler silinecek.', onayMetni: 'Vazgeç', yikici: true);
    if (onay && mounted) Navigator.pop(context);
  }

  Future<void> _kaydet() async {
    String? hata;
    if (_tedarikci == null) {
      hata = 'Tedarikçi seçin';
    } else if (_kalemler.isEmpty) {
      hata = 'En az bir ürün ekleyin';
    } else if (_kalemler.any((k) => k.birimFiyat <= 0)) {
      hata = 'Alış fiyatı girilmemiş ürünler var';
    }
    if (hata != null) {
      setState(() => _hata = hata);
      HapticFeedback.heavyImpact();
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      await AlimApi.ekle({
        'tedarikci_id': _tedarikci!['id'],
        'kalemler': [for (final k in _kalemler) k.json()],
      });
      veriDegisti();
      if (!mounted) return;
      bildir(context, 'Alım kaydedildi · ${para(_toplam)}');
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
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && !_kaydediliyor) _vazgec();
      },
      child: LayoutBuilder(builder: (context, c) {
        final genis = c.maxWidth >= 900;
        final baslik = PanelBaslik(
          'Yeni Alım',
          solEylem: UstDugme(metin: 'Vazgeç', onTap: _kaydediliyor ? null : _vazgec),
          eylemler: [UstDugme(metin: 'Kaydet', kalin: true, yukleniyor: _kaydediliyor, onTap: _kaydet)],
        );
        final form = ListView(padding: const EdgeInsets.only(top: 16), children: _gruplar(dar: !genis));
        final alt = _ToplamCubugu(toplam: _toplam, adet: _kalemler.fold(0, (t, k) => t + k.miktar));
        if (!genis) {
          return Column(children: [baslik, Expanded(child: form), alt]);
        }
        return Column(children: [
          baslik,
          Expanded(
            child: Row(children: [
              Expanded(
                child: UrunAramaPaneli(
                  maliyetGoster: true,
                  sec: _urunEkle,
                  qrOkut: _qrOkut,
                  qrMetni: 'QR / EPREL',
                  sepet: {for (final k in _kalemler) k.urunId: k.miktar},
                ),
              ),
              VerticalDivider(width: 1, thickness: 0, color: context.renk.ayrac),
              SizedBox(
                width: (c.maxWidth * 0.36).clamp(380.0, 460.0),
                child: Column(children: [Expanded(child: form), alt]),
              ),
            ]),
          ),
        ]);
      }),
    );
  }

  List<Widget> _gruplar({required bool dar}) {
    final r = context.renk;
    return [
      if (_hata != null) HataKutusu(_hata!),
      Grup(baslik: 'Tedarikçi', children: [
        if (_tedarikci == null)
          EylemSatiri('Tedarikçi Seç', ikon: CupertinoIcons.building_2_fill, onTap: _tedarikciSec)
        else
          Satir(
            baslik: _tedarikci!['ad'] as String? ?? '',
            alt: sayi(_tedarikci!['guncel_borc']) > 0 ? 'Mevcut borç: ${para(_tedarikci!['guncel_borc'])}' : null,
            sag: Text('Değiştir', style: context.yazi.bodyMedium?.copyWith(color: r.ana)),
            okIsareti: false,
            onTap: _tedarikciSec,
          ),
      ]),
      Grup(
        baslik: 'Ürünler',
        altNot: _kalemler.isEmpty ? null : 'Alış fiyatını değiştirmek için fiyata dokunun',
        children: [
          if (_kalemler.isEmpty && !dar)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text('Soldan ürün seçin ya da etiket QR\'ını okutun',
                  textAlign: TextAlign.center, style: context.yazi.bodyMedium?.copyWith(color: r.ikincil)),
            ),
          for (final k in _kalemler)
            Dismissible(
              key: ObjectKey(k),
              direction: DismissDirection.endToStart,
              background: Container(
                color: r.tehlike,
                alignment: Alignment.centerRight,
                padding: const EdgeInsets.only(right: 20),
                child: const Icon(CupertinoIcons.trash, color: Colors.white),
              ),
              onDismissed: (_) => setState(() => _kalemler.remove(k)),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 10, 8, 10),
                child: Row(children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(k.ad, maxLines: 2, overflow: TextOverflow.ellipsis, style: context.yazi.bodyLarge),
                      const SizedBox(height: 2),
                      GestureDetector(
                        onTap: () => _fiyatDegistir(k),
                        child: Text(
                          k.birimFiyat > 0 ? '${para(k.birimFiyat)}  ·  ${para(k.toplam)}' : 'Alış fiyatı girin',
                          style: context.yazi.bodyMedium?.copyWith(color: k.birimFiyat > 0 ? r.ana : r.tehlike),
                        ),
                      ),
                    ]),
                  ),
                  const SizedBox(width: 8),
                  Adimlayici(deger: k.miktar, degisti: (v) => setState(() => k.miktar = v)),
                  UstDugme(
                      ikon: CupertinoIcons.trash,
                      renk: r.tehlike,
                      ipucu: 'Kaldır',
                      onTap: () => setState(() => _kalemler.remove(k))),
                ]),
              ),
            ),
          if (dar) ...[
            EylemSatiri('Listeden Ürün Ekle', ikon: CupertinoIcons.add_circled, onTap: _urunListedenSec),
            EylemSatiri('QR / EPREL Etiketi Okut', ikon: CupertinoIcons.qrcode_viewfinder, onTap: _qrOkut),
          ],
        ],
      ),
    ];
  }
}

class _ToplamCubugu extends StatelessWidget {
  final double toplam;
  final int adet;
  const _ToplamCubugu({required this.toplam, required this.adet});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 16 + MediaQuery.paddingOf(context).bottom),
      decoration: BoxDecoration(color: r.kart, border: Border(top: BorderSide(color: r.ayrac, width: 0))),
      child: Row(children: [
        Text('Toplam', style: context.yazi.titleMedium),
        const SizedBox(width: 8),
        if (adet > 0) Text('$adet adet', style: context.yazi.bodySmall),
        const Spacer(),
        Text(para(toplam), style: context.yazi.headlineSmall),
      ]),
    );
  }
}

/// EPREL etiketinden gelen lastiği onaylatıp ürün olarak kaydeder.
class _EprelFormu extends StatefulWidget {
  final Json eprel;
  const _EprelFormu({required this.eprel});

  @override
  State<_EprelFormu> createState() => _EprelFormuState();
}

class _EprelFormuState extends State<_EprelFormu> {
  late final _marka = TextEditingController(text: widget.eprel['marka'] as String? ?? '');
  late final _model = TextEditingController(text: widget.eprel['model'] as String? ?? '');
  late final _ebat = TextEditingController(text: widget.eprel['ebat'] as String? ?? '');
  late String _mevsim = widget.eprel['mevsim'] as String? ?? 'Yaz';
  final _alis = TextEditingController();
  final _satis = TextEditingController();
  int _miktar = 4;
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    for (final c in [_marka, _model, _ebat, _alis, _satis]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _kaydet() async {
    final alis = sayiOku(_alis.text) ?? 0;
    if (_marka.text.trim().isEmpty || _model.text.trim().isEmpty || _ebat.text.trim().isEmpty) {
      setState(() => _hata = 'Marka, model ve ebat zorunludur');
      return;
    }
    if (alis <= 0) {
      setState(() => _hata = 'Alış fiyatı girin');
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      final d = await UrunApi.eprelKaydet({
        'eprel_no': widget.eprel['eprel_no'],
        'marka': _marka.text.trim(),
        'model': _model.text.trim(),
        'ebat': _ebat.text.trim(),
        'mevsim': _mevsim,
        'satis_fiyati': sayiOku(_satis.text) ?? 0,
        'maliyet_fiyati': alis,
      });
      if (!mounted) return;
      if (dogruMu(d['yeni_mi'])) bildir(context, 'Yeni ürün oluşturuldu: ${d['urun_ad']}');
      Navigator.pop(
        context,
        _Kalem(
          urunId: tamSayi(d['urun_id']),
          ad: d['urun_ad'] as String? ?? '',
          alt: '${_ebat.text.trim()}  ·  $_mevsim',
          miktar: _miktar,
          birimFiyat: alis,
        ),
      );
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
      baslik: 'EPREL Lastik',
      kaydetMetni: 'Ekle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(
          baslik: 'Etiket Bilgisi',
          altNot: 'EPREL kayıt no: ${widget.eprel['eprel_no']}. Ürün yoksa otomatik oluşturulur.',
          children: [
            MetinSatiri(etiket: 'Marka', kontrolcu: _marka),
            MetinSatiri(etiket: 'Model', kontrolcu: _model),
            MetinSatiri(etiket: 'Ebat', kontrolcu: _ebat),
            SegmentSatiri<String>(
              etiket: 'Mevsim',
              secenekler: const {'Yaz': 'Yaz', 'Kış': 'Kış', 'Dört Mevsim': '4 Mevsim'},
              secili: _mevsim,
              degisti: (v) => setState(() => _mevsim = v),
            ),
          ],
        ),
        Grup(baslik: 'Alım', children: [
          MetinSatiri.para(etiket: 'Alış Fiyatı', kontrolcu: _alis, otomatikOdak: true),
          MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satis),
          AdimSatiri(etiket: 'Miktar', deger: _miktar, degisti: (v) => setState(() => _miktar = v)),
        ]),
      ],
    );
  }
}
