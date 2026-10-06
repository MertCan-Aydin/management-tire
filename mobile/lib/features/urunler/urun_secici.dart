import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/tema.dart';

/// Ürün satırının alt metni. Ürün adında zaten geçen marka/model/ebat
/// tekrar yazılmaz.
String urunAlt(Json u) {
  final ad = (u['ad'] as String? ?? '').toLowerCase();
  bool adda(dynamic v) => v != null && ad.contains('$v'.toLowerCase());
  final markaModel = [u['marka_adi'], u['model_adi']].where((e) => e != null && '$e'.isNotEmpty && !adda(e)).join(' ');
  return [
    u['ebat'],
    markaModel,
    u['mevsim'],
  ].where((e) => e != null && '$e'.isNotEmpty).join('  ·  ');
}

/// Dar ekranda ürün seçimi: aramalı liste sayfası açar.
Future<Json?> urunSec(BuildContext context, {bool sadeceStoklu = false, bool maliyetGoster = false}) => aramaliSec(
      context,
      baslik: 'Ürün Seç',
      aramaIpucu: 'Ürün adı, barkod veya ebat',
      yukle: (q) => UrunApi.liste(arama: q, sadeceStoklu: sadeceStoklu, limit: 50),
      satirBaslik: (u) => u['ad'] as String? ?? '',
      satirAlt: (u) => '${urunAlt(u)}  ·  Stok ${tamSayi(u['stok'])}',
      satirSag: (u) => para(maliyetGoster ? u['maliyet_fiyati'] : u['satis_fiyati']),
    );

/// Geniş ekranda formun yanında sürekli açık duran ürün arama paneli.
class UrunAramaPaneli extends StatefulWidget {
  final bool sadeceStoklu;
  final bool maliyetGoster;
  final ValueChanged<Json> sec;
  final VoidCallback? qrOkut;
  final String? qrMetni;

  /// Sepette kaç adet olduğunu göstermek için (ürün id → adet).
  final Map<int, int> sepet;

  const UrunAramaPaneli({
    required this.sec,
    this.sadeceStoklu = false,
    this.maliyetGoster = false,
    this.qrOkut,
    this.qrMetni,
    this.sepet = const {},
    super.key,
  });

  @override
  State<UrunAramaPaneli> createState() => _UrunAramaPaneliState();
}

class _UrunAramaPaneliState extends State<UrunAramaPaneli> {
  List<Json> _sonuc = [];
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
    final no = ++_istek;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    try {
      final v = await UrunApi.liste(arama: q, sadeceStoklu: widget.sadeceStoklu, limit: 60);
      if (!mounted || no != _istek) return;
      setState(() {
        _sonuc = v;
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

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
        child: Row(children: [
          Expanded(child: AramaKutusu(ipucu: 'Ürün adı, barkod veya ebat', degisti: _getir)),
          if (widget.qrOkut != null) ...[
            const SizedBox(width: 10),
            CupertinoButton.tinted(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              minimumSize: const Size(44, 40),
              onPressed: widget.qrOkut,
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(CupertinoIcons.qrcode_viewfinder, size: 20),
                const SizedBox(width: 6),
                Text(widget.qrMetni ?? 'QR Okut',
                    style: const TextStyle(fontFamily: kFont, fontSize: 15, fontWeight: FontWeight.w600)),
              ]),
            ),
          ],
        ]),
      ),
      Expanded(
        child: _yukleniyor
            ? const Yukleniyor()
            : _hata != null
                ? HataDurum(_hata!, () => _getir(_arama))
                : _sonuc.isEmpty
                    ? BosDurum(
                        ikon: CupertinoIcons.cube_box,
                        baslik: 'Ürün bulunamadı',
                        aciklama: widget.sadeceStoklu ? 'Yalnızca stokta olan ürünler listelenir' : null,
                      )
                    : LayoutBuilder(builder: (context, c) {
                        final sutun = (c.maxWidth / 260).floor().clamp(1, 4);
                        return GridView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: sutun,
                            mainAxisSpacing: 10,
                            crossAxisSpacing: 10,
                            mainAxisExtent: 118,
                          ),
                          itemCount: _sonuc.length,
                          itemBuilder: (_, i) {
                            final u = _sonuc[i];
                            final adet = widget.sepet[tamSayi(u['id'])] ?? 0;
                            final stok = tamSayi(u['stok']);
                            return Material(
                              color: r.kart,
                              borderRadius: BorderRadius.circular(12),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(12),
                                onTap: () => widget.sec(u),
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: adet > 0 ? r.ana : Colors.transparent, width: 1.6),
                                  ),
                                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                    Row(children: [
                                      Expanded(
                                        child: Text(u['ad'] as String? ?? '',
                                            maxLines: 2, overflow: TextOverflow.ellipsis, style: context.yazi.titleSmall),
                                      ),
                                      if (adet > 0)
                                        Container(
                                          margin: const EdgeInsets.only(left: 6),
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(color: r.ana, borderRadius: BorderRadius.circular(10)),
                                          child: Text('$adet',
                                              style: const TextStyle(
                                                  fontFamily: kFont,
                                                  color: Colors.white,
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 13)),
                                        ),
                                    ]),
                                    const SizedBox(height: 2),
                                    Text(urunAlt(u), maxLines: 1, overflow: TextOverflow.ellipsis, style: context.yazi.bodySmall),
                                    const Spacer(),
                                    Row(children: [
                                      Text(para(widget.maliyetGoster ? u['maliyet_fiyati'] : u['satis_fiyati']),
                                          style: context.yazi.titleMedium),
                                      const Spacer(),
                                      Rozet('Stok $stok', stok > 0 ? r.basari : r.tehlike),
                                    ]),
                                  ]),
                                ),
                              ),
                            );
                          },
                        );
                      }),
      ),
    ]);
  }
}
