import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/eprel_client.dart';
import '../../core/format.dart';
import '../../core/lastik_verileri.dart';
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
  bool maliyetBilinmiyor;
  bool guncelBorctan;

  _Kalem({required this.urunId, required this.ad, this.alt = '', this.miktar = 1, this.birimFiyat = 0, this.maliyetBilinmiyor = false, this.guncelBorctan = false});

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

  Future<void> _urunEkle(Json u) async {
    final id = tamSayi(u['id']);
    final mevcut = _kalemler.where((k) => k.urunId == id).firstOrNull;
    if (mevcut != null) {
      setState(() => mevcut.miktar++);
      HapticFeedback.selectionClick();
      return;
    }
    final kalem = await formAc<_Kalem>(context, (_) => _UrunAlimFormu(urun: u));
    if (kalem == null || !mounted) return;
    setState(() => _kalemler.add(kalem));
  }

  Future<void> _qrOkut() async {
    final s = await Navigator.of(context).push<Json>(
      CupertinoPageRoute(builder: (_) => const BarkodScreen(eprelDestekli: true)),
    );
    if (s == null || !mounted) return;
    if (s['tip'] == 'eprel') {
      await _eprelEkle(s);
    } else {
      await _urunEkle(s);
    }
  }

  Future<void> _eprelEkle(Json eprel) async {
    final kalem = await formAc<_Kalem>(context, (_) => _EprelFormu(eprel: eprel));
    if (kalem == null || !mounted) return;
    setState(() => _kalemler.add(kalem));
  }

  Future<void> _eprelNoIleAra() async {
    final ctrl = TextEditingController();
    final no = await showCupertinoDialog<String>(
      context: context,
      builder: (ctx) => CupertinoAlertDialog(
        title: const Text('EPREL No Gir'),
        content: Padding(
          padding: const EdgeInsets.only(top: 12),
          child: CupertinoTextField(controller: ctrl, placeholder: 'Örn: 1020064', keyboardType: TextInputType.number, autofocus: true),
        ),
        actions: [
          CupertinoDialogAction(isDestructiveAction: true, onPressed: () => Navigator.pop(ctx), child: const Text('İptal')),
          CupertinoDialogAction(isDefaultAction: true, onPressed: () => Navigator.pop(ctx, ctrl.text), child: const Text('Ara')),
        ],
      ),
    );
    ctrl.dispose();
    if (no == null || no.trim().isEmpty || !mounted) return;
    try {
      bildir(context, 'EPREL sorgulanıyor…');
      final eprel = await EprelClient.fetchByNo(no.trim());
      if (!mounted) return;
      await _eprelEkle(eprel.toMap());
    } catch (e) {
      if (!mounted) return;
      bildir(context, 'EPREL bulunamadı, bilgileri elle girin');
      await _manuelEtiketGirisi(eprelNo: no.trim());
    }
  }

  Future<void> _manuelEtiketGirisi({String? eprelNo}) async {
    final kalem = await formAc<_Kalem>(context, (_) => _ManuelEtiketFormu(eprelNo: eprelNo));
    if (kalem == null || !mounted) return;
    setState(() => _kalemler.add(kalem));
  }

  Future<void> _urunListedenSec() async {
    final u = await urunSec(context, maliyetGoster: true);
    if (u != null && mounted) await _urunEkle(u);
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
            EylemSatiri('EPREL No ile Ara', ikon: CupertinoIcons.number, onTap: _eprelNoIleAra),
            EylemSatiri('Etiket Bilgilerini Elle Gir', ikon: CupertinoIcons.pencil, onTap: _manuelEtiketGirisi),
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
  bool _maliyetBilinmiyor = false;
  bool _guncelBorctan = false;
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
    if (alis <= 0 && !_maliyetBilinmiyor && !_guncelBorctan) {
      setState(() => _hata = 'Alış fiyatı girin veya bir seçenek işaretleyin');
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
        'maliyet_bilinmiyor': _maliyetBilinmiyor,
        'guncel_borctan': _guncelBorctan,
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
          Opacity(opacity: _maliyetBilinmiyor ? 0.4 : 1, child: AbsorbPointer(absorbing: _maliyetBilinmiyor, child: MetinSatiri.para(etiket: 'Alış Fiyatı', kontrolcu: _alis, otomatikOdak: true))),
          AnahtarSatiri(etiket: 'Alış fiyatı bilinmiyor', deger: _maliyetBilinmiyor, degisti: (v) {
            setState(() {
              _maliyetBilinmiyor = v;
              if (v) _alis.clear();
            });
          }),
          AnahtarSatiri(etiket: 'Güncel borçtan', deger: _guncelBorctan, degisti: (v) => setState(() => _guncelBorctan = v)),
          MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satis),
          AdimSatiri(etiket: 'Miktar', deger: _miktar, degisti: (v) => setState(() => _miktar = v)),
        ]),
      ],
    );
  }
}

