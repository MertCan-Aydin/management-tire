import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/api_client.dart';
import 'bilesenler.dart';
import 'liste_detay.dart';
import 'tema.dart';

/// Ekranın verisini yükler, hata/yükleniyor durumunu tutar ve başka bir
/// ekranda kayıt değiştiğinde ([veriDegisti]) kendini sessizce yeniler.
mixin VeriYukleyici<W extends StatefulWidget, V> on State<W> {
  V? veri;
  bool yukleniyor = true;
  String? hata;
  int _istek = 0;

  Future<V> getir();

  /// Detay ekranları ilk anda listedeki satırı göstermek için kullanır.
  V? get ilkVeri => null;

  @override
  void initState() {
    super.initState();
    veri = ilkVeri;
    veriSurumu.addListener(_disaridanDegisti);
    yenile();
  }

  @override
  void dispose() {
    veriSurumu.removeListener(_disaridanDegisti);
    super.dispose();
  }

  void _disaridanDegisti() => yenile(sessiz: true);

  Future<void> yenile({bool sessiz = false}) async {
    final no = ++_istek;
    if (!sessiz) {
      setState(() {
        yukleniyor = true;
        hata = null;
      });
    }
    try {
      final v = await getir();
      if (!mounted || no != _istek) return;
      setState(() {
        veri = v;
        yukleniyor = false;
        hata = null;
      });
    } catch (e) {
      if (!mounted || no != _istek) return;
      setState(() {
        hata = hataMesaji(e);
        yukleniyor = false;
      });
    }
  }

  /// Veri yoksa yükleniyor/hata ekranını, varsa [icerik]'i gösterir.
  Widget durum(Widget Function(V veri) icerik) {
    if (veri == null) {
      if (hata != null) return HataDurum(hata!, yenile);
      return const Yukleniyor();
    }
    return icerik(veri as V);
  }
}

/// iOS tarzı "aşağı çekince yenile" destekli kaydırılabilir liste.
class YenilenebilirListe extends StatelessWidget {
  final Future<void> Function() yenile;
  final List<Widget> children;
  final EdgeInsetsGeometry padding;

  const YenilenebilirListe(
      {required this.yenile, required this.children, this.padding = const EdgeInsets.only(top: 4, bottom: 24), super.key});

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      slivers: [
        CupertinoSliverRefreshControl(onRefresh: yenile),
        SliverPadding(padding: padding, sliver: SliverList(delegate: SliverChildListDelegate(children))),
      ],
    );
  }
}

/// Liste modüllerinin üst kısmı: büyük başlık + arama + filtre.
class ListeUstu extends StatelessWidget {
  final String baslik;
  final String? altBaslik;
  final List<Widget> eylemler;
  final Widget? arama;
  final Widget? filtre;

  const ListeUstu({required this.baslik, this.altBaslik, this.eylemler = const [], this.arama, this.filtre, super.key});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      BuyukBaslik(baslik, altBaslik: altBaslik, eylemler: eylemler),
      if (arama != null) Padding(padding: const EdgeInsets.fromLTRB(16, 6, 16, 4), child: arama),
      if (filtre != null) Padding(padding: const EdgeInsets.fromLTRB(16, 8, 16, 4), child: filtre),
      const SizedBox(height: 8),
    ]);
  }
}

/// Detay paneli / sayfası iskeleti.
class DetayIskeleti extends StatelessWidget {
  final String baslik;
  final List<Widget> eylemler;
  final List<Widget> children;
  final Future<void> Function()? yenile;

  const DetayIskeleti({required this.baslik, required this.children, this.eylemler = const [], this.yenile, super.key});

  @override
  Widget build(BuildContext context) {
    final tamSayfa = DetayKapsami.of(context).tamSayfa;
    final icerik = OkunurGenislik(
      max: 720,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children),
    );
    return Column(children: [
      PanelBaslik(baslik, geri: tamSayfa, eylemler: eylemler),
      Expanded(
        child: yenile == null
            ? SingleChildScrollView(padding: const EdgeInsets.only(top: 20, bottom: 32), child: icerik)
            : YenilenebilirListe(yenile: yenile!, padding: const EdgeInsets.only(top: 20, bottom: 32), children: [icerik]),
      ),
    ]);
  }
}

/// Detay sayfasının en üstündeki büyük ikon + başlık (iOS Kişiler).
class DetayKafa extends StatelessWidget {
  final IconData? ikon;
  final String? harfler;
  final Color renk;
  final String baslik;
  final String? alt;
  final Widget? rozet;
  final String? buyukDeger;
  final bool ikonGoster;

  const DetayKafa({
    required this.renk,
    required this.baslik,
    this.ikon,
    this.harfler,
    this.alt,
    this.rozet,
    this.buyukDeger,
    this.ikonGoster = true,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      child: Column(children: [
        if (ikonGoster) ...[
          Container(
            width: 76,
            height: 76,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [renk.withValues(alpha: 0.75), renk],
              ),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: harfler != null
                  ? Text(harfler!,
                      style: const TextStyle(fontFamily: kFont, fontSize: 28, fontWeight: FontWeight.w600, color: Colors.white))
                  : Icon(ikon, color: Colors.white, size: 36),
            ),
          ),
          const SizedBox(height: 12),
        ],
        Text(baslik, textAlign: TextAlign.center, style: context.yazi.headlineSmall),
        if (alt != null && alt!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(alt!, textAlign: TextAlign.center, style: context.yazi.bodyMedium?.copyWith(color: context.renk.ikincil)),
        ],
        if (buyukDeger != null) ...[
          const SizedBox(height: 10),
          Text(buyukDeger!, style: context.yazi.headlineMedium?.copyWith(fontFeatures: const [FontFeature.tabularFigures()])),
        ],
        if (rozet != null) ...[const SizedBox(height: 10), rozet!],
      ]),
    );
  }
}

/// Detay ekranındaki büyük eylem düğmeleri satırı (Düzenle / Sil / Ödeme...).
class EylemDugmeleri extends StatelessWidget {
  final List<(IconData, String, VoidCallback?, Color?)> dugmeler;
  const EylemDugmeleri(this.dugmeler, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 22),
      child: Row(children: [
        for (var i = 0; i < dugmeler.length; i++) ...[
          if (i > 0) const SizedBox(width: 10),
          Expanded(child: _EylemKutusu(dugmeler[i])),
        ],
      ]),
    );
  }
}

class _EylemKutusu extends StatelessWidget {
  final (IconData, String, VoidCallback?, Color?) d;
  const _EylemKutusu(this.d);

  @override
  Widget build(BuildContext context) {
    final (ikon, metin, onTap, renk) = d;
    final c = onTap == null ? context.renk.ucuncul : (renk ?? context.renk.ana);
    return Material(
      color: context.renk.kart,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: SizedBox(
          height: 64,
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(ikon, color: c, size: 22),
            const SizedBox(height: 4),
            Text(metin, style: context.yazi.labelSmall?.copyWith(color: c, fontSize: 13)),
          ]),
        ),
      ),
    );
  }
}

/// "Ahmet Yılmaz" → "AY"
String basHarfler(String ad) {
  final p = ad.trim().split(RegExp(r'\s+')).where((e) => e.isNotEmpty).toList();
  if (p.isEmpty) return '?';
  final a = p.first.characters.first;
  final b = p.length > 1 ? p.last.characters.first : '';
  return (a + b).toUpperCase();
}
