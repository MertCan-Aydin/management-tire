import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/config.dart';
import 'core/token_store.dart';
import 'features/auth/login_screen.dart';
import 'app_shell.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
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

  void _onLogin() => setState(() => _loggedIn = true);
  void _onLogout() => setState(() => _loggedIn = false);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: kAppName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.blue, useMaterial3: true),
      home: _loggedIn
          ? AppShell(onLogout: _onLogout)
          : LoginScreen(onLoginSuccess: _onLogin),
    );
  }
}
