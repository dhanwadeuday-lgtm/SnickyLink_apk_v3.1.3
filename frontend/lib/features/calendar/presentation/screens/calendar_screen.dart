import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/calendar_notifier.dart';

class CalendarScreen extends ConsumerStatefulWidget {
  const CalendarScreen({super.key});

  @override
  ConsumerState<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends ConsumerState<CalendarScreen> {
  DateTime _selectedDate = DateTime.now();

  void _showAddEventDialog() {
    final titleController = TextEditingController();
    final descController = TextEditingController();
    bool isAnniversary = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          title: Text("Add Event", style: TextStyle(fontFamily: 'InstrumentSerif', fontStyle: FontStyle.italic, color: AppTheme.copperRose)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: InputDecoration(labelText: "Event Title", labelStyle: TextStyle(fontFamily: 'Satoshi')),
              ),
              TextField(
                controller: descController,
                decoration: InputDecoration(labelText: "Description (Optional)", labelStyle: TextStyle(fontFamily: 'Satoshi')),
              ),
              SwitchListTile(
                title: Text("Is this an anniversary?", style: TextStyle(fontFamily: 'Satoshi')),
                value: isAnniversary,
                onChanged: (val) => setStateDialog(() => isAnniversary = val),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel")),
            ElevatedButton(
              onPressed: () {
                ref.read(calendarProvider.notifier).addEvent(
                  title: titleController.text,
                  eventDate: _selectedDate,
                  description: descController.text,
                  isAnniversary: isAnniversary,
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.copperRose, foregroundColor: Colors.white),
              child: Text("Save"),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final calendarState = ref.watch(calendarProvider);

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          "Our Calendar",
          style: TextStyle(
            fontFamily: 'InstrumentSerif',
            fontStyle: FontStyle.italic,
            fontSize: 28,
            color: AppTheme.copperRose,
          ),
        ),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: AppTheme.copperRose),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Column(
        children: [
          // Simple Date Selector
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  DateFormat('MMMM yyyy').format(_selectedDate),
                  style: TextStyle(fontFamily: 'Satoshi', fontSize: 20, fontWeight: FontWeight.bold),
                ),
                TextButton.icon(
                  onPressed: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: _selectedDate,
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100),
                    );
                    if (picked != null) setState(() => _selectedDate = picked);
                  },
                  icon: Icon(Icons.calendar_month, color: AppTheme.copperRose),
                  label: Text("Change Date", style: TextStyle(color: AppTheme.copperRose)),
                ),
              ],
            ),
          ),
          Expanded(
            child: _buildEventsList(calendarState),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddEventDialog,
        backgroundColor: AppTheme.copperRose,
        foregroundColor: Colors.white,
        child: Icon(Icons.add),
      ),
    );
  }

  Widget _buildEventsList(CalendarState state) {
    if (state.isLoading) {
      return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    }

    if (state.errorMessage != null) {
      return Center(child: Text(state.errorMessage!, style: TextStyle(color: Colors.red)));
    }

    final dayEvents = state.events.where((e) =>
      e['event_date'].toString().contains(DateFormat('yyyy-MM-dd').format(_selectedDate))
    ).toList();

    if (dayEvents.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_busy, size: 64, color: Colors.grey[300]),
            SizedBox(height: 16),
            Text(
              "No events for this day",
              style: TextStyle(fontFamily: 'Satoshi', color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.symmetric(horizontal: 16),
      itemCount: dayEvents.length,
      itemBuilder: (context, index) {
        final event = dayEvents[index];
        return Card(
          margin: EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            leading: Icon(
              event['is_anniversary'] ? Icons.favorite : Icons.event,
              color: event['is_anniversary'] ? Colors.red : AppTheme.copperRose,
            ),
            title: Text(
              event['title'],
              style: TextStyle(fontFamily: 'Satoshi', fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              event['description'] ?? "",
              style: TextStyle(fontFamily: 'Satoshi', fontSize: 13),
            ),
            trailing: event['is_anniversary']
              ? Chip(label: Text("Anniversary", style: TextStyle(fontSize: 10, color: Colors.white)), backgroundColor: Colors.red)
              : null,
          ),
        );
      },
    );
  }
}
