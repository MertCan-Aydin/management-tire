import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../barkod/barkod_screen.dart';

class AlimScreen extends StatefulWidget {
  const AlimScreen({super.key});

  @override
  State<AlimScreen> createState() => _AlimScreenState();
}

class _AlimScreenState extends State<AlimScreen> {
  bool _yeniAlim = false;

  @override
  Widget build(BuildContext context) => _yeniAlim
      ? _YeniAlimView(onBitti: () => setState(() => _yeniAlim = false))
      : _AlimListesiView(onYeniAlim: () => setState(() => _yeniAlim = true));
}

// ── Liste ────────────────────────────────────────────────────────────────────

class _AlimListesiView extends StatefulWidget {
  final VoidCallback onYeniAlim;
  const _AlimListesiView({required this.onYeniAlim});

  @override
  State<_AlimListesiView> createState() => _AlimListesiViewState();
}

class _AlimListesiViewState extends State<_AlimListesiView> {
  List<dynamic> _alimlar = [];
  bool _yukleniyor = true;

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  Future<void> _yukle() async {
    setState(() => _yukleniyor = true);
    try {
      final bugun = DateTime.now();
      final bas =
          '${bugun.year}-${bugun.month.toString().padLeft(2, '0')}-01';
      final bit =
          '${bugun.year}-${bugun.month.toString().padLeft(2, '0')}-${bugun.day.toString().padLeft(2, '0')}';
      final data = await ApiClient.instance.get('/api/alimlar',
          params: {'baslangic': bas, 'bitis': bit, 'limit': 100});
      setState(() {
        _alimlar = data as List? ?? [];
        _yukleniyor = false;
      });
    } catch (_) {
      setState(() => _yukleniyor = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: _yukleniyor
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _yukle,
                child: _alimlar.isEmpty
                    ? const Center(child: Text('Bu ay alım yok'))
                    : ListView.builder(
                        itemCount: _alimlar.length,
                        itemBuilder: (_, i) {
                          final a = _alimlar[i] as Map<String, dynamic>;
                          return ListTile(
                            leading:
                                const Icon(Icons.local_shipping_outlined),
                            title: Text(a['tedarikci_adi'] as String? ?? ''),
                            subtitle: Text(
                                (a['tarih'] as String? ?? '').substring(0, 16)),
                            trailing: Text(
                                '${(a['toplam_tutar'] as num?)?.toStringAsFixed(2)} ₺',
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold)),
                          );
                        }),
              ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: widget.onYeniAlim,
          icon: const Icon(Icons.add),
          label: const Text('Yeni Alım'),
        ),
      );
}

// ── Yeni Alım ────────────────────────────────────────────────────────────────

class _YeniAlimView extends StatefulWidget {
  final VoidCallback onBitti;
  const _YeniAlimView({required this.onBitti});

  @override
  State<_YeniAlimView> createState() => _YeniAlimViewState();
}

class _YeniAlimViewState extends State<_YeniAlimView> {
  List<dynamic> _tedarikciler = [];
  int? _seciliTedId;
  final List<Map<String, dynamic>> _kalemler = [];
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void initState() {
    super.initState();
    _tedarikcileriYukle();
  }

  Future<void> _tedarikcileriYukle() async {
    try {
      final data = await ApiClient.instance.get('/api/tedarikciler');
      setState(() => _tedarikciler = data as List? ?? []);
    } catch (_) {}
  }

