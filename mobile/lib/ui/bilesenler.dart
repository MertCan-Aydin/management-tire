import 'dart:async';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/format.dart';
import 'tema.dart';

// ─── Ekran genişliği eşikleri ────────────────────────────────────────────────

/// Honor Pad X9 yatay ≈ 1333 dp, dikey ≈ 800 dp.
class Ekran {
  static const tabletEsik = 600.0; // altı telefon
  static const kenarCubuguEsik = 1000.0; // üstünde kalıcı kenar çubuğu
  static const bolunmusEsik = 900.0; // içerik alanı bundan genişse liste+detay yan yana (dikey tablette tek sütun)

  static double genislik(BuildContext c) => MediaQuery.sizeOf(c).width;
  static bool telefon(BuildContext c) => genislik(c) < tabletEsik;
  static bool tablet(BuildContext c) => genislik(c) >= tabletEsik;
}

// ─── Kabuk: alt sayfaların kenar çubuğunu açabilmesi için ──────────────────

class KabukKapsami extends InheritedWidget {
  /// Dikey tablette kenar çubuğunu açar; diğer düzenlerde null.
  final VoidCallback? menuAc;
  const KabukKapsami({required this.menuAc, required super.child, super.key});

  static VoidCallback? menuAcici(BuildContext c) => c.dependOnInheritedWidgetOfExactType<KabukKapsami>()?.menuAc;

  @override
  bool updateShouldNotify(KabukKapsami old) => old.menuAc != menuAc;
}

// ─── Büyük başlık (iOS Large Title) ─────────────────────────────────────────

class BuyukBaslik extends StatelessWidget {
  final String baslik;
  final String? altBaslik;
  final List<Widget> eylemler;
  final bool geriDugmesi;

  const BuyukBaslik(this.baslik, {this.altBaslik, this.eylemler = const [], this.geriDugmesi = false, super.key});

  @override
  Widget build(BuildContext context) {
    final menuAc = KabukKapsami.menuAcici(context);
    final geri = geriDugmesi || (ModalRoute.of(context)?.canPop ?? false);
    final ust = <Widget>[
      if (geri)
        const GeriDugmesi()
      else if (menuAc != null)
        UstDugme(ikon: CupertinoIcons.sidebar_left, ipucu: 'Menü', onTap: menuAc),
      const Spacer(),
      ...eylemler,
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 12, 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(height: 44, child: Row(children: ust)),
          Text(baslik, style: context.yazi.displaySmall, maxLines: 1, overflow: TextOverflow.ellipsis),
          if (altBaslik != null) ...[
            const SizedBox(height: 2),
            Text(altBaslik!, style: context.yazi.bodyMedium?.copyWith(color: context.renk.ikincil)),
          ],
        ],
      ),
    );
  }
}

/// Detay panelinin / itilen sayfanın üst çubuğu (iOS Navigation Bar).
class PanelBaslik extends StatelessWidget {
  final String baslik;
  final bool geri;
  final List<Widget> eylemler;
  final Widget? solEylem;

  const PanelBaslik(this.baslik, {this.geri = false, this.eylemler = const [], this.solEylem, super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: context.renk.arkaplan,
        border: Border(bottom: BorderSide(color: context.renk.ayrac, width: 0)),
      ),
      child: NavigationToolbar(
        leading: geri ? const GeriDugmesi() : solEylem,
        middle: Text(baslik, style: context.yazi.titleMedium, maxLines: 1, overflow: TextOverflow.ellipsis),
        trailing: Row(mainAxisSize: MainAxisSize.min, children: eylemler),
        centerMiddle: true,
        middleSpacing: 12,
      ),
    );
  }
}

class GeriDugmesi extends StatelessWidget {
  final String etiket;
  const GeriDugmesi({this.etiket = 'Geri', super.key});

