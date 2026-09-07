import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/auth_service.dart';
import '../../core/services/device_service.dart';
import '../../core/models/device.dart';
import '../devices/device_detail_page.dart';
import '../logs/logs_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DeviceService>().loadDevices();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final deviceSvc = context.watch<DeviceService>();

    return Scaffold(
      appBar: AppBar(
        title: Text(_tab == 0 ? 'Smart Lock' : 'Lịch sử'),
        actions: [
          if (_tab == 0)
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed: () => deviceSvc.refresh(),
            ),
          PopupMenuButton(
            icon: const Icon(Icons.more_vert),
            itemBuilder: (_) => [
              PopupMenuItem(
                enabled: false,
                child: Row(
                  children: [
                    const Icon(Icons.person_outline, size: 20),
                    const SizedBox(width: 10),
                    Flexible(child: Text(auth.user?.fullName ?? auth.user?.email ?? 'User')),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              PopupMenuItem(
                onTap: () => auth.logout(),
                child: const Row(
                  children: [
                    Icon(Icons.logout, size: 20, color: Color(0xFFEF4444)),
                    SizedBox(width: 10),
                    Text('Đăng xuất', style: TextStyle(color: Color(0xFFEF4444))),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          if (_tab == 0 && deviceSvc.error != null)
            Material(
              color: const Color(0xFFEF4444).withValues(alpha: 0.15),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  children: [
                    const Icon(Icons.cloud_off, size: 18, color: Color(0xFFEF4444)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        deviceSvc.error!,
                        style: const TextStyle(color: Color(0xFFEF4444), fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          Expanded(child: _tab == 0 ? _DevicesTab(deviceSvc: deviceSvc) : const LogsPage()),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        backgroundColor: const Color(0xFF1E293B),
        indicatorColor: const Color(0xFF6366F1).withValues(alpha: 0.25),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.lock_outline),
            selectedIcon: Icon(Icons.lock_rounded),
            label: 'Khóa',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history),
            label: 'Lịch sử',
          ),
        ],
      ),
    );
  }
}

class _DevicesTab extends StatelessWidget {
  final DeviceService deviceSvc;
  const _DevicesTab({required this.deviceSvc});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () => deviceSvc.refresh(),
      color: const Color(0xFF6366F1),
      child: deviceSvc.isLoading && deviceSvc.devices.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : deviceSvc.devices.isEmpty
              ? ListView(
                  children: [
                    SizedBox(height: MediaQuery.of(context).size.height * 0.28),
                    Icon(Icons.lock_outline, size: 64, color: Colors.white24),
                    const SizedBox(height: 16),
                    const Center(
                      child: Text('Chưa có khóa nào', style: TextStyle(fontSize: 16, color: Color(0xFF94A3B8))),
                    ),
                    const SizedBox(height: 8),
                    Center(child: TextButton(onPressed: () => deviceSvc.refresh(), child: const Text('Tải lại'))),
                  ],
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: deviceSvc.devices.length,
                  itemBuilder: (context, index) {
                    final device = deviceSvc.devices[index];
                    return _DeviceCard(
                      device: device,
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => DeviceDetailPage(device: device)),
                        ).then((_) => deviceSvc.refresh());
                      },
                    );
                  },
                ),
    );
  }
}

class _DeviceCard extends StatelessWidget {
  final SmartDevice device;
  final VoidCallback onTap;

  const _DeviceCard({required this.device, required this.onTap});

  Color get _statusColor {
    switch (device.status) {
      case DeviceStatus.locked:
        return const Color(0xFF10B981);
      case DeviceStatus.unlocked:
        return const Color(0xFF22D3EE);
      case DeviceStatus.tamper:
        return const Color(0xFFEF4444);
      case DeviceStatus.offline:
        return const Color(0xFF94A3B8);
      default:
        return const Color(0xFFF59E0B);
    }
  }

  IconData get _statusIcon {
    switch (device.status) {
      case DeviceStatus.locked:
        return Icons.lock_rounded;
      case DeviceStatus.unlocked:
        return Icons.lock_open_rounded;
      case DeviceStatus.tamper:
        return Icons.warning_amber_rounded;
      case DeviceStatus.offline:
        return Icons.cloud_off_rounded;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: const Color(0xFF1E293B),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: _statusColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(_statusIcon, color: _statusColor, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(device.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text(
                      device.location ?? 'Không có vị trí',
                      style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: _statusColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      device.statusLabel,
                      style: TextStyle(color: _statusColor, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ),
                  if (device.batteryLevel != null) ...[
                    const SizedBox(height: 6),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          device.batteryLevel! > 20 ? Icons.battery_std : Icons.battery_alert,
                          size: 14,
                          color: device.batteryLevel! > 20 ? const Color(0xFF94A3B8) : const Color(0xFFEF4444),
                        ),
                        const SizedBox(width: 2),
                        Text('${device.batteryLevel}%', style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                      ],
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
