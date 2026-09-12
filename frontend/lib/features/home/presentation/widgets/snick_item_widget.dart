import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class SnickItemWidget extends StatelessWidget {
  final dynamic snick;
  final VoidCallback onTap;

  const SnickItemWidget({super.key, required this.snick, required this.onTap});

  Color _getStateColor() {
    switch (snick['state']) {
      case 'ACTIVE': return AppTheme.copperRose;
      case 'VERIFIED': return Colors.green;
      case 'SUBMITTED': return Colors.amber;
      case 'EXPIRED': return Colors.grey[400]!;
      case 'LOCKED': return Colors.grey[300]!;
      default: return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getStateColor();
    final isLocked = snick['state'] == 'LOCKED';

    return GestureDetector(
      onTap: isLocked ? null : onTap,
      child: Container(
        margin: EdgeInsets.only(bottom: 16),
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color, width: 2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: color.withOpacity(0.2),
              child: Text(
                "${snick['order_index']}",
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Satoshi',
                ),
              ),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    snick['state'],
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: color,
                      fontFamily: 'Satoshi',
                    ),
                  ),
                  Text(
                    "Tap to view mission",
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                      fontFamily: 'Satoshi',
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              isLocked ? Icons.lock : Icons.chevron_right,
              color: Colors.grey,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}
