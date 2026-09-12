import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/memory_notifier.dart';

class MemoriesScreen extends ConsumerWidget {
  const MemoriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memoryState = ref.watch(memoryProvider);

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          "Our Memories",
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
      body: _buildContent(context, ref, memoryState),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateMemoryDialog(context, ref),
        backgroundColor: AppTheme.copperRose,
        foregroundColor: Colors.white,
        child: Icon(Icons.add),
      ),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, MemoryState state) {
    if (state.isLoading) {
      return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    }

    if (state.errorMessage != null) {
      return Center(child: Text(state.errorMessage!, style: TextStyle(color: Colors.red)));
    }

    if (state.memories.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.photo_library_outlined, size: 64, color: Colors.grey[300]),
            SizedBox(height: 16),
            Text(
              "No memories saved yet",
              style: TextStyle(fontFamily: 'Satoshi', color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return GridView.builder(
      padding: EdgeInsets.all(16),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.8,
      ),
      itemCount: state.memories.length,
      itemBuilder: (context, index) {
        final memory = state.memories[index];
        return MemoryCard(memory: memory);
      },
    );
  }

  void _showCreateMemoryDialog(BuildContext context, WidgetRef ref) {
    final titleController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Save Memory", style: TextStyle(fontFamily: 'InstrumentSerif', fontStyle: FontStyle.italic, color: AppTheme.copperRose)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleController,
              decoration: InputDecoration(labelText: "Title", labelStyle: TextStyle(fontFamily: 'Satoshi')),
            ),
            TextField(
              controller: descController,
              decoration: InputDecoration(labelText: "Description (Optional)", labelStyle: TextStyle(fontFamily: 'Satoshi')),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("Choose a photo first. Memories are linked to real media."),
                ),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.copperRose, foregroundColor: Colors.white),
            child: Text("Save"),
          ),
        ],
      ),
    );
  }
}

class MemoryCard extends StatelessWidget {
  final dynamic memory;
  const MemoryCard({super.key, required this.memory});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
              ),
              child: Center(
                child: Icon(Icons.image, color: Colors.grey[400]),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  memory['title'],
                  style: TextStyle(
                    fontFamily: 'Satoshi',
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (memory['description'] != null)
                  Text(
                    memory['description'],
                    style: TextStyle(fontFamily: 'Satoshi', fontSize: 12, color: Colors.grey),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
