import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';

class MusterilerScreen extends StatefulWidget {
  const MusterilerScreen({super.key});

  @override
  State<MusterilerScreen> createState() => _MusterilerScreenState();
}

class _MusterilerScreenState extends State<MusterilerScreen> {
  List<dynamic> _musteriler = [];
  bool _yukleniyor = true;
  final _araCtrl = TextEditingController();

  @override
  void initState() { super.initState(); _yukle(); }

  @override
  void dispose() { _araCtrl.dispose(); super.dispose(); }

  Future<void> _yukle({String? arama}) async {
    setState(() => _yukleniyor = true);
    try {
      final params = <String, dynamic>{'limit': 100};
      if (arama != null && arama.isNotEmpty) params['arama'] = arama;
      final data = await ApiClient.instance.get('/api/musteriler', params: params);
      setState(() { _musteriler = data as List? ?? []; _yukleniyor = false; });
    } catch (_) { setState(() => _yukleniyor = false); }
  }

  Future<void> _yeniMusteri() async {
    final sonuc = await showDialog<bool>(
      context: context,
      builder: (_) => const _MusteriFormDialog(),
    );
    if (sonuc == true) _yukle();
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Padding(
        padding: const EdgeInsets.all(8),
        child: SearchBar(
          controller: _araCtrl,
          hintText: 'Ad, telefon veya plaka…',
          onSubmitted: (v) => _yukle(arama: v),
          trailing: [
            IconButton(icon: const Icon(Icons.search), onPressed: () => _yukle(arama: _araCtrl.text)),
            IconButton(icon: const Icon(Icons.clear), onPressed: () { _araCtrl.clear(); _yukle(); }),
          ],
        ),
      ),
      Expanded(
        child: _yukleniyor
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: () => _yukle(arama: _araCtrl.text),
                child: _musteriler.isEmpty
                    ? const Center(child: Text('Müşteri bulunamadı'))
                    : ListView.builder(
                        itemCount: _musteriler.length,
                        itemBuilder: (_, i) {
                          final m = _musteriler[i] as Map<String, dynamic>;
                          return ListTile(
                            leading: const CircleAvatar(child: Icon(Icons.person)),
                            title: Text(m['ad_soyad'] as String? ?? ''),
                            subtitle: Text(
                              '${m['telefon']}${m['arac_plakasi'] != null ? '  •  ${m['arac_plakasi']}' : ''}${m['arac_markasi'] != null ? '  (${m['arac_markasi']})' : ''}',
                            ),
                          );
                        },
                      ),
              ),
      ),
      Padding(
        padding: const EdgeInsets.all(12),
        child: SizedBox(width: double.infinity,
          child: FilledButton.icon(
            onPressed: _yeniMusteri,
            icon: const Icon(Icons.person_add),
            label: const Text('Yeni Müşteri'),
          ),
        ),
      ),
    ]);
  }
}

class _MusteriFormDialog extends StatefulWidget {
  const _MusteriFormDialog();

  @override
  State<_MusteriFormDialog> createState() => _MusteriFormDialogState();
}

class _MusteriFormDialogState extends State<_MusteriFormDialog> {
  final _adCtrl = TextEditingController();
  final _telCtrl = TextEditingController();
  final _markaCtrl = TextEditingController();
  final _plakaCtrl = TextEditingController();
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    _adCtrl.dispose(); _telCtrl.dispose();
    _markaCtrl.dispose(); _plakaCtrl.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    if (_adCtrl.text.trim().isEmpty || _telCtrl.text.trim().isEmpty) {
      setState(() => _hata = 'Ad soyad ve telefon zorunludur');
      return;
    }
    setState(() { _kaydediliyor = true; _hata = null; });
    try {
      await ApiClient.instance.post('/api/musteriler', data: {
        'ad_soyad': _adCtrl.text.trim(),
        'telefon': _telCtrl.text.trim(),
        'arac_markasi': _markaCtrl.text.trim().isEmpty ? null : _markaCtrl.text.trim(),
        'arac_plakasi': _plakaCtrl.text.trim().isEmpty ? null : _plakaCtrl.text.trim().toUpperCase(),
        'notlar': null,
      });
      if (mounted) Navigator.pop(context, true);
    } on DioException catch (e) {
      setState(() { _hata = (e.error as ApiError?)?.detail ?? 'Hata'; _kaydediliyor = false; });
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Yeni Müşteri'),
    content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
      TextField(controller: _adCtrl, decoration: const InputDecoration(labelText: 'Ad Soyad *')),
      TextField(controller: _telCtrl, keyboardType: TextInputType.phone,
          decoration: const InputDecoration(labelText: 'Telefon *')),
      TextField(controller: _markaCtrl, decoration: const InputDecoration(labelText: 'Araç Markası')),
      TextField(controller: _plakaCtrl,
          textCapitalization: TextCapitalization.characters,
          decoration: const InputDecoration(labelText: 'Plaka')),
      if (_hata != null) Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Text(_hata!, style: const TextStyle(color: Colors.red, fontSize: 12)),
      ),
    ])),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('İptal')),
      FilledButton(
        onPressed: _kaydediliyor ? null : _kaydet,
        child: _kaydediliyor
            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
            : const Text('Kaydet'),
      ),
    ],
  );
}
