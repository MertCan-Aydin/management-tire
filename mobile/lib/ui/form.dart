import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/api_client.dart';
import '../core/format.dart';
import 'bilesenler.dart';
import 'tema.dart';

/// Formu tablette ortada kart (iPad form sheet), telefonda tam sayfa açar.
Future<T?> formAc<T>(BuildContext context, WidgetBuilder builder, {double genislik = 560}) {
  if (Ekran.tablet(context)) {
    return showDialog<T>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        final h = MediaQuery.sizeOf(ctx).height;
        return Dialog(
          backgroundColor: ctx.renk.arkaplan,
          clipBehavior: Clip.antiAlias,
          insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: ConstrainedBox(
            constraints: BoxConstraints(maxWidth: genislik, maxHeight: h * 0.9),
            child: builder(ctx),
          ),
        );
      },
    );
  }
  return Navigator.of(context).push<T>(CupertinoPageRoute(
    fullscreenDialog: true,
    builder: (ctx) => Scaffold(body: SafeArea(child: builder(ctx))),
  ));
}

/// Form iskeleti: "Vazgeç  |  Başlık  |  Kaydet" çubuğu + kaydırılabilir içerik.
class FormIskeleti extends StatelessWidget {
  final String baslik;
  final List<Widget> children;
  final VoidCallback? kaydet;
  final bool kaydediliyor;
  final String kaydetMetni;
  final String? hata;

  const FormIskeleti({
    required this.baslik,
    required this.children,
    this.kaydet,
    this.kaydediliyor = false,
    this.kaydetMetni = 'Kaydet',
    this.hata,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: context.renk.arkaplan,
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        PanelBaslik(
          baslik,
          solEylem: UstDugme(metin: 'Vazgeç', onTap: kaydediliyor ? null : () => Navigator.pop(context)),
          eylemler: [
            if (kaydet != null) UstDugme(metin: kaydetMetni, kalin: true, yukleniyor: kaydediliyor, onTap: kaydet),
          ],
        ),
        Flexible(
          child: SingleChildScrollView(
            padding: const EdgeInsets.only(top: 20, bottom: 12),
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              if (hata != null) HataKutusu(hata!),
              ...children,
            ]),
          ),
        ),
      ]),
    );
  }
}

class HataKutusu extends StatelessWidget {
  final String mesaj;
  const HataKutusu(this.mesaj, {super.key});

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 18),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: context.renk.tehlike.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(children: [
          Icon(CupertinoIcons.exclamationmark_triangle_fill, color: context.renk.tehlike, size: 20),
          const SizedBox(width: 10),
          Expanded(child: Text(mesaj, style: context.yazi.bodyMedium?.copyWith(color: context.renk.tehlike))),
        ]),
      );
}

double _etiketGenislik(BuildContext c) => Ekran.tablet(c) ? 150 : 116;

/// "Etiket   [metin alanı]" — iOS ayar formu satırı.
class MetinSatiri extends StatelessWidget {
  final String etiket;
  final TextEditingController kontrolcu;
  final String? ipucu;
  final TextInputType? klavye;
  final bool buyukHarfli;
  final int satir;
  final String? sonEk;
  final bool otomatikOdak;
  final ValueChanged<String>? degisti;
  final Widget? sag;
  final List<TextInputFormatter>? bicim;

  const MetinSatiri({
    required this.etiket,
    required this.kontrolcu,
    this.ipucu,
    this.klavye,
    this.buyukHarfli = false,
    this.satir = 1,
    this.sonEk,
    this.otomatikOdak = false,
    this.degisti,
    this.sag,
    this.bicim,
    super.key,
  });

  /// Para / ondalık alanı.
  const MetinSatiri.para({
    required this.etiket,
    required this.kontrolcu,
    this.ipucu = '0,00',
    this.degisti,
    this.otomatikOdak = false,
    super.key,
  })  : klavye = const TextInputType.numberWithOptions(decimal: true),
        buyukHarfli = false,
        satir = 1,
        sonEk = '₺',
        sag = null,
        bicim = null;

