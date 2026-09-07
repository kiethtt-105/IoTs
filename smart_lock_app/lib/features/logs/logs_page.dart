import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/auth_service.dart';

/// Hiển thị AccessLogOut từ backend:
/// id, device_id, device_name, user_id, user_name, method, result, failure_reason, created_at
class LogsPage extends StatefulWidget {
  const LogsPage({super.key});

  @override
  State<LogsPage> createState() => _LogsPageState();
}

class _LogsPageState extends State<LogsPage> {
  List<Map<String, dynamic>> _logs = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = context.read<AuthService>().api;
      final data = await api.getLogs(limit: 80);
      setState(() {
        _logs = data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _loading = false;
      });
    } catch (e) {
      final msg = e.toString().toLowerCase();
      String err = 'Không tải được lịch sử';
      if (msg.contains('connection') || msg.contains('timeout')) {
        err = 'Mất kết nối backend / CSDL';
      } else if (msg.contains('500')) {
        err = 'Lỗi CSDL khi đọc access_logs';
      }
      setState(() {
        _error = err;
        _loading = false;
      });
    }
  }

  Color _resultColor(String? result) {
    switch (result?.toLowerCase()) {
      case 'success':
        return AppColors.success;
      case 'denied':
        return AppColors.warning;
      case 'failed':
        return AppColors.danger;
      default:
        return AppColors.textSecondary;
    }
  }

  String _resultLabel(String? result) {
    switch (result?.toLowerCase()) {
      case 'success':
        return 'Thành công';
      case 'denied':
        return 'Từ chối';
      case 'failed':
        return 'Thất bại';
      default:
        return result ?? '—';
    }
  }

  IconData _methodIcon(String? method) {
    switch (method?.toLowerCase()) {
      case 'app_ble':
        return Icons.bluetooth;
      case 'app_remote':
        return Icons.wifi;
      case 'nfc_card':
        return Icons.contactless;
      case 'pin':
        return Icons.pin;
      case 'auto':
        return Icons.schedule;
      default:
        return Icons.history;
    }
  }

  String _methodLabel(String? method) {
    switch (method?.toLowerCase()) {
      case 'app_ble':
        return 'BLE App';
      case 'app_remote':
        return 'Remote';
      case 'nfc_card':
        return 'NFC';
      case 'pin':
        return 'PIN';
      case 'auto':
        return 'Auto';
      default:
        return method ?? '—';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off, size: 40, color: AppColors.textSecondary.withValues(alpha: 0.5)),
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 12),
            TextButton.icon(
              onPressed: _load,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      );
    }
    if (_logs.isEmpty) {
      return const Center(
        child: Text('Chưa có lịch sử truy cập', style: TextStyle(color: AppColors.textSecondary)),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      color: AppColors.primary,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _logs.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, i) {
          final log = _logs[i];
          final result = log['result']?.toString();
          final method = log['method']?.toString();
          final deviceName = log['device_name']?.toString() ?? 'Khóa';
          final userName = log['user_name']?.toString();
          final failure = log['failure_reason']?.toString();
          final timeStr = log['created_at']?.toString();
          DateTime? time;
          if (timeStr != null) time = DateTime.tryParse(timeStr);

          return Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: _resultColor(result).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(_methodIcon(method), color: _resultColor(result), size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        deviceName,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${_methodLabel(method)} · ${_resultLabel(result)}',
                        style: TextStyle(
                          fontSize: 12,
                          color: _resultColor(result),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (userName != null && userName.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          userName,
                          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                        ),
                      ],
                      if (failure != null && failure.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          failure,
                          style: const TextStyle(fontSize: 11, color: AppColors.danger),
                        ),
                      ],
                    ],
                  ),
                ),
                if (time != null)
                  Text(
                    DateFormat('HH:mm\ndd/MM').format(time.toLocal()),
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
