# Mobil Uygulama Kurulumu

Flutter SDK kurulumu yapılmadan proje dosyaları oluşturuldu.
IDE'de görünen "package not found" hataları aşağıdaki adımlarla düzelir.

## Ön Koşullar

- Flutter SDK kurulu olmalı: https://docs.flutter.dev/get-started/install
- Android Studio veya VS Code + Flutter eklentisi

## Adımlar

```bash
# 1. Bu klasöre gel
cd mobile/

# 2. Flutter proje altyapısını oluştur (mevcut lib/ korunur)
flutter create . --project-name dijital_lastik_servisi --org com.dijitallastik

# 3. Bağımlılıkları indir
flutter pub get

# 4. API adresini ayarla
# lib/core/config.dart içindeki kApiBaseUrl'i güncelle:
# const String kApiBaseUrl = 'https://SENIN_VPS_IP_VEYA_DOMAININ';

# 5. Android için kamera ve güvenli depolama izinleri
# android/app/src/main/AndroidManifest.xml dosyasına ekle:
# <uses-permission android:name="android.permission.CAMERA"/>

# 6. Çalıştır
flutter run
```

## Android Manifest Eklentileri

`android/app/src/main/AndroidManifest.xml` dosyasında `<manifest>` etiketinin içine ekle:

```xml
<uses-permission android:name="android.permission.CAMERA"/>
<uses-feature android:name="android.hardware.camera" android:required="false"/>
```

## iOS (opsiyonel)

`ios/Runner/Info.plist` dosyasına ekle:

```xml
<key>NSCameraUsageDescription</key>
<string>Barkod ve QR kod okumak için kamera erişimi gereklidir.</string>
```

## Release Build

```bash
# Android APK
flutter build apk --release --obfuscate --split-debug-info=build/debug-info

# Android AAB (Google Play)
flutter build appbundle --release --obfuscate --split-debug-info=build/debug-info
```
