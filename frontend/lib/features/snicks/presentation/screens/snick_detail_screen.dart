import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/snick_notifier.dart';
import '../widgets/domino_reward_widget.dart';

class SnickDetailScreen extends ConsumerStatefulWidget {
  final dynamic snick; // Passed from Home screen

  const SnickDetailScreen({super.key, required this.snick});

  @override
  ConsumerState<SnickDetailScreen> createState() => _SnickDetailScreenState();
}

class _SnickDetailScreenState extends ConsumerState<SnickDetailScreen> {
  Timer? _timer;
  Duration _timeLeft = Duration.zero;
  final _contentController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _contentController.dispose();
    super.dispose();
  }

  void _startTimer() {
    final windowEnd = DateTime.parse(widget.snick['window_end']);
    _timer = Timer.periodic(Duration(seconds: 1), (timer) {
      final diff = windowEnd.difference(DateTime.now());
      if (diff.isNegative) {
        setState(() => _timeLeft = Duration.zero);
        timer.cancel();
      } else {
        setState(() => _timeLeft = diff);
      }
    });
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final hours = twoDigits(duration.inHours);
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return "$hours:$minutes:$seconds";
  }

  void _handleSubmit() async {
    final content = _contentController.text.trim();
    if (content.isEmpty) return;

    final type = widget.snick['requires_photo'] ? 'photo' : 'text';
    await ref.read(snickDetailProvider(widget.snick['id'].toString()).notifier)
        .submit(widget.snick['id'].toString(), content, type);
  }

  @override
  Widget build(BuildContext context) {
    final detailState = ref.watch(snickDetailProvider(widget.snick['id'].toString()));

    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: AppTheme.copperRose),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mission Header
            Text(
              "Daily Mission",
              style: TextStyle(
                fontFamily: 'Satoshi',
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppTheme.copperRose,
                letterSpacing: 1.2,
              ),
            ),
            SizedBox(height: 8),
            Text(
              widget.snick['title'],
              style: TextStyle(
                fontFamily: 'InstrumentSerif',
                fontStyle: FontStyle.italic,
                fontSize: 32,
                color: Colors.black,
              ),
            ),
            SizedBox(height: 24),

            // Countdown Timer
            Container(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: AppTheme.copperRose.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.timer, color: AppTheme.copperRose, size: 18),
                  SizedBox(width: 8),
                  Text(
                    "Ends in ${_formatDuration(_timeLeft)}",
                    style: TextStyle(
                      fontFamily: 'Satoshi',
                      fontWeight: FontWeight.bold,
                      color: AppTheme.copperRose,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 32),

            // Description
            Text(
              widget.snick['description'] ?? "No description provided.",
              style: TextStyle(
                fontFamily: 'Satoshi',
                fontSize: 18,
                color: Colors.grey[700],
                height: 1.5,
              ),
            ),
            SizedBox(height: 48),

            // Dynamic Interaction Area
            Expanded(
              child: _buildInteractionArea(detailState),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInteractionArea(SnickDetailState state) {
    if (state.isVerified) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 80),
            SizedBox(height: 16),
            Text(
              "Verified!",
              style: TextStyle(
                fontFamily: 'InstrumentSerif',
                fontSize: 28,
                color: Colors.green,
              ),
            ),
            Text(
              "You've earned your diamonds.",
              style: TextStyle(fontFamily: 'Satoshi', color: Colors.grey),
            ),
          ],
        ),
      );
    }

    if (state.status == SnickDetailStatus.submitted) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                color: AppTheme.copperRose,
                strokeWidth: 4,
              ),
            ),
            SizedBox(height: 24),
            Text(
              "Waiting for Partner...",
              style: TextStyle(
                fontFamily: 'Satoshi',
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.grey[600],
              ),
            ),
            SizedBox(height: 8),
            Text(
              "Your partner will need to confirm your submission.",
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Satoshi',
                fontSize: 14,
                color: Colors.grey[400],
              ),
            ),
          ],
        ),
      );
    }

    if (state.status == SnickDetailStatus.submitting) {
      return Center(child: CircularProgressIndicator(color: AppTheme.copperRose));
    }

    // Submission Form
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.snick['requires_photo'])
          Container(
            width: double.infinity,
            height: 120,
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.camera_alt, color: Colors.grey, size: 32),
                SizedBox(height: 8),
                Text("Upload Proof Photo", style: TextStyle(fontFamily: 'Satoshi', color: Colors.grey)),
              ],
            ),
          ),
        if (!widget.snick['requires_photo'])
          TextField(
            controller: _contentController,
            maxLines: 4,
            decoration: InputDecoration(
              hintText: "How did it go?",
              hintStyle: TextStyle(fontFamily: 'Satoshi'),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: BorderSide(color: AppTheme.copperRose),
              ),
            ),
          ),
        SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _handleSubmit,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.copperRose,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              "Submit Completion",
              style: TextStyle(
                fontFamily: 'Satoshi',
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
