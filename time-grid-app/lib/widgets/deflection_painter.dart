import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import '../physics/deflection_2d.dart';

/// 2D 격자 그림(시계 지도 + 파속) 위에 덩어리, 휘지 않은 직선, 파속 궤적을 그림. 가로 = 진행 방향 z, 세로 = 휨 방향 x(위가 +).
class DeflectionPainter extends CustomPainter {
  final ui.Image? image;
  final List<Offset> trail; // (z, x)
  final DeflectionParams p;
  final ColorScheme cs;
  DeflectionPainter(this.image, this.trail, this.p, this.cs);

  @override
  void paint(Canvas canvas, Size size) {
    final half = p.length / 2;
    Offset at(double z, double x) => Offset((z + half) / p.length * size.width, (half - x) / p.length * size.height);
    final rect = Offset.zero & size;
    canvas.clipRect(rect);
    if (image != null) {
      paintImage(canvas: canvas, rect: rect, image: image!, fit: BoxFit.fill, filterQuality: FilterQuality.low);
    } else {
      canvas.drawRect(rect, Paint()..color = cs.surfaceContainerHighest);
    }
    final scale = size.width / p.length;

    // 덩어리 (반지름 RS)
    canvas.drawCircle(at(0, 0), p.rs * scale, Paint()
      ..color = cs.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2);
    // 휘지 않았을 때의 직선 (x = b)
    final dash = Paint()
      ..color = cs.onSurface.withValues(alpha: 0.6)
      ..strokeWidth = 1;
    for (var z = -half; z < half; z += 0.6) {
      canvas.drawLine(at(z, p.b), at(z + 0.3, p.b), dash);
    }
    // 파속 에너지 중심의 궤적
    if (trail.length > 1) {
      final path = Path()..moveTo(at(trail.first.dx, trail.first.dy).dx, at(trail.first.dx, trail.first.dy).dy);
      for (final t in trail.skip(1)) {
        final o = at(t.dx, t.dy);
        path.lineTo(o.dx, o.dy);
      }
      canvas.drawPath(path, Paint()
        ..color = cs.error
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2);
    }
    final tp = TextPainter(
      text: TextSpan(text: '덩어리', style: TextStyle(color: cs.onSurface, fontSize: 11)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, at(0, 0) + Offset(-tp.width / 2, p.rs * scale + 2));
  }

  @override
  bool shouldRepaint(covariant DeflectionPainter old) => true;
}
