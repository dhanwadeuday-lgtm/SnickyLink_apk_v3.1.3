import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/home_notifier.dart';
import '../widgets/stat_header_widget.dart';
import '../widgets/snick_item_widget.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final homeState = ref.watch(homeProvider);

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      body: Column(
        children: [
          // 1. Stats Header
          StatHeaderWidget(
            diamonds: homeState.diamonds,
            streak: homeState.streak,
          ),

          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: _buildContent(context, ref, homeState),
            ),
          ),
        ],
      ),
      // Quick links FAB
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // TODO: Open Global Navigation Menu (Chat/Memories/Calendar)
        },
        backgroundColor: AppTheme.copperRose,
        foregroundColor: Colors.white,
        icon: Icon(Icons.grid_view),
        label: Text("Hub"),
      ),
    );
  }

  Widget _buildContent(BuildContext context, WidgetRef ref, HomeState state) {
    if (state.isLoading) {
      return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    }

    if (state.errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(state.errorMessage!, textAlign: TextAlign.center),
            TextButton(
              onPressed: () => ref.read(homeProvider.notifier).fetchData(),
              child: Text("Retry", style: TextStyle(color: AppTheme.copperRose)),
            ),
          ],
        ),
      );
    }

    if (state.todaySnicks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.hourglass_empty, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              "No Snicks for today yet",
              style: TextStyle(fontFamily: 'Satoshi', fontSize: 18, color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Today's Missions",
          style: TextStyle(
            fontFamily: 'InstrumentSerif',
            fontStyle: FontStyle.italic,
            fontSize: 28,
            color: Colors.black,
          ),
        ),
        SizedBox(height: 24),
        ListView.builder(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          itemCount: state.todaySnicks.length,
          itemBuilder: (context, index) {
            final snick = state.todaySnicks[index];
            return SnickItemWidget(
              snick: snick,
              onTap: () {
                // TODO: Navigate to Snick Detail Screen
              },
            );
          },
        ),
      ],
    );
  }
}