  @override
  Widget build(BuildContext context) {
    return CupertinoButton(
      padding: const EdgeInsets.only(left: 2, right: 8),
      minimumSize: const Size(44, 44),
      onPressed: () => Navigator.maybePop(context),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(CupertinoIcons.chevron_back, color: context.renk.ana, size: 26),
        Text(etiket, style: TextStyle(fontFamily: kFont, fontSize: 17, color: context.renk.ana)),
      ]),
    );
  }
}

/// Başlık çubuğundaki ikon ya da metin düğmesi.
class UstDugme extends StatelessWidget {
  final IconData? ikon;
  final String? metin;
  final String? ipucu;
  final VoidCallback? onTap;
  final bool kalin;
  final bool yukleniyor;
  final Color? renk;

  const UstDugme(
      {this.ikon, this.metin, this.ipucu, this.onTap, this.kalin = false, this.yukleniyor = false, this.renk, super.key});

  @override
  Widget build(BuildContext context) {
    final c = onTap == null ? context.renk.ucuncul : (renk ?? context.renk.ana);
    Widget icerik = yukleniyor
        ? const CupertinoActivityIndicator()
        : ikon != null
            ? Icon(ikon, color: c, size: 24)
            : Text(metin ?? '',
                style:
                    TextStyle(fontFamily: kFont, fontSize: 17, color: c, fontWeight: kalin ? FontWeight.w600 : FontWeight.w400));
    final dugme = CupertinoButton(
      padding: const EdgeInsets.symmetric(horizontal: 10),
      minimumSize: const Size(44, 44),
      onPressed: yukleniyor ? null : onTap,
      child: icerik,
    );
    return ipucu == null ? dugme : Tooltip(message: ipucu!, child: dugme);
  }
}

// ─── Arama ve segment ───────────────────────────────────────────────────────

class AramaKutusu extends StatefulWidget {
  final String ipucu;
  final ValueChanged<String> degisti;
  final TextEditingController? kontrolcu;
  final Duration gecikme;
  final bool otomatikOdak;

  const AramaKutusu({
    required this.degisti,
    this.ipucu = 'Ara',
    this.kontrolcu,
    this.gecikme = const Duration(milliseconds: 350),
    this.otomatikOdak = false,
    super.key,
  });

  @override
  State<AramaKutusu> createState() => _AramaKutusuState();
}

class _AramaKutusuState extends State<AramaKutusu> {
  Timer? _zamanlayici;

  @override
  void dispose() {
    _zamanlayici?.cancel();
    super.dispose();
  }

  void _degisti(String v) {
    _zamanlayici?.cancel();
    _zamanlayici = Timer(widget.gecikme, () => widget.degisti(v.trim()));
  }

  @override
  Widget build(BuildContext context) {
    return CupertinoSearchTextField(
      controller: widget.kontrolcu,
      placeholder: widget.ipucu,
      autofocus: widget.otomatikOdak,
      style: TextStyle(fontFamily: kFont, fontSize: 17, color: context.renk.metin),
      placeholderStyle: TextStyle(fontFamily: kFont, fontSize: 17, color: context.renk.ikincil),
      backgroundColor: context.renk.dolgu,
      itemColor: context.renk.ikincil,
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 10),
      onChanged: _degisti,
      onSubmitted: (v) {
        _zamanlayici?.cancel();
        widget.degisti(v.trim());
      },
      onSuffixTap: () {
        widget.kontrolcu?.clear();
        _zamanlayici?.cancel();
        widget.degisti('');
      },
    );
  }
}

class SegmentSecici<T extends Object> extends StatelessWidget {
  final Map<T, String> secenekler;
  final T secili;
  final ValueChanged<T> degisti;

  const SegmentSecici({required this.secenekler, required this.secili, required this.degisti, super.key});

