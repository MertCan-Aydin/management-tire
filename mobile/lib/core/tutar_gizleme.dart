import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'format.dart';

/// Özet ekranındaki tutarları gizle/göster tercihi (banka uygulamalarındaki göz).
/// Cihazda saklanır; uygulama yeniden açıldığında tutarlar gizli kalır.
final tutarlarGizli = ValueNotifier<bool>(false);

const _storage = FlutterSecureStorage(aOptions: AndroidOptions(encryptedSharedPreferences: true));
const _anahtar = 'tutarlar_gizli';

Future<void> tutarGizlemeYukle() async {
  try {
    tutarlarGizli.value = await _storage.read(key: _anahtar) == '1';
  } catch (_) {
    // Okunamazsa varsayılan: görünür
  }
}

void tutarGizlemeDegistir() {
  tutarlarGizli.value = !tutarlarGizli.value;
  _storage.write(key: _anahtar, value: tutarlarGizli.value ? '1' : '0').ignore();
}

/// [para] gibi biçimler; gizliyken tutar yerine nokta gösterir.
String gizlenebilirPara(dynamic v) => tutarlarGizli.value ? '•••••• ₺' : para(v);
