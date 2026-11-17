import 'package:dio/dio.dart';

class EprelUrun {
  final String eprelNo;
  final String marka;
  final String model;
  final String ebat;
  final String mevsim;
  final String? yukIndeksi;
  final String? hizKodu;
  final bool ekstraYuk;
  final int? uretimYili;

  const EprelUrun({
    required this.eprelNo,
    required this.marka,
    required this.model,
    required this.ebat,
    required this.mevsim,
    this.yukIndeksi,
    this.hizKodu,
    this.ekstraYuk = false,
    this.uretimYili,
  });

  Map<String, dynamic> toMap() => {
        'tip': 'eprel',
        'eprel_no': eprelNo,
        'marka': marka,
        'model': model,
        'ebat': ebat,
        'mevsim': mevsim,
        'yuk_indeksi': yukIndeksi,
        'hiz_kodu': hizKodu,
        'ekstra_yuk': ekstraYuk,
        'uretim_yili': uretimYili,
      };
}

class EprelClient {
  static final Dio _dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
  ));

  // EPREL URL formatları:
  //   https://eprel.ec.europa.eu/qr/492633
  //   https://eprel.ec.europa.eu/screen/product/tyres/1160716
  // Greedy .* ile son /rakam segmentini yakala
  static final _pattern = RegExp(r'eprel\.ec\.europa\.eu.*/(\d+)');

  /// QR değerinden EPREL kayıt numarasını çıkarır, EPREL URL değilse null döner.
  static String? parseEprelNo(String raw) {
    final match = _pattern.firstMatch(raw);
    return match?.group(1);
  }

  /// EPREL API'den lastik verisini çekip parse eder.
  static Future<EprelUrun> fetchByNo(String eprelNo) async {
    final resp = await _dio.get(
      'https://eprel.ec.europa.eu/api/products/tyres/$eprelNo',
    );
    final data = resp.data as Map<String, dynamic>;

    final iceTyre = data['iceTyre'] as bool? ?? false;
    final severeSnow = data['severeSnowTyre'] as bool? ?? false;
    final mevsim = (iceTyre || severeSnow) ? 'Kış' : 'Yaz';

    final details = data['additionalDetails'] as Map<String, dynamic>?;
    final modelAd = (details?['commercialName'] as String?)?.trim().isNotEmpty == true
        ? (details!['commercialName'] as String).trim()
        : (data['modelIdentifier'] as String? ?? '').trim();

    final yukIndeksi = _str(data['loadCapacityIndex'] ?? data['loadIndex']);
    final hizKodu = _str(data['speedRating'] ?? data['speedCategory']);
    final ekstraYuk = data['extraLoad'] == true || data['reinforced'] == true;
    final yilRaw = data['onMarketStartDateYear'] ?? data['onMarketStartYear'];
    final uretimYili = yilRaw is int ? yilRaw : int.tryParse('$yilRaw');

    return EprelUrun(
      eprelNo: eprelNo,
      marka: (data['supplierOrTrademark'] as String? ?? '').trim(),
      model: modelAd,
      ebat: (data['sizeDesignation'] as String? ?? '').trim(),
      mevsim: mevsim,
      yukIndeksi: yukIndeksi,
      hizKodu: hizKodu,
      ekstraYuk: ekstraYuk,
      uretimYili: uretimYili,
    );
  }

  static String? _str(dynamic v) {
    if (v == null) return null;
    final s = '$v'.trim();
    return s.isEmpty ? null : s;
  }
}