  @override
  Widget build(BuildContext context) {
    return CupertinoSlidingSegmentedControl<T>(
      groupValue: secili,
      backgroundColor: context.renk.dolgu,
      thumbColor: Theme.of(context).brightness == Brightness.light ? Colors.white : context.renk.kart2,
      padding: const EdgeInsets.all(2),
      children: {
        for (final e in secenekler.entries)
          e.key: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            child: Text(e.value,
                style: TextStyle(
                  fontFamily: kFont,
                  fontSize: 14,
                  fontWeight: e.key == secili ? FontWeight.w600 : FontWeight.w500,
                  color: context.renk.metin,
                )),
          ),
      },
      onValueChanged: (v) {
        if (v != null) degisti(v);
      },
    );
  }
}

// ─── Gruplu liste (iOS Inset Grouped) ───────────────────────────────────────

class Grup extends StatelessWidget {
  final String? baslik;
  final Widget? baslikEylem;
  final String? altNot;
  final List<Widget> children;
  final EdgeInsetsGeometry dis;
  final double girinti; // ayraç sol boşluğu

  const Grup({
    required this.children,
    this.baslik,
    this.baslikEylem,
    this.altNot,
    this.dis = const EdgeInsets.fromLTRB(16, 0, 16, 22),
    this.girinti = 16,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final ogeler = <Widget>[];
    for (var i = 0; i < children.length; i++) {
      if (i > 0) ogeler.add(Padding(padding: EdgeInsetsDirectional.only(start: girinti), child: const Divider()));
      ogeler.add(children[i]);
    }
    return Padding(
      padding: dis,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (baslik != null || baslikEylem != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 4, 6),
              child: Row(children: [
                if (baslik != null)
                  Expanded(
                    child: Text(buyukHarf(baslik!), style: context.yazi.labelMedium?.copyWith(letterSpacing: 0.2)),
                  ),
                if (baslikEylem != null) baslikEylem!,
              ]),
            ),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Material(
              color: context.renk.kart,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: ogeler),
            ),
          ),
          if (altNot != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
              child: Text(altNot!, style: context.yazi.bodySmall),
            ),
        ],
      ),
    );
  }
}

/// Renkli kare zeminli ikon (iOS Ayarlar).
class IkonKutusu extends StatelessWidget {
  final IconData ikon;
  final Color renk;
  final double boyut;
  const IkonKutusu(this.ikon, this.renk, {this.boyut = 30, super.key});

  @override
  Widget build(BuildContext context) => Container(
        width: boyut,
        height: boyut,
        decoration: BoxDecoration(color: renk, borderRadius: BorderRadius.circular(boyut * 0.24)),
        child: Icon(ikon, color: Colors.white, size: boyut * 0.6),
      );
}

class Satir extends StatelessWidget {
  final Widget? onde;
  final String baslik;
  final String? alt;
  final Widget? sag;
  final String? sagMetin;
  final VoidCallback? onTap;
  final bool secili;
  final bool okIsareti;
  final Color? baslikRengi;
  final int altSatirSayisi;

  const Satir({
    required this.baslik,
    this.onde,
    this.alt,
    this.sag,
    this.sagMetin,
    this.onTap,
    this.secili = false,
    this.okIsareti = true,
    this.baslikRengi,
    this.altSatirSayisi = 1,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Material(
      color: secili ? r.anaAcik : Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 50),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(children: [
              if (onde != null) ...[onde!, const SizedBox(width: 12)],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(baslik,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: context.yazi.bodyLarge?.copyWith(
                          color: baslikRengi,
                          fontWeight: secili ? FontWeight.w600 : null,
                        )),
                    if (alt != null && alt!.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(alt!,
                          maxLines: altSatirSayisi,
                          overflow: TextOverflow.ellipsis,
                          style: context.yazi.bodyMedium?.copyWith(color: r.ikincil)),
                    ],
                  ],
                ),
              ),
              if (sagMetin != null) ...[
                const SizedBox(width: 8),
                Text(sagMetin!, style: context.yazi.bodyLarge?.copyWith(color: r.ikincil)),
              ],
              if (sag != null) ...[const SizedBox(width: 8), sag!],
              if (onTap != null && okIsareti) ...[
                const SizedBox(width: 6),
                Icon(CupertinoIcons.chevron_forward, size: 18, color: r.ucuncul),
              ],
            ]),
          ),
        ),
      ),
    );
  }
}

