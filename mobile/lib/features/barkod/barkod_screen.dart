import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../core/api_client.dart';
import '../../core/eprel_client.dart';

/// Telefon kamerasıyla barkod / QR okur.
///
/// [eprelDestekli] = true → EPREL EU etiket URL'lerini tanır, EPREL API'den
/// ürün bilgisi çeker ve {'tip':'eprel', ...} map'i döner.
/// [eprelDestekli] = false (varsayılan) → yalnızca kendi DB'mizde arar.
class BarkodScreen extends StatefulWidget {
  final bool eprelDestekli;
  const BarkodScreen({this.eprelDestekli = false, super.key});

  @override
  State<BarkodScreen> createState() => _BarkodScreenState();
}

class _BarkodScreenState extends State<BarkodScreen> {
  final MobileScannerController _ctrl = MobileScannerController();
  bool _isleniyor = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _barkodOkundu(BarcodeCapture capture) async {
    if (_isleniyor) return;
    final barkod = capture.barcodes.firstOrNull?.rawValue;
    if (barkod == null || barkod.isEmpty) return;

    setState(() => _isleniyor = true);
    _ctrl.stop();

    debugPrint('=== BARKOD OKUNDU: $barkod');

    // EPREL URL mi?
    if (widget.eprelDestekli) {
      final eprelNo = EprelClient.parseEprelNo(barkod);
      debugPrint('=== EPREL NO: $eprelNo');
      if (eprelNo != null) {
        await _eprelIsle(eprelNo);
        return;
      }
    }

    // Normal barkod — kendi DB'mize bak
    try {
      final urun = await ApiClient.instance.get('/api/urunler/barkod/$barkod');
      if (!mounted) return;
      Navigator.of(context).pop(urun);
    } on DioException {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ürün bulunamadı.\nBarkod: ${barkod.length > 50 ? '${barkod.substring(0, 50)}...' : barkod}')),
      );
      _ctrl.start();
      setState(() => _isleniyor = false);
    }
  }

  Future<void> _eprelIsle(String eprelNo) async {
    try {
      final eprel = await EprelClient.fetchByNo(eprelNo);
      if (!mounted) return;
      Navigator.of(context).pop(eprel.toMap());
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('EPREL verisi alınamadı: $e')),
      );
      _ctrl.start();
      setState(() => _isleniyor = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Barkod / QR Okut'),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: _ctrl.toggleTorch,
            tooltip: 'Flaş',
          ),
          IconButton(
            icon: const Icon(Icons.flip_camera_ios),
            onPressed: _ctrl.switchCamera,
            tooltip: 'Kamera değiştir',
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _ctrl,
            onDetect: _barkodOkundu,
          ),
          Center(
            child: Container(
              width: 240,
              height: 240,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.green, width: 2),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          if (_isleniyor)
            const Center(child: CircularProgressIndicator()),
          if (widget.eprelDestekli)
            Positioned(
              bottom: 16,
              left: 0,
              right: 0,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'EU lastik etiketindeki QR\'ı okutun',
                    style: TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
