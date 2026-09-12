import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import 'dart:math' as math;

class DominoRewardWidget extends StatefulWidget {
  final VoidCallback onComplete;

  const DominoRewardWidget({super.key, required this.onComplete});

  @override
  State<DominoRewardWidget> createState() => _DominoRewardWidgetState();
}

class _DominoRewardWidgetState extends State<DominoRewardWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _rotation;
  late Animation<double> _scale;
  late Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );

    _rotation = Tween<double>(begin: 0, end: math.pi / 2.5).animate(
      CurvedAnimation(parent: _controller, curve: Interval(0.0, 0.4, curve: Curves.easeOut)),
    );

    _scale = Tween<double>(begin: 0.0, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Interval(0.4, 0.6, curve: Curves.elasticOut)),
    );

    _opacity = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Interval(0.4, 0.6, curve: Curves.easeIn)),
    );

    _controller.forward().then((_) {
      Future.delayed(const Duration(milliseconds: 500), () {
        widget.onComplete();
      });
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Stack(
          alignment: Alignment.center,
          children: [
            // The "Reward Burst" - background diamonds
            if (_controller.value > 0.4)
              ...List.generate(12, (index) => _buildParticle(index)),

            // The Domino
            Transform.rotate(
              angle: _rotation.value,
              child: Transform.scale(
                scale: _scale.value,
                child: Opacity(
                  opacity: _opacity.value,
                  child: _buildDomino(),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildDomino() {
    return Container(
      width: 60,
      height: 100,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildDotRow(2),
          Divider(color: Colors.grey[300], thickness: 2),
          _buildDotRow(3),
        ],
      ),
    );
  }

  Widget _buildDotRow(int dots) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(dots, (index) => Container(
        width: 8,
        height: 8,
        margin: EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(
          color: AppTheme.copperRose,
          shape: BoxShape.circle,
        ),
      )),
    );
  }

  Widget _buildParticle(int index) {
    final angle = (index * 30) * (math.pi / 180);
    final distance = 100.0 * _controller.value;

    return Positioned(
      left: 0,
      top: 0,
      child: Transform.translate(
        offset: Offset(
          math.cos(angle) * distance,
          math.sin(angle) * distance,
        ),
        child: Icon(
          Icons.diamond,
          color: AppTheme.copperRose.withOpacity(1.0 - _controller.value),
          size: 20 * (1.0 - _controller.value),
        ),
      ),
    );
  }
}
