import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/couple_notifier.dart';

class InviteCreateScreen extends ConsumerWidget {
  const InviteCreateScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final coupleState = ref.watch(coupleProvider);

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
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "Invite Your Partner",
                style: TextStyle(
                  fontFamily: 'InstrumentSerif',
                  fontStyle: FontStyle.italic,
                  fontSize: 32,
                  color: AppTheme.copperRose,
                ),
              ),
              SizedBox(height: 8),
              Text(
                "The first step to your shared journey.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Satoshi',
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 48),

              // Branded Invite Card
              Container(
                width: double.infinity,
                padding: EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: AppTheme.copperRose,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.copperRose.withOpacity(0.3),
                      blurRadius: 20,
                      offset: Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Icon(Icons.favorite, color: Colors.white, size: 64),
                    SizedBox(height: 16),
                    Text(
                      "You're Invited!",
                      style: TextStyle(
                        fontFamily: 'InstrumentSerif',
                        fontStyle: FontStyle.italic,
                        fontSize: 28,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      "Join me on SnickyLink to grow our connection together.",
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: 'Satoshi',
                        fontSize: 16,
                        color: Colors.white.withOpacity(0.9),
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 48),

              if (coupleState.inviteLink == null)
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: () => ref.read(coupleProvider.notifier).createInvite(),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.copperRose,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text(
                      "Generate Invite Link",
                      style: TextStyle(
                        fontFamily: 'Satoshi',
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                )
              else
                Column(
                  children: [
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              coupleState.inviteLink!,
                              style: TextStyle(fontFamily: 'Satoshi', fontSize: 14),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.copy, color: AppTheme.copperRose),
                            onPressed: () {
                              // TODO: Copy to clipboard
                            },
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton.icon(
                        icon: Icon(Icons.share),
                        label: Text(
                          "Share with Partner",
                          style: TextStyle(
                            fontFamily: 'Satoshi',
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        onPressed: () {
                          Share.share("Join me on SnickyLink! ${coupleState.inviteLink}");
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.copperRose,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }
}