/// Listeden seçilen ürün için alım detayları formu.
class _UrunAlimFormu extends StatefulWidget {
  final Json urun;
  const _UrunAlimFormu({required this.urun});

  @override
  State<_UrunAlimFormu> createState() => _UrunAlimFormuState();
}

class _UrunAlimFormuState extends State<_UrunAlimFormu> {
  late final _alis = TextEditingController(text: sayi(widget.urun['maliyet_fiyati']) > 0 ? paraSade(widget.urun['maliyet_fiyati']) : '');
  late final _satis = TextEditingController(text: sayi(widget.urun['satis_fiyati']) > 0 ? paraSade(widget.urun['satis_fiyati']) : '');
  int _miktar = 4;
  bool _maliyetBilinmiyor = false;
  bool _guncelBorctan = false;
  String? _hata;

  @override
  void dispose() {
    _alis.dispose();
    _satis.dispose();
    super.dispose();
  }

  void _kaydet() {
    final alis = sayiOku(_alis.text) ?? 0;
    if (alis <= 0 && !_maliyetBilinmiyor && !_guncelBorctan) {
      setState(() => _hata = 'Alış fiyatı girin veya bir seçenek işaretleyin');
      return;
    }
    final satisFiyati = sayiOku(_satis.text);
    if (satisFiyati != null && satisFiyati > 0 && satisFiyati != sayi(widget.urun['satis_fiyati'])) {
      UrunApi.guncelle(tamSayi(widget.urun['id']), {
        ...widget.urun,
        'satis_fiyati': satisFiyati,
        'maliyet_fiyati': alis > 0 ? alis : widget.urun['maliyet_fiyati'],
        'maliyet_bilinmiyor': _maliyetBilinmiyor,
        'guncel_borctan': _guncelBorctan,
        'silindi_mi': false,
      }).catchError((_) {});
    }
    Navigator.pop(
      context,
      _Kalem(
        urunId: tamSayi(widget.urun['id']),
        ad: widget.urun['ad'] as String? ?? '',
        alt: urunAlt(widget.urun),
        miktar: _miktar,
        birimFiyat: alis,
        maliyetBilinmiyor: _maliyetBilinmiyor,
        guncelBorctan: _guncelBorctan,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final u = widget.urun;
    return FormIskeleti(
      baslik: 'Alım Detayı',
      kaydetMetni: 'Ekle',
      kaydet: _kaydet,
      kaydediliyor: false,
      hata: _hata,
      children: [
        Grup(baslik: 'Ürün', children: [
          BilgiSatiri('Ürün', u['ad'] as String?),
          BilgiSatiri('Ebat', u['ebat'] as String?),
          BilgiSatiri('Marka', u['marka_adi'] as String?),
          BilgiSatiri('Model', u['model_adi'] as String?),
        ]),
        Grup(baslik: 'Alım', children: [
          Opacity(opacity: _maliyetBilinmiyor ? 0.4 : 1, child: AbsorbPointer(absorbing: _maliyetBilinmiyor, child: MetinSatiri.para(etiket: 'Alış Fiyatı', kontrolcu: _alis, otomatikOdak: true))),
          AnahtarSatiri(etiket: 'Alış fiyatı bilinmiyor', deger: _maliyetBilinmiyor, degisti: (v) {
            setState(() {
              _maliyetBilinmiyor = v;
              if (v) _alis.clear();
            });
          }),
          AnahtarSatiri(etiket: 'Güncel borçtan', deger: _guncelBorctan, degisti: (v) => setState(() => _guncelBorctan = v)),
          MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satis),
          AdimSatiri(etiket: 'Miktar', deger: _miktar, degisti: (v) => setState(() => _miktar = v)),
        ]),
      ],
    );
  }
}

/// Etiket bilgilerini elle girerek yeni ürün oluşturur (QR bozuk olduğunda).
/// Üstte arama kutusu ile mevcut ürünler aranabilir; seçilince form otomatik dolar.
class _ManuelEtiketFormu extends StatefulWidget {
  final String? eprelNo;
  const _ManuelEtiketFormu({this.eprelNo});

