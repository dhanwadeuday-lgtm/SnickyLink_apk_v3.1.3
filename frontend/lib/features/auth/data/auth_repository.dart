import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class AuthRepository {
  final ApiClient _apiClient;
  AuthRepository(this._apiClient);

  Future<void> signup(String email, String password) async {
    await _apiClient.post('/auth/signup', data: {
      'email': email,
      'password': password,
    });
  }

  Future<void> login(String email, String password) async {
    final response = await _apiClient.post('/auth/login', data: {
      'email': email,
      'password': password,
    });

    final accessToken = response.data['access_token'];
    final refreshToken = response.data['refresh_token'];
    await _apiClient.saveTokens(accessToken, refreshToken);
  }

  Future<void> logout() async {
    try {
      await _apiClient.post('/auth/logout');
    } finally {
      await _apiClient.clearTokens();
    }
  }

  Future<bool> isAuthenticated() async {
    try {
      await _apiClient.get('/auth/me');
      return true;
    } catch (_) {
      return false;
    }
  }
}

final authRepositoryProvider = Provider((ref) {
  return AuthRepository(ApiClient());
});
