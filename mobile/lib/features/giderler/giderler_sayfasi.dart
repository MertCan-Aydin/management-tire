import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';

class GiderlerSayfasi extends StatefulWidget {
  const GiderlerSayfasi({super.key});

  @override
  State<GiderlerSayfasi> createState() => _GiderlerSayfasiState();
}

class _GiderlerSayfasiState extends State<GiderlerSayfasi> with VeriYukleyici<GiderlerSayfasi, List<Json>> {
  Donem _donem = Donem.ay;

  @override
  Future<List<Json>> getir() => GiderApi.liste(donem: _donem.parametreler());

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return OkunurGenislik(
      max: 820,
      child: Column(children: [
        ListeUstu(
          baslik: 'Giderler',
          eylemler: [UstDugme(ikon: CupertinoIcons.add, ipucu: 'Yeni gider', onTap: () => giderFormuAc(context))],
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
                ikon: CupertinoIcons.creditcard,
                baslik: 'Bu dönemde gider yok',
                eylem: CupertinoButton.filled(onPressed: () => giderFormuAc(context), child: const Text('Gider Ekle')),
              );
            }
            final toplam = liste.fold<double>(0, (t, g) => t + sayi(g['tutar']));
            return YenilenebilirListe(
              yenile: yenile,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  child: IstatistikKarti(
                    baslik: '${_donem.etiket} toplam gider',
                    deger: para(toplam),
                    ikon: CupertinoIcons.creditcard_fill,
                    renk: r.tehlike,
                    alt: '${liste.length} kayıt',
                  ),
                ),
                Grup(
                  altNot: 'Düzenlemek veya silmek için kayda dokunun',
                  children: [
                    for (final g in liste)
                      Satir(
                        baslik: g['aciklama'] as String? ?? '',
                        alt: [
                          if (g['kategori'] != null) g['kategori'] as String,
                          if (g['urun_adi'] != null) g['urun_adi'] as String,
                          tarihSaat(g['tarih']),
                        ].join(' · '),
                        sag: Text(para(g['tutar']), style: context.yazi.titleSmall?.copyWith(color: r.tehlike)),
                        onTap: () => giderFormuAc(context, mevcut: g),
                      ),
                  ],
                ),
              ],
            );
          }),
        ),
      ]),
    );
  }
}

Future<void> giderFormuAc(BuildContext context, {Json? mevcut, Json? taslakVeri, int? taslakId}) =>
    formAc(context, (_) => _GiderFormu(mevcut: mevcut, taslakVeri: taslakVeri, taslakId: taslakId), genislik: 500);

class _GiderFormu extends StatefulWidget {
  final Json? mevcut;
  final Json? taslakVeri;
  final int? taslakId;
  const _GiderFormu({this.mevcut, this.taslakVeri, this.taslakId});

  @override
  State<_GiderFormu> createState() => _GiderFormuState();
}

class _GiderFormuState extends State<_GiderFormu> {
  Json? get _vk => widget.taslakVeri ?? widget.mevcut;
  late final _aciklama = TextEditingController(text: _vk?['aciklama'] as String? ?? '');
  late final _tutar = TextEditingController(text: _vk?['tutar'] != null ? (_vk!['tutar'] is String ? _vk!['tutar'] as String : paraSade(_vk!['tutar'])) : '');
  late DateTime _tarih = tarihOku(widget.mevcut?['tarih']) ?? DateTime.now();
  late String? _kategori = _vk?['kategori'] as String?;
  late final _urunAdi = TextEditingController(text: _vk?['urun_adi'] as String? ?? '');
  late final _marka = TextEditingController(text: _vk?['marka'] as String? ?? '');
  late final _alisFiyati = TextEditingController(text: _vk?['alis_fiyati'] != null ? (_vk!['alis_fiyati'] is String ? _vk!['alis_fiyati'] as String : paraSade(_vk!['alis_fiyati'])) : '');
  late final _satisFiyati = TextEditingController(text: _vk?['satis_fiyati'] != null ? (_vk!['satis_fiyati'] is String ? _vk!['satis_fiyati'] as String : paraSade(_vk!['satis_fiyati'])) : '');
  late final _yil = TextEditingController(text: _vk?['yil']?.toString() ?? '');
  late bool _maliyetBilinmiyor = _vk?['maliyet_bilinmiyor'] == true || _vk?['maliyet_bilinmiyor'] == 1;
  bool _kaydediliyor = false;
  String? _hata;

  bool get _urunAlimi => _kategori == 'Ürün Alımı';

  static const _kategoriler = ['Kira', 'Fatura', 'Personel', 'Yakıt', 'Vergi', 'Ürün Alımı', 'Diğer'];
  static const _hizliAciklamalar = ['Kira', 'Elektrik', 'Su', 'Doğalgaz', 'İnternet', 'Personel', 'Yemek', 'Yakıt', 'Vergi'];

