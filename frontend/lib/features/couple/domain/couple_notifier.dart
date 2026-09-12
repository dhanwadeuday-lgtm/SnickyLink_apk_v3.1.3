import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/couple_repository.dart';

enum CoupleStatus { initial, pairing, paired, error }

class CoupleState {
  final CoupleStatus status;
  final String? coupleId;
  final String? inviteLink;
  final String? errorMessage;

  CoupleState({
    required this.status,
    this.coupleId,
    this.inviteLink,
    this.errorMessage,
  });

  factory CoupleState.initial() => CoupleState(status: CoupleStatus.initial);
  factory CoupleState.paired(String id) => CoupleState(status: CoupleStatus.paired, coupleId: id);
  factory CoupleState.pairing() => CoupleState(status: CoupleStatus.pairing);
  factory CoupleState.error(String message) => CoupleState(status: CoupleStatus.error, errorMessage: message);
}

class CoupleNotifier extends StateNotifier<CoupleState> {
  final CoupleRepository _repository;

  CoupleNotifier(this._repository) : super(CoupleState.initial());

  Future<void> createInvite() async {
    state = CoupleState(status: CoupleStatus.pairing);
    try {
      final data = await _repository.generateInvite();
      state = CoupleState(
        status: CoupleStatus.initial,
        inviteLink: data['invite_link'],
      );
    } catch (e) {
      state = CoupleState.error(e.toString());
    }
  }

  Future<void> joinCouple(String token) async {
    state = CoupleState(status: CoupleStatus.pairing);
    try {
      await _repository.pairPartner(token);
      final coupleData = await _repository.getMyCouple();
      state = CoupleState.paired(coupleData['couple_id']);
    } catch (e) {
      state = CoupleState.error(e.toString());
    }
  }

  void clearInvite() {
    state = CoupleState.initial();
  }
}

final coupleProvider = StateNotifierProvider<CoupleNotifier, CoupleState>((ref) {
  return CoupleNotifier(ref.watch(coupleRepositoryProvider));
});
