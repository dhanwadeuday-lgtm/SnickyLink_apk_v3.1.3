import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/memory_repository.dart';

class MemoryState {
  final List<dynamic> memories;
  final bool isLoading;
  final String? errorMessage;

  MemoryState({
    required this.memories,
    this.isLoading = false,
    this.errorMessage,
  });

  factory MemoryState.initial() => MemoryState(memories: [], isLoading: true);
  factory MemoryState.loaded(List<dynamic> memories) => MemoryState(memories: memories, isLoading: false);
  factory MemoryState.error(String message) => MemoryState(memories: [], isLoading: false, errorMessage: message);
}

class MemoryNotifier extends StateNotifier<MemoryState> {
  final MemoryRepository _repository;

  MemoryNotifier(this._repository) : super(MemoryState.initial()) {
    fetchMemories();
  }

  Future<void> fetchMemories() async {
    try {
      final memories = await _repository.getMemories();
      state = MemoryState.loaded(memories);
    } catch (e) {
      state = MemoryState.error(e.toString());
    }
  }

  Future<void> addMemory(String mediaId, String title, String? description) async {
    try {
      await _repository.createMemory(
        mediaId: mediaId,
        title: title,
        description: description,
      );
      await fetchMemories();
    } catch (e) {
      state = MemoryState.error(e.toString());
    }
  }
}

final memoryProvider = StateNotifierProvider<MemoryNotifier, MemoryState>((ref) {
  return MemoryNotifier(ref.watch(memoryRepositoryProvider));
});
