import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/api_client.dart';
import '../models/user.dart';

class AuthService extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  User? _user;
  bool _isLoading = true;
  String? _error;
  ConnectionCheckResult? _lastConnectionCheck;

  User? get user => _user;
  bool get isLoggedIn => _user != null;
  bool get isLoading => _isLoading;
  String? get error => _error;
  ApiClient get api => _api;
  ConnectionCheckResult? get lastConnectionCheck => _lastConnectionCheck;

  AuthService() {
    _init();
  }

  Future<void> _init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedIp = prefs.getString('backend_ip');
      if (savedIp != null && savedIp.isNotEmpty) {
        _api.setBaseUrl('http://$savedIp:8000');
      }

      await _api.loadToken();
      if (_api.hasToken) {
        final data = await _api.me();
        _user = User.fromJson(data);
      }
    } catch (_) {
      await _api.clearToken();
      _user = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<ConnectionCheckResult> checkConnection({bool deep = false}) async {
    final result = await _api.checkConnection(deep: deep);
    _lastConnectionCheck = result;
    notifyListeners();
    return result;
  }

  Future<bool> login(String email, String password) async {
    _error = null;
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _api.login(email, password);
      final token = data['access_token'] as String?;
      if (token == null || token.isEmpty) {
        throw Exception('Không nhận được access_token từ server');
      }

      await _api.setToken(token);

      final userJson = data['user'];
      if (userJson is Map<String, dynamic>) {
        _user = User.fromJson(userJson);
      } else if (userJson is Map) {
        _user = User.fromJson(Map<String, dynamic>.from(userJson));
      } else {
        final me = await _api.me();
        _user = User.fromJson(me);
      }

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_email', _user!.email);
      await prefs.setString('user_name', _user!.fullName);

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = _parseError(e);
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _api.clearToken();
    _user = null;
    notifyListeners();
  }

  Future<void> setBaseUrl(String url) async {
    _api.setBaseUrl(url);
    try {
      final uri = Uri.parse(url);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('backend_ip', uri.host);
    } catch (_) {}
  }

  String _parseError(dynamic e) {
    final msg = e.toString().toLowerCase();
    if (msg.contains('connection') ||
        msg.contains('socket') ||
        msg.contains('timeout') ||
        msg.contains('failed host lookup')) {
      return 'Không kết nối được backend. Kiểm tra IP và PostgreSQL đã chạy chưa.';
    }
    if (msg.contains('401') || msg.contains('email hoặc mật khẩu')) {
      return 'Email hoặc mật khẩu không đúng';
    }
    if (msg.contains('500') || msg.contains('internal server')) {
      return 'Lỗi server — PostgreSQL chưa chạy hoặc sai DATABASE_URL trong .env';
    }
    if (msg.contains('403')) {
      return 'Tài khoản đã bị khóa';
    }
    return 'Đăng nhập thất bại. Thử lại.';
  }
}
