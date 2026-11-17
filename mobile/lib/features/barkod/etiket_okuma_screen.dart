import 'dart:io';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';

final _ebatRe = RegExp(r'(\d{3})\s*/?\s*(\d{2,3})\s*[RZV]?\s*(\d{2})');
final _yukHizRe = RegExp(r'\b(\d{2,3})\s*([A-Z])\b');
final _xlRe = RegExp(r'\bXL\b', caseSensitive: false);
final _eprelRe = RegExp(r'\b(\d{6,8})\b');

const _bilgilenMarkalar = [
  'BRIDGESTONE', 'MICHELIN', 'CONTINENTAL', 'GOODYEAR', 'PIRELLI',
  'DUNLOP', 'HANKOOK', 'YOKOHAMA', 'TOYO', 'FIRESTONE',
  'KUMHO', 'NEXEN', 'FALKEN', 'COOPER', 'LAUFENN',
  'MAXXIS', 'NOKIAN', 'PETLAS', 'LASSA', 'KORMORAN',
  'BARUM', 'UNIROYAL', 'GENERAL', 'MATADOR', 'SAILUN',
  'TRIANGLE', 'LINGLONG', 'WESTLAKE', 'DEBICA', 'NANKANG',
];

class EtiketOkumaSonuc {
  final String? marka;
  final String? ebat;
  final String? yukIndeksi;
  final String? hizKodu;
  final bool ekstraYuk;
  final String? eprelNo;

  const EtiketOkumaSonuc({
    this.marka,
    this.ebat,
    this.yukIndeksi,
    this.hizKodu,
    this.ekstraYuk = false,
    this.eprelNo,
  });
}

Future<EtiketOkumaSonuc?> etiketOku(BuildContext context) async {
  final picker = ImagePicker();
  final xFile = await picker.pickImage(source: ImageSource.camera, imageQuality: 90);
  if (xFile == null) return null;

  final inputImage = InputImage.fromFile(File(xFile.path));
  final recognizer = TextRecognizer();
  try {
    final result = await recognizer.processImage(inputImage);
    final text = result.text.toUpperCase();

    String? marka;
    for (final m in _bilgilenMarkalar) {
      if (text.contains(m)) {
        marka = m[0] + m.substring(1).toLowerCase();
        break;
      }
    }

    String? ebat;
    final ebatMatch = _ebatRe.firstMatch(text);
    if (ebatMatch != null) {
      ebat = '${ebatMatch.group(1)}/${ebatMatch.group(2)} R${ebatMatch.group(3)}';
    }

    String? yukIndeksi;
    String? hizKodu;
    final yukHizMatch = _yukHizRe.firstMatch(text);
    if (yukHizMatch != null) {
      yukIndeksi = yukHizMatch.group(1);
      hizKodu = yukHizMatch.group(2);
    }

    final ekstraYuk = _xlRe.hasMatch(text);

    String? eprelNo;
    final eprelMatch = _eprelRe.firstMatch(text);
    if (eprelMatch != null) {
      eprelNo = eprelMatch.group(1);
    }

    return EtiketOkumaSonuc(
      marka: marka,
      ebat: ebat,
      yukIndeksi: yukIndeksi,
      hizKodu: hizKodu,
      ekstraYuk: ekstraYuk,
      eprelNo: eprelNo,
    );
  } finally {
    recognizer.close();
  }
}
