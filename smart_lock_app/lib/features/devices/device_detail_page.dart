import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/models/device.dart';
import '../../core/services/device_service.dart';

class DeviceDetailPage extends StatefulWidget {
  final SmartDevice device;

  const DeviceDetailPage({super.key, required this.device});

  @override
  State<DeviceDetailPage> createState() => _DeviceDetailPageState();
}

class _DeviceDetailPageState extends State<DeviceDetailPage> {
  late SmartDevice _device;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _device = widget.device;
  }

  Future<void> _control(String command) async {
    setState(() => _busy = true);
    final svc = context.read<DeviceService>();
    final ok = await svc.controlDevice(_device, command);

    if (mounted) {
      setState(() {
        _busy = false;
        // Cập nhật status local
        if (ok) {
          _device = _device.copyWith(
            status: command == 'unlock' ? DeviceStatus.unlocked : DeviceStatus.locked,
          );
        }
      });

      final method = svc.lastMethod;
      String msg;
      Color bg;

      if (ok) {
        final via = method == ControlMethod.ble ? 'BLE (Offline)' : 'Online (MQTT)';
        msg = command == 'unlock' ? 'Đã mở khóa via $via' : 'Đã khóa via $via';
        bg = AppColors.success;
      } else {
        msg = svc.error ?? 'Thất bại';
        bg = AppColors.danger;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(msg), backgroundColor: bg, behavior: SnackBarBehavior.floating),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLocked = _device.isLocked;
    final statusColor = isLocked
        ? AppColors.success
        : _device.isTamper
            ? AppColors.danger
            : AppColors.accent;

    return Scaffold(
      appBar: AppBar(title: Text(_device.name)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Status big circle
            Container(
              width: 160,
              height: 160,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    statusColor.withValues(alpha: 0.25),
                    statusColor.withValues(alpha: 0.05),
                  ],
                ),
                border: Border.all(color: statusColor.withValues(alpha: 0.4), width: 3),
              ),
              child: Icon(
                isLocked ? Icons.lock_rounded : Icons.lock_open_rounded,
                size: 64,
                color: statusColor,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _device.statusLabel,
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: statusColor),
            ),
            if (_device.location != null) ...[
              const SizedBox(height: 6),
              Text(_device.location!, style: const TextStyle(color: AppColors.textSecondary)),
            ],
            const SizedBox(height: 32),

            // Info cards
            Row(
              children: [
                Expanded(child: _InfoTile(icon: Icons.battery_std, label: 'Pin', value: '${_device.batteryLevel ?? '--'}%')),
                const SizedBox(width: 12),
                Expanded(child: _InfoTile(icon: Icons.memory, label: 'Firmware', value: _device.firmwareVersion ?? '--')),
              ],
            ),
            const SizedBox(height: 12),
            _InfoTile(icon: Icons.bluetooth, label: 'MAC Address', value: _device.macAddress),
            const SizedBox(height: 36),

            // Action buttons
            if (_busy)
              const CircularProgressIndicator()
            else ...[
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: () => _control(isLocked ? 'unlock' : 'lock'),
                  icon: Icon(isLocked ? Icons.lock_open_rounded : Icons.lock_rounded),
                  label: Text(isLocked ? 'Mở khóa' : 'Khóa lại', style: const TextStyle(fontSize: 17)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isLocked ? AppColors.accent : AppColors.primary,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Ưu tiên BLE gần → fallback Online',
                style: TextStyle(color: AppColors.textSecondary.withValues(alpha: 0.7), fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoTile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppColors.textSecondary),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              const SizedBox(height: 2),
              Text(value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            ],
          ),
        ],
      ),
    );
  }
}