  @override
  State<_ManuelEtiketFormu> createState() => _ManuelEtiketFormuState();
}

class _ManuelEtiketFormuState extends State<_ManuelEtiketFormu> {
  final _arama = TextEditingController();
  String _markaAdi = '';
  String _modelAdi = '';
  String _ebatAdi = '';
  String _mevsim = 'Yaz';
  String _ebatKategori = 'Otomobil';
  final _alis = TextEditingController();
  final _satis = TextEditingController();
  int _miktar = 4;
  bool _maliyetBilinmiyor = false;
  bool _guncelBorctan = false;
  bool _kaydediliyor = false;
  String? _hata;
  List<Json> _sonuclar = [];
  bool _araniyor = false;
  bool _secildi = false;
  int? _secilenUrunId;

  @override
  void dispose() {
    _arama.dispose();
    _alis.dispose();
    _satis.dispose();
    super.dispose();
  }

  Future<void> _ara() async {
    final q = _arama.text.trim();
    if (q.isEmpty) return;
    setState(() => _araniyor = true);
    try {
      final liste = await UrunApi.liste(arama: q, limit: 20);
      if (!mounted) return;
      setState(() { _sonuclar = liste; _araniyor = false; });
    } catch (_) {
      if (mounted) setState(() => _araniyor = false);
    }
  }

  void _urunSec(Json u) {
    setState(() {
      _markaAdi = (u['marka_adi'] as String?) ?? '';
      _modelAdi = (u['model_adi'] as String?) ?? '';
      _ebatAdi = (u['ebat'] as String?) ?? '';
      _mevsim = (u['mevsim'] as String?) ?? 'Yaz';
      final sf = sayi(u['satis_fiyati']);
      if (sf > 0) _satis.text = paraSade(u['satis_fiyati']);
      _secildi = true;
      _secilenUrunId = tamSayi(u['id']);
      _sonuclar = [];
    });
  }

  Future<String?> _listeSec(String baslik, Future<List<String>> Function() yukle, String mevcutDeger) async {
    final liste = await yukle();
    if (!mounted) return null;
    return formAc<String>(
      context,
      (_) => _MetinListeSec(baslik: baslik, liste: liste, mevcutDeger: mevcutDeger),
    );
  }

  Future<void> _markaSec() async {
    final v = await _listeSec('Marka Seç', LastikVerileri.markalar, _markaAdi);
    if (v != null && mounted) {
      setState(() { _markaAdi = v; _secildi = false; _secilenUrunId = null; });
      if (!varsayilanMarkalar.contains(v)) LastikVerileri.markaEkle(v);
    }
  }

  Future<void> _modelSec() async {
    final v = await _listeSec('Model Seç', LastikVerileri.modeller, _modelAdi);
    if (v != null && mounted) {
      setState(() { _modelAdi = v; _secildi = false; _secilenUrunId = null; });
      if (!varsayilanModeller.contains(v)) LastikVerileri.modelEkle(v);
    }
  }

  Future<void> _ebatSec() async {
    final v = await _listeSec('Ebat Seç', () => LastikVerileri.ebatlar(_ebatKategori), _ebatAdi);
    if (v != null && mounted) {
      setState(() { _ebatAdi = v; _secildi = false; _secilenUrunId = null; });
      if (!otomobilEbatlari.contains(v) && !kamyonEbatlari.contains(v) && !tirEbatlari.contains(v)) {
        LastikVerileri.ebatEkle(v);
      }
    }
  }

