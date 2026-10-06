import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/api.dart';
import '../../core/api_client.dart';
import '../../core/config.dart';
import '../../core/format.dart';
import '../../core/token_store.dart';
import '../../ui/bilesenler.dart';
import '../../ui/tema.dart';

class LoginScreen extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginScreen({required this.onLoginSuccess, super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  String _pin = '';
  String _pinTekrar = '';
  bool _setupModu = false;
  bool _ilkPinGirildi = false; // setup modunda ilk PIN girildi, şimdi tekrar bekleniyor
  bool _yukleniyor = true;
  bool _isleniyor = false;
  String? _hata;
  String? _baglantiHatasi;
  final _odak = FocusNode();

  @override
  void initState() {
    super.initState();
    _setupDurumuKontrol();
  }

  @override
  void dispose() {
    _odak.dispose();
    super.dispose();
  }

  Future<void> _setupDurumuKontrol() async {
    setState(() {
      _yukleniyor = true;
      _baglantiHatasi = null;
    });
    try {
      final kurulu = await AuthApi.kuruluMu();
      setState(() {
        _setupModu = !kurulu;
        _yukleniyor = false;
      });
      _odak.requestFocus();
    } catch (e) {
      setState(() {
        _baglantiHatasi = hataMesaji(e);
        _yukleniyor = false;
      });
    }
  }

  void _tusaBasildi(String deger) {
    if (_isleniyor) return;
    final hedef = _ilkPinGirildi ? _pinTekrar : _pin;
    if (hedef.length >= 4) return;

    setState(() {
      _hata = null;
      if (_ilkPinGirildi) {
        _pinTekrar += deger;
      } else {
        _pin += deger;
      }
    });

    // 4 hane tamamlandıysa otomatik işle
    final yeniHedef = _ilkPinGirildi ? _pinTekrar : _pin;
    if (yeniHedef.length == 4) {
      Future.delayed(const Duration(milliseconds: 150), _isle);
    }
  }

  void _silTus() {
    if (_isleniyor) return;
    setState(() {
      _hata = null;
      if (_ilkPinGirildi) {
        if (_pinTekrar.isNotEmpty) {
          _pinTekrar = _pinTekrar.substring(0, _pinTekrar.length - 1);
        } else {
          // Geri dön, ilk PIN girişine
          _ilkPinGirildi = false;
        }
      } else if (_pin.isNotEmpty) {
        _pin = _pin.substring(0, _pin.length - 1);
      }
    });
  }

  Future<void> _isle() async {
    if (_isleniyor) return;

    if (_setupModu) {
      if (!_ilkPinGirildi) {
        setState(() => _ilkPinGirildi = true);
        return;
      }
      if (_pin != _pinTekrar) {
        HapticFeedback.heavyImpact();
        setState(() {
          _hata = 'PIN kodları eşleşmiyor';
          _pinTekrar = '';
          _pin = '';
          _ilkPinGirildi = false;
        });
        return;
      }
      await _girisYap(() => AuthApi.pinKurulum(_pin), kurulum: true);
    } else {
      await _girisYap(() => AuthApi.pinGiris(_pin), kurulum: false);
    }
  }

  Future<void> _girisYap(Future<Json> Function() istek, {required bool kurulum}) async {
    setState(() {
      _isleniyor = true;
      _hata = null;
    });
    try {
      final data = await istek();
      await TokenStore.saveTokens(data['access_token'] as String, data['refresh_token'] as String);
      widget.onLoginSuccess();
    } catch (e) {
      HapticFeedback.heavyImpact();
      final kod = hataKodu(e);
      setState(() {
        _hata = kurulum ? hataMesaji(e) : (kod == 401 || kod == 400 ? 'Hatalı PIN' : hataMesaji(e));
        _pin = '';
        _pinTekrar = '';
        _ilkPinGirildi = false;
        _isleniyor = false;
      });
    }
  }

  KeyEventResult _klavye(FocusNode _, KeyEvent e) {
    if (e is! KeyDownEvent) return KeyEventResult.ignored;
    final k = e.character;
    if (k != null && RegExp(r'^\d$').hasMatch(k)) {
      _tusaBasildi(k);
      return KeyEventResult.handled;
    }
    if (e.logicalKey == LogicalKeyboardKey.backspace) {
      _silTus();
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    if (_yukleniyor) return const Scaffold(body: Yukleniyor());

    if (_baglantiHatasi != null) {
      return Scaffold(body: HataDurum(_baglantiHatasi!, _setupDurumuKontrol));
    }

    final aktifPin = _ilkPinGirildi ? _pinTekrar : _pin;
    final r = context.renk;

    final String baslik;
    final String altBaslik;
    if (_setupModu) {
      baslik = 'PIN Oluştur';
      altBaslik = _ilkPinGirildi ? 'PIN\'i tekrar girin' : '4 haneli yeni PIN belirleyin';
    } else {
      baslik = 'Hoş Geldiniz';
      altBaslik = 'PIN kodunuzu girin';
    }

    return Scaffold(
      body: Focus(
        focusNode: _odak,
        autofocus: true,
        onKeyEvent: _klavye,
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 340),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: Image.asset('assets/icon/icon.png', width: 76, height: 76),
                  ),
                  const SizedBox(height: 14),
                  Text(kAppName, style: context.yazi.labelMedium),
                  const SizedBox(height: 22),
                  Text(baslik, style: context.yazi.headlineMedium),
                  const SizedBox(height: 6),
                  Text(altBaslik, style: context.yazi.bodyMedium?.copyWith(color: r.ikincil)),
                  const SizedBox(height: 28),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(4, (i) {
                      final dolu = i < aktifPin.length;
                      final renk = _hata != null ? r.tehlike : r.metin;
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 150),
                        margin: const EdgeInsets.symmetric(horizontal: 11),
                        width: 14,
                        height: 14,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: dolu ? renk : Colors.transparent,
                          border: Border.all(color: renk, width: 1.4),
                        ),
                      );
                    }),
                  ),
                  SizedBox(
                    height: 44,
                    child: Center(
                      child: _isleniyor
                          ? const CupertinoActivityIndicator()
                          : _hata != null
                              ? Text(_hata!, style: context.yazi.bodyMedium?.copyWith(color: r.tehlike))
                              : null,
                    ),
                  ),
                  _Numpad(onTus: _tusaBasildi, onSil: _silTus, isleniyor: _isleniyor),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Numpad extends StatelessWidget {
  final void Function(String) onTus;
  final VoidCallback onSil;
  final bool isleniyor;

  const _Numpad({required this.onTus, required this.onSil, required this.isleniyor});

  @override
  Widget build(BuildContext context) {
    const tuslar = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['', '0', 'DEL'],
    ];

    return Column(
      children: tuslar
          .map((satir) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 7),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: satir.map((tus) {
                    if (tus.isEmpty) return const SizedBox(width: 78, height: 78);
                    return _Tus(
                      etiket: tus,
                      onTap: () {
                        if (isleniyor) return;
                        HapticFeedback.lightImpact();
                        tus == 'DEL' ? onSil() : onTus(tus);
                      },
                    );
                  }).toList(),
                ),
              ))
          .toList(),
    );
  }
}

class _Tus extends StatefulWidget {
  final String etiket;
  final VoidCallback onTap;
  const _Tus({required this.etiket, required this.onTap});

  @override
  State<_Tus> createState() => _TusState();
}

class _TusState extends State<_Tus> {
  bool _basili = false;

  @override
  Widget build(BuildContext context) {
    final silTus = widget.etiket == 'DEL';
    final r = context.renk;
    return GestureDetector(
      onTapDown: (_) => setState(() => _basili = true),
      onTapUp: (_) => setState(() => _basili = false),
      onTapCancel: () => setState(() => _basili = false),
      onTap: widget.onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 90),
        width: 78,
        height: 78,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: silTus ? Colors.transparent : (_basili ? r.ucuncul : r.kart),
        ),
        child: Center(
          child: silTus
              ? Icon(CupertinoIcons.delete_left, size: 28, color: r.metin)
              : Text(widget.etiket,
                  style: TextStyle(fontFamily: kFont, fontSize: 32, fontWeight: FontWeight.w400, color: r.metin)),
        ),
      ),
    );
  }
}
