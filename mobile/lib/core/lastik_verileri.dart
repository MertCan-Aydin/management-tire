import 'api.dart';

class LastikVerileri {
  static Future<List<String>> markalar() async {
    final liste = await LastikVeriApi.markalar();
    return liste.map((e) => e['ad'] as String).toList();
  }

  static Future<List<String>> modeller() async {
    final liste = await LastikVeriApi.modeller();
    return liste.map((e) => e['ad'] as String).toList();
  }

  static Future<List<String>> ebatlar(String kategori) async {
    final liste = await LastikVeriApi.ebatlar(kategori: kategori);
    return liste.map((e) => e['ebat'] as String).toList();
  }

  static Future<void> markaEkle(String v) => LastikVeriApi.markaEkle(v);
  static Future<void> modelEkle(String v) => LastikVeriApi.modelEkle(v);
  static Future<void> ebatEkle(String v, String kategori) => LastikVeriApi.ebatEkle(v, kategori);
}
