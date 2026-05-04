import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/api_client.dart';
import '../../core/token_store.dart';

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

  @override
  void initState() {
    super.initState();
    _setupDurumuKontrol();
  }

  Future<void> _setupDurumuKontrol() async {
    setState(() { _yukleniyor = true; _hata = null; });
    try {
      final data = await ApiClient.instance.get('/api/auth/setup-durumu');
      final kurulu = (data as Map<String, dynamic>)['kurulu_mu'] as bool? ?? false;
      setState(() { _setupModu = !kurulu; _yukleniyor = false; });
    } catch (e) {
      setState(() { _hata = 'Sunucuya bağlanılamıyor'; _yukleniyor = false; });
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
      } else {
        if (_pin.isNotEmpty) {
          _pin = _pin.substring(0, _pin.length - 1);
        }
      }
    });
  }

  Future<void> _isle() async {
    if (_isleniyor) return;

    if (_setupModu) {
      if (!_ilkPinGirildi) {
        // İlk PIN girildi, tekrar bekleniyor
        setState(() { _ilkPinGirildi = true; });
        return;
      }
      // Tekrar girişi kontrol
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
      await _pinKurulum();
    } else {
      await _pinGiris();
    }
  }

  Future<void> _pinGiris() async {
    setState(() { _isleniyor = true; _hata = null; });
    try {
      final data = await ApiClient.instance.post(
        '/api/auth/pin-giris',
        data: {'pin': _pin},
      );
      await TokenStore.saveTokens(
        (data as Map<String, dynamic>)['access_token'] as String,
        data['refresh_token'] as String,
      );
      widget.onLoginSuccess();
    } on DioException catch (e) {
      HapticFeedback.heavyImpact();
      setState(() {
        _hata = 'Hatalı PIN';
        _pin = '';
        _isleniyor = false;
      });
    } catch (_) {
      setState(() {
        _hata = 'Bağlantı hatası';
        _pin = '';
        _isleniyor = false;
      });
    }
  }

  Future<void> _pinKurulum() async {
    setState(() { _isleniyor = true; _hata = null; });
    try {
      final data = await ApiClient.instance.post(
        '/api/auth/pin-kurulum',
        data: {'pin': _pin},
      );
      await TokenStore.saveTokens(
        (data as Map<String, dynamic>)['access_token'] as String,
        data['refresh_token'] as String,
      );
      widget.onLoginSuccess();
    } on DioException catch (e) {
      final detay = (e.error as ApiError?)?.detail ?? 'Hata oluştu';
      setState(() {
        _hata = detay;
        _pin = '';
        _pinTekrar = '';
        _ilkPinGirildi = false;
        _isleniyor = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_yukleniyor) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_hata != null && !_isleniyor && _pin.isEmpty && _pinTekrar.isEmpty) {
      return Scaffold(
        body: Center(child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_hata!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _setupDurumuKontrol,
              child: const Text('Tekrar Dene'),
            ),
          ],
        )),
      );
    }

    final aktifPin = _ilkPinGirildi ? _pinTekrar : _pin;

    String baslik;
    String altBaslik;
    if (_setupModu) {
      baslik = 'PIN Oluştur';
      altBaslik = _ilkPinGirildi
          ? 'PIN\'i tekrar girin'
          : '4 haneli yeni PIN belirleyin';
    } else {
      baslik = 'Hoş Geldiniz';
      altBaslik = 'PIN kodunuzu girin';
    }

    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const Spacer(),
              // Başlık
              Text(baslik, style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              )),
              const SizedBox(height: 8),
              Text(altBaslik, style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey,
              )),
              const SizedBox(height: 40),

              // 4 Nokta Göstergesi
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(4, (i) {
                  final dolu = i < aktifPin.length;
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    margin: const EdgeInsets.symmetric(horizontal: 10),
                    width: 18,
                    height: 18,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _hata != null
                          ? Colors.red
                          : dolu
                              ? Theme.of(context).colorScheme.primary
                              : Colors.grey.shade300,
                      border: Border.all(
                        color: dolu
                            ? Theme.of(context).colorScheme.primary
                            : Colors.grey.shade400,
                        width: 1.5,
                      ),
                    ),
                  );
                }),
              ),

              if (_hata != null) ...[
                const SizedBox(height: 16),
                Text(_hata!, style: const TextStyle(color: Colors.red, fontSize: 13)),
              ],

              const Spacer(),

              // Numpad
              _Numpad(
                onTus: _tusaBasildi,
                onSil: _silTus,
                isleniyor: _isleniyor,
              ),

              const SizedBox(height: 24),
            ],
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
    final tuslar = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['', '0', 'DEL'],
    ];

    return Column(
      children: tuslar.map((satir) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: satir.map((tus) {
            if (tus.isEmpty) return const SizedBox(width: 80, height: 80);
            return _Tus(
              etiket: tus,
              onTap: () {
                if (isleniyor) return;
                HapticFeedback.lightImpact();
                if (tus == 'DEL') {
                  onSil();
                } else {
                  onTus(tus);
                }
              },
            );
          }).toList(),
        ),
      )).toList(),
    );
  }
}

class _Tus extends StatelessWidget {
  final String etiket;
  final VoidCallback onTap;

  const _Tus({required this.etiket, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final silTus = etiket == 'DEL';
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(40),
      child: Container(
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: silTus
              ? Colors.transparent
              : Theme.of(context).colorScheme.surfaceVariant,
        ),
        child: Center(
          child: silTus
              ? const Icon(Icons.backspace_outlined, size: 24)
              : Text(
                  etiket,
                  style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w500),
                ),
        ),
      ),
    );
  }
}