  @override
  void dispose() {
    _aciklama.dispose();
    _tutar.dispose();
    _urunAdi.dispose();
    _marka.dispose();
    _alisFiyati.dispose();
    _satisFiyati.dispose();
    _yil.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    final tutar = sayiOku(_tutar.text);
    if (_aciklama.text.trim().isEmpty) {
      setState(() => _hata = 'Açıklama zorunludur');
      return;
    }
    if (tutar == null || tutar <= 0) {
      setState(() => _hata = 'Tutar 0\'dan büyük olmalıdır');
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      final v = <String, dynamic>{
        'aciklama': _aciklama.text.trim(),
        'tutar': tutar,
        'kategori': _kategori,
        if (_urunAlimi) ...{
          'urun_adi': _urunAdi.text.trim().isEmpty ? null : _urunAdi.text.trim(),
          'marka': _marka.text.trim().isEmpty ? null : _marka.text.trim(),
          'alis_fiyati': sayiOku(_alisFiyati.text),
          'satis_fiyati': sayiOku(_satisFiyati.text),
          'yil': int.tryParse(_yil.text.trim()),
          'maliyet_bilinmiyor': _maliyetBilinmiyor,
        },
      };
      if (widget.mevcut == null) {
        await GiderApi.ekle(v);
      } else {
        final eski = tarihOku(widget.mevcut!['tarih']) ?? DateTime.now();
        final yeni = DateTime(_tarih.year, _tarih.month, _tarih.day, eski.hour, eski.minute, eski.second);
        await GiderApi.guncelle(tamSayi(widget.mevcut!['id']), {...v, 'tarih': yeni.toIso8601String()});
      }
      if (widget.taslakId != null) {
        try { await TaslakApi.sil(widget.taslakId!); } catch (_) {}
      }
      veriDegisti();
      if (!mounted) return;
      bildir(context, widget.mevcut == null ? 'Gider eklendi' : 'Değişiklikler kaydedildi');
      Navigator.pop(context);
    } catch (e) {
      setState(() {
        _hata = hataMesaji(e);
        _kaydediliyor = false;
      });
    }
  }

  Future<void> _taslakKaydet() async {
    final baslik = _aciklama.text.trim().isEmpty ? 'Gider taslağı' : _aciklama.text.trim();
    final veri = <String, dynamic>{
      'aciklama': _aciklama.text.trim(),
      'tutar': _tutar.text.trim(),
      'kategori': _kategori,
      'urun_adi': _urunAdi.text.trim(),
      'marka': _marka.text.trim(),
      'alis_fiyati': _alisFiyati.text.trim(),
      'satis_fiyati': _satisFiyati.text.trim(),
      'yil': _yil.text.trim(),
      'maliyet_bilinmiyor': _maliyetBilinmiyor,
    };
    try {
      await TaslakApi.ekle('gider', baslik, veri);
      veriDegisti();
      if (!mounted) return;
      bildir(context, 'Taslak kaydedildi');
      Navigator.pop(context);
    } catch (e) {
      setState(() => _hata = hataMesaji(e));
    }
  }

  Future<void> _sil() async {
    final onay = await onayla(context,
        baslik: 'Gideri Sil', mesaj: '"${widget.mevcut!['aciklama']}" silinecek.', onayMetni: 'Sil', yikici: true);
    if (!onay || !mounted) return;
    try {
      await GiderApi.sil(tamSayi(widget.mevcut!['id']));
      veriDegisti();
      if (!mounted) return;
      bildir(context, 'Gider silindi');
      Navigator.pop(context);
    } catch (e) {
      setState(() => _hata = hataMesaji(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return FormIskeleti(
      baslik: widget.taslakVeri != null ? 'Taslaktan Devam' : widget.mevcut == null ? 'Yeni Gider' : 'Gideri Düzenle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Wrap(spacing: 8, runSpacing: 8, children: [
            for (final k in _kategoriler)
              ChoiceChip(
                label: Text(k),
                selected: _kategori == k,
                selectedColor: r.anaAcik,
                backgroundColor: r.kart,
                side: BorderSide(color: _kategori == k ? r.ana : r.ayrac),
                shape: const StadiumBorder(),
                onSelected: (s) => setState(() => _kategori = s ? k : null),
              ),
          ]),
        ),
        Grup(children: [
          MetinSatiri(
              etiket: 'Açıklama', kontrolcu: _aciklama, ipucu: 'Örn. Elektrik faturası', otomatikOdak: widget.mevcut == null),
          MetinSatiri.para(etiket: 'Tutar', kontrolcu: _tutar),
          if (widget.mevcut != null) TarihSatiri(etiket: 'Tarih', deger: _tarih, degisti: (t) => setState(() => _tarih = t)),
        ]),
        if (_urunAlimi)
          Grup(
            baslik: 'Ürün Detayları',
            children: [
              MetinSatiri(etiket: 'Ürün Adı', kontrolcu: _urunAdi, ipucu: 'Örn. Jant, Akü, Yağ'),
              MetinSatiri(etiket: 'Marka', kontrolcu: _marka, ipucu: 'Opsiyonel'),
              MetinSatiri.para(etiket: 'Alış Fiyatı', kontrolcu: _alisFiyati),
              MetinSatiri.para(etiket: 'Satış Fiyatı', kontrolcu: _satisFiyati),
              MetinSatiri(etiket: 'Yıl', kontrolcu: _yil, ipucu: 'Örn: 2024', klavye: TextInputType.number),
              AnahtarSatiri(etiket: 'Fiyat Bilinmiyor', deger: _maliyetBilinmiyor, degisti: (v) => setState(() => _maliyetBilinmiyor = v)),
            ],
          ),
        if (!_urunAlimi && widget.mevcut == null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 22),
            child: Wrap(spacing: 8, runSpacing: 8, children: [
              for (final a in _hizliAciklamalar)
                ActionChip(
                  label: Text(a),
                  backgroundColor: r.kart,
                  side: BorderSide(color: r.ayrac),
                  shape: const StadiumBorder(),
                  onPressed: () => setState(() => _aciklama.text = a),
                ),
            ]),
          ),
        if (widget.mevcut == null && widget.taslakVeri == null)
          Grup(children: [EylemSatiri('Taslak Olarak Kaydet', ikon: CupertinoIcons.doc, onTap: _taslakKaydet)]),
        if (widget.mevcut != null) Grup(children: [EylemSatiri('Gideri Sil', yikici: true, onTap: _sil)]),
      ],
    );
  }
}
