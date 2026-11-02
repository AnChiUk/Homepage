// 동역학 1 Dart 변환 확인: Python(time-grid/deflection_dynamics.py)이 낸 기준값과 비교.
// 기준값은 tool/make_reference.py 가 만든 test/reference/deflection_2d{,_small}.json.
// 원본 크기(768²)는 경우마다 수십 초 걸린다.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:time_grid_app/physics/deflection_2d.dart';

void checkFile(String path) {
  final file = File(path);
  if (!file.existsSync()) return;
  final ref = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  final p = DeflectionParams(a: ref['a'] as double, ng: ref['ng'] as int);
  group('${p.ng}² 간격 ${p.a}', () {
    test('설정이 원본과 같음', () {
      expect(p.mu, ref['mu']);
      expect(p.rs, ref['rs']);
      expect(p.b, ref['b']);
      expect(p.gm, ref['gm']);
      expect(p.sig, ref['sig']);
      expect(p.z0, ref['z0']);
    });
    for (final c in (ref['cases'] as List).cast<Map<String, dynamic>>()) {
      final gamma = c['gamma'] as double, q = c['q'] as double;
      test('γ = ${gamma.toStringAsFixed(3)}, q = $q', () {
        final d = Deflection2D(p, gamma, q);
        expect(d.vg, closeTo(c['vg'] as double, 1e-13));
        while (!d.done) {
          d.advance(500);
        }
        expect(d.theta() / (c['theta'] as double), closeTo(1, 1e-8));
      }, timeout: const Timeout(Duration(minutes: 5)));
    }
  });
}

void main() {
  test('erf 가 scipy 와 같음', () {
    final ref = <double, double>{
      0.1: 0.1124629160182849,
      1.0: 0.8427007929497148,
      2.4: 0.999311486103355,
      2.6: 0.9997639655834707,
      4.0: 0.9999999845827421,
      6.0: 1.0,
    };
    ref.forEach((x, y) {
      expect(erf(x), closeTo(y, 1e-15));
      expect(erf(-x), closeTo(-y, 1e-15));
    });
  });
  checkFile('test/reference/deflection_2d_small.json');
  checkFile('test/reference/deflection_2d.json');
}