  @override
  Widget build(BuildContext context) {
    final alan = TextField(
      controller: kontrolcu,
      keyboardType: klavye ?? (satir > 1 ? TextInputType.multiline : TextInputType.text),
      textCapitalization: buyukHarfli ? TextCapitalization.characters : TextCapitalization.sentences,
      inputFormatters: buyukHarfli ? [_BuyukHarfBicimi(), ...?bicim] : bicim,
      minLines: satir > 1 ? satir : 1,
      maxLines: satir > 1 ? satir + 3 : 1,
      autofocus: otomatikOdak,
      onChanged: degisti,
      style: context.yazi.bodyLarge,
      decoration: InputDecoration(
        hintText: ipucu,
        filled: false,
        border: InputBorder.none,
        contentPadding: const EdgeInsets.symmetric(vertical: 14),
        suffixText: sonEk,
        suffixStyle: context.yazi.bodyLarge?.copyWith(color: context.renk.ikincil),
      ),
    );
    if (satir > 1) {
      return Padding(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(etiket, style: context.yazi.labelMedium),
          alan,
        ]),
      );
    }
    return Padding(
      padding: const EdgeInsets.only(left: 16, right: 8),
      child: Row(children: [
        SizedBox(width: _etiketGenislik(context), child: Text(etiket, style: context.yazi.bodyLarge)),
        Expanded(child: alan),
        if (sag != null) sag!,
      ]),
    );
  }
}

class _BuyukHarfBicimi extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue eski, TextEditingValue yeni) => yeni.copyWith(text: buyukHarf(yeni.text));
}

/// "Etiket ........ Seçili değer ›" — dokununca seçim açar.
class SecimSatiri extends StatelessWidget {
  final String etiket;
  final String? deger;
  final String ipucu;
  final VoidCallback? onTap;

  const SecimSatiri({required this.etiket, this.deger, this.ipucu = 'Seçin', this.onTap, super.key});

  @override
  Widget build(BuildContext context) {
    final bos = deger == null || deger!.isEmpty;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(children: [
          SizedBox(width: _etiketGenislik(context), child: Text(etiket, style: context.yazi.bodyLarge)),
          Expanded(
            child: Text(
              bos ? ipucu : deger!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: context.yazi.bodyLarge?.copyWith(
                color: onTap == null ? context.renk.ucuncul : (bos ? context.renk.ikincil : context.renk.metin),
              ),
            ),
          ),
          Icon(CupertinoIcons.chevron_up_chevron_down, size: 16, color: context.renk.ikincil),
        ]),
      ),
    );
  }
}

class AnahtarSatiri extends StatelessWidget {
  final String etiket;
  final bool deger;
  final ValueChanged<bool> degisti;
  const AnahtarSatiri({required this.etiket, required this.deger, required this.degisti, super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(children: [
          Expanded(child: Text(etiket, style: context.yazi.bodyLarge)),
          CupertinoSwitch(value: deger, activeTrackColor: context.renk.basari, onChanged: degisti),
        ]),
      );
}

/// iOS adım düğmesi:  [ − ]  4  [ + ]
class Adimlayici extends StatelessWidget {
  final int deger;
  final int min;
  final int max;
  final ValueChanged<int> degisti;
  const Adimlayici({required this.deger, required this.degisti, this.min = 1, this.max = 9999, super.key});

  @override
  Widget build(BuildContext context) {
    Widget dugme(IconData ikon, bool aktif, VoidCallback f) => CupertinoButton(
          padding: EdgeInsets.zero,
          minimumSize: const Size(40, 34),
          onPressed: aktif
              ? () {
                  HapticFeedback.selectionClick();
                  f();
                }
              : null,
          child: Icon(ikon, size: 18, color: aktif ? context.renk.metin : context.renk.ucuncul),
        );
    return Container(
      decoration: BoxDecoration(color: context.renk.dolgu, borderRadius: BorderRadius.circular(9)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        dugme(CupertinoIcons.minus, deger > min, () => degisti(deger - 1)),
        ConstrainedBox(
          constraints: const BoxConstraints(minWidth: 28),
          child: Text('$deger', textAlign: TextAlign.center, style: context.yazi.titleSmall),
        ),
        dugme(CupertinoIcons.plus, deger < max, () => degisti(deger + 1)),
      ]),
    );
  }
}

