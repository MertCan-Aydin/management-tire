import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'core/api_client.dart';
import 'core/config.dart';
import 'core/token_store.dart';
import 'features/auth/login_screen.dart';
import 'app_shell.dart';
import 'ui/tema.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('tr_TR');
  Intl.defaultLocale = 'tr_TR';
  // Her açılışta önceki oturumu sil — PIN her seferinde sorulsun
  await TokenStore.clearTokens();
  runApp(const ProviderScope(child: DijitalLastikApp()));
}

class DijitalLastikApp extends StatefulWidget {
  const DijitalLastikApp({super.key});

  @override
  State<DijitalLastikApp> createState() => _DijitalLastikAppState();
}

class _DijitalLastikAppState extends State<DijitalLastikApp> {
  bool _loggedIn = false;

  @override
  void initState() {
    super.initState();
    ApiClient.instance.oturumDustu = () {
      if (mounted && _loggedIn) _onLogout();
    };
  }

  void _onLogin() => setState(() => _loggedIn = true);
  void _onLogout() => setState(() => _loggedIn = false);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: kAppName,
      debugShowCheckedModeBanner: false,
      theme: temaOlustur(Brightness.light),
      darkTheme: temaOlustur(Brightness.dark),
      themeMode: ThemeMode.system,
      locale: const Locale('tr', 'TR'),
      supportedLocales: const [Locale('tr', 'TR')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ],
      home: _loggedIn ? AppShell(onLogout: _onLogout) : LoginScreen(onLoginSuccess: _onLogin),
    );
  }
}
