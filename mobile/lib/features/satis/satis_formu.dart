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
import '../musteriler/musteriler_sayfasi.dart';
import '../urunler/urun_secici.dart';

const odemeYontemleri = ['Nakit', 'Kredi Kartı', 'Havale'];

/// Segment düğmesinde sığması için kısa etiketler (API'ye tam ad gider).
const _odemeEtiketleri = {'Nakit': 'Nakit', 'Kredi Kartı': 'Kart', 'Havale': 'Havale'};

Future<void> satisFormuAc(BuildContext context) => Navigator.of(context).push(CupertinoPageRoute(
      fullscreenDialog: true,
      builder: (_) => const Scaffold(body: SafeArea(child: _SatisFormu())),
    ));

class _Kalem {
  final int urunId;
  final String ad;
  final String alt;
  final int? stokSiniri; // fiziksel olmayan ürünlerde (hizmet) sınır yok
  int miktar;
  double birimFiyat;
  final double birimMaliyet;

  _Kalem.urundan(Json u)
      : urunId = tamSayi(u['id']),
        ad = u['ad'] as String? ?? '',
        alt = urunAlt(u),
        stokSiniri = dogruMu(u['fiziksel_urun_mu'] ?? true) ? tamSayi(u['stok']) : null,
        miktar = 1,
        birimFiyat = sayi(u['satis_fiyati']),
        birimMaliyet = sayi(u['maliyet_fiyati']);

  double get toplam => miktar * birimFiyat;

  Json json() => {
        'urun_id': urunId,
        'urun_adi_anlik': ad,
        'miktar': miktar,
        'birim_fiyat': birimFiyat,
        'birim_maliyet': birimMaliyet,
      };
}

class _SatisFormu extends StatefulWidget {
  const _SatisFormu();

  @override
  State<_SatisFormu> createState() => _SatisFormuState();
}