class AdimSatiri extends StatelessWidget {
  final String etiket;
  final int deger;
  final int min;
  final int max;
  final ValueChanged<int> degisti;
  const AdimSatiri({required this.etiket, required this.deger, required this.degisti, this.min = 1, this.max = 9999, super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(children: [
          Expanded(child: Text(etiket, style: context.yazi.bodyLarge)),
          Adimlayici(deger: deger, min: min, max: max, degisti: degisti),
        ]),
      );
}

class SegmentSatiri<T extends Object> extends StatelessWidget {
  final String etiket;
  final Map<T, String> secenekler;
  final T secili;
  final ValueChanged<T> degisti;
  const SegmentSatiri({required this.etiket, required this.secenekler, required this.secili, required this.degisti, super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
        child: Row(children: [
          SizedBox(width: _etiketGenislik(context), child: Text(etiket, style: context.yazi.bodyLarge)),
          Expanded(
            child: Align(
              alignment: Alignment.centerRight,
              child: SegmentSecici<T>(secenekler: secenekler, secili: secili, degisti: degisti),
            ),
          ),
        ]),
      );
}

class TarihSatiri extends StatelessWidget {
  final String etiket;
  final DateTime deger;
  final ValueChanged<DateTime> degisti;
  const TarihSatiri({required this.etiket, required this.deger, required this.degisti, super.key});

  @override
  Widget build(BuildContext context) => SecimSatiri(
        etiket: etiket,
        deger: tarih(deger.toIso8601String()),
        onTap: () async {
          final t = await showDatePicker(
            context: context,
            initialDate: deger,
            firstDate: DateTime(2020),
            lastDate: DateTime.now().add(const Duration(days: 365)),
          );
          if (t != null) degisti(t);
        },
      );
}

// ─── Aramalı seçim listesi ──────────────────────────────────────────────────

/// Arama yapılabilen seçim sayfası. Seçilen kaydı döner.
Future<Json?> aramaliSec(
  BuildContext context, {
  required String baslik,
  required Future<List<Json>> Function(String arama) yukle,
  required String Function(Json) satirBaslik,
  String? Function(Json)? satirAlt,
  String? Function(Json)? satirSag,
  String aramaIpucu = 'Ara',
  bool yerelFiltre = false,
  Future<Json?> Function(BuildContext)? yeniEkle,
}) {
  return formAc<Json>(
    context,
    (ctx) => _AramaliSecim(
      baslik: baslik,
      yukle: yukle,
      satirBaslik: satirBaslik,
      satirAlt: satirAlt,
      satirSag: satirSag,
      aramaIpucu: aramaIpucu,
      yerelFiltre: yerelFiltre,
      yeniEkle: yeniEkle,
    ),
    genislik: 520,
  );
}

class _AramaliSecim extends StatefulWidget {
  final String baslik;
  final Future<List<Json>> Function(String) yukle;
  final String Function(Json) satirBaslik;
  final String? Function(Json)? satirAlt;
  final String? Function(Json)? satirSag;
  final String aramaIpucu;
  final bool yerelFiltre;
  final Future<Json?> Function(BuildContext)? yeniEkle;

  const _AramaliSecim({
    required this.baslik,
    required this.yukle,
    required this.satirBaslik,
    required this.aramaIpucu,
    required this.yerelFiltre,
    this.satirAlt,
    this.satirSag,
    this.yeniEkle,
  });

  @override
  State<_AramaliSecim> createState() => _AramaliSecimState();
}

class _AramaliSecimState extends State<_AramaliSecim> {
  List<Json> _hepsi = [];
  List<Json> _gorunen = [];
  bool _yukleniyor = true;
  String? _hata;
  String _arama = '';
  int _istek = 0;

