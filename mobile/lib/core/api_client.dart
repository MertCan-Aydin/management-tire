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

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: kApiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      // SSL doğrulama her zaman açık (production)
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

  Future<void> delete(String path) async {
    await _dio.delete(path);
  }

  Future<Map<String, dynamic>> login(String kullaniciAdi, String parola) async {
    final resp = await _dio.post(
      '/api/auth/giris',
      data: 'username=$kullaniciAdi&password=$parola',
      options: Options(contentType: 'application/x-www-form-urlencoded'),
    );
    return resp.data as Map<String, dynamic>;
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
    if (err.response?.statusCode == 401) {
      // Refresh token dene
      final refreshed = await _tryRefresh();
      if (refreshed) {
        // Orijinal isteği tekrar gönder
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
    }

    final detail = err.response?.data?['detail'] ?? err.message ?? 'Bilinmeyen hata';
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        error: ApiError(err.response?.statusCode ?? 0, detail.toString()),
        response: err.response,
      ),
    );
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