/// Detay ekranlarında "Etiket ........ Değer" satırı.
class BilgiSatiri extends StatelessWidget {
  final String etiket;
  final String? deger;
  final Color? degerRengi;
  final bool kalin;

  const BilgiSatiri(this.etiket, this.deger, {this.degerRengi, this.kalin = false, super.key});

  @override
  Widget build(BuildContext context) {
    final d = (deger == null || deger!.trim().isEmpty) ? '—' : deger!;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(etiket, style: context.yazi.bodyLarge),
        const SizedBox(width: 16),
        Expanded(
          child: Text(d,
              textAlign: TextAlign.right,
              style: context.yazi.bodyLarge?.copyWith(
                color: degerRengi ?? context.renk.ikincil,
                fontWeight: kalin ? FontWeight.w600 : null,
              )),
        ),
      ]),
    );
  }
}

/// Grup içinde ortalanmış eylem satırı (ör. kırmızı "Sil").
class EylemSatiri extends StatelessWidget {
  final String metin;
  final IconData? ikon;
  final VoidCallback? onTap;
  final bool yikici;

  const EylemSatiri(this.metin, {this.ikon, this.onTap, this.yikici = false, super.key});

  @override
  Widget build(BuildContext context) {
    final c = onTap == null ? context.renk.ucuncul : (yikici ? context.renk.tehlike : context.renk.ana);
    return InkWell(
      onTap: onTap,
      child: SizedBox(
        height: 50,
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          if (ikon != null) ...[Icon(ikon, color: c, size: 20), const SizedBox(width: 8)],
          Text(metin, style: context.yazi.bodyLarge?.copyWith(color: c)),
        ]),
      ),
    );
  }
}

class Rozet extends StatelessWidget {
  final String metin;
  final Color renk;
  const Rozet(this.metin, this.renk, {super.key});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: renk.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(6)),
        child: Text(metin, style: TextStyle(fontFamily: kFont, fontSize: 12, fontWeight: FontWeight.w600, color: renk)),
      );
}

// ─── İstatistik kartı ───────────────────────────────────────────────────────

class IstatistikKarti extends StatelessWidget {
  final String baslik;
  final String deger;
  final IconData ikon;
  final Color renk;
  final String? alt;

  const IstatistikKarti({required this.baslik, required this.deger, required this.ikon, required this.renk, this.alt, super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: context.renk.kart, borderRadius: BorderRadius.circular(14)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(children: [
            IkonKutusu(ikon, renk, boyut: 28),
            const SizedBox(width: 10),
            Expanded(
              child: Text(baslik,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: context.yazi.titleSmall?.copyWith(color: context.renk.ikincil)),
            ),
          ]),
          const SizedBox(height: 14),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(deger, style: context.yazi.headlineMedium?.copyWith(fontFeatures: const [FontFeature.tabularFigures()])),
          ),
          if (alt != null) ...[
            const SizedBox(height: 2),
            Text(alt!, style: context.yazi.bodySmall),
          ],
        ],
      ),
    );
  }
}

/// Kartları genişliğe göre 1–4 sütuna yerleştirir.
class KartIzgarasi extends StatelessWidget {
  final List<Widget> children;
  final double minGenislik;
  final double bosluk;
  final int maxSutun;

  const KartIzgarasi({required this.children, this.minGenislik = 220, this.bosluk = 12, this.maxSutun = 4, super.key});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, c) {
      final sutun = (c.maxWidth / minGenislik).floor().clamp(1, maxSutun);
      final w = (c.maxWidth - bosluk * (sutun - 1)) / sutun;
      return Wrap(
        spacing: bosluk,
        runSpacing: bosluk,
        children: [for (final k in children) SizedBox(width: w, child: k)],
      );
    });
  }
}

