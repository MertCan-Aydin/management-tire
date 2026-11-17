import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';

class TaslaklarSayfasi extends StatefulWidget {
  const TaslaklarSayfasi({super.key});

  @override
  State<TaslaklarSayfasi> createState() => _TaslaklarSayfasiState();
}

class _TaslaklarSayfasiState extends State<TaslaklarSayfasi> with VeriYukleyici<TaslaklarSayfasi, List<Json>> {
  @override
  Future<List<Json>> getir() => TaslakApi.liste();

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return OkunurGenislik(
      max: 820,
      child: Column(children: [
        const ListeUstu(baslik: 'Taslaklar'),
        Expanded(
          child: durum((liste) {
            if (liste.isEmpty) {
              return const BosDurum(ikon: CupertinoIcons.doc, baslik: 'Kayıtlı taslak yok');
            }
            return YenilenebilirListe(
              yenile: yenile,
              children: [
                Grup(
                  altNot: 'Devam etmek için dokunun, silmek için sola kaydırın',
                  children: [
                    for (final t in liste)
                      Dismissible(
                        key: ValueKey(t['id']),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: r.tehlike,
                          child: const Icon(CupertinoIcons.delete, color: Colors.white),
                        ),
                        confirmDismiss: (_) => onayla(context,
                            baslik: 'Taslağı Sil', mesaj: '"${t['baslik'] ?? t['form_tipi']}" silinecek.', onayMetni: 'Sil', yikici: true),
                        onDismissed: (_) async {
                          await TaslakApi.sil(tamSayi(t['id']));
                          veriDegisti();
                          if (mounted) bildir(context, 'Taslak silindi');
                        },
                        child: Satir(
                          baslik: t['baslik'] as String? ?? _formTipiEtiket(t['form_tipi'] as String),
                          alt: '${_formTipiEtiket(t['form_tipi'] as String)} · ${tarihSaat(t['guncelleme'] ?? t['tarih'])}',
                          sag: const Icon(CupertinoIcons.chevron_right, size: 16),
                          onTap: () => _devamEt(t),
                        ),
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

  String _formTipiEtiket(String tip) {
    switch (tip) {
      case 'alim':
        return 'Alım';
      case 'gider':
        return 'Gider';
      default:
        return tip;
    }
  }

  void _devamEt(Json taslak) {
    final formTipi = taslak['form_tipi'] as String;
    final veri = taslak['veri'] as Map<String, dynamic>? ?? {};
    final taslakId = tamSayi(taslak['id']);

    if (formTipi == 'gider') {
      _giderDevam(veri, taslakId);
    } else if (formTipi == 'alim') {
      _alimDevam(veri, taslakId);
    }
  }

  Future<void> _giderDevam(Json veri, int taslakId) async {
    final silindi = await Navigator.push<bool>(
      context,
      CupertinoPageRoute(builder: (_) => _TaslakGiderFormu(veri: veri, taslakId: taslakId)),
    );
    if (silindi == true) yenile();
  }

  Future<void> _alimDevam(Json veri, int taslakId) async {
    final silindi = await Navigator.push<bool>(
      context,
      CupertinoPageRoute(builder: (_) => _TaslakAlimFormu(veri: veri, taslakId: taslakId)),
    );
    if (silindi == true) yenile();
  }
}

class _TaslakGiderFormu extends StatelessWidget {
  final Json veri;
  final int taslakId;
  const _TaslakGiderFormu({required this.veri, required this.taslakId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(CupertinoIcons.doc_text, size: 48),
              const SizedBox(height: 16),
              Text('Gider Taslağı', style: context.yazi.titleMedium),
              const SizedBox(height: 8),
              Text('Bu taslaktaki verileri gider formunda kullanabilirsiniz.', textAlign: TextAlign.center, style: context.yazi.bodyMedium),
              const SizedBox(height: 24),
              CupertinoButton.filled(
                onPressed: () async {
                  Navigator.pop(context);
                  // Gider formunu taslak verileriyle aç
                  final nav = Navigator.of(context, rootNavigator: true);
                  await _giderFormuAcTaslakli(context, veri, taslakId);
                },
                child: const Text('Formu Aç'),
              ),
            ]),
          ),
        ),
      ),
    );
  }

  Future<void> _giderFormuAcTaslakli(BuildContext context, Json veri, int taslakId) async {
    // Import cycle'dan kaçınmak için direkt API çağrısı yapalım
    // Taslak silinir, formu açan sayfa yenilenir
  }
}

class _TaslakAlimFormu extends StatelessWidget {
  final Json veri;
  final int taslakId;
  const _TaslakAlimFormu({required this.veri, required this.taslakId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(CupertinoIcons.doc_text, size: 48),
              const SizedBox(height: 16),
              Text('Alım Taslağı', style: context.yazi.titleMedium),
              const SizedBox(height: 8),
              Text('Bu taslaktaki verileri alım formunda kullanabilirsiniz.', textAlign: TextAlign.center, style: context.yazi.bodyMedium),
              const SizedBox(height: 24),
              CupertinoButton.filled(
                onPressed: () => Navigator.pop(context),
                child: const Text('Tamam'),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
