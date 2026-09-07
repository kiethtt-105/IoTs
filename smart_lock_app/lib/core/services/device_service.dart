import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../api/api_client.dart';
import '../models/device.dart';
import 'auth_service.dart';
import 'ble_service.dart';

enum ControlMethod { ble, online, none }

class DeviceService extends ChangeNotifier {
  AuthService? _auth;
  final BleService _ble = BleService();
  List<SmartDevice> _devices = [];
  bool _isLoading = false;
  String? _error;
  ControlMethod _lastMethod = ControlMethod.none;
  bool _backendReachable = true;

  List<SmartDevice> get devices => _devices;
  bool get isLoading => _isLoading;
  String? get error => _error;
  ControlMethod get lastMethod => _lastMethod;
  BleService get ble => _ble;
  bool get backendReachable => _backendReachable;

  void updateAuth(AuthService auth) {
    _auth = auth;
  }

  ApiClient get _api => _auth!.api;

  Future<void> loadDevices() async {
    if (_auth == null || !_auth!.isLoggedIn) return;
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final list = await _api.getDevices();
      _devices = list.map((e) => SmartDevice.fromJson(Map<String, dynamic>.from(e as Map))).toList();
      _backendReachable = true;
    } catch (e) {
      _backendReachable = false;
      final msg = e.toString().toLowerCase();
      if (msg.contains('500')) {
        _error = 'Lỗi CSDL khi đọc danh sách khóa (PostgreSQL)';
      } else if (msg.contains('connection') || msg.contains('timeout')) {
        _error = 'Mất kết nối backend';
      } else {
        _error = 'Không tải được danh sách khóa';
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// HYBRID: BLE trước → Online fallback. Có mạng thì sync log.
  Future<bool> controlDevice(SmartDevice device, String command) async {
    _error = null;
    notifyListeners();

    final bleOk = await _tryBle(device, command);
    if (bleOk) {
      _lastMethod = ControlMethod.ble;
      _updateLocalStatus(device.id, command);
      _syncToBackend(device.id, command);
      notifyListeners();
      return true;
    }

    final onlineOk = await _tryOnline(device, command);
    if (onlineOk) {
      _lastMethod = ControlMethod.online;
      _updateLocalStatus(device.id, command);
      // Refresh từ DB để lấy status thật sau MQTT
      Future.delayed(const Duration(milliseconds: 800), loadDevices);
      notifyListeners();
      return true;
    }

    _lastMethod = ControlMethod.none;
    _error = _ble.lastError ?? 'Không thể điều khiển (không BLE + không kết nối CSDL/backend)';
    notifyListeners();
    return false;
  }

  Future<bool> _tryBle(SmartDevice device, String command) async {
    try {
      final connected = await _ble.connectByMac(device.macAddress);
      if (!connected) return false;
      return await _ble.sendCommand(command);
    } catch (_) {
      return false;
    }
  }

  Future<bool> _tryOnline(SmartDevice device, String command) async {
    try {
      final connectivity = await Connectivity().checkConnectivity();
      if (connectivity.contains(ConnectivityResult.none)) return false;
      await _api.sendCommand(device.id, command);
      _backendReachable = true;
      return true;
    } catch (e) {
      final msg = e.toString().toLowerCase();
      if (msg.contains('500')) {
        _error = 'Lệnh online thất bại — lỗi CSDL/MQTT';
      }
      _backendReachable = false;
      return false;
    }
  }

  void _updateLocalStatus(String deviceId, String command) {
    final idx = _devices.indexWhere((d) => d.id == deviceId);
    if (idx == -1) return;
    final newStatus = command == 'unlock' ? DeviceStatus.unlocked : DeviceStatus.locked;
    _devices[idx] = _devices[idx].copyWith(status: newStatus);
  }

  Future<void> _syncToBackend(String deviceId, String command) async {
    try {
      final connectivity = await Connectivity().checkConnectivity();
      if (!connectivity.contains(ConnectivityResult.none)) {
        await _api.sendCommand(deviceId, command);
        _backendReachable = true;
      }
    } catch (_) {}
  }

  Future<void> refresh() => loadDevices();
}
