import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'core/api.dart';
import 'core/config.dart';
import 'core/token_store.dart';
import 'features/alim/alimlar_sayfasi.dart';
import 'features/dashboard/ozet_sayfasi.dart';
import 'features/giderler/giderler_sayfasi.dart';
import 'features/lastik_oteli/lastik_oteli_sayfasi.dart';
import 'features/musteriler/musteriler_sayfasi.dart';
import 'features/raporlar/raporlar_sayfasi.dart';
import 'features/satis/satislar_sayfasi.dart';
import 'features/tedarikciler/tedarikciler_sayfasi.dart';
import 'features/urunler/urunler_sayfasi.dart';
import 'ui/bilesenler.dart';
import 'ui/tema.dart';

class _Modul {
  final String baslik;
  final IconData ikon;
  final Color Function(Renkler) renk;
  final Widget Function() sayfa;
  const _Modul(this.baslik, this.ikon, this.renk, this.sayfa);
}

final _moduller = <_Modul>[
  _Modul('Özet', CupertinoIcons.square_grid_2x2_fill, (r) => r.ana, () => const OzetSayfasi()),
  _Modul('Satışlar', CupertinoIcons.cart_fill, (r) => r.basari, () => const SatislarSayfasi()),
  _Modul('Lastik Oteli', CupertinoIcons.archivebox_fill, (r) => r.camgobegi, () => const LastikOteliSayfasi()),
  _Modul('Ürünler', CupertinoIcons.cube_box_fill, (r) => r.turuncu, () => const UrunlerSayfasi()),
  _Modul('Alımlar', CupertinoIcons.arrow_down_doc_fill, (r) => r.mor, () => const AlimlarSayfasi()),
  _Modul('Tedarikçiler', CupertinoIcons.building_2_fill, (r) => const Color(0xFFA2845E), () => const TedarikcilerSayfasi()),
  _Modul('Müşteriler', CupertinoIcons.person_2_fill, (r) => const Color(0xFF5856D6), () => const MusterilerSayfasi()),
  _Modul('Giderler', CupertinoIcons.creditcard_fill, (r) => r.tehlike, () => const GiderlerSayfasi()),
  _Modul('Raporlar', CupertinoIcons.chart_bar_alt_fill, (r) => const Color(0xFFFF2D55), () => const RaporlarSayfasi()),
];

/// Kenar çubuğundaki gruplar (modül indeksleri).
const _kenarGruplari = <(String, List<int>)>[
  ('Günlük', [0, 1, 2]),
  ('Stok', [3, 4, 5]),
  ('Kayıtlar', [6, 7]),
  ('Analiz', [8]),
];

/// Telefonda alt sekmede görünen modüller; geri kalanı "Diğer" altında.
const _telefonSekmeleri = [0, 1, 2, 3];

class AppShell extends StatefulWidget {
  final VoidCallback onLogout;
  const AppShell({required this.onLogout, super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _secili = 0;
  final _acilanlar = <int>{0}; // ziyaret edilen modüller canlı tutulur
  final _iskeletAnahtari = GlobalKey<ScaffoldState>();

  void _sec(int i) {
    setState(() {
      _secili = i;
      _acilanlar.add(i);
    });
  }

  /// [diger] yalnızca telefonda: "Diğer" sekmesi (_secili == -1).
  Widget _icerik({Widget? diger}) => IndexedStack(
        index: _secili < 0 ? _moduller.length : _secili,
        children: [
          for (var i = 0; i < _moduller.length; i++) _acilanlar.contains(i) ? _moduller[i].sayfa() : const SizedBox.shrink(),
          diger ?? const SizedBox.shrink(),
        ],
      );

  @override
  Widget build(BuildContext context) {
    final w = Ekran.genislik(context);

    // Tablet yatay: kalıcı kenar çubuğu
    if (w >= Ekran.kenarCubuguEsik) {
      return Scaffold(
        body: Row(children: [
          SizedBox(width: 270, child: _KenarCubugu(secili: _secili, sec: _sec, cikis: _cikis)),
          VerticalDivider(width: 1, thickness: 0, color: context.renk.ayrac),
          Expanded(child: SafeArea(left: false, bottom: false, child: KabukKapsami(menuAc: null, child: _icerik()))),
        ]),
      );
    }

    // Tablet dikey: açılır kenar çubuğu
    if (w >= Ekran.tabletEsik) {
      return Scaffold(
        key: _iskeletAnahtari,
        drawer: Drawer(
          shape: const RoundedRectangleBorder(),
          child: _KenarCubugu(
            secili: _secili,
            sec: (i) {
              _sec(i);
              Navigator.pop(context);
            },
            cikis: _cikis,
          ),
        ),
        body: SafeArea(
          bottom: false,
          child: KabukKapsami(menuAc: () => _iskeletAnahtari.currentState?.openDrawer(), child: _icerik()),
        ),
      );
    }

    // Telefon: alt sekme çubuğu
    final sekmeIndeksi = _telefonSekmeleri.contains(_secili) ? _telefonSekmeleri.indexOf(_secili) : _telefonSekmeleri.length;
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: KabukKapsami(
          menuAc: null,
          child: _icerik(diger: _DigerSayfasi(cikis: _cikis)),
        ),
      ),
      bottomNavigationBar: CupertinoTabBar(
        currentIndex: sekmeIndeksi,
        activeColor: context.renk.ana,
        inactiveColor: context.renk.ikincil,
        backgroundColor: context.renk.kart.withValues(alpha: 0.94),
        border: Border(top: BorderSide(color: context.renk.ayrac, width: 0)),
        height: 56,
        onTap: (i) {
          if (i < _telefonSekmeleri.length) {
            _sec(_telefonSekmeleri[i]);
          } else {
            setState(() => _secili = -1);
          }
        },
        items: [
          for (final i in _telefonSekmeleri) BottomNavigationBarItem(icon: Icon(_moduller[i].ikon), label: _moduller[i].baslik),
          const BottomNavigationBarItem(icon: Icon(CupertinoIcons.ellipsis_circle_fill), label: 'Diğer'),
        ],
      ),
    );
  }

