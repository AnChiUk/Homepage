// 시험 1 Dart 변환 확인: Python(time-grid/relabel_test_1d.py)이 낸 기준값과 비교.
// 기준값은 tool/make_reference.py 가 만든 test/reference/relabel_1d.json.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:time_grid_app/physics/relabel_1d.dart';

Mapping mappingOf(String name) => switch (name) {
      'uniform' => Mapping.uniform(),
      'sine' => Mapping.sine(0.5),
      'sinh' => Mapping.sinh(10.0),
      _ => throw ArgumentError(name),
    };

void main() {
  final ref = jsonDecode(File('test/reference/relabel_1d.json').readAsStringSync()) as Map<String, dynamic>;

  test('예측 시계비 N_A/N_B', () {
    expect(predictedO1, closeTo(ref['predicted_O1'] as double, 1e-12));
  });

  for (final c in (ref['cases'] as List).cast<Map<String, dynamic>>()) {
    final label = '${c['mapping']} h=${c['h']} dt=${c['dt_frac']}${c['naive'] == true ? ' (변환 안 함)' : ''}';
    test(label, () {
      final g = Grid.build(mappingOf(c['mapping'] as String), c['h'] as double, naive: c['naive'] as bool);
      final r = measure(g, c['dt_frac'] as double);
      expect(r.nodes, c['nodes']);
      expect(r.hops, c['hops']);
      expect(r.dt, closeTo(c['dt'] as double, 1e-12));
      // 같은 알고리즘이므로 반올림 오차 수준(상대 1e-9)까지 같아야 함
      expect(r.fB / (c['fB'] as double), closeTo(1, 1e-9));
      expect(r.o1 / (c['O1'] as double), closeTo(1, 1e-9));
      expect(r.o2 / (c['O2'] as double), closeTo(1, 1e-9));
    });
  }

  test('화면용 LiveExperiment 를 끝까지 돌린 값 = measure', () {
    final g = Grid.build(Mapping.sine(0.5), 0.05);
    final live = LiveExperiment(g);
    while (!live.done) {
      live.advance(97);
    }
    final a = live.result(), b = measure(g, 0.5);
    expect(a.o1, b.o1);
    expect(a.o2, b.o2);
    expect(a.fB, b.fB);
  });

  test('이름표를 바꿔도 시계비는 같고(0.02% 안), 변환하지 않으면 달라짐', () {
    final cases = (ref['cases'] as List).cast<Map<String, dynamic>>();
    final base = cases.first['O1'] as double;
    for (final c in cases.where((c) => c['naive'] == false && c['h'] != 0.1 && c['dt_frac'] == 0.5)) {
      expect((c['O1'] as double) / base, closeTo(1, 2e-4));
    }
    final naive = cases.firstWhere((c) => c['naive'] == true);
    expect((naive['O1'] as double) / base - 1, greaterThan(0.01));
  });
}
