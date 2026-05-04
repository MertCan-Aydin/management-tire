import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../barkod/barkod_screen.dart';

class LastikOteliScreen extends StatefulWidget {
  const LastikOteliScreen({super.key});

  @override
  State<LastikOteliScreen> createState() => _LastikOteliScreenState();
}

class _LastikOteliScreenState extends State<LastikOteliScreen> {
  List<dynamic> _kayitlar = [];
  bool _yukleniyor = true;
  bool _sadeceAktif = true;
  String _arama = '';

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  Future<void> _yukle() async {
    setState(() => _yukleniyor = true);
    try {
      final data = await ApiClient.instance.get(
        '/api/lastik-oteli',
        params: {'sadece_aktif': _sadeceAktif, 'arama': _arama, 'limit': 500},
      );
      setState(() {
        _kayitlar = data as List? ?? [];
        _yukleniyor = false;
      });
    } catch (_) {
      setState(() => _yukleniyor = false);
    }
  }

  Future<void> _rafSorgula() async {
    // QR okutarak raf sorgula
    final sonuc = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(builder: (_) => const BarkodScreen()),
    );
    if (sonuc == null || !mounted) return;
    final rafKodu = (sonuc['rawValue'] ?? sonuc['barkod_qr'] ?? '').toString().trim().toUpperCase();
    if (rafKodu.isEmpty) return;
    try {
      final data = await ApiClient.instance.get('/api/lastik-oteli/raf/$rafKodu');
      if (!mounted) return;
      _rafDetayGoster(data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text((e.error as ApiError?)?.detail ?? 'Raf boş veya bulunamadı')),
      );
    }
  }

  void _rafDetayGoster(Map<String, dynamic> kayit) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Raf ${kayit['raf_kodu']}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _detaySatir('Müşteri', kayit['musteri_adi'] as String? ?? ''),
            _detaySatir('Plaka', kayit['arac_plakasi'] as String? ?? '—'),
            _detaySatir('Lastik', kayit['lastik_bilgisi'] as String? ?? '—'),
            _detaySatir('Sezon', kayit['sezon'] as String? ?? ''),
            _detaySatir('Giriş', (kayit['giris_tarihi'] as String? ?? '').substring(0, 10)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Kapat')),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              _teslimDialog(kayit);
            },
            child: const Text('Teslim Et'),
          ),
        ],
      ),
    );
  }

  Widget _detaySatir(String baslik, String deger) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          children: [
            SizedBox(
              width: 72,
              child: Text('$baslik:', style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ),
            Expanded(child: Text(deger, style: const TextStyle(fontWeight: FontWeight.w500))),
          ],
        ),
      );

  Future<void> _teslimDialog(Map<String, dynamic> kayit) async {
    DateTime cikisTarih = DateTime.now();
    final onay = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Teslim Et — Raf ${kayit['raf_kodu']}'),
        content: Text(
          '${kayit['musteri_adi']} müşterisinin lastiği teslim ediliyor.\n'
          'Çıkış tarihi: ${cikisTarih.day}.${cikisTarih.month}.${cikisTarih.year}',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('İptal')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Onayla')),
        ],
      ),
    );
    if (onay != true || !mounted) return;
    try {
      final cikis =
          '${cikisTarih.year}-${cikisTarih.month.toString().padLeft(2, '0')}-${cikisTarih.day.toString().padLeft(2, '0')}';
      await ApiClient.instance.put(
        '/api/lastik-oteli/${kayit['id']}/teslim',
        data: {'cikis_tarihi': cikis},
      );
      _yukle();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Teslim edildi')),
        );
      }
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text((e.error as ApiError?)?.detail ?? 'Hata')),
      );
    }
  }

  Future<void> _yeniKayit() async {
    final sonuc = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _YeniKayitSheet(onKaydet: () => Navigator.pop(context, true)),
    );
    if (sonuc == true) _yukle();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Arama + filtre çubuğu
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: 'Raf / müşteri / plaka ara…',
                      prefixIcon: const Icon(Icons.search, size: 20),
                      contentPadding: const EdgeInsets.symmetric(vertical: 0),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onChanged: (v) {
                      _arama = v;
                      _yukle();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Depoda'),
                  selected: _sadeceAktif,
                  onSelected: (v) {
                    setState(() => _sadeceAktif = v);
                    _yukle();
                  },
                ),
              ],
            ),
          ),

          Expanded(
            child: _yukleniyor
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: _yukle,
                    child: _kayitlar.isEmpty
                        ? const Center(child: Text('Kayıt yok'))
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            itemCount: _kayitlar.length,
                            itemBuilder: (_, i) {
                              final k = _kayitlar[i] as Map<String, dynamic>;
                              final aktif = k['aktif_mi'] == true || k['aktif_mi'] == 1;
                              return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                child: ListTile(
                                  leading: Container(
                                    width: 48,
                                    height: 48,
                                    decoration: BoxDecoration(
                                      color: aktif ? const Color(0xFFEEF2FF) : const Color(0xFFF3F4F6),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Center(
                                      child: Text(
                                        k['raf_kodu'] as String? ?? '',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13,
                                          color: aktif ? const Color(0xFF003D9B) : Colors.grey,
                                        ),
                                      ),
                                    ),
                                  ),
                                  title: Text(
                                    k['musteri_adi'] as String? ?? '',
                                    style: const TextStyle(fontWeight: FontWeight.w600),
                                  ),
                                  subtitle: Text(
                                    '${k['arac_plakasi'] ?? ''}  •  '
                                    '${k['lastik_bilgisi'] ?? '—'}  •  '
                                    '${k['sezon']}',
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  trailing: aktif
                                      ? TextButton(
                                          onPressed: () => _teslimDialog(k),
                                          child: const Text('Teslim'),
                                        )
                                      : const Chip(label: Text('Teslim ✓')),
                                  onTap: () => _rafDetayGoster(k),
                                ),
                              );
                            },
                          ),
                  ),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton.small(
            heroTag: 'raf_qr',
            onPressed: _rafSorgula,
            tooltip: 'QR ile Raf Sorgula',
            child: const Icon(Icons.qr_code_scanner),
          ),
          const SizedBox(height: 8),
          FloatingActionButton.extended(
            heroTag: 'yeni_kayit',
            onPressed: _yeniKayit,
            icon: const Icon(Icons.add),
            label: const Text('Yeni Kayıt'),
          ),
        ],
      ),
    );
  }
}

