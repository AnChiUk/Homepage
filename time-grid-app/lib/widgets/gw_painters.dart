import 'dart:math' as math;

import 'package:flutter/material.dart';

enum ModeKind { oscillating, gauge, fixed, constraint }

/// 모양 6가지를 칸 6개로: 종류별 색
class ModeCells extends StatelessWidget {
  final List<(ModeKind, String)> kinds;
  const ModeCells({super.key, required this.kinds});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    Color bg(ModeKind k) => switch (k) {
          ModeKind.oscillating => cs.primaryContainer,
          ModeKind.gauge => cs.surfaceContainerHighest,
          ModeKind.fixed => cs.secondaryContainer,
          ModeKind.constraint => cs.tertiaryContainer,
        };
    Color fg(ModeKind k) => switch (k) {
          ModeKind.oscillating => cs.onPrimaryContainer,
          ModeKind.gauge => cs.onSurfaceVariant,
          ModeKind.fixed => cs.onSecondaryContainer,
          ModeKind.constraint => cs.onTertiaryContainer,
        };
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        for (final (k, label) in kinds)
          Container(
            width: 112,
            height: 64,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: bg(k), borderRadius: BorderRadius.circular(10)),
            child: Text(label, textAlign: TextAlign.center, style: TextStyle(color: fg(k), fontSize: 12.5)),
          ),
      ],
    );
  }
}

/// xz 단면 (가로 z, 세로 x), 32×32, 발산 색
class SlicePainter extends CustomPainter {
  final List<List<double>> slice; // [x][z]
  final ColorScheme cs;
  SlicePainter(this.slice, this.cs);

  @override
  void paint(Canvas canvas, Size size) {
    final n = slice.length;
    final cw = size.width / n, ch = size.height / n;
    canvas.drawRect(Offset.zero & size, Paint()..color = cs.surfaceContainerLowest);
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        final v = (slice[i][j] / 1.0).clamp(-1.0, 1.0);
        if (v.abs() < 0.01) continue;
        final c = (v > 0 ? cs.primary : cs.error).withValues(alpha: math.sqrt(v.abs()) * 0.9);
        canvas.drawRect(Rect.fromLTWH(j * cw, (n - 1 - i) * ch, cw + 0.5, ch + 0.5), Paint()..color = c);
      }
    }
    // 고리 위치 z = 0 (격자 96 칸을 32 로 줄임: 가운데)
    final dash = Paint()
      ..color = cs.onSurface.withValues(alpha: 0.6)
      ..strokeWidth = 1;
    for (var y = 0.0; y < size.height; y += 8) {
      canvas.drawLine(Offset(size.width / 2, y), Offset(size.width / 2, y + 4), dash);
    }
    final tp = TextPainter(
      text: TextSpan(text: 'z →   (고리: z = 0)', style: TextStyle(color: cs.onSurfaceVariant, fontSize: 11)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, Offset(6, size.height - tp.height - 4));
  }

  @override
  bool shouldRepaint(covariant SlicePainter old) => true;
}

/// 고리 표지 16개: 흐린 점 = 처음 모양, 진한 점 = 지금 모양 (거리 변화 과장)
class RingPainter extends CustomPainter {
  final double radius, exaggerate;
  final List<double> angles, now, start;
  final ColorScheme cs;
  RingPainter({
    required this.radius,
    required this.angles,
    required this.now,
    required this.start,
    required this.exaggerate,
    required this.cs,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final c = size.center(Offset.zero);
    final scale = size.shortestSide * 0.36 / radius;
    canvas.drawCircle(c, radius * scale, Paint()
      ..color = cs.outlineVariant
      ..style = PaintingStyle.stroke);
    Offset at(int k, double dr) {
      final r = (radius + exaggerate * dr) * scale;
      return c + Offset(r * math.cos(angles[k]), -r * math.sin(angles[k]));
    }

    Path loop(List<double> d) {
      final p = Path()..moveTo(at(0, d[0]).dx, at(0, d[0]).dy);
      for (var k = 1; k < angles.length; k++) {
        p.lineTo(at(k, d[k]).dx, at(k, d[k]).dy);
      }
      return p..close();
    }

    canvas.drawPath(loop(start), Paint()
      ..color = cs.onSurfaceVariant.withValues(alpha: 0.35)
      ..style = PaintingStyle.stroke);
    canvas.drawPath(loop(now), Paint()
      ..color = cs.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6);
    for (var k = 0; k < angles.length; k++) {
      canvas.drawCircle(at(k, start[k]), 3, Paint()..color = cs.onSurfaceVariant.withValues(alpha: 0.35));
      canvas.drawCircle(at(k, now[k]), 4, Paint()..color = cs.primary);
    }
    final tp = TextPainter(
      text: TextSpan(text: 'x →   (고리 평면 xy, 파동은 지면을 뚫고 지나감)', style: TextStyle(color: cs.onSurfaceVariant, fontSize: 11)),
      textDirection: TextDirection.ltr,
    )..layout(maxWidth: size.width - 12);
    tp.paint(canvas, Offset(6, size.height - tp.height - 4));
  }

  @override
  bool shouldRepaint(covariant RingPainter old) => true;
}