class _SatisFormuState extends State<_SatisFormu> {
  Json? _musteri;
  final List<_Kalem> _kalemler = [];
  String _odeme = odemeYontemleri.first;
  final _indirim = TextEditingController();
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    _indirim.dispose();
    super.dispose();
  }

  double get _araToplam => _kalemler.fold(0, (t, k) => t + k.toplam);
  double get _indirimTutari => sayiOku(_indirim.text) ?? 0;
  double get _net => _araToplam - _indirimTutari;
  double get _kar => _net - _kalemler.fold<double>(0, (t, k) => t + k.miktar * k.birimMaliyet);

  void _urunEkle(Json u) {
    final id = tamSayi(u['id']);
    final mevcut = _kalemler.where((k) => k.urunId == id).firstOrNull;
    if (mevcut != null) {
      if (mevcut.stokSiniri != null && mevcut.miktar >= mevcut.stokSiniri!) {
        bildir(context, 'Stokta yalnızca ${mevcut.stokSiniri} adet var', hata: true);
        return;
      }
      setState(() => mevcut.miktar++);
    } else {
      final k = _Kalem.urundan(u);
      if (k.stokSiniri != null && k.stokSiniri! < 1) {
        bildir(context, '"${k.ad}" stokta yok', hata: true);
        return;
      }
      setState(() => _kalemler.add(k));
    }
    HapticFeedback.selectionClick();
  }

  Future<void> _qrOkut() async {
    final u = await Navigator.of(context).push<Json>(CupertinoPageRoute(builder: (_) => const BarkodScreen()));
    if (u != null && mounted) _urunEkle(u);
  }

  Future<void> _urunListedenSec() async {
    final u = await urunSec(context, sadeceStoklu: true);
    if (u != null && mounted) _urunEkle(u);
  }

  Future<void> _musteriSec() async {
    final m = await aramaliSec(
      context,
      baslik: 'Müşteri Seç',
      aramaIpucu: 'Ad, telefon veya plaka',
      yukle: (q) => MusteriApi.liste(arama: q, limit: 50),
      satirBaslik: (m) => m['ad_soyad'] as String? ?? '',
      satirAlt: (m) => [m['telefon'], m['arac_plakasi']].where((e) => e != null && '$e'.isNotEmpty).join('  ·  '),
      yeniEkle: (ctx) => musteriFormuAc(ctx),
    );
    if (m != null) setState(() => _musteri = m);
  }

  Future<void> _fiyatDegistir(_Kalem k) async {
    final v = await sayiSor(context, baslik: 'Birim Fiyat', mesaj: k.ad, baslangic: k.birimFiyat);
    if (v != null && v >= 0) setState(() => k.birimFiyat = v);
  }

  Future<void> _vazgec() async {
    if (_kalemler.isEmpty && _musteri == null) {
      Navigator.pop(context);
      return;
    }
    final onay = await onayla(context,
        baslik: 'Satıştan vazgeçilsin mi?', mesaj: 'Sepetteki ürünler silinecek.', onayMetni: 'Vazgeç', yikici: true);
    if (onay && mounted) Navigator.pop(context);
  }

  Future<void> _kaydet() async {
    String? hata;
    if (_musteri == null) {
      hata = 'Müşteri seçin';
    } else if (_kalemler.isEmpty) {
      hata = 'Sepete en az bir ürün ekleyin';
    } else if (_indirimTutari < 0 || _indirimTutari > _araToplam) {
      hata = 'İndirim, ara toplamdan büyük olamaz';
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
      await SatisApi.ekle({
        'musteri_id': _musteri!['id'],
        'odeme_yontemi': _odeme,
        'indirim': _indirimTutari,
        'kalemler': [for (final k in _kalemler) k.json()],
      });
      veriDegisti();
      if (!mounted) return;
      bildir(context, 'Satış kaydedildi · ${para(_net)}');
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
          'Yeni Satış',
          solEylem: UstDugme(metin: 'Vazgeç', onTap: _kaydediliyor ? null : _vazgec),
          eylemler: [
            if (!genis) UstDugme(metin: 'Kaydet', kalin: true, yukleniyor: _kaydediliyor, onTap: _kaydet),
          ],
        );
        if (!genis) {
          return Column(children: [
            baslik,
            Expanded(child: ListView(padding: const EdgeInsets.only(top: 20), children: _formGruplari(dar: true))),
            _AltOzet(net: _net, kar: _kar, adet: _kalemler.length),
          ]);
        }
        return Column(children: [
          baslik,
          Expanded(
            child: Row(children: [
              Expanded(
                child: UrunAramaPaneli(
                  sadeceStoklu: true,
                  sec: _urunEkle,
                  qrOkut: _qrOkut,
                  sepet: {for (final k in _kalemler) k.urunId: k.miktar},
                ),
              ),
              VerticalDivider(width: 1, thickness: 0, color: context.renk.ayrac),
              SizedBox(
                width: (c.maxWidth * 0.36).clamp(380.0, 460.0),
                child: Column(children: [
                  Expanded(child: ListView(padding: const EdgeInsets.only(top: 16), children: _formGruplari(dar: false))),
                  _AltOzet(net: _net, kar: _kar, adet: _kalemler.length, kaydet: _kaydet, kaydediliyor: _kaydediliyor),
                ]),
              ),
            ]),
          ),
        ]);
      }),
    );
  }

  List<Widget> _formGruplari({required bool dar}) {
    final r = context.renk;
    return [
      if (_hata != null) HataKutusu(_hata!),
      Grup(baslik: 'Müşteri', children: [
        if (_musteri == null)
          EylemSatiri('Müşteri Seç', ikon: CupertinoIcons.person_crop_circle_badge_plus, onTap: _musteriSec)
        else
          Satir(
            onde: CircleAvatar(
              radius: 18,
              backgroundColor: r.anaAcik,
              child: Icon(CupertinoIcons.person_fill, color: r.ana, size: 18),
            ),
            baslik: _musteri!['ad_soyad'] as String? ?? '',
            alt: [_musteri!['telefon'], _musteri!['arac_plakasi']].where((e) => e != null && '$e'.isNotEmpty).join('  ·  '),
            sag: Text('Değiştir', style: context.yazi.bodyMedium?.copyWith(color: r.ana)),
            okIsareti: false,
            onTap: _musteriSec,
          ),
      ]),
      Grup(
        baslik: 'Sepet',
        altNot: _kalemler.isEmpty ? null : 'Birim fiyatı değiştirmek için fiyata dokunun',
        children: [
          if (_kalemler.isEmpty && !dar)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text('Soldaki listeden ürün seçin ya da QR okutun',
                  textAlign: TextAlign.center, style: context.yazi.bodyMedium?.copyWith(color: r.ikincil)),
            ),
          for (final k in _kalemler) _sepetSatiri(k),
          if (dar) ...[
            EylemSatiri('Listeden Ürün Ekle', ikon: CupertinoIcons.add_circled, onTap: _urunListedenSec),
            EylemSatiri('QR / Barkod Okut', ikon: CupertinoIcons.qrcode_viewfinder, onTap: _qrOkut),
          ],
        ],
      ),
      Grup(baslik: 'Ödeme', children: [
        SegmentSatiri<String>(
          etiket: 'Yöntem',
          secenekler: _odemeEtiketleri,
          secili: _odeme,
          degisti: (v) => setState(() => _odeme = v),
        ),
        MetinSatiri.para(etiket: 'İndirim', kontrolcu: _indirim, degisti: (_) => setState(() {})),
      ]),
    ];
  }

  Widget _sepetSatiri(_Kalem k) {
    final r = context.renk;
    return Dismissible(
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
                child:
                    Text('${para(k.birimFiyat)}  ·  ${para(k.toplam)}', style: context.yazi.bodyMedium?.copyWith(color: r.ana)),
              ),
            ]),
          ),
          const SizedBox(width: 8),
          Adimlayici(
            deger: k.miktar,
            max: k.stokSiniri ?? 9999,
            degisti: (v) => setState(() => k.miktar = v),
          ),
          UstDugme(
              ikon: CupertinoIcons.trash, renk: r.tehlike, ipucu: 'Kaldır', onTap: () => setState(() => _kalemler.remove(k))),
        ]),
      ),
    );
  }
}

