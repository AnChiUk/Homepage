import 'package:flutter/material.dart';

/// 앱에서 잰 한 점
class AppPoint {
  final double gamma, q, v, theta, normalized;
  const AppPoint(this.gamma, this.q, this.v, this.theta, this.normalized);
}

/// 원본 Python(768² 격자)의 결과: (γ, v, θv²/(2GM/b)). 출처: test/reference/deflection_2d.json
const pythonFullSize = <(double, double, double)>[
  (1, 0.4468, 1.1736),
  (1, 0.7045, 1.4888),
  (1, 0.8822, 1.7493),
  (1, 0.9206, 1.8411),
  (0, 0.4468, 0.9435),
  (0, 0.7045, 0.9738),
  (0, 0.8822, 0.9590),
  (0, 0.9206, 0.9571),
];

/// 가로 v², 세로 θv²/(2GM/b). 예측선: 규칙 1 + v², 대조 1.
class DeflectionChart extends StatelessWidget {
  final List<AppPoint> points;
  const DeflectionChart({super.key, required this.points});

  @override
  Widget build(BuildContext context) => CustomPaint(painter: _ChartPainter(points, Theme.of(context)));
}

class _ChartPainter extends CustomPainter {
  final List<AppPoint> points;
  final ThemeData t;
  _ChartPainter(this.points, this.t);

  static const yMin = 0.8, yMax = 2.1;

  @override
  void paint(Canvas canvas, Size size) {
    final cs = t.colorScheme;
    const left = 44.0, bottom = 34.0, top = 8.0, right = 8.0;
    final w = size.width - left - right, h = size.height - top - bottom;
    Offset at(double v2, double y) => Offset(left + v2 * w, top + (yMax - y) / (yMax - yMin) * h);
    final style = TextStyle(color: cs.onSurfaceVariant, fontSize: 11);
    void text(String s, Offset o, {bool right = false, bool center = false}) {
      final tp = TextPainter(text: TextSpan(text: s, style: style), textDirection: TextDirection.ltr)..layout();
      tp.paint(canvas, o - Offset(right ? tp.width : (center ? tp.width / 2 : 0), tp.height / 2));
    }

    final grid = Paint()..color = cs.outlineVariant;
    for (var y = 1.0; y <= 2.0; y += 0.5) {
      canvas.drawLine(at(0, y), at(1, y), grid);
      text(y.toStringAsFixed(1), at(0, y) - const Offset(6, 0), right: true);
    }
    for (var x = 0.0; x <= 1.0; x += 0.25) {
      canvas.drawLine(at(x, yMin), at(x, yMin) + const Offset(0, 4), grid);
      text(x.toStringAsFixed(2), at(x, yMin) + const Offset(0, 12), center: true);
    }
    canvas.drawLine(at(0, yMin), at(1, yMin), Paint()..color = cs.outline);
    text('v² (빛 = 1)', Offset(left + w / 2, size.height - 6), center: true);

    final rule = cs.primary, control = cs.tertiary;
    final pred = Paint()..strokeWidth = 1.2;
    canvas.drawLine(at(0, 1), at(1, 2), pred..color = rule.withValues(alpha: 0.7));
    canvas.drawLine(at(0, 1), at(1, 1), pred..color = control.withValues(alpha: 0.7));
    text('예측 1 + v² (γ = 1)', at(0.55, 1.55) + const Offset(-8, -12), right: true);
    text('예측 1 (γ = 0)', at(0.3, 1) + const Offset(0, -10));

    for (final (g, v, y) in pythonFullSize) {
      canvas.drawCircle(at(v * v, y), 5, Paint()
        ..color = g == 1 ? rule : control
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5);
    }
    for (final p in points) {
      canvas.drawCircle(at(p.v * p.v, p.normalized), 4.5, Paint()..color = p.gamma == 1 ? rule : control);
    }
    // 범례
    final lx = left + 8, ly = at(0, 1.95).dy;
    canvas.drawCircle(Offset(lx, ly), 4.5, Paint()..color = cs.onSurfaceVariant);
    text('이 앱 (256²)', Offset(lx + 10, ly));
    canvas.drawCircle(Offset(lx, ly + 16), 5, Paint()
      ..color = cs.onSurfaceVariant
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5);
    text('원본 Python (768²)', Offset(lx + 10, ly + 16));
    text('세로: θv² / (2GM/b)', Offset(lx, ly + 32));
  }

  @override
  bool shouldRepaint(covariant _ChartPainter old) => true;
}
