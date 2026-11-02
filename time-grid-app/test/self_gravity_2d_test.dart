// 동역학 2-c Dart 변환 확인: Python(time-grid/self_gravity_slow.py)이 낸 기준값과 비교.
// 기준값은 tool/make_reference.py 가 만든 test/reference/self_gravity{,_small}.json.
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:time_grid_app/physics/fft.dart';
import 'package:time_grid_app/physics/self_gravity_2d.dart';

void checkFile(String path, SlowGravityParams p) {
  final file = File(path);
  if (!file.existsSync()) return;
  final ref = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  group('${p.ng}² 간격 ${p.a}', () {
    late SlowGravity sim;
    late GroundStateSolver gs;

    setUpAll(() {
      sim = SlowGravity(p);
      gs = GroundStateSolver(sim);
      while (!gs.done) {
        gs.advance(50);
      }
    });

    test('설정이 원본과 같음', () {
      expect(p.a, ref['a']);
      expect(p.ng, ref['ng']);
      expect(p.mu, ref['mu']);
      expect(p.g, closeTo(ref['G'] as double, 1e-17));
      expect(p.dt, ref['dt']);
      expect(p.dtau, ref['dtau']);
      expect(p.groundSteps, ref['ground_steps']);
      expect(p.orbitSpeed, closeTo(ref['v'] as double, 1e-15));
    });

    test('바닥 상태: 폭과 가운데 시계 몫', () {
      expect(sim.moments(gs.phi).width, closeTo(ref['ground_width'] as double, 1e-9));
      expect(gs.phiMin(), closeTo(ref['ground_phi_min'] as double, 1e-11));
    });

    for (final mode in ['mutual', 'off']) {
      test('두 덩어리 궤도 ($mode): 중심 위치가 매 기록마다 같음', () {
        final b = Binary(sim, gs.phi, mutual: mode == 'mutual');
        for (final rec in (ref['runs'][mode] as List).cast<Map<String, dynamic>>()) {
          b.advance((rec['n'] as int) - b.n);
          final centers = (rec['centers'] as List).cast<List>();
          final c1 = b.blob1(), c2 = b.blob2();
          expect(c1.x, closeTo(centers[0][0] as double, 1e-7), reason: 't = ${b.time}');
          expect(c1.y, closeTo(centers[0][1] as double, 1e-7), reason: 't = ${b.time}');
          expect(c2.x, closeTo(centers[1][0] as double, 1e-7), reason: 't = ${b.time}');
          expect(c2.y, closeTo(centers[1][1] as double, 1e-7), reason: 't = ${b.time}');
        }
      }, timeout: const Timeout(Duration(minutes: 20)));
    }
  });
}

void main() {
  test('FFT: 앞뒤 변환이 원래로 돌아오고, 한 점의 변환이 해석값과 같음', () {
    final f = Fft(16);
    final re = Float64List(16), im = Float64List(16);
    re[3] = 1;
    f.transform(re, im, 0, 1, false);
    for (var k = 0; k < 16; k++) {
      expect(re[k], closeTo(math.cos(2 * math.pi * 3 * k / 16), 1e-15));
      expect(im[k], closeTo(-math.sin(2 * math.pi * 3 * k / 16), 1e-15));
    }
    f.transform(re, im, 0, 1, true);
    for (var k = 0; k < 16; k++) {
      expect(re[k], closeTo(k == 3 ? 1 : 0, 1e-15));
      expect(im[k], closeTo(0, 1e-15));
    }
  });
  checkFile('test/reference/self_gravity_small.json', SlowGravityParams.small);
  checkFile('test/reference/self_gravity.json', SlowGravityParams.original);
}