  Future<void> _cikis() async {
    final onay = await onayla(context,
        baslik: 'Çıkış Yap', mesaj: 'Oturumu kapatmak istiyor musunuz?', onayMetni: 'Çıkış Yap', yikici: true);
    if (!onay) return;
    try {
      final refresh = await TokenStore.getRefreshToken();
      if (refresh != null) await AuthApi.cikis(refresh);
    } catch (_) {}
    await TokenStore.clearTokens();
    widget.onLogout();
  }
}

// ─── iPadOS tarzı kenar çubuğu ──────────────────────────────────────────────

class _KenarCubugu extends StatelessWidget {
  final int secili;
  final ValueChanged<int> sec;
  final VoidCallback cikis;
  const _KenarCubugu({required this.secili, required this.sec, required this.cikis});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return ColoredBox(
      color: r.arkaplan,
      child: SafeArea(
        right: false,
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 16, 14),
            child: Row(children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(9),
                child: Image.asset('assets/icon/icon.png', width: 38, height: 38),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Lastik Servisi', style: context.yazi.titleMedium),
                  Text(kAppName, style: context.yazi.labelSmall, maxLines: 1, overflow: TextOverflow.ellipsis),
                ]),
              ),
            ]),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                for (final (grupAdi, indeksler) in _kenarGruplari) ...[
                  Padding(
                    padding: const EdgeInsets.fromLTRB(10, 14, 10, 6),
                    child: Text(grupAdi, style: context.yazi.titleSmall?.copyWith(color: r.ikincil)),
                  ),
                  for (final i in indeksler) _KenarOgesi(modul: _moduller[i], secili: secili == i, onTap: () => sec(i)),
                ],
              ],
            ),
          ),
          Divider(color: r.ayrac),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
            child: Row(children: [
              CircleAvatar(
                radius: 17,
                backgroundColor: r.anaAcik,
                child: Icon(CupertinoIcons.person_fill, size: 18, color: r.ana),
              ),
              const SizedBox(width: 10),
              Expanded(child: Text('Yönetici', style: context.yazi.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
              UstDugme(ikon: CupertinoIcons.square_arrow_right, ipucu: 'Çıkış Yap', renk: r.tehlike, onTap: cikis),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _KenarOgesi extends StatelessWidget {
  final _Modul modul;
  final bool secili;
  final VoidCallback onTap;
  const _KenarOgesi({required this.modul, required this.secili, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final renk = secili ? Colors.white : modul.renk(r);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: Material(
        color: secili ? r.ana : Colors.transparent,
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          borderRadius: BorderRadius.circular(10),
          onTap: onTap,
          child: SizedBox(
            height: 46,
            child: Row(children: [
              const SizedBox(width: 12),
              Icon(modul.ikon, size: 22, color: renk),
              const SizedBox(width: 14),
              Text(modul.baslik,
                  style: context.yazi.bodyLarge?.copyWith(
                    color: secili ? Colors.white : r.metin,
                    fontWeight: secili ? FontWeight.w600 : FontWeight.w400,
                  )),
            ]),
          ),
        ),
      ),
    );
  }
}

// ─── Telefon: "Diğer" sekmesi ───────────────────────────────────────────────

class _DigerSayfasi extends StatelessWidget {
  final VoidCallback cikis;
  const _DigerSayfasi({required this.cikis});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final digerleri = [
      for (var i = 0; i < _moduller.length; i++)
        if (!_telefonSekmeleri.contains(i)) i
    ];
    return ListView(children: [
      const BuyukBaslik('Diğer'),
      const SizedBox(height: 8),
      Grup(
        girinti: 58,
        children: [
          for (final i in digerleri)
            Satir(
              onde: IkonKutusu(_moduller[i].ikon, _moduller[i].renk(r)),
              baslik: _moduller[i].baslik,
              onTap: () => Navigator.of(context).push(CupertinoPageRoute(
                builder: (_) => Scaffold(body: SafeArea(bottom: false, child: _moduller[i].sayfa())),
              )),
            ),
        ],
      ),
      Grup(children: [EylemSatiri('Çıkış Yap', ikon: CupertinoIcons.square_arrow_right, yikici: true, onTap: cikis)]),
    ]);
  }
}
