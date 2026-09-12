import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';

class PairingSuccessScreen extends ConsumerWidget {
  const PairingSuccessScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppTheme.dayBackground,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Celebration Icon
              Icon(Icons.check_circle, color: AppTheme.copperRose, size: 100),
              SizedBox(height: 32),
              Text(
                "You're Paired!",
                style: TextStyle(
                  fontFamily: 'InstrumentSerif',
                  fontStyle: FontStyle.italic,
                  fontSize: 42,
                  color: AppTheme.copperRose,
                ),
              ),
              SizedBox(height: 16),
              Text(
                "Welcome to SnickyLink. Your shared journey begins now.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Satoshi',
                  fontSize: 18,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 64),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () {
                    // TODO: Navigate to Home screen
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.copperRose,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: Text(
                    "Enter Your Hub",
                    style: TextStyle(
                      fontFamily: 'Satoshi',
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
