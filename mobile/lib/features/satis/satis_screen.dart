import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../barkod/barkod_screen.dart';

class SatisScreen extends StatefulWidget {
  const SatisScreen({super.key});

  @override
  State<SatisScreen> createState() => _SatisScreenState();
}

class _SatisScreenState extends State<SatisScreen> {
  // Mevcut aktif satış ekranı veya satış listesi
  bool _yeniSatis = false;

  @override
  Widget build(BuildContext context) {
    return _yeniSatis
        ? _YeniSatisView(onBitti: () => setState(() => _yeniSatis = false))
        : _SatisListesiView(onYeniSatis: () => setState(() => _yeniSatis = true));
  }
}

// ── Satış Listesi ────────────────────────────────────────────────────────────

class _SatisListesiView extends StatefulWidget {
  final VoidCallback onYeniSatis;
  const _SatisListesiView({required this.onYeniSatis});

  @override
  State<_SatisListesiView> createState() => _SatisListesiViewState();
}

class _SatisListesiViewState extends State<_SatisListesiView> {
  List<dynamic> _satislar = [];
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
      final bas = '${bugun.year}-${bugun.month.toString().padLeft(2, '0')}-01';
      final bit = '${bugun.year}-${bugun.month.toString().padLeft(2, '0')}-${bugun.day.toString().padLeft(2, '0')}';
      final data = await ApiClient.instance.get('/api/satislar', params: {'baslangic': bas, 'bitis': bit, 'limit': 100});
      setState(() { _satislar = data as List? ?? []; _yukleniyor = false; });
    } catch (_) {
      setState(() => _yukleniyor = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _yukleniyor
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _yukle,
              child: _satislar.isEmpty
                  ? const Center(child: Text('Bu ay satış yok'))
                  : ListView.builder(
                      itemCount: _satislar.length,
                      itemBuilder: (_, i) {
                        final s = _satislar[i] as Map<String, dynamic>;
                        return ListTile(
                          leading: const Icon(Icons.receipt_long),
                          title: Text(s['musteri_adi'] as String? ?? ''),
                          subtitle: Text('${(s['tarih'] as String? ?? '').substring(0, 16)}  •  ${s['odeme_yontemi']}'),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text('${(s['toplam_tutar'] as num?)?.toStringAsFixed(2)} ₺',
                                  style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('Kâr: ${(s['kar'] as num?)?.toStringAsFixed(2)} ₺',
                                  style: const TextStyle(fontSize: 11, color: Colors.green)),
                            ],
                          ),
                        );
                      },
                    ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: widget.onYeniSatis,
        icon: const Icon(Icons.add),
        label: const Text('Yeni Satış'),
      ),
    );
  }
}

// ── Yeni Satış Formu ─────────────────────────────────────────────────────────

class _YeniSatisView extends StatefulWidget {
  final VoidCallback onBitti;
  const _YeniSatisView({required this.onBitti});

  @override
  State<_YeniSatisView> createState() => _YeniSatisViewState();
}

class _YeniSatisViewState extends State<_YeniSatisView> {
  Map<String, dynamic>? _musteri;
  final List<Map<String, dynamic>> _kalemler = [];
  String _odemeYontemi = 'Nakit';
  double _indirim = 0;
  bool _kaydediliyor = false;
  String? _hata;

  final _musteriAraCtrl = TextEditingController();
  final _indirimCtrl = TextEditingController(text: '0');

  @override
  void dispose() {
    _musteriAraCtrl.dispose();
    _indirimCtrl.dispose();
    super.dispose();
  }

  double get _toplam => _kalemler.fold(0, (s, k) => s + (k['miktar'] as int) * (k['birim_fiyat'] as double));
  double get _kar => _toplam - _indirim - _kalemler.fold(0.0, (s, k) => s + (k['miktar'] as int) * (k['birim_maliyet'] as double));

