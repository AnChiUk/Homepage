/// 동역학 2-a 자유 중력파 재생 데이터. 원본: time-grid/gw_free_dynamics.py → viz_data/gw_free_{plus,cross}.json
/// (3D 96³ 격자 계산이라 앱에서는 저장된 장면을 재생한다)
///   slice: xz 단면의 막 변형 성분 (+ 편광이면 ½(h_xx − h_yy), × 편광이면 h_xy), 진폭 1로 나눈 값, 32×32
///   ring:  xy 평면 고리 표지 16개까지 틱으로 잰 거리의 변화 (반지름 6 기준)
library;

class GwFrame {
  final double t, zPeak;
  final List<List<double>> slice;
  final List<double> ring;
  const GwFrame(this.t, this.zPeak, this.slice, this.ring);
}

class GwPlayback {
  final String pol;
  final int grid;
  final double ringRadius, speed, dtFrame;
  final List<double> ringAngles;
  final List<GwFrame> frames;
  const GwPlayback(this.pol, this.grid, this.ringRadius, this.speed, this.dtFrame, this.ringAngles, this.frames);

  factory GwPlayback.fromJson(Map<String, dynamic> j) => GwPlayback(
        j['pol'] as String,
        j['grid'] as int,
        (j['ring_radius'] as num).toDouble(),
        (j['speed'] as num).toDouble(),
        (j['dt_frame'] as num).toDouble(),
        [for (final a in j['ring_angles'] as List) (a as num).toDouble()],
        [
          for (final f in (j['frames'] as List).cast<Map<String, dynamic>>())
            GwFrame(
              (f['t'] as num).toDouble(),
              (f['z_peak'] as num).toDouble(),
              [
                for (final r in f['slice'] as List) [for (final v in r as List) (v as num).toDouble()]
              ],
              [for (final v in f['ring'] as List) (v as num).toDouble()],
            ),
        ],
      );

  double get tEnd => frames.last.t;

  /// 시각 t 의 고리 (앞뒤 장면 선형 보간)
  List<double> ringAt(double t) {
    final (i, w) = _locate(t);
    final a = frames[i].ring, b = frames[i + 1 < frames.length ? i + 1 : i].ring;
    return [for (var k = 0; k < a.length; k++) a[k] * (1 - w) + b[k] * w];
  }

  List<List<double>> sliceAt(double t) {
    final (i, w) = _locate(t);
    final a = frames[i].slice, b = frames[i + 1 < frames.length ? i + 1 : i].slice;
    return [
      for (var r = 0; r < a.length; r++) [for (var c = 0; c < a[r].length; c++) a[r][c] * (1 - w) + b[r][c] * w]
    ];
  }

  (int, double) _locate(double t) {
    final x = (t / dtFrame).clamp(0.0, (frames.length - 1).toDouble());
    final i = x.floor().clamp(0, frames.length - 1);
    return (i, x - i);
  }
}
