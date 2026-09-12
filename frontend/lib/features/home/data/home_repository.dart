import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class HomeRepository {
  final ApiClient _apiClient;
  HomeRepository(this._apiClient);

  Future<Map<String, dynamic>> getCoupleStats() async {
    // Leaderboard-me is the current trusted engagement summary endpoint.
    final response = await _apiClient.get('/engagement/leaderboard/me');
    return response.data; // contains 'score' (diamonds) and 'rank'
  }

  Future<List<dynamic>> getTodaySnicks() async {
    final response = await _apiClient.get('/snicks/today');
    return response.data; // List of DailySnickResponse
  }
}

final homeRepositoryProvider = Provider((ref) {
  return HomeRepository(ApiClient());
});