  Future<void> _kaydet() async {
    final alis = sayiOku(_alis.text) ?? 0;
    if (_markaAdi.trim().isEmpty || _ebatAdi.trim().isEmpty) {
      setState(() => _hata = 'Marka ve ebat zorunludur');
      return;
    }
    if (alis <= 0 && !_maliyetBilinmiyor && !_guncelBorctan) {
      setState(() => _hata = 'Alış fiyatı girin veya bir seçenek işaretleyin');
      return;
    }
    setState(() { _kaydediliyor = true; _hata = null; });
    try {
      if (_secildi && _secilenUrunId != null) {
        final satisYeni = sayiOku(_satis.text) ?? 0;
        final mevcutSatis = sayi((await UrunApi.getir(_secilenUrunId!))['satis_fiyati']);
        if (satisYeni > 0 && satisYeni != mevcutSatis) {
          await UrunApi.guncelle(_secilenUrunId!, (await UrunApi.getir(_secilenUrunId!))..['satis_fiyati'] = satisYeni);
        }
        if (!mounted) return;
        Navigator.pop(
          context,
          _Kalem(
            urunId: _secilenUrunId!,
            ad: '$_markaAdi $_modelAdi $_ebatAdi',
            alt: '$_ebatAdi  ·  $_mevsim',
            miktar: _miktar,
            birimFiyat: alis,
            maliyetBilinmiyor: _maliyetBilinmiyor,
            guncelBorctan: _guncelBorctan,
          ),
        );
      } else {
        final eprelNo = widget.eprelNo ?? _markaAdi.trim().hashCode.abs().toString();
        final d = await UrunApi.eprelKaydet({
          'eprel_no': eprelNo,
          'marka': _markaAdi.trim(),
          'model': _modelAdi.trim().isEmpty ? _ebatAdi.trim() : _modelAdi.trim(),
          'ebat': _ebatAdi.trim(),
          'mevsim': _mevsim,
          'satis_fiyati': sayiOku(_satis.text) ?? 0,
          'maliyet_fiyati': alis,
          'maliyet_bilinmiyor': _maliyetBilinmiyor,
          'guncel_borctan': _guncelBorctan,
        });
        if (!mounted) return;
        if (dogruMu(d['yeni_mi'])) bildir(context, 'Yeni ürün oluşturuldu: ${d['urun_ad']}');
        Navigator.pop(
          context,
          _Kalem(
            urunId: tamSayi(d['urun_id']),
            ad: d['urun_ad'] as String? ?? '',
            alt: '$_ebatAdi  ·  $_mevsim',
            miktar: _miktar,
            birimFiyat: alis,
          ),
        );
      }
    } catch (e) {
      setState(() { _hata = hataMesaji(e); _kaydediliyor = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormIskeleti(
      baslik: 'Etiket Bilgilerini Gir',
      kaydetMetni: 'Ekle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(
          baslik: 'Ürün Ara',
          altNot: 'Marka, model veya ebat yazıp arayın. Mevcut ürün bulunursa bilgiler otomatik dolar.',
          children: [
            Row(children: [
              Expanded(child: CupertinoTextField(
                controller: _arama,
                placeholder: 'Örn: Continental 205/55',
                onSubmitted: (_) => _ara(),
                textInputAction: TextInputAction.search,
              )),
              const SizedBox(width: 8),
              CupertinoButton(padding: EdgeInsets.zero, onPressed: _araniyor ? null : _ara,
                child: _araniyor ? const CupertinoActivityIndicator() : const Icon(CupertinoIcons.search)),
            ]),
            if (_sonuclar.isNotEmpty) ...[
              const SizedBox(height: 8),
              ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 200),
                child: CupertinoScrollbar(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: _sonuclar.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (_, i) {
                      final u = _sonuclar[i];
                      return CupertinoButton(
                        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
                        onPressed: () => _urunSec(u),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text('${u['marka_adi']} ${u['model_adi']}', style: context.yazi.bodyMedium),
                            Text('${u['ebat'] ?? ''}  ·  ${u['mevsim'] ?? ''}', style: context.yazi.bodySmall?.copyWith(color: CupertinoColors.systemGrey)),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],
            if (_sonuclar.isEmpty && _arama.text.trim().isNotEmpty && !_araniyor)
              const Padding(padding: EdgeInsets.only(top: 8), child: Text('Sonuç bulunamadı — bilgileri elle girin', style: TextStyle(color: CupertinoColors.systemGrey, fontSize: 13))),
          ],
        ),
        if (_secildi)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text('$_markaAdi $_modelAdi seçildi', style: const TextStyle(color: CupertinoColors.activeBlue, fontSize: 13)),
          ),
        Grup(
          baslik: 'Etiket Bilgisi',
          altNot: 'Listeden seçin veya yeni değer yazın',
          children: [
            SecimSatiri(etiket: 'Marka', deger: _markaAdi.isEmpty ? null : _markaAdi, onTap: _markaSec),
            SecimSatiri(etiket: 'Model', deger: _modelAdi.isEmpty ? null : _modelAdi, ipucu: 'Opsiyonel', onTap: _modelSec),
            SegmentSatiri<String>(
              etiket: 'Araç Tipi',
              secenekler: const {'Otomobil': 'Otomobil', 'Kamyon': 'Kamyon', 'TIR': 'TIR'},
              secili: _ebatKategori,
              degisti: (v) => setState(() => _ebatKategori = v),
            ),
            SecimSatiri(etiket: 'Ebat', deger: _ebatAdi.isEmpty ? null : _ebatAdi, onTap: _ebatSec),
            SegmentSatiri<String>(
              etiket: 'Mevsim',
              secenekler: const {'Yaz': 'Yaz', 'Kış': 'Kış', 'Dört Mevsim': '4 Mevsim'},
              secili: _mevsim,
              degisti: (v) => setState(() => _mevsim = v),
            ),
          ],
        ),
        Grup(baslik: 'Alım', children: [
          Opacity(opacity: _maliyetBilinmiyor ? 0.4 : 1, child: AbsorbPointer(absorbing: _maliyetBilinmiyor, child: MetinSatiri.para(etiket: 'Alış Fiyatı', kontrolcu: _alis))),
          AnahtarSatiri(etiket: 'Alış fiyatı bilinmiyor', deger: _maliyetBilinmiyor, degisti: (v) {
            setState(() {
              _maliyetBilinmiyor = v;
              if (v) _alis.clear();
            });
          }),
          AnahtarSatiri(etiket: 'Güncel borçtan', deger: _guncelBorctan, degisti: (v) => setState(() => _guncelBorctan = v)),
          MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satis),
          AdimSatiri(etiket: 'Miktar', deger: _miktar, degisti: (v) => setState(() => _miktar = v)),
        ]),
      ],
    );
  }
}

/// Metin listesinden seçim + yeni ekleme. Arama ile filtrelenir.
class _MetinListeSec extends StatefulWidget {
  final String baslik;
  final List<String> liste;
  final String mevcutDeger;
  const _MetinListeSec({required this.baslik, required this.liste, required this.mevcutDeger});

