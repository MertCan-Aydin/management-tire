import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../giderler/giderler_sayfasi.dart';
import '../alim/alim_formu.dart';

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

  Future<void> _devamEt(Json taslak) async {
    final formTipi = taslak['form_tipi'] as String;
    final veri = taslak['veri'] as Map<String, dynamic>? ?? {};
    final taslakId = tamSayi(taslak['id']);

    if (formTipi == 'gider') {
      await giderFormuAc(context, taslakVeri: veri, taslakId: taslakId);
    } else if (formTipi == 'alim') {
      await alimFormuAcTaslakli(context, taslakVeri: veri, taslakId: taslakId);
    }
    yenile();
  }
}
