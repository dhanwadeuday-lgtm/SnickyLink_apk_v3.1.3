import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';
import '../data/chat_repository.dart';

class ChatState {
  final List<dynamic> messages;
  final bool isLoading;
  final bool isSending;
  final String? errorMessage;

  ChatState({
    required this.messages,
    this.isLoading = false,
    this.isSending = false,
    this.errorMessage,
  });

  factory ChatState.initial() => ChatState(messages: [], isLoading: true);
  factory ChatState.loaded(List<dynamic> messages) => ChatState(messages: messages, isLoading: false);
  factory ChatState.sending(List<dynamic> messages) => ChatState(messages: messages, isSending: true);
  factory ChatState.error(String message) => ChatState(messages: [], isLoading: false, errorMessage: message);
}

class ChatNotifier extends StateNotifier<ChatState> {
  final ChatRepository _repository;
  Timer? _pollingTimer;

  ChatNotifier(this._repository) : super(ChatState.initial()) {
    fetchMessages();
    _startPolling();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(Duration(seconds: 5), (timer) {
      fetchMessages();
    });
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchMessages() async {
    try {
      final messages = await _repository.getMessages();
      state = ChatState.loaded(messages);
    } catch (e) {
      state = ChatState.error(e.toString());
    }
  }

  Future<void> send(String content, {int? expiresAt, String? mediaId}) async {
    // TODO: Implement E2EE encryption here.
    // For now, we send plaintext as per the "gap-fix" instruction.
    final encryptedContent = content;

    state = ChatState.sending(state.messages);
    try {
      await _repository.sendMessage(
        encryptedContent: encryptedContent,
        expiresAtSeconds: expiresAt,
        mediaId: mediaId,
      );
      // Refresh messages to show the newly sent one
      await fetchMessages();
    } catch (e) {
      state = ChatState.error(e.toString());
    }
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(ref.watch(chatRepositoryProvider));
});
