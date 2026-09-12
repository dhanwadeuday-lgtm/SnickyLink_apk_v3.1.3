import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/community_repository.dart';

class CommunityState {
  final List<dynamic> posts;
  final bool isLoading;
  final String? errorMessage;

  CommunityState({
    required this.posts,
    this.isLoading = false,
    this.errorMessage,
  });

  factory CommunityState.initial() => CommunityState(posts: [], isLoading: true);
  factory CommunityState.loaded(List<dynamic> posts) => CommunityState(posts: posts, isLoading: false);
  factory CommunityState.error(String message) => CommunityState(posts: [], isLoading: false, errorMessage: message);
}

class CommunityNotifier extends StateNotifier<CommunityState> {
  final CommunityRepository _repository;

  CommunityNotifier(this._repository) : super(CommunityState.initial()) {
    fetchFeed();
  }

  Future<void> fetchFeed({int offset = 0}) async {
    try {
      final posts = await _repository.getFeed(offset: offset);
      state = CommunityState.loaded(posts);
    } catch (e) {
      state = CommunityState.error(e.toString());
    }
  }

  Future<void> createPost(String content, String visibility, {String? mediaId}) async {
    try {
      await _repository.createPost(
        content: content,
        visibility: visibility,
        mediaId: mediaId,
      );
      await fetchFeed();
    } catch (e) {
      state = CommunityState.error(e.toString());
    }
  }

  Future<void> react(String postId, String type) async {
    try {
      await _repository.reactToPost(postId, type);
      // In a real app, we'd update the local state for the reaction count
    } catch (e) {
      // Silently fail or show toast
    }
  }

  Future<void> report(String postId, String reason) async {
    try {
      await _repository.reportPost(postId, reason);
    } catch (e) {
      state = CommunityState.error(e.toString());
    }
  }

  Future<void> block(String userId) async {
    try {
      await _repository.blockUser(userId);
      await fetchFeed(); // Refresh feed to remove blocked user's posts
    } catch (e) {
      state = CommunityState.error(e.toString());
    }
  }
}

final communityProvider = StateNotifierProvider<CommunityNotifier, CommunityState>((ref) {
  return CommunityNotifier(ref.watch(communityRepositoryProvider));
});
