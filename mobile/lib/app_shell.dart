import 'package:flutter/material.dart';
import 'core/token_store.dart';
import 'core/api_client.dart';
import 'features/barkod/barkod_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/urunler/urunler_screen.dart';
import 'features/satis/satis_screen.dart';
import 'features/alim/alim_screen.dart';
import 'features/musteriler/musteriler_screen.dart';
import 'features/lastik_oteli/lastik_oteli_screen.dart';

class AppShell extends StatefulWidget {
  final VoidCallback onLogout;
  const AppShell({required this.onLogout, super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tab = 0;

  static const _basliklar = ['Dashboard', 'Ürünler', 'Satış', 'Alım', 'Müşteriler', 'Lastik Oteli'];
  static const _ikonlar = [
    Icons.dashboard,
    Icons.inventory_2,
    Icons.point_of_sale,
    Icons.local_shipping,
    Icons.people,
    Icons.store,
  ];

  @override
  Widget build(BuildContext context) {
    // Ekranlar burada oluşturuluyor çünkü onLogout callback'i gerekiyor
    final ekranlar = [
      const DashboardScreen(),
      const UrunlerScreen(),
      const SatisScreen(),
      const AlimScreen(),
      const MusterilerScreen(),
      const LastikOteliScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(_basliklar[_tab]),
        actions: [
          if (_tab != 1)
            IconButton(
              icon: const Icon(Icons.qr_code_scanner),
              tooltip: 'Barkod / QR Okut',
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const BarkodScreen()),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Çıkış',
            onPressed: _cikis,
          ),
        ],
      ),
      body: IndexedStack(index: _tab, children: ekranlar),
      bottomNavigationBar: _ScrollableBottomNav(
        basliklar: _basliklar,
        ikonlar: _ikonlar,
        secili: _tab,
        onTap: (i) => setState(() => _tab = i),
      ),
    );
  }

  Future<void> _cikis() async {
    final onay = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Çıkış'),
        content: const Text('Oturumu kapatmak istiyor musunuz?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('İptal')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Çıkış')),
        ],
      ),
    );
    if (onay != true) return;
    try {
      final refresh = await TokenStore.getRefreshToken();
      if (refresh != null) {
        await ApiClient.instance.post('/api/auth/cikis', data: {'refresh_token': refresh});
      }
    } catch (_) {}
    await TokenStore.clearTokens();
    widget.onLogout();
  }
}

// ─── Yatay kaydırılabilir alt navigasyon ─────────────────────────────────────

class _ScrollableBottomNav extends StatelessWidget {
  final List<String> basliklar;
  final List<IconData> ikonlar;
  final int secili;
  final ValueChanged<int> onTap;

  const _ScrollableBottomNav({
    required this.basliklar,
    required this.ikonlar,
    required this.secili,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return SafeArea(
      top: false,
      child: Container(
        height: 70,
        decoration: BoxDecoration(
          color: cs.surface,
          border: Border(top: BorderSide(color: Colors.grey.shade300)),
        ),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: List.generate(basliklar.length, (i) {
              final aktif = secili == i;
              final renk = aktif ? cs.primary : Colors.grey.shade600;
              return InkWell(
                onTap: () => onTap(i),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: 86,
                  margin: const EdgeInsets.symmetric(horizontal: 2, vertical: 6),
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  decoration: BoxDecoration(
                    color: aktif ? cs.primaryContainer.withOpacity(0.4) : Colors.transparent,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(ikonlar[i], color: renk, size: 22),
                      const SizedBox(height: 4),
                      Text(
                        basliklar[i],
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 11,
                          color: renk,
                          fontWeight: aktif ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}
