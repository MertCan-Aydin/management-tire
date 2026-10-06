import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/eprel_client.dart';
import '../../ui/tema.dart';

/// Kamerayla barkod / QR okur.
///
/// [eprelDestekli] = true → EPREL EU etiket URL'lerini tanır, EPREL API'den
/// ürün bilgisi çeker ve {'tip':'eprel', ...} map'i döner.
/// [hamDeger] = true → hiçbir arama yapmadan {'rawValue': ...} döner
/// (raf kodu, yeni ürünün barkodu vb.).
/// Varsayılan → yalnızca kendi DB'mizde ürün arar ve ürünü döner.
class BarkodScreen extends StatefulWidget {
  final bool eprelDestekli;
  final bool hamDeger;
  final String? ipucu;
  const BarkodScreen({this.eprelDestekli = false, this.hamDeger = false, this.ipucu, super.key});

  @override
  State<BarkodScreen> createState() => _BarkodScreenState();
}

class _BarkodScreenState extends State<BarkodScreen> {
  final MobileScannerController _ctrl = MobileScannerController();
  bool _isleniyor = false;
  String? _mesaj;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _barkodOkundu(BarcodeCapture capture) async {
    if (_isleniyor) return;
    final barkod = capture.barcodes.firstOrNull?.rawValue?.trim();
    if (barkod == null || barkod.isEmpty) return;

    HapticFeedback.mediumImpact();
    setState(() {
      _isleniyor = true;
      _mesaj = null;
    });

    if (widget.hamDeger) {
      Navigator.of(context).pop({'rawValue': barkod});
      return;
    }

    _ctrl.stop();

    // EPREL URL mi?
    final eprelNo = EprelClient.parseEprelNo(barkod);
    if (widget.eprelDestekli && eprelNo != null) {
      await _eprelIsle(eprelNo);
      return;
    }

    // Kendi DB'mize bak. EPREL'den kaydedilen ürünlerin barkod_qr alanında
    // URL değil yalnızca EPREL numarası tutulur.
    try {
      final urun = await UrunApi.barkod(eprelNo ?? barkod);
      if (!mounted) return;
      Navigator.of(context).pop(urun);
    } catch (e) {
      if (!mounted) return;
      final kisa = barkod.length > 40 ? '${barkod.substring(0, 40)}…' : barkod;
      _devamEt(hataKodu(e) == 404 ? 'Ürün bulunamadı\n$kisa' : hataMesaji(e));
    }
  }

  Future<void> _eprelIsle(String eprelNo) async {
    try {
      final eprel = await EprelClient.fetchByNo(eprelNo);
      if (!mounted) return;
      Navigator.of(context).pop(eprel.toMap());
    } catch (e) {
      if (!mounted) return;
      _devamEt('EPREL verisi alınamadı');
    }
  }

  void _devamEt(String mesaj) {
    HapticFeedback.heavyImpact();
    setState(() {
      _mesaj = mesaj;
      _isleniyor = false;
    });
    _ctrl.start();
  }

  @override
  Widget build(BuildContext context) {
    final ipucu = widget.ipucu ??
        (widget.eprelDestekli
            ? 'Ürün barkodunu ya da EU lastik etiketindeki QR\'ı çerçeveye getirin'
            : 'Barkodu veya QR kodu çerçeveye getirin');
    return AnnotatedRegion(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: Colors.black,
        body: Stack(fit: StackFit.expand, children: [
          MobileScanner(controller: _ctrl, onDetect: _barkodOkundu),
          // Çerçeve dışını karart
          IgnorePointer(child: CustomPaint(painter: _CerceveBoyaci())),
          SafeArea(
            child: Column(children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: Row(children: [
                  CupertinoButton(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Kapat', style: TextStyle(fontFamily: kFont, color: Colors.white, fontSize: 17)),
                  ),
                  const Spacer(),
                  _YuvarlakDugme(ikon: CupertinoIcons.bolt_fill, onTap: _ctrl.toggleTorch),
                  const SizedBox(width: 10),
                  _YuvarlakDugme(ikon: CupertinoIcons.camera_rotate_fill, onTap: _ctrl.switchCamera),
                  const SizedBox(width: 8),
                ]),
              ),
              const Spacer(),
              Padding(
                padding: const EdgeInsets.fromLTRB(32, 0, 32, 32),
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  child: _isleniyor
                      ? const CupertinoActivityIndicator(color: Colors.white, radius: 14)
                      : Container(
                          key: ValueKey(_mesaj),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: _mesaj != null ? const Color(0xE6FF3B30) : const Color(0x99000000),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Text(
                            _mesaj ?? ipucu,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                                fontFamily: kFont, color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500),
                          ),
                        ),
                ),
              ),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _YuvarlakDugme extends StatelessWidget {
  final IconData ikon;
  final VoidCallback onTap;
  const _YuvarlakDugme({required this.ikon, required this.onTap});

  @override
  Widget build(BuildContext context) => GestureDetector(
        onTap: onTap,
        child: Container(
          width: 44,
          height: 44,
          decoration: const BoxDecoration(color: Color(0x66000000), shape: BoxShape.circle),
          child: Icon(ikon, color: Colors.white, size: 22),
        ),
      );
}

class _CerceveBoyaci extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final kenar = (size.shortestSide * 0.62).clamp(220.0, 360.0);
    final cerceve = RRect.fromRectAndRadius(
      Rect.fromCenter(center: size.center(Offset.zero), width: kenar, height: kenar),
      const Radius.circular(22),
    );
    final disi = Path()
      ..addRect(Offset.zero & size)
      ..addRRect(cerceve)
      ..fillType = PathFillType.evenOdd;
    canvas.drawPath(disi, Paint()..color = const Color(0x8C000000));
    canvas.drawRRect(
      cerceve,
      Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
