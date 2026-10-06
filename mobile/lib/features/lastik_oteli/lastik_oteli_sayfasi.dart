import 'package:flutter/cupertino.dart';

import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../ui/bilesenler.dart';
import '../../ui/form.dart';
import '../../ui/liste_detay.dart';
import '../../ui/tema.dart';
import '../../ui/veri.dart';
import '../barkod/barkod_screen.dart';
import '../musteriler/musteriler_sayfasi.dart';

class LastikOteliSayfasi extends StatelessWidget {
  const LastikOteliSayfasi({super.key});

  @override
  Widget build(BuildContext context) => ListeDetay(
        bosIkon: CupertinoIcons.archivebox,
        liste: (ctx, sec, seciliId) => _OtelListesi(sec: sec, seciliId: seciliId),
        detay: (ctx, k) => OtelDetay(kayit: k),
      );
}

class _OtelListesi extends StatefulWidget {
  final void Function(Json) sec;
  final int? seciliId;
  const _OtelListesi({required this.sec, this.seciliId});

  @override
  State<_OtelListesi> createState() => _OtelListesiState();
}

class _OtelListesiState extends State<_OtelListesi> with VeriYukleyici<_OtelListesi, List<Json>> {
  bool _sadeceDepoda = true;
  String _arama = '';

  @override
  Future<List<Json>> getir() => OtelApi.liste(sadeceAktif: _sadeceDepoda, arama: _arama);

  Future<void> _rafSorgula() async {
    final s = await Navigator.of(context).push<Json>(CupertinoPageRoute(
      builder: (_) => const BarkodScreen(hamDeger: true, ipucu: 'Rafın üzerindeki QR kodu okutun'),
    ));
    final kod = (s?['rawValue'] as String?)?.trim().toUpperCase();
    if (kod == null || kod.isEmpty || !mounted) return;
    try {
      final kayit = await OtelApi.raf(kod);
      if (mounted) widget.sec(kayit);
    } catch (e) {
      if (mounted) bildir(context, hataKodu(e) == 404 ? 'Raf $kod boş' : hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      ListeUstu(
        baslik: 'Lastik Oteli',
        eylemler: [
          UstDugme(ikon: CupertinoIcons.qrcode_viewfinder, ipucu: 'QR ile raf sorgula', onTap: _rafSorgula),
          UstDugme(ikon: CupertinoIcons.add, ipucu: 'Yeni kayıt', onTap: () => otelFormuAc(context)),
        ],
        arama: AramaKutusu(
          ipucu: 'Raf, müşteri veya plaka',
          degisti: (v) {
            _arama = v;
            yenile();
          },
        ),
        filtre: SizedBox(
          width: double.infinity,
          child: SegmentSecici<bool>(
            secenekler: const {true: 'Depoda', false: 'Tümü'},
            secili: _sadeceDepoda,
            degisti: (v) {
              _sadeceDepoda = v;
              yenile();
            },
          ),
        ),
      ),
      Expanded(
        child: durum((liste) {
          if (liste.isEmpty) {
            return BosDurum(
              ikon: CupertinoIcons.archivebox,
              baslik: _arama.isNotEmpty ? 'Sonuç bulunamadı' : 'Depoda lastik yok',
              eylem: _arama.isEmpty
                  ? CupertinoButton.filled(onPressed: () => otelFormuAc(context), child: const Text('Yeni Kayıt'))
                  : null,
            );
          }
          final depodaki = liste.where((k) => dogruMu(k['aktif_mi']));
          final lastikSayisi = depodaki.fold<int>(0, (t, k) => t + tamSayi(k['lastik_adedi']));
          return YenilenebilirListe(
            yenile: yenile,
            children: [
              Grup(
                girinti: 72,
                altNot: '${liste.length} kayıt · depoda $lastikSayisi lastik',
                children: [
                  for (final k in liste)
                    Satir(
                      onde: RafKutusu(k['raf_kodu'] as String? ?? '', aktif: dogruMu(k['aktif_mi'])),
                      baslik: k['musteri_adi'] as String? ?? '',
                      alt: [
                        k['arac_plakasi'],
                        k['lastik_bilgisi'],
                        '${tamSayi(k['lastik_adedi'])} adet ${k['sezon'] ?? ''}',
                      ].where((e) => e != null && '$e'.trim().isNotEmpty).join('  ·  '),
                      sag: dogruMu(k['aktif_mi']) ? null : Rozet('Teslim edildi', r.ikincil),
                      secili: widget.seciliId == k['id'],
                      onTap: () => widget.sec(k),
                    ),
                ],
              ),
            ],
          );
        }),
      ),
    ]);
  }
}

