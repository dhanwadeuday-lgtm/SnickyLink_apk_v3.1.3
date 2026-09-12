import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/home_repository.dart';

class HomeState {
  final bool isLoading;
  final List<dynamic> todaySnicks;
  final int diamonds;
  final int streak;
  final String? errorMessage;

  HomeState({
    required this.isLoading,
    this.todaySnicks = const [],
    this.diamonds = 0,
    this.streak = 0,
    this.errorMessage,
  });

  factory HomeState.initial() => HomeState(isLoading: true);
  factory HomeState.loaded({
    required List<dynamic> snicks,
    required int diamonds,
    required int streak,
  }) => HomeState(isLoading: false, todaySnicks: snicks, diamonds: diamonds, streak: streak);
  factory HomeState.error(String message) => HomeState(isLoading: false, errorMessage: message);
}

class HomeNotifier extends StateNotifier<HomeState> {
  final HomeRepository _repository;

  HomeNotifier(this._repository) : super(HomeState.initial()) {
    fetchData();
  }

  Future<void> fetchData() async {
    try {
      // Fetch stats and snicks in parallel
      final results = await Future.wait([
        _repository.getCoupleStats(),
        _repository.getTodaySnicks(),
      ]);

      final stats = results[0] as Map<String, dynamic>;
      final snicks = results[1] as List<dynamic>;

      state = HomeState.loaded(
        snicks: snicks,
        diamonds: stats['score'] ?? 0,
        streak: 0, // Stub until streak endpoint is dedicated
      );
    } catch (e) {
      state = HomeState.error(e.toString());
    }
  }
}

final homeProvider = StateNotifierProvider<HomeNotifier, HomeState>((ref) {
  return HomeNotifier(ref.watch(homeRepositoryProvider));
});
