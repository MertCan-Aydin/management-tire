import 'package:intl/intl.dart';

typedef Json = Map<String, dynamic>;

final _paraFormat = NumberFormat('#,##0.00', 'tr_TR');
final _tarihFormat = DateFormat('dd.MM.yyyy', 'tr_TR');
final _tarihSaatFormat = DateFormat('dd.MM.yyyy HH:mm', 'tr_TR');
final _uzunTarihFormat = DateFormat('d MMMM y, EEEE', 'tr_TR');

/// API'den gelen sayı alanları num, String ya da null olabilir.
double sayi(dynamic v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? 0;
  return 0;
}

int tamSayi(dynamic v) {
  if (v is int) return v;
  if (v is num) return v.toInt();
  if (v is String) return int.tryParse(v) ?? 0;
  return 0;
}

bool dogruMu(dynamic v) => v == true || v == 1 || v == '1';

/// 1234.5 → "1.234,50 ₺"
String para(dynamic v) => '${_paraFormat.format(sayi(v))} ₺';

/// 1234.5 → "1.234,50" (₺ işaretsiz, form alanları için)
String paraSade(dynamic v) => _paraFormat.format(sayi(v));

/// Kullanıcının yazdığı "1.234,50" veya "1234.50" değerini sayıya çevirir.
double? sayiOku(String metin) {
  var s = metin.trim().replaceAll(' ', '').replaceAll('₺', '');
  if (s.isEmpty) return null;
  if (s.contains(',')) s = s.replaceAll('.', '').replaceAll(',', '.');
  return double.tryParse(s);
}

DateTime? tarihOku(dynamic v) => v == null ? null : DateTime.tryParse(v.toString());

String tarih(dynamic v) {
  final t = tarihOku(v);
  return t == null ? (v?.toString() ?? '') : _tarihFormat.format(t);
}

String tarihSaat(dynamic v) {
  final t = tarihOku(v);
  if (t == null) return v?.toString() ?? '';
  // Sadece tarih içeren alanlarda 00:00 göstermeyelim
  if (v.toString().length <= 10) return _tarihFormat.format(t);
  return _tarihSaatFormat.format(t);
}

String uzunTarih(DateTime t) => _uzunTarihFormat.format(t);

/// API sorgu parametresi: 2026-10-07
String isoGun(DateTime t) => DateFormat('yyyy-MM-dd').format(t);

/// Liste ekranlarındaki dönem seçici.
enum Donem {
  bugun('Bugün'),
  hafta('Bu Hafta'),
  ay('Bu Ay'),
  tumu('Tümü');

  final String etiket;
  const Donem(this.etiket);

  /// Sorgu parametreleri — [tumu] için boş.
  /// Liste SP'leri DATETIME karşılaştırdığı için bitiş günün sonu olmalı,
  /// yoksa bugünün kayıtları dışarıda kalır.
  Map<String, dynamic> parametreler() {
    final bugun = DateTime.now();
    final gun = DateTime(bugun.year, bugun.month, bugun.day);
    final DateTime? bas = switch (this) {
      Donem.bugun => gun,
      Donem.hafta => gun.subtract(Duration(days: gun.weekday - 1)),
      Donem.ay => DateTime(gun.year, gun.month, 1),
      Donem.tumu => null,
    };
    if (bas == null) return {};
    return {'baslangic': '${isoGun(bas)} 00:00:00', 'bitis': '${isoGun(gun)} 23:59:59'};
  }
}

/// Türkçe büyük harf: "lastik oteli" → "LASTİK OTELİ"
String buyukHarf(String s) => s.replaceAll('i', 'İ').replaceAll('ı', 'I').toUpperCase();