class RafKutusu extends StatelessWidget {
  final String kod;
  final bool aktif;
  final double boyut;
  const RafKutusu(this.kod, {this.aktif = true, this.boyut = 44, super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final renk = aktif ? r.camgobegi : r.ikincil;
    return Container(
      width: boyut,
      height: boyut,
      decoration: BoxDecoration(color: renk.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(boyut * 0.24)),
      child: Center(
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Padding(
            padding: const EdgeInsets.all(4),
            child:
                Text(kod, style: TextStyle(fontFamily: kFont, fontWeight: FontWeight.w700, fontSize: boyut * 0.34, color: renk)),
          ),
        ),
      ),
    );
  }
}

// ─── Detay ──────────────────────────────────────────────────────────────────

class OtelDetay extends StatefulWidget {
  final Json kayit;
  const OtelDetay({required this.kayit, super.key});

  @override
  State<OtelDetay> createState() => _OtelDetayState();
}

class _OtelDetayState extends State<OtelDetay> with VeriYukleyici<OtelDetay, Json> {
  int get _id => tamSayi(widget.kayit['id']);

  @override
  Json? get ilkVeri => widget.kayit;

  @override
  Future<Json> getir() => OtelApi.getir(_id);

  Future<void> _teslim(Json k) async {
    final ok = await formAc<bool>(context, (_) => _TeslimFormu(kayit: k), genislik: 480);
    if (ok == true && mounted) bildir(context, 'Raf ${k['raf_kodu']} teslim edildi');
  }

  Future<void> _sil(Json k) async {
    final onay = await onayla(context,
        baslik: 'Kaydı Sil',
        mesaj: 'Raf ${k['raf_kodu']} — ${k['musteri_adi']} kaydı silinecek.',
        onayMetni: 'Sil',
        yikici: true);
    if (!onay || !mounted) return;
    try {
      await OtelApi.sil(_id);
      if (!mounted) return;
      bildir(context, 'Kayıt silindi');
      DetayKapsami.of(context).kapat();
      veriDegisti();
    } catch (e) {
      if (mounted) bildir(context, hataMesaji(e), hata: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return durum((k) {
      final r = context.renk;
      final aktif = dogruMu(k['aktif_mi']);
      final giris = tarihOku(k['giris_tarihi']);
      final gun = giris == null ? null : DateTime.now().difference(giris).inDays;
      return DetayIskeleti(
        baslik: 'Raf ${k['raf_kodu'] ?? ''}',
        yenile: yenile,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Center(child: RafKutusu(k['raf_kodu'] as String? ?? '', aktif: aktif, boyut: 84)),
          ),
          DetayKafa(
            ikonGoster: false,
            renk: aktif ? r.camgobegi : r.ikincil,
            baslik: k['musteri_adi'] as String? ?? '',
            alt: k['arac_plakasi'] as String?,
            rozet:
                Rozet(aktif ? 'Depoda${gun != null ? ' · $gun gündür' : ''}' : 'Teslim edildi', aktif ? r.camgobegi : r.ikincil),
          ),
          if (aktif)
            EylemDugmeleri([
              (CupertinoIcons.checkmark_seal_fill, 'Teslim Et', () => _teslim(k), r.basari),
            ]),
          Grup(baslik: 'Lastik', children: [
            BilgiSatiri('Lastik Bilgisi', k['lastik_bilgisi'] as String?),
            BilgiSatiri('Adet', '${tamSayi(k['lastik_adedi'])}'),
            BilgiSatiri('Sezon', k['sezon'] as String?),
          ]),
          Grup(baslik: 'Tarihler', children: [
            BilgiSatiri('Giriş', tarih(k['giris_tarihi'])),
            BilgiSatiri('Çıkış', k['cikis_tarihi'] == null ? null : tarih(k['cikis_tarihi'])),
          ]),
          if ((k['notlar'] as String?)?.isNotEmpty == true)
            Grup(baslik: 'Notlar', children: [
              Padding(padding: const EdgeInsets.all(16), child: Text(k['notlar'] as String, style: context.yazi.bodyLarge)),
            ]),
          Grup(children: [EylemSatiri('Kaydı Sil', yikici: true, onTap: () => _sil(k))]),
        ],
      );
    });
  }
}

