import 'dart:ui' as ui;

import 'package:flutter/material.dart';

/// 두 덩어리 궤도 그림: 시계 지도 + 밀도 그림 위에 두 중심의 궤적과 케플러 원.
class OrbitPainter extends CustomPainter {
  final ui.Image? image;
  final List<Offset> trail1, trail2; // (x, y)
  final double viewHalf, r0;
  final bool showKepler;
  final ColorScheme cs;
  OrbitPainter({
    required this.image,
    required this.trail1,
    required this.trail2,
    required this.viewHalf,
    required this.r0,
    required this.showKepler,
    required this.cs,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.clipRect(rect);
    Offset at(Offset p) => Offset((p.dx + viewHalf) / (2 * viewHalf) * size.width, (viewHalf - p.dy) / (2 * viewHalf) * size.height);
    if (image != null) {
      paintImage(canvas: canvas, rect: rect, image: image!, fit: BoxFit.fill, filterQuality: FilterQuality.medium);
    } else {
      canvas.drawRect(rect, Paint()..color = cs.surfaceContainerHighest);
    }
    final scale = size.width / (2 * viewHalf);
    if (showKepler) {
      final dash = Paint()
        ..color = cs.onSurface.withValues(alpha: 0.45)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1;
      for (var k = 0; k < 72; k += 2) {
        canvas.drawArc(Rect.fromCircle(center: at(Offset.zero), radius: r0 * scale), k * 3.14159265 / 36, 3.14159265 / 36, false, dash);
      }
    }
    void trail(List<Offset> pts, Color c) {
      if (pts.length < 2) return;
      final paint = Paint()
        ..color = c
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.8;
      // 주기 경계로 반대편에 다시 들어오면 선을 끊음
      var path = Path()..moveTo(at(pts.first).dx, at(pts.first).dy);
      for (var i = 1; i < pts.length; i++) {
        final o = at(pts[i]);
        if ((pts[i] - pts[i - 1]).distance > viewHalf) {
          canvas.drawPath(path, paint);
          path = Path()..moveTo(o.dx, o.dy);
        } else {
          path.lineTo(o.dx, o.dy);
        }
      }
      canvas.drawPath(path, paint);
    }

    trail(trail1, cs.error);
    trail(trail2, cs.primary);
  }

  @override
  bool shouldRepaint(covariant OrbitPainter old) => true;
}