  Future<void> _urunEkle() async {
    final sonuc = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
          builder: (_) => const BarkodScreen(eprelDestekli: true)),
    );
    if (sonuc == null || !mounted) return;

    if (sonuc['tip'] == 'eprel') {
      await _eprelUrunEkle(sonuc);
    } else {
      // Normal DB ürünü
      final miktar =
          await _miktarVeFiyatSor(sonuc['ad'] as String? ?? '', null, null);
      if (miktar == null) return;
      setState(() => _kalemler.add({
            'urun_id': sonuc['id'],
            'urun_adi_anlik': sonuc['ad'],
            'miktar': miktar['miktar'],
            'birim_fiyat': miktar['fiyat'],
          }));
    }
  }

  Future<void> _eprelUrunEkle(Map<String, dynamic> eprel) async {
    // Dialog: EPREL bilgilerini göster + fiyat/miktar al
    final sonuc = await _eprelDialogGoster(eprel);
    if (sonuc == null || !mounted) return;

    // Backend'de ürünü bul veya oluştur
    try {
      final data = await ApiClient.instance.post('/api/urunler/eprel-kaydet',
          data: {
            'eprel_no': eprel['eprel_no'],
            'marka': sonuc['marka'],
            'model': sonuc['model'],
            'ebat': sonuc['ebat'],
            'mevsim': sonuc['mevsim'],
            'satis_fiyati': sonuc['satis_fiyati'],
            'maliyet_fiyati': sonuc['alis_fiyati'],
          });
      final urunId = (data as Map<String, dynamic>)['urun_id'] as int;
      final urunAd = data['urun_ad'] as String;
      final yeniMi = data['yeni_mi'] as bool;

      if (mounted && yeniMi) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Yeni ürün oluşturuldu: $urunAd')),
        );
      }

      setState(() => _kalemler.add({
            'urun_id': urunId,
            'urun_adi_anlik': urunAd,
            'miktar': sonuc['miktar'],
            'birim_fiyat': sonuc['alis_fiyati'],
          }));
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(
                (e.error as ApiError?)?.detail ?? 'Ürün kaydedilemedi')),
      );
    }
  }

  Future<Map<String, dynamic>?> _eprelDialogGoster(
      Map<String, dynamic> eprel) {
    final markaCtrl =
        TextEditingController(text: eprel['marka'] as String? ?? '');
    final modelCtrl =
        TextEditingController(text: eprel['model'] as String? ?? '');
    final ebatCtrl =
        TextEditingController(text: eprel['ebat'] as String? ?? '');
    String mevsim = eprel['mevsim'] as String? ?? 'Yaz';
    final alisCtrl = TextEditingController(text: '0');
    final satisCtrl = TextEditingController(text: '0');
    final miktarCtrl = TextEditingController(text: '1');

    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: const Text('EPREL Lastik'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                    controller: markaCtrl,
                    decoration: const InputDecoration(labelText: 'Marka')),
                const SizedBox(height: 8),
                TextField(
                    controller: modelCtrl,
                    decoration: const InputDecoration(labelText: 'Model')),
                const SizedBox(height: 8),
                TextField(
                    controller: ebatCtrl,
                    decoration: const InputDecoration(labelText: 'Ebat')),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: mevsim,
                  decoration:
                      const InputDecoration(labelText: 'Mevsim'),
                  items: const [
                    DropdownMenuItem(value: 'Yaz', child: Text('Yaz')),
                    DropdownMenuItem(value: 'Kış', child: Text('Kış')),
                    DropdownMenuItem(
                        value: 'Dört Mevsim',
                        child: Text('Dört Mevsim')),
                  ],
                  onChanged: (v) => setS(() => mevsim = v ?? 'Yaz'),
                ),
                const SizedBox(height: 12),
                const Divider(),
                const SizedBox(height: 4),
                TextField(
                  controller: alisCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true),
                  decoration:
                      const InputDecoration(labelText: 'Alış Fiyatı (₺)'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: satisCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true),
                  decoration:
                      const InputDecoration(labelText: 'Satış Fiyatı (₺)'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: miktarCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Miktar'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('İptal')),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, {
                'marka': markaCtrl.text.trim(),
                'model': modelCtrl.text.trim(),
                'ebat': ebatCtrl.text.trim(),
                'mevsim': mevsim,
                'alis_fiyati':
                    double.tryParse(alisCtrl.text) ?? 0.0,
                'satis_fiyati':
                    double.tryParse(satisCtrl.text) ?? 0.0,
                'miktar': int.tryParse(miktarCtrl.text) ?? 1,
              }),
              child: const Text('Ekle'),
            ),
          ],
        ),
      ),
    );
  }

  Future<Map<String, dynamic>?> _miktarVeFiyatSor(
      String ad, double? varsayilanSatis, double? varsayilanAlis) {
    final mCtrl = TextEditingController(text: '1');
    final fCtrl = TextEditingController(
        text: varsayilanAlis?.toStringAsFixed(2) ?? '0');
    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(ad),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(
              controller: mCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Miktar')),
          const SizedBox(height: 8),
          TextField(
              controller: fCtrl,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration:
                  const InputDecoration(labelText: 'Birim Alış Fiyatı (₺)')),
        ]),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('İptal')),
          FilledButton(
            onPressed: () => Navigator.pop(context, {
              'miktar': int.tryParse(mCtrl.text) ?? 1,
              'fiyat': double.tryParse(fCtrl.text) ?? 0,
            }),
            child: const Text('Ekle'),
          ),
        ],
      ),
    );
  }

  double get _toplam => _kalemler.fold(
      0,
      (s, k) =>
          s + (k['miktar'] as int) * (k['birim_fiyat'] as double));

  Future<void> _kaydet() async {
    setState(() {
      _hata = null;
      _kaydediliyor = true;
    });
    if (_seciliTedId == null) {
      setState(() {
        _hata = 'Tedarikçi seçin';
        _kaydediliyor = false;
      });
      return;
    }
    if (_kalemler.isEmpty) {
      setState(() {
        _hata = 'En az bir ürün ekleyin';
        _kaydediliyor = false;
      });
      return;
    }
    try {
      await ApiClient.instance.post('/api/alimlar', data: {
        'tedarikci_id': _seciliTedId,
        'kalemler': _kalemler,
      });
      if (mounted) widget.onBitti();
    } on DioException catch (e) {
      setState(() {
        _hata = (e.error as ApiError?)?.detail ?? 'Hata';
        _kaydediliyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Yeni Alım'),
          leading: IconButton(
              icon: const Icon(Icons.close), onPressed: widget.onBitti),
          actions: [
            TextButton(
              onPressed: _kaydediliyor ? null : _kaydet,
              child: _kaydediliyor
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('KAYDET',
                      style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
        body: ListView(
          padding: const EdgeInsets.all(12),
          children: [
            DropdownButtonFormField<int>(
              value: _seciliTedId,
              decoration: const InputDecoration(
                  labelText: 'Tedarikçi *',
                  border: OutlineInputBorder()),
              items: _tedarikciler.map((t) {
                final m = t as Map<String, dynamic>;
                return DropdownMenuItem<int>(
                    value: m['id'] as int,
                    child: Text(m['ad'] as String));
              }).toList(),
              onChanged: (v) => setState(() => _seciliTedId = v),
            ),
            const SizedBox(height: 12),
            Card(
                child: Column(children: [
              ListTile(
                title: const Text('Ürünler',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                trailing: FilledButton.tonal(
                    onPressed: _urunEkle,
                    child: const Text('+ QR Okut')),
              ),
              ..._kalemler.asMap().entries.map((e) => ListTile(
                    dense: true,
                    title: Text(e.value['urun_adi_anlik'] as String),
                    subtitle: Text(
                        '${e.value['miktar']} × ${(e.value['birim_fiyat'] as double).toStringAsFixed(2)} ₺'),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline, size: 18),
                      onPressed: () =>
                          setState(() => _kalemler.removeAt(e.key)),
                    ),
                  )),
              if (_kalemler.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Toplam:',
                            style:
                                TextStyle(fontWeight: FontWeight.bold)),
                        Text('${_toplam.toStringAsFixed(2)} ₺',
                            style: const TextStyle(
                                fontWeight: FontWeight.bold)),
                      ]),
                ),
            ])),
            if (_hata != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(_hata!,
                    style: const TextStyle(color: Colors.red)),
              ),
          ],
        ),
      );
}
