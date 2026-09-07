enum DeviceStatus { locked, unlocked, offline, tamper, unknown }

class SmartDevice {
  final String id;
  final String name;
  final String? location;
  final DeviceStatus status;
  final int? batteryLevel;
  final String macAddress;
  final String? firmwareVersion;
  final String? ownerName;
  final DateTime? updatedAt;

  SmartDevice({
    required this.id,
    required this.name,
    this.location,
    required this.status,
    this.batteryLevel,
    required this.macAddress,
    this.firmwareVersion,
    this.ownerName,
    this.updatedAt,
  });

  factory SmartDevice.fromJson(Map<String, dynamic> json) {
    return SmartDevice(
      id: json['id']?.toString() ?? '',
      name: json['name'] ?? 'Unknown',
      location: json['location'],
      status: _parseStatus(json['status']),
      batteryLevel: json['battery_level'],
      macAddress: json['mac_address'] ?? '',
      firmwareVersion: json['firmware_version'],
      ownerName: json['owner_name'],
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'])
          : null,
    );
  }

  static DeviceStatus _parseStatus(dynamic value) {
    if (value == null) return DeviceStatus.unknown;
    switch (value.toString().toLowerCase()) {
      case 'locked':
        return DeviceStatus.locked;
      case 'unlocked':
        return DeviceStatus.unlocked;
      case 'offline':
        return DeviceStatus.offline;
      case 'tamper':
        return DeviceStatus.tamper;
      default:
        return DeviceStatus.unknown;
    }
  }

  bool get isLocked => status == DeviceStatus.locked;
  bool get isOnline => status != DeviceStatus.offline && status != DeviceStatus.unknown;
  bool get isTamper => status == DeviceStatus.tamper;

  String get statusLabel {
    switch (status) {
      case DeviceStatus.locked:
        return 'Đã khóa';
      case DeviceStatus.unlocked:
        return 'Đã mở';
      case DeviceStatus.offline:
        return 'Offline';
      case DeviceStatus.tamper:
        return 'Báo động';
      default:
        return 'Không rõ';
    }
  }

  SmartDevice copyWith({
    DeviceStatus? status,
    int? batteryLevel,
  }) {
    return SmartDevice(
      id: id,
      name: name,
      location: location,
      status: status ?? this.status,
      batteryLevel: batteryLevel ?? this.batteryLevel,
      macAddress: macAddress,
      firmwareVersion: firmwareVersion,
      ownerName: ownerName,
      updatedAt: updatedAt,
    );
  }
}
