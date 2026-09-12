import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/profile_repository.dart';

class ProfileState {
  final Map<String, dynamic> user;
  final bool isLoading;
  final String? errorMessage;

  ProfileState({
    required this.user,
    this.isLoading = false,
    this.errorMessage,
  });

  factory ProfileState.initial() => ProfileState(user: {}, isLoading: true);
  factory ProfileState.loaded(Map<String, dynamic> user) => ProfileState(user: user, isLoading: false);
  factory ProfileState.error(String message) => ProfileState(user: {}, isLoading: false, errorMessage: message);
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  final ProfileRepository _repository;

  ProfileNotifier(this._repository) : super(ProfileState.initial()) {
    fetchProfile();
  }

  Future<void> fetchProfile() async {
    try {
      final user = await _repository.getProfile();
      state = ProfileState.loaded(user);
    } catch (e) {
      state = ProfileState.error(e.toString());
    }
  }

  Future<void> updateSettings(Map<String, dynamic> settings) async {
    try {
      await _repository.updateSettings(settings);
    } catch (e) {
      state = ProfileState.error(e.toString());
    }
  }
}

final profileProvider = StateNotifierProvider<ProfileNotifier, ProfileState>((ref) {
  return ProfileNotifier(ref.watch(profileRepositoryProvider));
});
