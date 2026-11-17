import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';

class LoglarSayfasi extends StatefulWidget {
  const LoglarSayfasi({super.key});

  @override
  State<LoglarSayfasi> createState() => _LoglarSayfasiState();
}

class _LoglarSayfasiState extends State<LoglarSayfasi> with VeriYukleyici<LoglarSayfasi, List<Json>> {
  String? _filtre;

  @override
  Future<List<Json>> getir() => AktiviteApi.liste(limit: 500, islemTipi: _filtre);

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return OkunurGenislik(
      max: 820,
      child: Column(children: [
        ListeUstu(
          baslik: 'Aktivite Logları',
          filtre: SizedBox(
            width: double.infinity,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(spacing: 8, runSpacing: 8, children: [
                for (final f in [null, 'sayfa_goruntulem', 'POST', 'PUT', 'DELETE'])
                  ChoiceChip(
                    label: Text(f == null ? 'Tümü' : f == 'sayfa_goruntulem' ? 'Sayfa' : f),
                    selected: _filtre == f,
                    selectedColor: r.anaAcik,
                    backgroundColor: r.kart,
                    side: BorderSide(color: _filtre == f ? r.ana : r.ayrac),
                    shape: const StadiumBorder(),
                    onSelected: (s) {
                      _filtre = s ? f : null;
                      yenile();
                    },
                  ),
              ]),
            ),
          ),
        ),
        Expanded(
          child: durum((liste) {
            if (liste.isEmpty) {
              return const BosDurum(ikon: CupertinoIcons.doc_text, baslik: 'Henüz log kaydı yok');
            }
            return YenilenebilirListe(
              yenile: yenile,
              children: [
                Grup(
                  children: [
                    for (final l in liste)
                      Satir(
                        baslik: _logBaslik(l),
                        alt: tarihSaat(l['tarih']),
                        sag: Text(
                          l['islem_tipi'] as String? ?? '',
                          style: context.yazi.bodySmall?.copyWith(
                            color: _islemRenk(l['islem_tipi'] as String? ?? '', r),
                          ),
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

  String _logBaslik(Json l) {
    final sayfa = l['sayfa'] as String? ?? '';
    final detay = l['detay'] as String? ?? '';
    final ip = l['ip_adresi'] as String? ?? '';
    if (sayfa.isNotEmpty) return sayfa;
    if (detay.isNotEmpty) return detay;
    if (ip.isNotEmpty) return ip;
    return l['islem_tipi'] as String? ?? '—';
  }

  Color _islemRenk(String tip, Renkler r) {
    switch (tip) {
      case 'POST':
        return r.basari;
      case 'DELETE':
        return r.tehlike;
      case 'PUT':
        return r.turuncu;
      default:
        return r.ikincil;
    }
  }
}
