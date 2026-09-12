import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class SnickRepository {
  final ApiClient _apiClient;
  SnickRepository(this._apiClient);

  Future<void> submitSnick(String dailySnickId, String content, String type) async {
    await _apiClient.post('/snicks/$dailySnickId/submit', data: {
      'content': content,
      'submission_type': type,
    });
  }

  Future<void> skipSnick(String dailySnickId) async {
    await _apiClient.post('/snicks/$dailySnickId/skip');
  }

  Future<void> confirmSubmission(String submissionId) async {
    await _apiClient.post('/snicks/submissions/$submissionId/confirm');
  }
}

final snickRepositoryProvider = Provider((ref) {
  return SnickRepository(ApiClient());
});