  @override
  void initState() {
    super.initState();
    _getir('');
  }

  Future<void> _getir(String q) async {
    _arama = q;
    if (widget.yerelFiltre && _hepsi.isNotEmpty) {
      setState(() => _gorunen = _filtrele(_hepsi, q));
      return;
    }
    final no = ++_istek;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    try {
      final v = await widget.yukle(widget.yerelFiltre ? '' : q);
      if (!mounted || no != _istek) return;
      setState(() {
        _hepsi = v;
        _gorunen = widget.yerelFiltre ? _filtrele(v, q) : v;
        _yukleniyor = false;
      });
    } catch (e) {
      if (!mounted || no != _istek) return;
      setState(() {
        _hata = hataMesaji(e);
        _yukleniyor = false;
      });
    }
  }

  List<Json> _filtrele(List<Json> v, String q) {
    if (q.isEmpty) return v;
    final k = q.toLowerCase();
    return v.where((e) => e.values.any((d) => d != null && d.toString().toLowerCase().contains(k))).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: context.renk.arkaplan,
      child: Column(children: [
        PanelBaslik(
          widget.baslik,
          solEylem: UstDugme(metin: 'Vazgeç', onTap: () => Navigator.pop(context)),
          eylemler: [
            if (widget.yeniEkle != null)
              UstDugme(
                ikon: CupertinoIcons.add,
                ipucu: 'Yeni ekle',
                onTap: () async {
                  final yeni = await widget.yeniEkle!(context);
                  if (yeni != null && context.mounted) Navigator.pop(context, yeni);
                },
              ),
          ],
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: AramaKutusu(ipucu: widget.aramaIpucu, degisti: _getir),
        ),
        Expanded(
          child: _yukleniyor
              ? const Yukleniyor()
              : _hata != null
                  ? HataDurum(_hata!, () => _getir(_arama))
                  : _gorunen.isEmpty
                      ? const BosDurum(ikon: CupertinoIcons.search, baslik: 'Sonuç yok')
                      : ListView(
                          padding: const EdgeInsets.only(top: 8),
                          children: [
                            Grup(children: [
                              for (final o in _gorunen)
                                Satir(
                                  baslik: widget.satirBaslik(o),
                                  alt: widget.satirAlt?.call(o),
                                  sagMetin: widget.satirSag?.call(o),
                                  okIsareti: false,
                                  onTap: () => Navigator.pop(context, o),
                                ),
                            ]),
                          ],
                        ),
        ),
      ]),
    );
  }
}

/// Tek bir sayı soran iOS uyarı penceresi (fiyat düzeltme vb.).
Future<double?> sayiSor(BuildContext context, {required String baslik, String? mesaj, double? baslangic, String sonEk = '₺'}) {
  final k = TextEditingController(text: baslangic == null ? '' : paraSade(baslangic));
  return showCupertinoDialog<double>(
    context: context,
    barrierDismissible: true,
    builder: (ctx) => CupertinoAlertDialog(
      title: Text(baslik),
      content: Column(children: [
        if (mesaj != null) Padding(padding: const EdgeInsets.only(top: 4, bottom: 4), child: Text(mesaj)),
        const SizedBox(height: 10),
        CupertinoTextField(
          controller: k,
          autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          suffix: Padding(padding: const EdgeInsets.only(right: 8), child: Text(sonEk)),
          onTap: () => k.selection = TextSelection(baseOffset: 0, extentOffset: k.text.length),
        ),
      ]),
      actions: [
        CupertinoDialogAction(onPressed: () => Navigator.pop(ctx), child: const Text('Vazgeç')),
        CupertinoDialogAction(
          isDefaultAction: true,
          onPressed: () => Navigator.pop(ctx, sayiOku(k.text)),
          child: const Text('Tamam'),
        ),
      ],
    ),
  );
}
