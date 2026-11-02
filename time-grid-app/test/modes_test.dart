// 텐서 2단계 Dart 변환 확인: Python(time-grid/mode_count_test.py)이 낸 기준값과 비교.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:time_grid_app/physics/modes.dart';

void main() {
  final ref = jsonDecode(File('test/reference/modes.json').readAsStringSync()) as Map<String, dynamic>;
  for (final c in (ref['cases'] as List).cast<Map<String, dynamic>>()) {
    test('${c['candidate']} ${c['label']}', () {
      final cand = c['candidate'] == 'C1' ? Candidate.c1 : Candidate.c3;
      final q = (c['q'] as List).cast<double>();
      final m = analyze(cand, q);
      final speeds = (c['speeds'] as List).cast<double>();
      expect(m.speeds.length, speeds.length);
      for (var i = 0; i < speeds.length; i++) {
        expect(m.speeds[i], closeTo(speeds[i], 1e-10));
      }
      expect(m.gauge, c['gauge']);
      expect(m.staticModes, c['static']);
      // ω² 전부 (0 근처는 절대 오차로)
      final w2 = (c['w2'] as List).cast<double>();
      for (var i = 0; i < 6; i++) {
        expect(m.w2[i], closeTo(w2[i], 1e-7 * (q[0] * q[0] + q[1] * q[1] + q[2] * q[2])));
      }
      if (cand == Candidate.c3) {
        expect(m.oscillating, 2);
        expect(m.constraint, 1);
      }
    });
  }
}
