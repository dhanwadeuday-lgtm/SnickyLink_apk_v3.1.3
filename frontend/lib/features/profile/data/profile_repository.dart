import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class ProfileRepository {
  final ApiClient _apiClient;
  ProfileRepository(this._apiClient);

  Future<Map<String, dynamic>> getProfile() async {
    final response = await _apiClient.get('/auth/me');
    return response.data;
  }

  Future<void> updateSettings(Map<String, dynamic> settings) async {
    // Stub for settings endpoint
    await _apiClient.post('/profile/settings', data: settings);
  }
}

final profileRepositoryProvider = Provider((ref) {
  return ProfileRepository(ApiClient());
});
