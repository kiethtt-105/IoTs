import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

/// BLE Protocol cho Smart Lock (thiết kế sẵn cho ESP32 thật)
/// Service UUID: 0000fff0-0000-1000-8000-00805f9b34fb
/// Characteristic Command: 0000fff1-... (write)
/// Characteristic Status:  0000fff2-... (notify)
class BleService extends ChangeNotifier {
  static const String serviceUuid = '0000fff0-0000-1000-8000-00805f9b34fb';
  static const String cmdCharUuid = '0000fff1-0000-1000-8000-00805f9b34fb';
  static const String statusCharUuid = '0000fff2-0000-1000-8000-00805f9b34fb';

  bool _isScanning = false;
  bool _isConnected = false;
  BluetoothDevice? _connectedDevice;
  String? _lastError;
  List<ScanResult> _scanResults = [];

  bool get isScanning => _isScanning;
  bool get isConnected => _isConnected;
  BluetoothDevice? get connectedDevice => _connectedDevice;
  String? get lastError => _lastError;
  List<ScanResult> get scanResults => _scanResults;

  /// Xin quyền BLE (Android 12+)
  Future<bool> requestPermissions() async {
    if (await Permission.bluetoothScan.isDenied) {
      await Permission.bluetoothScan.request();
    }
    if (await Permission.bluetoothConnect.isDenied) {
      await Permission.bluetoothConnect.request();
    }
    if (await Permission.location.isDenied) {
      await Permission.location.request();
    }
    return await Permission.bluetoothScan.isGranted &&
        await Permission.bluetoothConnect.isGranted;
  }

  /// Kiểm tra Bluetooth đã bật chưa
  Future<bool> isBluetoothOn() async {
    try {
      return await FlutterBluePlus.isOn;
    } catch (_) {
      return false;
    }
  }

  /// Quét thiết bị gần (lọc theo tên chứa "SmartLock" hoặc MAC)
  Future<void> startScan({Duration timeout = const Duration(seconds: 6)}) async {
    final ok = await requestPermissions();
    if (!ok) {
      _lastError = 'Chưa cấp quyền Bluetooth';
      notifyListeners();
      return;
    }

    if (!await isBluetoothOn()) {
      _lastError = 'Bluetooth đang tắt. Hãy bật Bluetooth.';
      notifyListeners();
      return;
    }

    _isScanning = true;
    _scanResults = [];
    _lastError = null;
    notifyListeners();

    try {
      await FlutterBluePlus.startScan(
        timeout: timeout,
        withServices: [Guid(serviceUuid)], // chỉ quét device có service của ta
      );

      FlutterBluePlus.scanResults.listen((results) {
        _scanResults = results;
        notifyListeners();
      });

      await Future.delayed(timeout);
      await stopScan();
    } catch (e) {
      _lastError = 'Lỗi quét BLE: $e';
      _isScanning = false;
      notifyListeners();
    }
  }

  Future<void> stopScan() async {
    await FlutterBluePlus.stopScan();
    _isScanning = false;
    notifyListeners();
  }

  /// Kết nối tới device theo MAC address
  Future<bool> connectByMac(String macAddress) async {
    _lastError = null;
    try {
      // Tìm trong kết quả scan trước
      ScanResult? found;
      for (final r in _scanResults) {
        if (r.device.remoteId.str.toUpperCase() == macAddress.toUpperCase()) {
          found = r;
          break;
        }
      }

      // Nếu chưa scan thì scan nhanh
      if (found == null) {
        await startScan(timeout: const Duration(seconds: 4));
        for (final r in _scanResults) {
          if (r.device.remoteId.str.toUpperCase() == macAddress.toUpperCase()) {
            found = r;
            break;
          }
        }
      }

      if (found == null) {
        _lastError = 'Không tìm thấy khóa gần đây (BLE)';
        notifyListeners();
        return false;
      }

      await found.device.connect(timeout: const Duration(seconds: 8));
      _connectedDevice = found.device;
      _isConnected = true;
      notifyListeners();
      return true;
    } catch (e) {
      _lastError = 'Kết nối BLE thất bại: $e';
      _isConnected = false;
      notifyListeners();
      return false;
    }
  }

  /// Gửi lệnh unlock / lock qua BLE
  Future<bool> sendCommand(String command) async {
    if (_connectedDevice == null || !_isConnected) {
      _lastError = 'Chưa kết nối BLE';
      notifyListeners();
      return false;
    }

    try {
      final services = await _connectedDevice!.discoverServices();
      BluetoothCharacteristic? cmdChar;

      for (final s in services) {
        if (s.uuid.toString().toLowerCase().contains('fff0')) {
          for (final c in s.characteristics) {
            if (c.uuid.toString().toLowerCase().contains('fff1')) {
              cmdChar = c;
              break;
            }
          }
        }
      }

      if (cmdChar == null) {
        // Fallback: gửi raw nếu chưa có GATT đúng (dùng cho demo)
        // Trong thực tế ESP32 sẽ có characteristic này
        _lastError = 'Không tìm thấy characteristic lệnh';
        notifyListeners();
        return false;
      }

      final payload = utf8.encode(jsonEncode({
        'cmd': command, // "unlock" | "lock"
        'ts': DateTime.now().millisecondsSinceEpoch,
      }));

      await cmdChar.write(payload, withoutResponse: false);
      return true;
    } catch (e) {
      _lastError = 'Gửi lệnh BLE lỗi: $e';
      notifyListeners();
      return false;
    }
  }

  Future<void> disconnect() async {
    try {
      await _connectedDevice?.disconnect();
    } catch (_) {}
    _connectedDevice = null;
    _isConnected = false;
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
