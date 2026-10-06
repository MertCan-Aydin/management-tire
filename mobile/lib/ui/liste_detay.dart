import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../core/format.dart';
import 'bilesenler.dart';
import 'tema.dart';

/// Detay içeriğinin nerede gösterildiğini ve nasıl kapatılacağını bildirir.
class DetayKapsami extends InheritedWidget {
  /// true → itilen tam sayfa (geri düğmesi gösterilir).
  final bool tamSayfa;

  /// Kayıt silindiğinde/iptal edildiğinde detayı kapatır.
  final VoidCallback kapat;

  const DetayKapsami({required this.tamSayfa, required this.kapat, required super.child, super.key});

  static DetayKapsami of(BuildContext c) => c.dependOnInheritedWidgetOfExactType<DetayKapsami>()!;

  @override
  bool updateShouldNotify(DetayKapsami old) => old.tamSayfa != tamSayfa;
}

/// iPad tarzı liste + detay düzeni.
///
/// Geniş alanda liste solda, seçilen kaydın detayı sağda durur.
/// Dar alanda yalnızca liste görünür, seçim detay sayfasını iter.
class ListeDetay extends StatefulWidget {
  final Widget Function(BuildContext context, void Function(Json oge) sec, int? seciliId) liste;
  final Widget Function(BuildContext context, Json oge) detay;
  final IconData bosIkon;
  final String bosMetin;

  const ListeDetay({
    required this.liste,
    required this.detay,
    this.bosIkon = CupertinoIcons.doc_text,
    this.bosMetin = 'Ayrıntıları görmek için soldan bir kayıt seçin',
    super.key,
  });

  @override
  State<ListeDetay> createState() => _ListeDetayState();
}

class _ListeDetayState extends State<ListeDetay> {
  Json? _secili;
  bool _bolunmus = false;

  void _sec(Json oge) {
    if (_bolunmus) {
      setState(() => _secili = oge);
      return;
    }
    Navigator.of(context).push(CupertinoPageRoute(
      builder: (ctx) => Scaffold(
        body: SafeArea(
          bottom: false,
          child: Builder(
            builder: (ic) => DetayKapsami(
              tamSayfa: true,
              kapat: () => Navigator.of(ic).maybePop(),
              child: widget.detay(ic, oge),
            ),
          ),
        ),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, c) {
      _bolunmus = c.maxWidth >= Ekran.bolunmusEsik;
      final liste = widget.liste(context, _sec, _bolunmus ? tamSayi(_secili?['id']) : null);
      if (!_bolunmus) return liste;

      final listeGenislik = (c.maxWidth * 0.40).clamp(320.0, 440.0);
      return Row(children: [
        SizedBox(width: listeGenislik, child: liste),
        VerticalDivider(width: 1, thickness: 0, color: context.renk.ayrac),
        Expanded(
          child: _secili == null
              ? BosDurum(ikon: widget.bosIkon, baslik: 'Kayıt seçilmedi', aciklama: widget.bosMetin)
              : DetayKapsami(
                  key: ValueKey(_secili!['id']),
                  tamSayfa: false,
                  kapat: () => setState(() => _secili = null),
                  child: widget.detay(context, _secili!),
                ),
        ),
      ]);
    });
  }
}
