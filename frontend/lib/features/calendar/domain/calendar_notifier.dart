import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/calendar_repository.dart';

class CalendarState {
  final List<dynamic> events;
  final bool isLoading;
  final String? errorMessage;

  CalendarState({
    required this.events,
    this.isLoading = false,
    this.errorMessage,
  });

  factory CalendarState.initial() => CalendarState(events: [], isLoading: true);
  factory CalendarState.loaded(List<dynamic> events) => CalendarState(events: events, isLoading: false);
  factory CalendarState.error(String message) => CalendarState(events: [], isLoading: false, errorMessage: message);
}

class CalendarNotifier extends StateNotifier<CalendarState> {
  final CalendarRepository _repository;

  CalendarNotifier(this._repository) : super(CalendarState.initial()) {
    fetchEvents();
  }

  Future<void> fetchEvents() async {
    try {
      final events = await _repository.getEvents();
      state = CalendarState.loaded(events);
    } catch (e) {
      state = CalendarState.error(e.toString());
    }
  }

  Future<void> addEvent({
    required String title,
    required DateTime eventDate,
    String? description,
    bool isAllDay = false,
    bool isAnniversary = false,
    String? memoryId,
  }) async {
    try {
      await _repository.createEvent(
        title: title,
        eventDate: eventDate,
        description: description,
        isAllDay: isAllDay,
        isAnniversary: isAnniversary,
        memoryId: memoryId,
      );
      await fetchEvents();
    } catch (e) {
      state = CalendarState.error(e.toString());
    }
  }
}

final calendarProvider = StateNotifierProvider<CalendarNotifier, CalendarState>((ref) {
  return CalendarNotifier(ref.watch(calendarRepositoryProvider));
});
