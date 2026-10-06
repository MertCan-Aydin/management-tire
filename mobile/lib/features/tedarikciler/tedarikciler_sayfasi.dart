import 'package:flutter/cupertino.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../alim/alim_formu.dart';
import '../alim/alimlar_sayfasi.dart';

const _kahve = Color(0xFFA2845E);

class TedarikcilerSayfasi extends StatelessWidget {
  const TedarikcilerSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.building_2_fill,
        liste: (ctx, sec, seciliId) => _TedarikciListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, t) => TedarikciDetay(tedarikci: t),
      );
}

class _TedarikciListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _TedarikciListesi({required this.sec, this.seciliId});

  @override
  State<_TedarikciListesi> createState() => _TedarikciListesiState();
}

class _TedarikciListesiState extends State<_TedarikciListesi> with VeriYukleyici<_TedarikciListesi, List<Json>> {
  String _arama = '';

  @override
  Future<List<Json>> getir() => TedarikciApi.liste();

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      ListeUstu(
        baslik: 'Tedarikçiler',
        eylemler: [UstDugme(ikon: CupertinoIcons.add, ipucu: 'Yeni tedarikçi', onTap: () => tedarikciFormuAc(context))],
        arama: AramaKutusu(ipucu: 'Tedarikçi ara', degisti: (v) => setState(() => _arama = v.toLowerCase())),
      ),
      Expanded(
        child: durum((hepsi) {
          final liste = _arama.isEmpty
              ? hepsi
              : hepsi.where((t) => '${t['ad']} ${t['iletisim_bilgisi'] ?? ''}'.toLowerCase().contains(_arama)).toList();
          if (liste.isEmpty) {
            return BosDurum(
              ikon: CupertinoIcons.building_2_fill,
              baslik: hepsi.isEmpty ? 'Henüz tedarikçi yok' : 'Sonuç bulunamadı',
              eylem: hepsi.isEmpty
                  ? CupertinoButton.filled(onPressed: () => tedarikciFormuAc(context), child: const Text('Tedarikçi Ekle'))
                  : null,
            );
          }
          final toplamBorc = hepsi.fold<double>(0, (t, e) => t + sayi(e['guncel_borc']));
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: IstatistikKarti(
                  baslik: 'Toplam Tedarikçi Borcu',
                  deger: para(toplamBorc),
                  ikon: CupertinoIcons.exclamationmark_circle_fill,
                  renk: toplamBorc > 0 ? r.tehlike : r.basari,
                ),
              ),
              Grup(
                girinti: 60,
                children: [
                  for (final t in liste)
                    Satir(
                      onde: const IkonKutusu(CupertinoIcons.building_2_fill, _kahve, boyut: 32),
                      baslik: t['ad'] as String? ?? '',
                      alt: t['iletisim_bilgisi'] as String?,
                      sag: Text(
                        para(t['guncel_borc']),
                        style: context.yazi.titleSmall?.copyWith(color: sayi(t['guncel_borc']) > 0 ? r.tehlike : r.ikincil),
                      ),
                      secili: widget.seciliId == t['id'],
                      onTap: () => widget.sec(t),
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

// ─── Detay ──────────────────────────────────────────────────────────────────

class TedarikciDetay extends StatefulWidget {
  final Json tedarikci;
  const TedarikciDetay({required this.tedarikci, super.key});

  @override
  State<TedarikciDetay> createState() => _TedarikciDetayState();
}

typedef _TedarikciVeri = ({Json tedarikci, List<Json> odemeler, List<Json> alimlar});

class _TedarikciDetayState extends State<TedarikciDetay> with VeriYukleyici<TedarikciDetay, _TedarikciVeri> {
  int get _id => tamSayi(widget.tedarikci['id']);

  @override
  Future<_TedarikciVeri> getir() async {
    final r = await Future.wait([
      TedarikciApi.getir(_id),
      TedarikciApi.odemeler(_id),
      AlimApi.liste(tedarikciId: _id),
    ]);
    return (tedarikci: r[0] as Json, odemeler: r[1] as List<Json>, alimlar: r[2] as List<Json>);
  }

  Future<void> _sil(Json t) async {
    final onay =
        await onayla(context, baslik: 'Tedarikçiyi Sil', mesaj: '"${t['ad']}" silinecek.', onayMetni: 'Sil', yikici: true);
    if (!onay || !mounted) return;
    try {
      await TedarikciApi.sil(_id);
      if (!mounted) return;
      bildir(context, 'Tedarikçi silindi');
      DetayKapsami.of(context).kapat();
      veriDegisti();
    } catch (e) {
      if (mounted) bildir(context, hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = veri?.tedarikci ?? widget.tedarikci;
    final r = context.renk;
    final borc = sayi(t['guncel_borc']);
    return DetayIskeleti(
      baslik: t['ad'] as String? ?? 'Tedarikçi',
      yenile: yenile,
      eylemler: [UstDugme(metin: 'Düzenle', onTap: () => tedarikciFormuAc(context, mevcut: t))],
      children: [
        DetayKafa(
          ikon: CupertinoIcons.building_2_fill,
          renk: _kahve,
          baslik: t['ad'] as String? ?? '',
          alt: t['iletisim_bilgisi'] as String?,
          buyukDeger: para(borc),
          rozet: Rozet(borc > 0 ? 'Güncel borç' : 'Borç yok', borc > 0 ? r.tehlike : r.basari),
        ),
        EylemDugmeleri([
          (CupertinoIcons.money_dollar_circle_fill, 'Ödeme Yap', () => odemeFormuAc(context, t), r.basari),
          (CupertinoIcons.arrow_down_doc_fill, 'Yeni Alım', () => alimFormuAc(context, tedarikci: t), r.mor),
        ]),
        if (veri == null)
          const Padding(padding: EdgeInsets.all(24), child: Yukleniyor())
        else ...[
          Grup(
            baslik: 'Ödemeler',
            altNot: veri!.odemeler.isEmpty
                ? null
                : 'Toplam ödenen ${para(veri!.odemeler.fold<double>(0, (s, o) => s + sayi(o['tutar'])))}',
            children: veri!.odemeler.isEmpty
                ? [const BilgiSatiri('Henüz ödeme yok', '')]
                : [
                    for (final o in veri!.odemeler.take(20))
                      BilgiSatiri(tarihSaat(o['tarih']), para(o['tutar']), degerRengi: r.basari),
                  ],
          ),
          Grup(
            baslik: 'Alımlar',
            children: veri!.alimlar.isEmpty
                ? [const BilgiSatiri('Henüz alım yok', '')]
                : [
                    for (final a in veri!.alimlar.take(20))
                      Satir(
                        baslik: para(a['toplam_tutar']),
                        alt: tarihSaat(a['tarih']),
                        sag: dogruMu(a['iptal_mi']) ? Rozet('İptal', r.tehlike) : null,
                        onTap: () => alimDetayAc(context, a),
                      ),
                  ],
          ),
        ],
        Grup(children: [EylemSatiri('Tedarikçiyi Sil', yikici: true, onTap: () => _sil(t))]),
      ],
    );
  }
}

// ─── Formlar ────────────────────────────────────────────────────────────────

Future<Json?> tedarikciFormuAc(BuildContext context, {Json? mevcut}) =>
    formAc<Json>(context, (_) => _TedarikciFormu(mevcut: mevcut));

class _TedarikciFormu extends StatefulWidget {
  final Json? mevcut;
  const _TedarikciFormu({this.mevcut});

  @override
  State<_TedarikciFormu> createState() => _TedarikciFormuState();
}

class _TedarikciFormuState extends State<_TedarikciFormu> {
  late final _ad = TextEditingController(text: widget.mevcut?['ad'] as String? ?? '');
  late final _iletisim = TextEditingController(text: widget.mevcut?['iletisim_bilgisi'] as String? ?? '');
  late final _borc = TextEditingController(text: widget.mevcut == null ? '' : paraSade(widget.mevcut!['guncel_borc']));
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    for (final c in [_ad, _iletisim, _borc]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _kaydet() async {
    if (_ad.text.trim().isEmpty) {
      setState(() => _hata = 'Firma adı zorunludur');
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    final v = <String, dynamic>{
      'ad': _ad.text.trim(),
      'iletisim_bilgisi': _iletisim.text.trim().isEmpty ? null : _iletisim.text.trim(),
      'guncel_borc': sayiOku(_borc.text) ?? 0,
    };
    try {
      if (widget.mevcut == null) {
        v['id'] = await TedarikciApi.ekle(v);
      } else {
        await TedarikciApi.guncelle(tamSayi(widget.mevcut!['id']), {...v, 'silindi_mi': false});
        v['id'] = widget.mevcut!['id'];
      }
      veriDegisti();
      if (!mounted) return;
      bildir(context, widget.mevcut == null ? 'Tedarikçi eklendi' : 'Değişiklikler kaydedildi');
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
      baslik: widget.mevcut == null ? 'Yeni Tedarikçi' : 'Tedarikçiyi Düzenle',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          MetinSatiri(etiket: 'Firma Adı', kontrolcu: _ad, ipucu: 'Zorunlu', otomatikOdak: widget.mevcut == null),
          MetinSatiri(etiket: 'İletişim', kontrolcu: _iletisim, ipucu: 'Telefon, e-posta…'),
        ]),
        Grup(
          altNot: 'Alımlar borcu artırır, ödemeler azaltır. Bu alanı yalnızca düzeltme için değiştirin.',
          children: [MetinSatiri.para(etiket: 'Güncel Borç', kontrolcu: _borc)],
        ),
      ],
    );
  }
}

Future<void> odemeFormuAc(BuildContext context, Json tedarikci) =>
    formAc(context, (_) => _OdemeFormu(tedarikci: tedarikci), genislik: 480);

class _OdemeFormu extends StatefulWidget {
  final Json tedarikci;
  const _OdemeFormu({required this.tedarikci});

  @override
  State<_OdemeFormu> createState() => _OdemeFormuState();
}

class _OdemeFormuState extends State<_OdemeFormu> {
  final _tutar = TextEditingController();
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    _tutar.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    final tutar = sayiOku(_tutar.text);
    if (tutar == null || tutar <= 0) {
      setState(() => _hata = 'Geçerli bir tutar girin');
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      await TedarikciApi.odemeEkle(tamSayi(widget.tedarikci['id']), tutar);
      veriDegisti();
      if (!mounted) return;
      bildir(context, '${para(tutar)} ödeme kaydedildi');
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
    final borc = sayi(widget.tedarikci['guncel_borc']);
    return FormIskeleti(
      baslik: 'Ödeme Yap',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          BilgiSatiri('Tedarikçi', widget.tedarikci['ad'] as String?),
          BilgiSatiri('Güncel Borç', para(borc), degerRengi: borc > 0 ? context.renk.tehlike : null),
        ]),
        Grup(children: [
          MetinSatiri.para(etiket: 'Ödeme Tutarı', kontrolcu: _tutar, otomatikOdak: true),
          if (borc > 0) EylemSatiri('Borcun Tamamı (${para(borc)})', onTap: () => setState(() => _tutar.text = paraSade(borc))),
        ]),
      ],
    );
  }
}
