import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class CalendarRepository {
  final ApiClient _apiClient;
  CalendarRepository(this._apiClient);

  Future<List<dynamic>> getEvents() async {
    final response = await _apiClient.get('/engagement/calendar/events');
    return response.data; // List of CalendarEventOut
  }

  Future<void> createEvent({
    required String title,
    required DateTime eventDate,
    String? description,
    bool isAllDay = false,
    bool isAnniversary = false,
    String? memoryId,
  }) async {
    await _apiClient.post('/engagement/calendar/events', data: {
      'title': title,
      'event_date': eventDate.toIso8601String(),
      'description': description,
      'is_all_day': isAllDay,
      'is_anniversary': isAnniversary,
      'memory_id': memoryId,
    });
  }
}

final calendarRepositoryProvider = Provider((ref) {
  return CalendarRepository(ApiClient());
});
