// 중력파 재생 데이터가 원본(time-grid/viz_data)과 같고 앱이 읽을 수 있는지 확인.
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter_test/flutter_test.dart';
import 'package:time_grid_app/physics/gw_playback.dart';

void main() {
  for (final pol in ['plus', 'cross']) {
    test('$pol: 원본과 같은 파일, 49 장면, 고리 16개', () {
      final app = File('assets/viz_data/gw_free_$pol.json').readAsStringSync();
      expect(app, File('../time-grid/viz_data/gw_free_$pol.json').readAsStringSync());
      final g = GwPlayback.fromJson(jsonDecode(app) as Map<String, dynamic>);
      expect(g.pol, pol);
      expect(g.frames.length, 49);
      expect(g.ringAngles.length, 16);
      expect(g.frames.every((f) => f.ring.length == 16 && f.slice.length == 32), isTrue);
      // 고리 찌그러짐이 편광 모양을 따름: + 는 cos2θ, × 는 sin2θ 성분이 출렁임
      double comp(List<double> r, bool cos) {
        var s = 0.0;
        for (var k = 0; k < 16; k++) {
          s += r[k] * (cos ? math.cos(2 * g.ringAngles[k]) : math.sin(2 * g.ringAngles[k]));
        }
        return s * 2 / 16;
      }
      final r0 = g.frames.first.ring;
      double swing(bool cos) => g.frames.map((f) => (comp(f.ring, cos) - comp(r0, cos)).abs()).reduce(math.max);
      final main = swing(pol == 'plus'), other = swing(pol != 'plus');
      expect(main, greaterThan(20 * other));
      // 보간: 장면 시각에서는 그 장면 그대로
      expect(g.ringAt(g.frames[10].t), g.frames[10].ring);
    });
  }
}
