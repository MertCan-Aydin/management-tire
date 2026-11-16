import 'package:shared_preferences/shared_preferences.dart';

const varsayilanMarkalar = [
  'Michelin', 'Continental', 'Bridgestone', 'Pirelli', 'Goodyear',
  'Dunlop', 'Hankook', 'Yokohama', 'Firestone', 'Toyo',
  'Kumho', 'Nexen', 'Falken', 'Cooper', 'Maxxis',
  'Lassa', 'Petlas', 'Nankang', 'GT Radial', 'Sailun',
  'Linglong', 'Triangle', 'Westlake', 'Federal', 'Vredestein',
  'BFGoodrich', 'Nokian', 'Semperit', 'Uniroyal', 'Kormoran',
];

const varsayilanModeller = [
  'Primacy 4+', 'Pilot Sport 5', 'CrossClimate 2', 'Alpin 6',
  'PremiumContact 6', 'EcoContact 6', 'WinterContact TS 870', 'AllSeasonContact',
  'Turanza T005', 'Blizzak LM005', 'Potenza Sport', 'Ecopia EP150',
  'Cinturato P7', 'P Zero', 'Winter Sottozero 3', 'Scorpion Verde',
  'EfficientGrip Performance 2', 'UltraGrip 9+', 'Vector 4Seasons Gen-3',
  'Ventus Prime 4', 'Winter i*cept RS3', 'Kinergy Eco 2',
  'BluEarth-GT AE51', 'W.drive V905',
  'Snowprox S944', 'Proxes Sport', 'Competus A/T3',
  'Drivepoint 3', 'Snowmaster W651', 'Adreno A/T',
];

const otomobilEbatlari = [
  '155/65R14', '165/65R14', '165/70R14', '175/65R14', '175/70R14',
  '185/55R15', '185/60R15', '185/65R14', '185/65R15', '185/70R14',
  '195/55R16', '195/60R15', '195/65R15', '195/70R14',
  '205/55R16', '205/60R15', '205/60R16', '205/65R15',
  '215/55R16', '215/55R17', '215/60R16', '215/65R16',
  '225/40R18', '225/45R17', '225/45R18', '225/50R17', '225/55R17',
  '235/40R18', '235/45R17', '235/55R17',
  '245/40R18', '245/45R18',
];

const kamyonEbatlari = [
  '215/75R17.5', '225/75R17.5', '235/75R17.5',
  '245/70R17.5', '245/70R19.5',
  '265/70R17.5', '265/70R19.5',
  '275/70R22.5', '275/80R22.5',
  '285/70R19.5',
  '295/60R22.5', '295/80R22.5',
  '305/70R19.5', '305/70R22.5',
  '315/60R22.5', '315/70R22.5', '315/80R22.5',
  '325/95R24',
  '385/55R22.5', '385/65R22.5',
  '12R22.5', '13R22.5',
  '7.50R16', '8.25R16', '9.00R20', '10.00R20', '11.00R20', '12.00R20',
  '12.00R24', '14.00R20',
];

const tirEbatlari = [
  '315/80R22.5', '315/70R22.5', '315/60R22.5',
  '385/65R22.5', '385/55R22.5',
  '295/80R22.5', '295/60R22.5',
  '275/70R22.5', '275/80R22.5',
  '305/70R22.5',
  '12R22.5', '13R22.5', '11R22.5',
  '425/65R22.5', '445/45R19.5', '445/65R22.5',
  '455/40R22.5',
  '215/75R17.5', '225/75R17.5', '235/75R17.5',
  '245/70R17.5', '245/70R19.5',
  '265/70R19.5',
  '285/70R19.5',
  '305/70R19.5',
  '325/95R24',
  '12.00R20', '12.00R24', '14.00R20', '14.00R24',
  '11.00R20', '10.00R20', '9.00R20',
];

const _keyMarkalar = 'ek_markalar';
const _keyModeller = 'ek_modeller';
const _keyEbatlar = 'ek_ebatlar';

class LastikVerileri {
  static SharedPreferences? _prefs;

  static Future<void> _hazirla() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  static List<String> _ekler(String key) {
    return _prefs?.getStringList(key) ?? [];
  }

  static Future<void> _ekle(String key, String deger) async {
    await _hazirla();
    final liste = _ekler(key);
    if (!liste.contains(deger)) {
      liste.add(deger);
      await _prefs!.setStringList(key, liste);
    }
  }

  static Future<List<String>> markalar() async {
    await _hazirla();
    return {...varsayilanMarkalar, ..._ekler(_keyMarkalar)}.toList()..sort();
  }

  static Future<List<String>> modeller() async {
    await _hazirla();
    return {...varsayilanModeller, ..._ekler(_keyModeller)}.toList()..sort();
  }

  static Future<List<String>> ebatlar(String kategori) async {
    await _hazirla();
    final Set<String> temel;
    switch (kategori) {
      case 'Kamyon':
        temel = {...kamyonEbatlari};
      case 'TIR':
        temel = {...tirEbatlari};
      default:
        temel = {...otomobilEbatlari};
    }
    temel.addAll(_ekler(_keyEbatlar));
    final liste = temel.toList()..sort();
    return liste;
  }

  static Future<void> markaEkle(String v) => _ekle(_keyMarkalar, v);
  static Future<void> modelEkle(String v) => _ekle(_keyModeller, v);
  static Future<void> ebatEkle(String v) => _ekle(_keyEbatlar, v);
}
