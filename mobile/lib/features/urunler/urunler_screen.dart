import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../barkod/barkod_screen.dart';

class UrunlerScreen extends StatefulWidget {
  const UrunlerScreen({super.key});

  @override
  State<UrunlerScreen> createState() => _UrunlerScreenState();
}

class _UrunlerScreenState extends State<UrunlerScreen> {
  List<dynamic> _urunler = [];
  bool _yukleniyor = true;
  final _araCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  @override
  void dispose() {
    _araCtrl.dispose();
    super.dispose();
  }

  Future<void> _yukle({String? arama}) async {
    setState(() => _yukleniyor = true);
    try {
      final params = <String, dynamic>{'limit': 100};
      if (arama != null && arama.isNotEmpty) params['arama'] = arama;
      final data = await ApiClient.instance.get('/api/urunler', params: params);
      setState(() { _urunler = data as List? ?? []; _yukleniyor = false; });
    } catch (_) {
      setState(() => _yukleniyor = false);
    }
  }

  Future<void> _barkodOkut() async {
    final urun = await Navigator.push<dynamic>(
      context,
      MaterialPageRoute(builder: (_) => const BarkodScreen()),
    );
    if (urun != null && mounted) {
      _araCtrl.text = urun['barkod_qr'] ?? urun['ad'] ?? '';
      _yukle(arama: _araCtrl.text);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(
            children: [
              Expanded(
                child: SearchBar(
                  controller: _araCtrl,
                  hintText: 'Ürün adı, barkod veya ebat…',
                  onSubmitted: (v) => _yukle(arama: v),
                  trailing: [
                    IconButton(icon: const Icon(Icons.search), onPressed: () => _yukle(arama: _araCtrl.text)),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.qr_code_scanner),
                tooltip: 'Barkod Okut',
                onPressed: _barkodOkut,
              ),
            ],
          ),
        ),
        Expanded(
          child: _yukleniyor
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: () => _yukle(arama: _araCtrl.text),
                  child: _urunler.isEmpty
                      ? const Center(child: Text('Ürün bulunamadı'))
                      : ListView.builder(
                          itemCount: _urunler.length,
                          itemBuilder: (_, i) {
                            final u = _urunler[i] as Map<String, dynamic>;
                            final stok = u['stok'] as int? ?? 0;
                            return ListTile(
                              leading: CircleAvatar(
                                backgroundColor: stok > 0 ? Colors.green.shade100 : Colors.red.shade100,
                                child: Text('$stok', style: TextStyle(
                                  color: stok > 0 ? Colors.green.shade800 : Colors.red.shade800,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                )),
                              ),
                              title: Text(u['ad'] as String? ?? ''),
                              subtitle: Text(
                                '${u['ebat'] ?? ''}  •  ${u['marka_adi'] ?? ''}  ${u['model_adi'] ?? ''}  ${u['mevsim'] ?? ''}',
                              ),
                              trailing: Text(
                                '${(u['satis_fiyati'] as num?)?.toStringAsFixed(2) ?? '0.00'} ₺',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                            );
                          },
                        ),
                ),
        ),
      ],
    );
  }
}
