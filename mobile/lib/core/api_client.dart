import 'package:dio/dio.dart';
import 'config.dart';
import 'token_store.dart';

class ApiError implements Exception {
  final int statusCode;
  final String detail;
  ApiError(this.statusCode, this.detail);
  @override
  String toString() => detail;
}

/// Herhangi bir hatayı kullanıcıya gösterilecek Türkçe mesaja çevirir.
String hataMesaji(Object e) {
  if (e is DioException && e.error is ApiError) return (e.error as ApiError).detail;
  if (e is ApiError) return e.detail;
  return 'Beklenmeyen bir hata oluştu';
}

/// Hatanın HTTP durum kodu (bağlantı hatasında 0).
int hataKodu(Object e) {
  if (e is DioException && e.error is ApiError) return (e.error as ApiError).statusCode;
  if (e is ApiError) return e.statusCode;
  return 0;
}

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  /// Refresh token da geçersizse çağrılır — uygulama giriş ekranına döner.
  void Function()? oturumDustu;

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: kApiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    ),
  )..interceptors.add(_AuthInterceptor());

  Future<dynamic> get(String path, {Map<String, dynamic>? params}) async {
    final resp = await _dio.get(path, queryParameters: params);
    return resp.data;
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? data}) async {
    final resp = await _dio.post(path, data: data);
    return resp.data;
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? data}) async {
    final resp = await _dio.put(path, data: data);
    return resp.data;
  }

  Future<void> delete(String path, {Map<String, dynamic>? params}) async {
    await _dio.delete(path, queryParameters: params);
  }
}

class _AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await TokenStore.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final authIstegi = err.requestOptions.path.startsWith('/api/auth/');
    if (err.response?.statusCode == 401 && !authIstegi) {
      final refreshed = await _tryRefresh();
      if (refreshed) {
        final opts = err.requestOptions;
        final token = await TokenStore.getAccessToken();
        opts.headers['Authorization'] = 'Bearer $token';
        try {
          final resp = await ApiClient.instance._dio.fetch(opts);
          handler.resolve(resp);
          return;
        } catch (_) {}
      }
      await TokenStore.clearTokens();
      ApiClient.instance.oturumDustu?.call();
    }

    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        error: ApiError(err.response?.statusCode ?? 0, _detay(err)),
        response: err.response,
        type: err.type,
      ),
    );
  }

  /// FastAPI hata gövdesini okunur metne çevirir.
  /// `detail` düz metin olabilir ya da doğrulama hatalarında bir liste.
  static String _detay(DioException err) {
    final resp = err.response;
    if (resp == null) {
      return switch (err.type) {
        DioExceptionType.connectionTimeout ||
        DioExceptionType.receiveTimeout ||
        DioExceptionType.sendTimeout =>
          'Sunucu yanıt vermedi, bağlantınızı kontrol edin',
        _ => 'Sunucuya ulaşılamıyor',
      };
    }
    final data = resp.data;
    if (data is Map && data['detail'] != null) {
      final d = data['detail'];
      if (d is String) return d;
      if (d is List) {
        return d
            .map((e) => e is Map ? (e['msg'] ?? '').toString() : e.toString())
            .map((m) => m.replaceFirst('Value error, ', ''))
            .where((m) => m.isNotEmpty)
            .join('\n');
      }
      return d.toString();
    }
    if (resp.statusCode == 401) return 'Oturum süresi doldu';
    if (resp.statusCode == 404) return 'Kayıt bulunamadı';
    return 'Sunucu hatası (${resp.statusCode})';
  }

  Future<bool> _tryRefresh() async {
    final rawRefresh = await TokenStore.getRefreshToken();
    if (rawRefresh == null) return false;
    try {
      final resp = await Dio(BaseOptions(baseUrl: kApiBaseUrl)).post(
        '/api/auth/yenile',
        data: {'refresh_token': rawRefresh},
      );
      await TokenStore.saveTokens(
        resp.data['access_token'] as String,
        resp.data['refresh_token'] as String,
      );
      return true;
    } catch (_) {
      return false;
    }
  }
}