// ─── Durum ekranları ────────────────────────────────────────────────────────

class Yukleniyor extends StatelessWidget {
  const Yukleniyor({super.key});
  @override
  Widget build(BuildContext context) => const Center(child: CupertinoActivityIndicator(radius: 14));
}

class BosDurum extends StatelessWidget {
  final IconData ikon;
  final String baslik;
  final String? aciklama;
  final Widget? eylem;

  const BosDurum({required this.ikon, required this.baslik, this.aciklama, this.eylem, super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(ikon, size: 52, color: context.renk.ucuncul),
          const SizedBox(height: 14),
          Text(baslik, textAlign: TextAlign.center, style: context.yazi.titleMedium),
          if (aciklama != null) ...[
            const SizedBox(height: 6),
            Text(aciklama!, textAlign: TextAlign.center, style: context.yazi.bodyMedium?.copyWith(color: context.renk.ikincil)),
          ],
          if (eylem != null) ...[const SizedBox(height: 18), eylem!],
        ]),
      ),
    );
  }
}

class HataDurum extends StatelessWidget {
  final String mesaj;
  final VoidCallback tekrar;
  const HataDurum(this.mesaj, this.tekrar, {super.key});

  @override
  Widget build(BuildContext context) => BosDurum(
        ikon: CupertinoIcons.wifi_exclamationmark,
        baslik: 'Yüklenemedi',
        aciklama: mesaj,
        eylem: CupertinoButton.tinted(onPressed: tekrar, child: const Text('Tekrar Dene')),
      );
}

// ─── Diyaloglar ve bildirimler ──────────────────────────────────────────────

Future<bool> onayla(
  BuildContext context, {
  required String baslik,
  String? mesaj,
  String onayMetni = 'Onayla',
  bool yikici = false,
}) async {
  final sonuc = await showCupertinoDialog<bool>(
    context: context,
    barrierDismissible: true,
    builder: (ctx) => CupertinoAlertDialog(
      title: Text(baslik),
      content: mesaj == null ? null : Padding(padding: const EdgeInsets.only(top: 4), child: Text(mesaj)),
      actions: [
        CupertinoDialogAction(onPressed: () => Navigator.pop(ctx, false), child: const Text('Vazgeç')),
        CupertinoDialogAction(
          isDefaultAction: !yikici,
          isDestructiveAction: yikici,
          onPressed: () => Navigator.pop(ctx, true),
          child: Text(onayMetni),
        ),
      ],
    ),
  );
  return sonuc == true;
}

void bildir(BuildContext context, String mesaj, {bool hata = false}) {
  if (hata) HapticFeedback.heavyImpact();
  final m = ScaffoldMessenger.maybeOf(context);
  if (m == null) return;
  m.hideCurrentSnackBar();
  final genis = Ekran.tablet(context);
  m.showSnackBar(SnackBar(
    width: genis ? 440 : null,
    content: Row(children: [
      Icon(hata ? CupertinoIcons.exclamationmark_circle_fill : CupertinoIcons.checkmark_circle_fill,
          color: hata ? const Color(0xFFFF6961) : const Color(0xFF30D158), size: 22),
      const SizedBox(width: 10),
      Expanded(child: Text(mesaj)),
    ]),
    duration: Duration(milliseconds: hata ? 3500 : 2000),
  ));
}

/// İçeriği okunabilir genişlikte tutar (tablette çok yayılmasın).
class OkunurGenislik extends StatelessWidget {
  final Widget child;
  final double max;
  const OkunurGenislik({required this.child, this.max = 760, super.key});

  @override
  Widget build(BuildContext context) =>
      Align(alignment: Alignment.topCenter, child: ConstrainedBox(constraints: BoxConstraints(maxWidth: max), child: child));
}
