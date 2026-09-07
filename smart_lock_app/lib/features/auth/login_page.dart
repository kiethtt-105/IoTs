import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/auth_service.dart';
import '../../core/api/api_client.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _emailCtrl = TextEditingController(text: 'admin@admin.vn');
  final _passCtrl = TextEditingController(text: 'admin123');
  final _ipCtrl = TextEditingController(text: '192.168.1.100');
  bool _obscure = true;
  bool _showIp = true;
  bool _checking = false;
  ConnectionCheckResult? _connResult;

  @override
  void initState() {
    super.initState();
    _loadSavedIp();
  }

  Future<void> _loadSavedIp() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('backend_ip');
    if (ip != null && ip.isNotEmpty && mounted) {
      setState(() => _ipCtrl.text = ip);
    }
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _ipCtrl.dispose();
    super.dispose();
  }

  void _applyIp() {
    final ip = _ipCtrl.text.trim();
    if (ip.isEmpty) return;
    final auth = context.read<AuthService>();
    if (ip.startsWith('http')) {
      auth.setBaseUrl(ip);
    } else {
      auth.setBaseUrl('http://$ip:8000');
    }
  }

  Future<void> _checkConnection() async {
    _applyIp();
    setState(() {
      _checking = true;
      _connResult = null;
    });
    final auth = context.read<AuthService>();
    final result = await auth.checkConnection(deep: false);
    if (mounted) {
      setState(() {
        _checking = false;
        _connResult = result;
      });
    }
  }

  Future<void> _login() async {
    _applyIp();
    final auth = context.read<AuthService>();
    final ok = await auth.login(_emailCtrl.text.trim(), _passCtrl.text);
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.error ?? 'Đăng nhập thất bại'),
          backgroundColor: AppColors.danger,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.accent],
                  ),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.lock_rounded, size: 42, color: Colors.white),
              ),
              const SizedBox(height: 24),
              const Text('Smart Lock', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              const Text(
                'Đăng nhập để quản lý khóa thông minh',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  hintText: 'Email',
                  prefixIcon: Icon(Icons.email_outlined, color: AppColors.textSecondary),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _passCtrl,
                obscureText: _obscure,
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _login(),
                decoration: InputDecoration(
                  hintText: 'Mật khẩu',
                  prefixIcon: const Icon(Icons.lock_outline, color: AppColors.textSecondary),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscure ? Icons.visibility_off : Icons.visibility,
                      color: AppColors.textSecondary,
                    ),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: () => setState(() => _showIp = !_showIp),
                  child: Text(
                    _showIp ? 'Ẩn cấu hình server' : 'Cấu hình IP Backend + CSDL',
                    style: const TextStyle(color: AppColors.accent, fontSize: 13),
                  ),
                ),
              ),
              if (_showIp) ...[
                const SizedBox(height: 4),
                TextField(
                  controller: _ipCtrl,
                  keyboardType: TextInputType.url,
                  decoration: const InputDecoration(
                    hintText: 'IP backend (vd: 192.168.1.5) hoặc http://...',
                    prefixIcon: Icon(Icons.dns_outlined, color: AppColors.textSecondary),
                  ),
                ),
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  onPressed: _checking ? null : _checkConnection,
                  icon: _checking
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.wifi_tethering, size: 18),
                  label: Text(_checking ? 'Đang kiểm tra...' : 'Kiểm tra kết nối Backend + CSDL'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.accent,
                    side: const BorderSide(color: AppColors.surfaceLight),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
                if (_connResult != null) ...[
                  const SizedBox(height: 10),
                  _ConnectionBanner(result: _connResult!),
                ],
              ],
              const SizedBox(height: 24),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: auth.isLoading ? null : _login,
                  child: auth.isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Đăng nhập'),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Demo: admin@admin.vn / admin123\nBackend: uvicorn · PostgreSQL: smart_lock',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.textSecondary.withValues(alpha: 0.75),
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectionBanner extends StatelessWidget {
  final ConnectionCheckResult result;
  const _ConnectionBanner({required this.result});

  @override
  Widget build(BuildContext context) {
    final color = result.ok ? AppColors.success : AppColors.danger;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            result.ok ? Icons.check_circle : Icons.error_outline,
            color: color,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result.message,
                  style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 13),
                ),
                if (result.latencyMs != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    'Độ trễ: ${result.latencyMs} ms',
                    style: TextStyle(color: color.withValues(alpha: 0.85), fontSize: 11),
                  ),
                ],
                if (result.detail != null && !result.ok) ...[
                  const SizedBox(height: 2),
                  Text(
                    result.detail!,
                    style: TextStyle(color: color.withValues(alpha: 0.75), fontSize: 11),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
