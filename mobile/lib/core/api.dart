import 'package:flutter/foundation.dart';
import 'api_client.dart';
import 'format.dart';

/// Tüm endpoint yolları burada. Ekranlar ApiClient'a doğrudan değil,
/// bu sınıflar üzerinden erişir.

final _c = ApiClient.instance;

Future<List<Json>> _liste(String path, [Map<String, dynamic>? params]) async {
  final data = await _c.get(path, params: params);
  return (data as List? ?? []).cast<Json>();
}

/// POST sonrası dönen {"id": ...} değeri.
Future<int> _ekle(String path, Json v) async {
  final data = await _c.post(path, data: v);
  return data is Map ? tamSayi(data['id']) : 0;
}

Future<Json> _tek(String path, [Map<String, dynamic>? params]) async {
  final data = await _c.get(path, params: params);
  return (data as Map?)?.cast<String, dynamic>() ?? {};
}

/// Bir kayıt eklendiğinde/değiştiğinde artar; açık listeler ve detaylar
/// bunu dinleyip kendini yeniler.
final veriSurumu = ValueNotifier<int>(0);
void veriDegisti() => veriSurumu.value++;

class AuthApi {
  static Future<bool> kuruluMu() async => dogruMu((await _tek('/api/auth/setup-durumu'))['kurulu_mu']);
  static Future<Json> pinGiris(String pin) async => (await _c.post('/api/auth/pin-giris', data: {'pin': pin}) as Map).cast();
  static Future<Json> pinKurulum(String pin) async => (await _c.post('/api/auth/pin-kurulum', data: {'pin': pin}) as Map).cast();
  static Future<void> cikis(String refresh) => _c.post('/api/auth/cikis', data: {'refresh_token': refresh});
}

class UrunApi {
  static Future<List<Json>> liste({String? arama, bool sadeceStoklu = false, int limit = 200}) => _liste('/api/urunler', {
        if (arama != null && arama.isNotEmpty) 'arama': arama,
        if (sadeceStoklu) 'sadece_stoklu': true,
        'limit': limit,
      });
  static Future<Json> getir(int id) => _tek('/api/urunler/$id');
  static Future<Json> barkod(String barkod) => _tek('/api/urunler/barkod/${Uri.encodeComponent(barkod)}');
  static Future<void> ekle(Json v) => _c.post('/api/urunler', data: v);
  static Future<void> guncelle(int id, Json v) => _c.put('/api/urunler/$id', data: v);
  static Future<void> sil(int id) => _c.delete('/api/urunler/$id');

  static Future<List<Json>> tipler() => _liste('/api/urunler/tipler');
  static Future<List<Json>> markalar(int tipId) => _liste('/api/urunler/markalar', {'tip_id': tipId});
  static Future<List<Json>> modeller(int markaId) => _liste('/api/urunler/modeller', {'marka_id': markaId});

  static Future<Json> eprelKaydet(Json v) async => (await _c.post('/api/urunler/eprel-kaydet', data: v) as Map).cast();
}

class MusteriApi {
  static Future<List<Json>> liste({String? arama, int limit = 200}) => _liste('/api/musteriler', {
        if (arama != null && arama.isNotEmpty) 'arama': arama,
        'limit': limit,
      });
  static Future<Json> getir(int id) => _tek('/api/musteriler/$id');
  static Future<int> ekle(Json v) => _ekle('/api/musteriler', v);
  static Future<void> guncelle(int id, Json v) => _c.put('/api/musteriler/$id', data: v);
  static Future<void> sil(int id) => _c.delete('/api/musteriler/$id');
}

class TedarikciApi {
  static Future<List<Json>> liste() => _liste('/api/tedarikciler');
  static Future<Json> getir(int id) => _tek('/api/tedarikciler/$id');
  static Future<int> ekle(Json v) => _ekle('/api/tedarikciler', v);
  static Future<void> guncelle(int id, Json v) => _c.put('/api/tedarikciler/$id', data: v);
  static Future<void> sil(int id) => _c.delete('/api/tedarikciler/$id');

  static Future<List<Json>> odemeler(int id) => _liste('/api/tedarikciler/$id/odemeler');
  static Future<void> odemeEkle(int tedarikciId, double tutar) =>
      _c.post('/api/tedarikciler/odemeler', data: {'tedarikci_id': tedarikciId, 'tutar': tutar});
  static Future<void> odemeSil(int odemeId) => _c.delete('/api/tedarikciler/odemeler/$odemeId');
}

class AlimApi {
  static Future<List<Json>> liste({Map<String, dynamic>? donem, int? tedarikciId}) =>
      _liste('/api/alimlar', {...?donem, if (tedarikciId != null) 'tedarikci_id': tedarikciId, 'limit': 200});
  static Future<Json> getir(int id) => _tek('/api/alimlar/$id');
  static Future<void> ekle(Json v) => _c.post('/api/alimlar', data: v);
  static Future<void> iptal(int id) => _c.delete('/api/alimlar/$id');
}

class SatisApi {
  static Future<List<Json>> liste({Map<String, dynamic>? donem, int? musteriId, int limit = 200}) =>
      _liste('/api/satislar', {...?donem, if (musteriId != null) 'musteri_id': musteriId, 'limit': limit});
  static Future<Json> getir(int id) => _tek('/api/satislar/$id');
  static Future<void> ekle(Json v) => _c.post('/api/satislar', data: v);
  static Future<void> iptal(int id, {required bool stogaEkle}) =>
      _c.delete('/api/satislar/$id', params: {'stoga_ekle': stogaEkle});
}

class GiderApi {
  static Future<List<Json>> liste({Map<String, dynamic>? donem}) => _liste('/api/giderler', {...?donem, 'limit': 200});
  static Future<void> ekle(Json v) => _c.post('/api/giderler', data: v);
  static Future<void> guncelle(int id, Json v) => _c.put('/api/giderler/$id', data: v);
  static Future<void> sil(int id) => _c.delete('/api/giderler/$id');
}

class OtelApi {
  static Future<List<Json>> liste({bool sadeceAktif = true, String arama = ''}) =>
      _liste('/api/lastik-oteli', {'sadece_aktif': sadeceAktif, 'arama': arama, 'limit': 500});
  static Future<Json> getir(int id) => _tek('/api/lastik-oteli/$id');
  static Future<Json> raf(String rafKodu) => _tek('/api/lastik-oteli/raf/${Uri.encodeComponent(rafKodu)}');
  static Future<void> ekle(Json v) => _c.post('/api/lastik-oteli', data: v);
  static Future<void> teslim(int id, DateTime cikis) =>
      _c.put('/api/lastik-oteli/$id/teslim', data: {'cikis_tarihi': isoGun(cikis)});
  static Future<void> sil(int id) => _c.delete('/api/lastik-oteli/$id');
}

class RaporApi {
  static Future<Json> dashboard() => _tek('/api/raporlar/dashboard');
  static Future<Json> aralik(String bas, String bit) => _tek('/api/raporlar/aralik', {'baslangic': bas, 'bitis': bit});
  static Future<List<Json>> kirilim(String bas, String bit) => _liste('/api/raporlar/kirilim', {'baslangic': bas, 'bitis': bit});
  static Future<List<Json>> enCokSatan(String bas, String bit, {int limit = 10}) =>
      _liste('/api/raporlar/en-cok-satan', {'baslangic': bas, 'bitis': bit, 'limit': limit});
}
