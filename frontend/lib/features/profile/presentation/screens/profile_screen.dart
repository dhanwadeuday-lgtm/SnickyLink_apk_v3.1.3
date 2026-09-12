import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/profile_notifier.dart';
import '../../../auth/domain/auth_notifier.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileState = ref.watch(profileProvider);

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          "Settings",
          style: TextStyle(
            fontFamily: 'InstrumentSerif',
            fontStyle: FontStyle.italic,
            fontSize: 28,
            color: AppTheme.copperRose,
          ),
        ),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: AppTheme.copperRose),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _buildContent(context, ref, profileState),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, ProfileState state) {
    if (state.isLoading) {
      return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    }

    if (state.errorMessage != null) {
      return Center(child: Text(state.errorMessage!, style: TextStyle(color: Colors.red)));
    }

    return ListView(
      padding: EdgeInsets.all(24),
      children: [
        // User Info Header
        Center(
          child: Column(
            children: [
              CircleAvatar(
                radius: 50,
                backgroundColor: AppTheme.copperRose,
                child: Text(
                  state.user['email']?[0].toUpperCase() ?? "U",
                  style: TextStyle(fontSize: 32, color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              SizedBox(height: 16),
              Text(
                state.user['email'] ?? "User",
                style: TextStyle(fontFamily: 'Satoshi', fontSize: 18, fontWeight: FontWeight.w500),
              ),
            ],
          ),
        ),
        SizedBox(height: 48),

        // Settings Sections
        _buildSettingItem(
          icon: Icons.notifications,
          title: "Notifications",
          onTap: () {
            // TODO: Navigate to notification settings
          },
        ),
        _buildSettingItem(
          icon: Icons.security,
          title: "Privacy & Security",
          onTap: () {
            // TODO: Navigate to security settings
          },
        ),
        _buildSettingItem(
          icon: Icons.help_outline,
          title: "Help & Support",
          onTap: () {
            // TODO: Navigate to support
          },
        ),
        SizedBox(height: 32),
        Divider(),
        SizedBox(height: 16),
      _buildSettingItem(
        icon: Icons.logout,
        title: "Logout",
        color: Colors.red,
        onTap: () {
          ref.read(authProvider.notifier).logout(); Navigator.of(context).pushReplacementNamed('/login');
        },
      ),
      ],
    );
  }

  Widget _buildSettingItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    Color? color,
  }) {
    return ListTile(
      leading: Icon(icon, color: color ?? AppTheme.copperRose),
      title: Text(
 title,
        style: TextStyle(
          fontFamily: 'Satoshi',
          fontSize: 16,
          color: color ?? Colors.black87,
        ),
      ),
      trailing: Icon(Icons.chevron_right, color: Colors.grey),
      onTap: onTap,
    );
  }
}