  @override
  State<_MetinListeSec> createState() => _MetinListeSecState();
}

class _MetinListeSecState extends State<_MetinListeSec> {
  late List<String> _filtreli;
  String _arama = '';
  late final _ctrl = TextEditingController(text: widget.mevcutDeger);

  @override
  void initState() {
    super.initState();
    _filtreli = widget.liste;
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _filtrele(String q) {
    setState(() {
      _arama = q;
      if (q.isEmpty) {
        _filtreli = widget.liste;
      } else {
        final k = q.toLowerCase();
        _filtreli = widget.liste.where((e) => e.toLowerCase().contains(k)).toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Material(
      color: r.arkaplan,
      child: Column(children: [
        PanelBaslik(
          widget.baslik,
          solEylem: UstDugme(metin: 'Vazgeç', onTap: () => Navigator.pop(context)),
          eylemler: [
            UstDugme(metin: 'Tamam', onTap: () {
              final v = _ctrl.text.trim();
              if (v.isNotEmpty) Navigator.pop(context, v);
            }),
          ],
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: CupertinoTextField(
            controller: _ctrl,
            placeholder: 'Yazın veya listeden seçin',
            onChanged: _filtrele,
            autofocus: true,
            clearButtonMode: OverlayVisibilityMode.editing,
          ),
        ),
        if (_arama.isNotEmpty && _filtreli.isEmpty)
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text('"${_ctrl.text}" listede yok — Tamam ile eklenecek', style: TextStyle(color: CupertinoColors.systemGrey, fontSize: 13)),
          ),
        Expanded(
          child: CupertinoScrollbar(
            child: ListView.separated(
              itemCount: _filtreli.length,
              separatorBuilder: (_, __) => Divider(height: 1, color: r.ayrac),
              itemBuilder: (_, i) {
                final item = _filtreli[i];
                return CupertinoButton(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  onPressed: () => Navigator.pop(context, item),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(item, style: context.yazi.bodyLarge),
                  ),
                );
              },
            ),
          ),
        ),
      ]),
    );
  }
}
