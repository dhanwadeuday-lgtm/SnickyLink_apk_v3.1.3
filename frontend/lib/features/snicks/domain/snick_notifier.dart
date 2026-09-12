import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/snick_repository.dart';

enum SnickDetailStatus { initial, submitting, submitted, error }

class SnickDetailState {
  final SnickDetailStatus status;
  final String? errorMessage;
  final bool isVerified;

  SnickDetailState({
    required this.status,
    this.errorMessage,
    this.isVerified = false,
  });

  factory SnickDetailState.initial() => SnickDetailState(status: SnickDetailStatus.initial);
  factory SnickDetailState.submitting() => SnickDetailState(status: SnickDetailStatus.submitting);
  factory SnickDetailState.submitted() => SnickDetailState(status: SnickDetailStatus.submitted);
  factory SnickDetailState.verified() => SnickDetailState(status: SnickDetailStatus.submitted, isVerified: true);
  factory SnickDetailState.error(String message) => SnickDetailState(status: SnickDetailStatus.error, errorMessage: message);
}

class SnickDetailNotifier extends StateNotifier<SnickDetailState> {
  final SnickRepository _repository;

  SnickDetailNotifier(this._repository) : super(SnickDetailState.initial());

  Future<void> submit(String dailySnickId, String content, String type) async {
    state = SnickDetailState.submitting();
    try {
      await _repository.submitSnick(dailySnickId, content, type);
      state = SnickDetailState.submitted();
    } catch (e) {
      state = SnickDetailState.error(e.toString());
    }
  }

  Future<void> skip(String dailySnickId) async {
    try {
      await _repository.skipSnick(dailySnickId);
      state = SnickDetailState.initial(); // Or a 'skipped' state
    } catch (e) {
      state = SnickDetailState.error(e.toString());
    }
  }

  void setVerified() {
    state = SnickDetailState.verified();
  }
}

final snickDetailProvider = StateNotifierProvider.family<SnickDetailNotifier, SnickDetailState, String>((ref, id) {
  return SnickDetailNotifier(ref.watch(snickRepositoryProvider));
});
