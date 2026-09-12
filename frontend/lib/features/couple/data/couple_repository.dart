import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class CoupleRepository {
  final ApiClient _apiClient;
  CoupleRepository(this._apiClient);

  Future<Map<String, dynamic>> generateInvite() async {
    final response = await _apiClient.post('/couple/invites/generate');
    return response.data; // contains 'token' and 'invite_link'
  }

  Future<void> pairPartner(String token) async {
    await _apiClient.post('/couple/pair', data: {
      'token': token,
    });
  }

  Future<Map<String, dynamic>> getMyCouple() async {
    final response = await _apiClient.get('/couple/me/couple');
    return response.data; // contains 'couple_id'
  }
}

final coupleRepositoryProvider = Provider((ref) {
  return CoupleRepository(ApiClient());
});
