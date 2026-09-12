import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class MemoryRepository {
  final ApiClient _apiClient;
  MemoryRepository(this._apiClient);

  Future<List<dynamic>> getMemories() async {
    final response = await _apiClient.get('/memories');
    return response.data; // List of MemoryOut
  }

  Future<void> createMemory({
    required String mediaId,
    required String title,
    String? description,
  }) async {
    await _apiClient.post('/memories', data: {
      'media_id': mediaId,
      'title': title,
      'description': description,
    });
  }
}

final memoryRepositoryProvider = Provider((ref) {
  return MemoryRepository(ApiClient());
});
