import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../physics/relabel_1d.dart';

/// 1D 격자 그리기: 시계 속도 띠(배경), 위 줄 시계 A·B의 제자리 떨림, 아래 줄 B → C 신호, 맨 아래 노드(이름표) 위치.
class MembranePainter extends CustomPainter {
  final LiveExperiment exp;
  final ColorScheme cs;
  MembranePainter(this.exp, this.cs);

  static const double xMin = -28, xMax = 28;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    double px(double x) => (x - xMin) / (xMax - xMin) * w;
    final laneH = h * 0.36, top1 = h * 0.04, top2 = top1 + laneH + h * 0.04, nodeY = h * 0.92;

    // 배경: 시계 속도 N(x) (느릴수록 진하게)
    final nMin = background(0).n;
    const bands = 64;
    final colors = <Color>[], stops = <double>[];
    for (var i = 0; i <= bands; i++) {
      final slow = (1 - background(xMin + (xMax - xMin) * i / bands).n) / (1 - nMin);
      colors.add(cs.primary.withValues(alpha: 0.03 + 0.17 * slow));
      stops.add(i / bands);
    }
    final bg = Rect.fromLTRB(0, 0, w, nodeY - 10);
    canvas.drawRect(bg, Paint()..shader = LinearGradient(colors: colors, stops: stops).createShader(bg));

    final label = TextStyle(color: cs.onSurfaceVariant, fontSize: 11);
    void text(String s, Offset at, {TextStyle? style, bool center = false}) {
      final tp = TextPainter(text: TextSpan(text: s, style: style ?? label), textDirection: TextDirection.ltr)..layout();
      tp.paint(canvas, center ? at - Offset(tp.width / 2, 0) : at);
    }

    // 두 줄: 위는 시계 A + B, 아래는 신호
    void lane(double top, List<double> Function(int) value, Color color, String name) {
      final mid = top + laneH / 2, amp = laneH * 0.42;
      canvas.drawLine(Offset(0, mid), Offset(w, mid), Paint()..color = cs.outlineVariant);
      final path = Path();
      var first = true;
      final g = exp.grid;
      for (var i = 0; i < g.nodes; i++) {
        final x = g.x[i];
        if (x < xMin || x > xMax) continue;
        final y = mid - value(i).fold(0.0, (a, b) => a + b) * amp;
        if (first) {
          path.moveTo(px(x), y);
          first = false;
        } else {
          path.lineTo(px(x), y);
        }
      }
      canvas.drawPath(path, Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.6);
      text(name, Offset(6, top + 2));
    }

    lane(top1, (i) => [exp.clockA.u[i], exp.clockB.u[i]], cs.primary, '시계 A, B (제자리 떨림)');
    lane(top2, (i) => [exp.signal.u[i]], cs.tertiary, '신호 B → C');

    // 관측 지점
    for (final (x, name) in [(xA, 'A'), (xB, 'B'), (xC, 'C')]) {
      final p = Paint()
        ..color = cs.onSurface.withValues(alpha: 0.5)
        ..strokeWidth = 1;
      for (var y = top1; y < nodeY - 14; y += 6) {
        canvas.drawLine(Offset(px(x), y), Offset(px(x), y + 3), p);
      }
      text(name, Offset(px(x), nodeY - 26), style: label.copyWith(fontWeight: FontWeight.bold), center: true);
    }

    // 노드(이름표) 위치: 화면 안 노드를 약 70개로 솎아서
    final g = exp.grid;
    final inView = [for (var i = 0; i < g.nodes; i++) if (g.x[i] >= xMin && g.x[i] <= xMax) i];
    final every = math.max(1, inView.length ~/ 70);
    final np = Paint()
      ..color = cs.onSurface
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, nodeY), Offset(w, nodeY), Paint()..color = cs.outline);
    for (var j = 0; j < inView.length; j += every) {
      final x = px(g.x[inView[j]]);
      canvas.drawLine(Offset(x, nodeY - 5), Offset(x, nodeY + 5), np);
    }
    text('노드 위치 ($every개마다 하나) · 배경이 진할수록 시계가 느림', Offset(6, nodeY + 6));
  }

  @override
  bool shouldRepaint(covariant MembranePainter old) => true;
}
