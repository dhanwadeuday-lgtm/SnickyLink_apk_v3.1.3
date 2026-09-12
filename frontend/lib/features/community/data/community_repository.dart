import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class CommunityRepository {
  final ApiClient _apiClient;
  CommunityRepository(this._apiClient);

  Future<List<dynamic>> getFeed({int offset = 0, int limit = 20}) async {
    final response = await _apiClient.get('/community/feed', queryParameters: {
      'offset': offset,
      'limit': limit,
    });
    return response.data; // List of PostOut
  }

  Future<void> createPost({
    required String content,
    String? mediaId,
    required String visibility,
  }) async {
    await _apiClient.post('/community/posts', data: {
      'content': content,
      'media_id': mediaId,
      'visibility': visibility,
    });
  }

  Future<void> reactToPost(String postId, String reactionType) async {
    await _apiClient.post('/community/posts/$postId/react', data: {
      'reaction_type': reactionType,
    });
  }

  Future<void> reportPost(String postId, String reason) async {
    await _apiClient.post('/community/posts/$postId/report', data: {
      'reason': reason,
    });
  }

  Future<void> blockUser(String userId) async {
    await _apiClient.post('/community/block', data: {
      'blocked_id': userId,
    });
  }
}

final communityRepositoryProvider = Provider((ref) {
  return CommunityRepository(ApiClient());
});