// ── Yeni Kayıt Alt Paneli ────────────────────────────────────────────────────

class _YeniKayitSheet extends StatefulWidget {
  final VoidCallback onKaydet;
  const _YeniKayitSheet({required this.onKaydet});

  @override
  State<_YeniKayitSheet> createState() => _YeniKayitSheetState();
}

class _YeniKayitSheetState extends State<_YeniKayitSheet> {
  final _rafCtrl = TextEditingController();
  final _musteriCtrl = TextEditingController();
  final _plakaCtrl = TextEditingController();
  final _lastikCtrl = TextEditingController();
  String _sezon = 'Yaz';
  int _adet = 4;
  bool _kaydediliyor = false;
  String? _hata;

  List<dynamic> _musteriler = [];
  int? _musteriId;

  Future<void> _musteriAra(String q) async {
    if (q.length < 2) return;
    try {
      final data = await ApiClient.instance.get('/api/musteriler', params: {'arama': q, 'limit': 10});
      setState(() => _musteriler = data as List? ?? []);
    } catch (_) {}
  }

  Future<void> _kaydet() async {
    if (_rafCtrl.text.trim().isEmpty || _musteriCtrl.text.trim().isEmpty) {
      setState(() => _hata = 'Raf kodu ve müşteri zorunludur');
      return;
    }
    setState(() { _kaydediliyor = true; _hata = null; });
    try {
      final bugun = DateTime.now();
      await ApiClient.instance.post('/api/lastik-oteli', data: {
        'musteri_id': _musteriId,
        'musteri_adi_anlik': _musteriCtrl.text.trim(),
        'arac_plakasi': _plakaCtrl.text.trim().isEmpty ? null : _plakaCtrl.text.trim(),
        'raf_kodu': _rafCtrl.text.trim().toUpperCase(),
        'lastik_bilgisi': _lastikCtrl.text.trim().isEmpty ? null : _lastikCtrl.text.trim(),
        'lastik_adedi': _adet,
        'sezon': _sezon,
        'giris_tarihi': '${bugun.year}-${bugun.month.toString().padLeft(2,'0')}-${bugun.day.toString().padLeft(2,'0')}',
        'notlar': null,
      });
      widget.onKaydet();
    } on DioException catch (e) {
      setState(() {
        _hata = (e.error as ApiError?)?.detail ?? 'Hata oluştu';
        _kaydediliyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Yeni Lastik Oteli Kaydı',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),

            TextField(
              controller: _rafCtrl,
              decoration: const InputDecoration(labelText: 'Raf Kodu *', hintText: 'A1, B12…'),
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 10),

            TextField(
              controller: _musteriCtrl,
              decoration: const InputDecoration(labelText: 'Müşteri *'),
              onChanged: (v) {
                _musteriId = null;
                _musteriAra(v);
              },
            ),
            if (_musteriler.isNotEmpty) ...[
              const SizedBox(height: 4),
              SizedBox(
                height: 120,
                child: ListView.builder(
                  itemCount: _musteriler.length,
                  itemBuilder: (_, i) {
                    final m = _musteriler[i] as Map<String, dynamic>;
                    return ListTile(
                      dense: true,
                      title: Text(m['ad_soyad'] as String? ?? ''),
                      subtitle: Text(m['arac_plakasi'] as String? ?? ''),
                      onTap: () {
                        setState(() {
                          _musteriId = m['id'] as int;
                          _musteriCtrl.text = m['ad_soyad'] as String? ?? '';
                          _plakaCtrl.text = m['arac_plakasi'] as String? ?? '';
                          _musteriler = [];
                        });
                      },
                    );
                  },
                ),
              ),
            ],
            const SizedBox(height: 10),

            TextField(
              controller: _plakaCtrl,
              decoration: const InputDecoration(labelText: 'Araç Plakası'),
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 10),

            TextField(
              controller: _lastikCtrl,
              decoration: const InputDecoration(labelText: 'Lastik Bilgisi', hintText: '205/55 R17 Kış'),
            ),
            const SizedBox(height: 10),

            Row(children: [
              const Text('Sezon: '),
              const SizedBox(width: 8),
              ChoiceChip(label: const Text('Yaz'), selected: _sezon == 'Yaz',
                  onSelected: (_) => setState(() => _sezon = 'Yaz')),
              const SizedBox(width: 8),
              ChoiceChip(label: const Text('Kış'), selected: _sezon == 'Kış',
                  onSelected: (_) => setState(() => _sezon = 'Kış')),
              const Spacer(),
              const Text('Adet:'),
              const SizedBox(width: 8),
              DropdownButton<int>(
                value: _adet,
                items: [1,2,3,4,5,6,7,8].map((n) =>
                    DropdownMenuItem(value: n, child: Text('$n'))).toList(),
                onChanged: (v) => setState(() => _adet = v ?? 4),
              ),
            ]),

            if (_hata != null) ...[
              const SizedBox(height: 8),
              Text(_hata!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 16),

            Row(children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('İptal'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: _kaydediliyor ? null : _kaydet,
                  child: _kaydediliyor
                      ? const SizedBox(width: 18, height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Kaydet'),
                ),
              ),
            ]),
          ],
        ),
      ),
    );
  }
}
