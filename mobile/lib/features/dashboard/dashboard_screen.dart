import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/api_client.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _data;
  bool _yukleniyor = true;
  String? _hata;

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  Future<void> _yukle() async {
    setState(() { _yukleniyor = true; _hata = null; });
    try {
      final data = await ApiClient.instance.get('/api/raporlar/dashboard');
      setState(() { _data = data as Map<String, dynamic>?; _yukleniyor = false; });
    } on DioException catch (e) {
      setState(() { _hata = (e.error as ApiError?)?.detail ?? 'Hata'; _yukleniyor = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_yukleniyor) return const Center(child: CircularProgressIndicator());
    if (_hata != null) return Center(child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [Text(_hata!), TextButton(onPressed: _yukle, child: const Text('Tekrar dene'))],
    ));

    final d = _data ?? {};
    return RefreshIndicator(
      onRefresh: _yukle,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _baslik('Bugün'),
          _satirKartlar([
            _KartVeri('Ciro', _para(d['bugun_ciro']), Icons.trending_up, Colors.green),
            _KartVeri('Kâr', _para(d['bugun_kar']), Icons.attach_money, Colors.teal),
            _KartVeri('Satış', '${d['bugun_satis_adedi'] ?? 0}', Icons.receipt, Colors.blue),
          ]),
          _baslik('Bu Ay'),
          _satirKartlar([
            _KartVeri('Ciro', _para(d['bu_ay_ciro']), Icons.bar_chart, Colors.orange),
            _KartVeri('Kâr', _para(d['bu_ay_kar']), Icons.show_chart, Colors.deepOrange),
          ]),
          _baslik('Genel'),
          _satirKartlar([
            _KartVeri('Tedarikçi Borcu', _para(d['toplam_tedarikci_borcu']), Icons.account_balance, Colors.red),
            _KartVeri('Stok Değeri', _para(d['toplam_stok_degeri']), Icons.inventory, Colors.purple),
            _KartVeri('Müşteriler', '${d['toplam_musteri'] ?? 0}', Icons.people, Colors.indigo),
          ]),
        ],
      ),
    );
  }

  Widget _baslik(String text) => Padding(
    padding: const EdgeInsets.only(top: 16, bottom: 8),
    child: Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey)),
  );

  Widget _satirKartlar(List<_KartVeri> kartlar) => Row(
    children: kartlar.map((k) => Expanded(child: _Kart(veri: k))).toList(),
  );

  String _para(dynamic v) {
    if (v == null) return '0,00 ₺';
    return '${(v as num).toStringAsFixed(2).replaceAll('.', ',')} ₺';
  }
}

class _KartVeri {
  final String baslik, deger;
  final IconData ikon;
  final Color renk;
  const _KartVeri(this.baslik, this.deger, this.ikon, this.renk);
}

class _Kart extends StatelessWidget {
  final _KartVeri veri;
  const _Kart({required this.veri});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(veri.ikon, color: veri.renk, size: 20),
            const SizedBox(height: 6),
            Text(veri.deger, style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: veri.renk)),
            Text(veri.baslik, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
