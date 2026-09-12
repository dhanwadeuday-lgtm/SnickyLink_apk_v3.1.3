import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class ChatRepository {
  final ApiClient _apiClient;
  ChatRepository(this._apiClient);

  Future<List<dynamic>> getMessages({int offset = 0, int limit = 50, DateTime? sinceTimestamp}) async {
    final response = await _apiClient.get('/chat/messages/history', queryParameters: {
      'offset': offset,
      'limit': limit,
      if (sinceTimestamp != null) 'since_timestamp': sinceTimestamp.toUtc().toIso8601String(),
    });
    return response.data;
  }

  Future<void> sendMessage({
    required String encryptedContent,
    int? expiresAtSeconds,
    String? mediaId,
  }) async {
    await _apiClient.post('/chat/messages/send', data: {
      'encrypted_content': encryptedContent,
      'expires_at_seconds': expiresAtSeconds,
      'media_id': mediaId,
    });
  }
}

final chatRepositoryProvider = Provider((ref) {
  return ChatRepository(ApiClient());
});