class _TeslimFormu extends StatefulWidget {
  final Json kayit;
  const _TeslimFormu({required this.kayit});

  @override
  State<_TeslimFormu> createState() => _TeslimFormuState();
}

class _TeslimFormuState extends State<_TeslimFormu> {
  DateTime _tarih = DateTime.now();
  bool _kaydediliyor = false;
  String? _hata;

  Future<void> _kaydet() async {
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      await OtelApi.teslim(tamSayi(widget.kayit['id']), _tarih);
      veriDegisti();
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() {
        _hata = hataMesaji(e);
        _kaydediliyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final k = widget.kayit;
    return FormIskeleti(
      baslik: 'Teslim Et',
      kaydetMetni: 'Teslim Et',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          BilgiSatiri('Raf', k['raf_kodu'] as String?),
          BilgiSatiri('Müşteri', k['musteri_adi'] as String?),
          BilgiSatiri('Lastik', '${tamSayi(k['lastik_adedi'])} adet ${k['lastik_bilgisi'] ?? ''}'),
        ]),
        Grup(children: [TarihSatiri(etiket: 'Çıkış Tarihi', deger: _tarih, degisti: (t) => setState(() => _tarih = t))]),
      ],
    );
  }
}

// ─── Yeni kayıt ─────────────────────────────────────────────────────────────

Future<void> otelFormuAc(BuildContext context) => formAc(context, (_) => const _OtelFormu());

class _OtelFormu extends StatefulWidget {
  const _OtelFormu();

  @override
  State<_OtelFormu> createState() => _OtelFormuState();
}

class _OtelFormuState extends State<_OtelFormu> {
  final _raf = TextEditingController();
  final _musteriAdi = TextEditingController();
  final _plaka = TextEditingController();
  final _lastik = TextEditingController();
  final _not = TextEditingController();
  int? _musteriId;
  String _sezon = 'Yaz';
  int _adet = 4;
  DateTime _giris = DateTime.now();
  bool _kaydediliyor = false;
  String? _hata;

