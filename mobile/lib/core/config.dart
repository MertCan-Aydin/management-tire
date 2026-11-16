/// Varsayılan: canlı sunucu. Test için:
///   flutter run --dart-define=API_URL=http://10.0.2.2:8765
const String kApiBaseUrl = String.fromEnvironment('API_URL', defaultValue: 'http://144.225.242.39');
const String kAppName = 'Dijital Lastik Servisi';
