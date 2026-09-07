import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Kết quả kiểm tra kết nối backend + CSDL
class ConnectionCheckResult {
  final bool ok;
  final String message;
  final int? latencyMs;
  final String? detail;

  ConnectionCheckResult({
    required this.ok,
    required this.message,
    this.latencyMs,
    this.detail,
  });
}

class ApiClient {
  static const String defaultBaseUrl = 'http://192.168.1.100:8000';

  late Dio _dio;
  String? _token;
  String baseUrl;

  ApiClient({this.baseUrl = defaultBaseUrl}) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_token != null) {
          options.headers['Authorization'] = 'Bearer $_token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          clearToken();
        }
        return handler.next(error);
      },
    ));
  }

  void setBaseUrl(String url) {
    baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    _dio.options.baseUrl = baseUrl;
  }

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('access_token');
  }

  Future<void> setToken(String? token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    if (token != null) {
      await prefs.setString('access_token', token);
    } else {
      await prefs.remove('access_token');
    }
  }

  Future<void> clearToken() async => setToken(null);

  bool get hasToken => _token != null && _token!.isNotEmpty;

  /// Kiểm tra backend sống + CSDL (health + optional deep query)
  Future<ConnectionCheckResult> checkConnection({bool deep = false}) async {
    final sw = Stopwatch()..start();
    try {
      final health = await _dio.get(
        '/health',
        options: Options(
          receiveTimeout: const Duration(seconds: 5),
          sendTimeout: const Duration(seconds: 5),
        ),
      );
      sw.stop();
      final latency = sw.elapsedMilliseconds;

      if (health.statusCode != 200) {
        return ConnectionCheckResult(
          ok: false,
          message: 'Backend phản hồi lỗi (${health.statusCode})',
          latencyMs: latency,
        );
      }

      if (deep && hasToken) {
        try {
          await _dio.get(
            '/api/devices',
            options: Options(receiveTimeout: const Duration(seconds: 6)),
          );
          return ConnectionCheckResult(
            ok: true,
            message: 'Kết nối OK · Backend + CSDL hoạt động',
            latencyMs: latency,
            detail: 'Health + query devices thành công',
          );
        } on DioException catch (e) {
          if (e.type == DioExceptionType.connectionTimeout ||
              e.type == DioExceptionType.receiveTimeout) {
            return ConnectionCheckResult(
              ok: false,
              message: 'Backend sống nhưng CSDL/API chậm hoặc lỗi',
              latencyMs: latency,
              detail: e.message,
            );
          }
          if (e.response?.statusCode == 401) {
            return ConnectionCheckResult(
              ok: true,
              message: 'Backend + CSDL OK (token hết hạn)',
              latencyMs: latency,
            );
          }
          if (e.response?.statusCode == 500) {
            return ConnectionCheckResult(
              ok: false,
              message: 'Lỗi CSDL PostgreSQL (HTTP 500)',
              latencyMs: latency,
              detail: _extractDetail(e),
            );
          }
          return ConnectionCheckResult(
            ok: false,
            message: 'Backend sống nhưng lỗi khi truy vấn CSDL',
            latencyMs: latency,
            detail: _extractDetail(e),
          );
        }
      }

      return ConnectionCheckResult(
        ok: true,
        message: 'Backend đang chạy',
        latencyMs: latency,
        detail: health.data?.toString(),
      );
    } on DioException catch (e) {
      sw.stop();
      return ConnectionCheckResult(
        ok: false,
        message: _friendlyNetworkError(e),
        latencyMs: sw.elapsedMilliseconds,
        detail: e.message,
      );
    } catch (e) {
      sw.stop();
      return ConnectionCheckResult(
        ok: false,
        message: 'Lỗi không xác định',
        latencyMs: sw.elapsedMilliseconds,
        detail: e.toString(),
      );
    }
  }

  String _friendlyNetworkError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Timeout — kiểm tra IP backend & WiFi';
      case DioExceptionType.connectionError:
        return 'Không kết nối được backend. Kiểm tra IP / firewall / backend đã chạy chưa';
      case DioExceptionType.badResponse:
        final code = e.response?.statusCode;
        if (code == 500) {
          return 'Lỗi server — PostgreSQL có thể chưa chạy hoặc sai DATABASE_URL';
        }
        if (code == 503) return 'Service unavailable — backend hoặc DB đang down';
        return 'Backend trả lỗi HTTP $code';
      default:
        return 'Không kết nối được server';
    }
  }

  String _extractDetail(DioException e) {
    try {
      final data = e.response?.data;
      if (data is Map && data['detail'] != null) return data['detail'].toString();
      return data?.toString() ?? e.message ?? '';
    } catch (_) {
      return e.message ?? '';
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await _dio.post('/api/auth/login', data: {
      'email': email,
      'password': password,
    });
    return Map<String, dynamic>.from(res.data as Map);
  }

  Future<Map<String, dynamic>> me() async {
    final res = await _dio.get('/api/auth/me');
    return Map<String, dynamic>.from(res.data as Map);
  }

  Future<List<dynamic>> getDevices() async {
    final res = await _dio.get('/api/devices');
    return res.data as List;
  }

  Future<Map<String, dynamic>> getDevice(String id) async {
    final res = await _dio.get('/api/devices/$id');
    return Map<String, dynamic>.from(res.data as Map);
  }

  Future<Map<String, dynamic>> sendCommand(String deviceId, String command) async {
    final res = await _dio.post('/api/devices/$deviceId/command', data: {
      'command': command,
    });
    return Map<String, dynamic>.from(res.data as Map);
  }

  /// Khớp schema AccessLogOut: id, device_id, device_name, user_id, user_name, method, result, failure_reason, created_at
  Future<List<dynamic>> getLogs({int limit = 50}) async {
    final res = await _dio.get('/api/logs', queryParameters: {'limit': limit});
    return res.data as List;
  }

  Future<Map<String, dynamic>> getStats() async {
    final res = await _dio.get('/api/stats');
    return Map<String, dynamic>.from(res.data as Map);
  }
}