  Future<void> _musteriAra() async {
    final q = _musteriAraCtrl.text.trim();
    if (q.isEmpty) return;
    try {
      final data = await ApiClient.instance.get('/api/musteriler', params: {'arama': q, 'limit': 10});
      final liste = data as List? ?? [];
      if (!mounted) return;
      if (liste.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Müşteri bulunamadı')));
        return;
      }
      final secilen = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (_) => SimpleDialog(
          title: const Text('Müşteri Seç'),
          children: liste.map((m) {
            final mu = m as Map<String, dynamic>;
            return SimpleDialogOption(
              onPressed: () => Navigator.pop(context, mu),
              child: Text('${mu['ad_soyad']}  ${mu['arac_plakasi'] ?? ''}  (${mu['telefon']})'),
            );
          }).toList(),
        ),
      );
      if (secilen != null) setState(() => _musteri = secilen);
    } catch (_) {}
  }

  Future<void> _urunEkle() async {
    final urun = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(builder: (_) => const BarkodScreen()),
    );
    if (urun == null || !mounted) return;

    final miktar = await _miktarSor(urun['ad'] as String? ?? '');
    if (miktar == null) return;

    final fiyat = (urun['satis_fiyati'] as num?)?.toDouble() ?? 0;
    final maliyet = (urun['maliyet_fiyati'] as num?)?.toDouble() ?? 0;

    setState(() {
      _kalemler.add({
        'urun_id': urun['id'],
        'urun_adi_anlik': urun['ad'],
        'miktar': miktar,
        'birim_fiyat': fiyat,
        'birim_maliyet': maliyet,
      });
    });
  }

  Future<int?> _miktarSor(String urunAdi) {
    final ctrl = TextEditingController(text: '1');
    return showDialog<int>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(urunAdi),
        content: TextField(
          controller: ctrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Miktar'),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('İptal')),
          FilledButton(
            onPressed: () => Navigator.pop(context, int.tryParse(ctrl.text) ?? 1),
            child: const Text('Ekle'),
          ),
        ],
      ),
    );
  }

  Future<void> _kaydet() async {
    setState(() { _hata = null; _kaydediliyor = true; });
    if (_musteri == null) { setState(() { _hata = 'Müşteri seçin'; _kaydediliyor = false; }); return; }
    if (_kalemler.isEmpty) { setState(() { _hata = 'En az bir ürün ekleyin'; _kaydediliyor = false; }); return; }

    try {
      await ApiClient.instance.post('/api/satislar', data: {
        'musteri_id': _musteri!['id'],
        'odeme_yontemi': _odemeYontemi,
        'indirim': _indirim,
        'kalemler': _kalemler,
      });
      if (mounted) widget.onBitti();
    } on DioException catch (e) {
      setState(() { _hata = (e.error as ApiError?)?.detail ?? 'Hata'; _kaydediliyor = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Yeni Satış'),
        leading: IconButton(icon: const Icon(Icons.close), onPressed: widget.onBitti),
        actions: [
          TextButton(
            onPressed: _kaydediliyor ? null : _kaydet,
            child: _kaydediliyor
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('KAYDET', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          // Müşteri
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Müşteri', style: TextStyle(fontWeight: FontWeight.bold)),
                  if (_musteri != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Text('${_musteri!['ad_soyad']}  ${_musteri!['arac_plakasi'] ?? ''}',
                          style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                    ),
                  Row(children: [
                    Expanded(child: TextField(
                      controller: _musteriAraCtrl,
                      decoration: const InputDecoration(hintText: 'Telefon veya plaka…', isDense: true),
                      onSubmitted: (_) => _musteriAra(),
                    )),
                    IconButton(icon: const Icon(Icons.search), onPressed: _musteriAra),
                  ]),
                ],
              ),
            ),
          ),
          // Kalemler
          Card(
            child: Column(
              children: [
                ListTile(
                  title: const Text('Ürünler', style: TextStyle(fontWeight: FontWeight.bold)),
                  trailing: FilledButton.tonal(
                    onPressed: _urunEkle,
                    child: const Text('+ QR Okut'),
                  ),
                ),
                ..._kalemler.asMap().entries.map((e) {
                  final i = e.key;
                  final k = e.value;
                  return ListTile(
                    dense: true,
                    title: Text(k['urun_adi_anlik'] as String? ?? ''),
                    subtitle: Text('${k['miktar']} × ${(k['birim_fiyat'] as double).toStringAsFixed(2)} ₺'),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      Text('${((k['miktar'] as int) * (k['birim_fiyat'] as double)).toStringAsFixed(2)} ₺'),
                      IconButton(
                        icon: const Icon(Icons.delete_outline, size: 18),
                        onPressed: () => setState(() => _kalemler.removeAt(i)),
                      ),
                    ]),
                  );
                }),
              ],
            ),
          ),
          // Özet
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(children: [
                Row(children: [
                  const Text('İndirim (₺)'),
                  const Spacer(),
                  SizedBox(width: 100, child: TextField(
                    controller: _indirimCtrl,
                    keyboardType: TextInputType.number,
                    onChanged: (v) => setState(() => _indirim = double.tryParse(v) ?? 0),
                    decoration: const InputDecoration(isDense: true, suffix: Text('₺')),
                  )),
                ]),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _odemeYontemi,
                  decoration: const InputDecoration(labelText: 'Ödeme Yöntemi', isDense: true),
                  items: ['Nakit', 'Kredi Kartı', 'Havale']
                      .map((v) => DropdownMenuItem(value: v, child: Text(v)))
                      .toList(),
                  onChanged: (v) => setState(() => _odemeYontemi = v!),
                ),
                const SizedBox(height: 12),
                Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                  const Text('Toplam:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text('${_toplam.toStringAsFixed(2)} ₺', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ]),
                Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                  const Text('Tahmini Kâr:', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('${_kar.toStringAsFixed(2)} ₺', style: const TextStyle(color: Colors.green, fontSize: 12)),
                ]),
              ]),
            ),
          ),
          if (_hata != null) Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(_hata!, style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