  @override
  void dispose() {
    for (final c in [_raf, _musteriAdi, _plaka, _lastik, _not]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _musteriSec() async {
    final m = await aramaliSec(
      context,
      baslik: 'Müşteri Seç',
      aramaIpucu: 'Ad, telefon veya plaka',
      yukle: (q) => MusteriApi.liste(arama: q, limit: 50),
      satirBaslik: (m) => m['ad_soyad'] as String? ?? '',
      satirAlt: (m) => [m['telefon'], m['arac_plakasi']].where((e) => e != null && '$e'.isNotEmpty).join('  ·  '),
      yeniEkle: (ctx) => musteriFormuAc(ctx),
    );
    if (m == null) return;
    setState(() {
      _musteriId = tamSayi(m['id']);
      _musteriAdi.text = m['ad_soyad'] as String? ?? '';
      if ((m['arac_plakasi'] as String?)?.isNotEmpty == true) _plaka.text = m['arac_plakasi'] as String;
    });
  }

  Future<void> _rafOkut() async {
    final s = await Navigator.of(context).push<Json>(
      CupertinoPageRoute(builder: (_) => const BarkodScreen(hamDeger: true, ipucu: 'Rafın QR kodunu okutun')),
    );
    final v = (s?['rawValue'] as String?)?.trim().toUpperCase();
    if (v != null) setState(() => _raf.text = v);
  }

  Future<void> _kaydet() async {
    final raf = _raf.text.trim().toUpperCase();
    String? hata;
    if (!RegExp(r'^[A-Z]+\d+$').hasMatch(raf)) {
      hata = 'Raf kodu harf + sayı olmalıdır (ör. A3, B12)';
    } else if (_musteriAdi.text.trim().isEmpty) {
      hata = 'Müşteri adı zorunludur';
    }
    if (hata != null) {
      setState(() => _hata = hata);
      return;
    }
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    String? bosNull(TextEditingController c) => c.text.trim().isEmpty ? null : c.text.trim();
    try {
      await OtelApi.ekle({
        'musteri_id': _musteriId,
        'musteri_adi_anlik': _musteriAdi.text.trim(),
        'arac_plakasi': bosNull(_plaka)?.toUpperCase(),
        'raf_kodu': raf,
        'lastik_bilgisi': bosNull(_lastik),
        'lastik_adedi': _adet,
        'sezon': _sezon,
        'giris_tarihi': isoGun(_giris),
        'notlar': bosNull(_not),
      });
      veriDegisti();
      if (!mounted) return;
      bildir(context, 'Raf $raf kaydedildi');
      Navigator.pop(context);
    } catch (e) {
      setState(() {
        _hata = hataMesaji(e);
        _kaydediliyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormIskeleti(
      baslik: 'Yeni Otel Kaydı',
      kaydet: _kaydet,
      kaydediliyor: _kaydediliyor,
      hata: _hata,
      children: [
        Grup(children: [
          MetinSatiri(
            etiket: 'Raf Kodu',
            kontrolcu: _raf,
            ipucu: 'A3, B12…',
            buyukHarfli: true,
            sag: UstDugme(ikon: CupertinoIcons.qrcode_viewfinder, ipucu: 'Raf QR okut', onTap: _rafOkut),
          ),
        ]),
        Grup(
          baslik: 'Müşteri',
          altNot: 'Kayıtlı müşteri seçebilir ya da yalnızca ad yazabilirsiniz.',
          children: [
            EylemSatiri(_musteriId == null ? 'Kayıtlı Müşteriden Seç' : 'Başka Müşteri Seç',
                ikon: CupertinoIcons.person_crop_circle, onTap: _musteriSec),
            MetinSatiri(
              etiket: 'Ad Soyad',
              kontrolcu: _musteriAdi,
              ipucu: 'Zorunlu',
              degisti: (_) => _musteriId = null,
            ),
            MetinSatiri(etiket: 'Plaka', kontrolcu: _plaka, ipucu: '34 ABC 123', buyukHarfli: true),
          ],
        ),
        Grup(baslik: 'Lastik', children: [
          MetinSatiri(etiket: 'Lastik Bilgisi', kontrolcu: _lastik, ipucu: '205/55 R16 Michelin'),
          AdimSatiri(etiket: 'Adet', deger: _adet, min: 1, max: 8, degisti: (v) => setState(() => _adet = v)),
          SegmentSatiri<String>(
            etiket: 'Sezon',
            secenekler: const {'Yaz': 'Yaz', 'Kış': 'Kış'},
            secili: _sezon,
            degisti: (v) => setState(() => _sezon = v),
          ),
          TarihSatiri(etiket: 'Giriş Tarihi', deger: _giris, degisti: (t) => setState(() => _giris = t)),
        ]),
        Grup(children: [MetinSatiri(etiket: 'Notlar', kontrolcu: _not, satir: 2)]),
      ],
    );
  }
}
