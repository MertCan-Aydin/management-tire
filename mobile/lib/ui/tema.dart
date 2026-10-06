import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

/// iOS sistem renklerine yakın, masaüstü uygulamasının lacivertini (#003D9B)
/// ana renk olarak kullanan palet.
@immutable
class Renkler extends ThemeExtension<Renkler> {
  final Color arkaplan; // gruplu liste arka planı
  final Color kart; // grup / kart yüzeyi
  final Color kart2; // kart içindeki ikincil yüzey
  final Color dolgu; // arama kutusu, giriş alanı dolgusu
  final Color ayrac;
  final Color metin;
  final Color ikincil;
  final Color ucuncul;
  final Color ana;
  final Color anaAcik; // seçili satır, rozet zemini
  final Color basari;
  final Color tehlike;
  final Color uyari;
  final Color mor;
  final Color turuncu;
  final Color camgobegi;

  const Renkler({
    required this.arkaplan,
    required this.kart,
    required this.kart2,
    required this.dolgu,
    required this.ayrac,
    required this.metin,
    required this.ikincil,
    required this.ucuncul,
    required this.ana,
    required this.anaAcik,
    required this.basari,
    required this.tehlike,
    required this.uyari,
    required this.mor,
    required this.turuncu,
    required this.camgobegi,
  });

  static const acik = Renkler(
    arkaplan: Color(0xFFF2F2F7),
    kart: Color(0xFFFFFFFF),
    kart2: Color(0xFFF2F2F7),
    dolgu: Color(0x1F767680),
    ayrac: Color(0xFFE3E3E8),
    metin: Color(0xFF1C1C1E),
    ikincil: Color(0xFF8E8E93),
    ucuncul: Color(0xFFC7C7CC),
    ana: Color(0xFF003D9B),
    anaAcik: Color(0xFFE6EEFB),
    basari: Color(0xFF248A3D),
    tehlike: Color(0xFFD70015),
    uyari: Color(0xFFC93400),
    mor: Color(0xFF8944AB),
    turuncu: Color(0xFFC93400),
    camgobegi: Color(0xFF0071A4),
  );

  static const koyu = Renkler(
    arkaplan: Color(0xFF000000),
    kart: Color(0xFF1C1C1E),
    kart2: Color(0xFF2C2C2E),
    dolgu: Color(0x3D767680),
    ayrac: Color(0xFF38383A),
    metin: Color(0xFFFFFFFF),
    ikincil: Color(0xFF98989F),
    ucuncul: Color(0xFF48484A),
    ana: Color(0xFF6E9BFF),
    anaAcik: Color(0xFF1A2A4A),
    basari: Color(0xFF30D158),
    tehlike: Color(0xFFFF453A),
    uyari: Color(0xFFFF9F0A),
    mor: Color(0xFFBF5AF2),
    turuncu: Color(0xFFFF9F0A),
    camgobegi: Color(0xFF64D2FF),
  );

  @override
  Renkler copyWith() => this;

  @override
  Renkler lerp(ThemeExtension<Renkler>? other, double t) => t < 0.5 ? this : (other as Renkler? ?? this);
}

extension TemaKisayol on BuildContext {
  Renkler get renk => Theme.of(this).extension<Renkler>()!;
  TextTheme get yazi => Theme.of(this).textTheme;
}

const kFont = 'Inter';

ThemeData temaOlustur(Brightness parlaklik) {
  final r = parlaklik == Brightness.light ? Renkler.acik : Renkler.koyu;
  final cs = ColorScheme.fromSeed(
    seedColor: const Color(0xFF003D9B),
    brightness: parlaklik,
  ).copyWith(
    primary: r.ana,
    onPrimary: Colors.white,
    surface: r.kart,
    onSurface: r.metin,
    error: r.tehlike,
    surfaceContainerHighest: r.kart2,
    outlineVariant: r.ayrac,
  );

  // iOS tipografi ölçeğine yakın (Large Title 34 → Caption 12)
  TextStyle s(double boyut, FontWeight w, {Color? renk, double ls = 0}) =>
      TextStyle(fontFamily: kFont, fontSize: boyut, fontWeight: w, color: renk ?? r.metin, letterSpacing: ls, height: 1.25);
  final yazi = TextTheme(
    displaySmall: s(34, FontWeight.w700, ls: -0.6), // büyük başlık
    headlineMedium: s(28, FontWeight.w700, ls: -0.5),
    headlineSmall: s(22, FontWeight.w700, ls: -0.3),
    titleLarge: s(20, FontWeight.w600, ls: -0.3),
    titleMedium: s(17, FontWeight.w600, ls: -0.2),
    titleSmall: s(15, FontWeight.w600),
    bodyLarge: s(17, FontWeight.w400, ls: -0.2),
    bodyMedium: s(15, FontWeight.w400),
    bodySmall: s(13, FontWeight.w400, renk: r.ikincil),
    labelLarge: s(16, FontWeight.w600),
    labelMedium: s(13, FontWeight.w500, renk: r.ikincil),
    labelSmall: s(12, FontWeight.w500, renk: r.ikincil),
  );

  final kose10 = RoundedRectangleBorder(borderRadius: BorderRadius.circular(10));

  return ThemeData(
    useMaterial3: true,
    brightness: parlaklik,
    colorScheme: cs,
    fontFamily: kFont,
    textTheme: yazi,
    scaffoldBackgroundColor: r.arkaplan,
    canvasColor: r.arkaplan,
    extensions: [r],
    splashFactory: NoSplash.splashFactory,
    highlightColor: r.ayrac.withValues(alpha: 0.6),
    hoverColor: r.ayrac.withValues(alpha: 0.4),
    dividerTheme: DividerThemeData(color: r.ayrac, thickness: 0, space: 1),
    pageTransitionsTheme: const PageTransitionsTheme(builders: {
      TargetPlatform.android: CupertinoPageTransitionsBuilder(),
      TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
      TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
    }),
    cupertinoOverrideTheme: CupertinoThemeData(
      primaryColor: r.ana,
      brightness: parlaklik,
      textTheme: CupertinoTextThemeData(textStyle: s(17, FontWeight.w400)),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: r.arkaplan,
      foregroundColor: r.ana,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: true,
      titleTextStyle: yazi.titleMedium,
    ),
    iconTheme: IconThemeData(color: r.ana),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(64, 48),
        shape: kose10,
        textStyle: yazi.labelLarge,
        backgroundColor: r.ana,
        foregroundColor: Colors.white,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: r.ana,
        textStyle: s(16, FontWeight.w500),
        shape: kose10,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(64, 48),
        shape: kose10,
        foregroundColor: r.ana,
        side: BorderSide(color: r.ayrac),
        textStyle: yazi.labelLarge,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: r.dolgu,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      hintStyle: s(16, FontWeight.w400, renk: r.ikincil),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: r.kart,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: r.arkaplan,
      showDragHandle: true,
      dragHandleColor: r.ucuncul,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(14))),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      backgroundColor: parlaklik == Brightness.light ? const Color(0xF21C1C1E) : const Color(0xF22C2C2E),
      contentTextStyle: s(15, FontWeight.w500, renk: Colors.white),
      width: null,
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(color: r.ana),
    drawerTheme: DrawerThemeData(backgroundColor: r.arkaplan, width: 300),
  );
}