/// Formun altında sabit duran toplam çubuğu.
class _AltOzet extends StatelessWidget {
  final double net;
  final double kar;
  final int adet;
  final VoidCallback? kaydet;
  final bool kaydediliyor;

  const _AltOzet({required this.net, required this.kar, required this.adet, this.kaydet, this.kaydediliyor = false});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      padding: EdgeInsets.fromLTRB(20, 14, 20, 14 + MediaQuery.paddingOf(context).bottom),
      decoration: BoxDecoration(
        color: r.kart,
        border: Border(top: BorderSide(color: r.ayrac, width: 0)),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Row(children: [
          Text('Toplam', style: context.yazi.titleMedium),
          const SizedBox(width: 8),
          if (adet > 0) Text('$adet kalem', style: context.yazi.bodySmall),
          const Spacer(),
          Text(para(net), style: context.yazi.headlineSmall?.copyWith(fontFeatures: const [FontFeature.tabularFigures()])),
        ]),
        const SizedBox(height: 2),
        Row(children: [
          Text('Tahmini kâr', style: context.yazi.bodySmall),
          const Spacer(),
          Text(para(kar), style: context.yazi.bodyMedium?.copyWith(color: kar >= 0 ? r.basari : r.tehlike)),
        ]),
        if (kaydet != null) ...[
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: kaydediliyor ? null : kaydet,
              child: kaydediliyor ? const CupertinoActivityIndicator(color: Colors.white) : const Text('Satışı Tamamla'),
            ),
          ),
        ],
      ]),
    );
  }
}
