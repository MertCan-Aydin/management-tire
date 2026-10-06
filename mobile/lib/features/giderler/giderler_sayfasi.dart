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
                        alt: tarihSaat(g['tarih']),
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

Future<void> giderFormuAc(BuildContext context, {Json? mevcut}) =>
    formAc(context, (_) => _GiderFormu(mevcut: mevcut), genislik: 500);

class _GiderFormu extends StatefulWidget {
  final Json? mevcut;
  const _GiderFormu({this.mevcut});

  @override
  State<_GiderFormu> createState() => _GiderFormuState();
}

class _GiderFormuState extends State<_GiderFormu> {
  late final _aciklama = TextEditingController(text: widget.mevcut?['aciklama'] as String? ?? '');
  late final _tutar = TextEditingController(text: widget.mevcut == null ? '' : paraSade(widget.mevcut!['tutar']));
  late DateTime _tarih = tarihOku(widget.mevcut?['tarih']) ?? DateTime.now();
  bool _kaydediliyor = false;
  String? _hata;

  static const _hizliAciklamalar = ['Kira', 'Elektrik', 'Su', 'Doğalgaz', 'İnternet', 'Personel', 'Yemek', 'Yakıt', 'Vergi'];

  @override
  void dispose() {
    _aciklama.dispose();
    _tutar.dispose();
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
      final v = {'aciklama': _aciklama.text.trim(), 'tutar': tutar};
      if (widget.mevcut == null) {
        await GiderApi.ekle(v);
      } else {
        // Saat bilgisini koru, yalnızca günü değiştir
        final eski = tarihOku(widget.mevcut!['tarih']) ?? DateTime.now();
        final yeni = DateTime(_tarih.year, _tarih.month, _tarih.day, eski.hour, eski.minute, eski.second);
        await GiderApi.guncelle(tamSayi(widget.mevcut!['id']), {...v, 'tarih': yeni.toIso8601String()});
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
      baslik: widget.mevcut == null ? 'Yeni Gider' : 'Gideri Düzenle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          MetinSatiri(
              etiket: 'Açıklama', kontrolcu: _aciklama, ipucu: 'Örn. Elektrik faturası', otomatikOdak: widget.mevcut == null),
          MetinSatiri.para(etiket: 'Tutar', kontrolcu: _tutar),
          if (widget.mevcut != null) TarihSatiri(etiket: 'Tarih', deger: _tarih, degisti: (t) => setState(() => _tarih = t)),
        ]),
        if (widget.mevcut == null)
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
        if (widget.mevcut != null) Grup(children: [EylemSatiri('Gideri Sil', yikici: true, onTap: _sil)]),
      ],
    );
  }
}
