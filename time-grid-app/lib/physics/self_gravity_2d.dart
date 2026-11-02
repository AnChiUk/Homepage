/// 동역학 2-c (느린 극한): 저장 파동 덩어리의 자기 묶임과 서로 끌림. 원본: time-grid/self_gravity_slow.py
///
/// 같은 격자 규칙에서 느린 움직임만 남기면 u = Re[φ e^{−iμt}] 의 포락선 φ 가 따르는 방정식:
///     i ∂_t φ = −(1/2μ) Δ_격자 φ + μ Φ φ
///     Φ(x) = −G ∫ ρ(x') d²x' / |x − x'|,   ρ = ½ μ² |φ|²   (평면 위 물질, 3D 방식 1/r)
/// G = 1/32π (규칙 값). 분할 단계 방법이라 질량이 정확히 보존된다.
library;

import 'dart:math' as math;
import 'dart:typed_data';

import 'fft.dart';

class SlowGravityParams {
  final double a, mu, g, dt, dtau, gm, r0;
  final int ng, groundSteps;
  const SlowGravityParams({
    required this.a,
    required this.ng,
    required this.dt,
    required this.dtau,
    required this.groundSteps,
    this.mu = 3.0,
    this.g = 1 / (32 * math.pi),
    this.gm = 0.1,
    this.r0 = 6.0,
  });

  /// 원본과 같은 설정 (256², 간격 0.25, dt 0.1, 바닥 상태 1500 × 0.05)
  static const original = SlowGravityParams(a: 0.25, ng: 256, dt: 0.1, dtau: 0.05, groundSteps: 1500);

  /// 화면용: 같은 영역(한 변 64), 간격 2배, dt 1.0, 바닥 상태 375 × 0.2 (같은 허수 시간 75).
  /// Python 으로 dt 1.0 / 0.5 / 0.25 의 궤도가 같음을 확인 (회전 493°, 최소 거리 10.52; 원본 256² 는 486°, 10.90)
  static const small = SlowGravityParams(a: 0.5, ng: 128, dt: 1.0, dtau: 0.2, groundSteps: 375);

  double get mass => gm / g;
  double get orbitSpeed => math.sqrt(gm / (4 * r0)); // 점질량 원 궤도 속도 (평면, 1/r)
  double get keplerPeriod => 2 * math.pi * r0 / orbitSpeed;
  double coord(int i) => (i - ng ~/ 2) * a;
}

/// 복소 격자장 φ (re, im), [i*ng + j], i = x, j = y
class Field {
  final Float64List re, im;
  Field(int size)
      : re = Float64List(size),
        im = Float64List(size);
  Field.copy(Field f)
      : re = Float64List.fromList(f.re),
        im = Float64List.fromList(f.im);
}

class SlowGravity {
  final SlowGravityParams p;
  final int ng, pad;
  final Fft _fft, _fftPad;
  final Map<(double, double), (Float64List, Float64List)> _kinCache = {};
  late final Float64List lap, _kerRe, _kerIm, _padRe, _padIm, _qx, _qy;

  SlowGravity(this.p)
      : ng = p.ng,
        pad = 2 * p.ng,
        _fft = Fft(p.ng),
        _fftPad = Fft(2 * p.ng) {
    final n = ng, a = p.a;
    _qx = Float64List(n * n);
    _qy = Float64List(n * n);
    lap = Float64List(n * n);
    double freq(int i) => 2 * math.pi * (i < n ~/ 2 ? i : i - n) / (n * a); // numpy fftfreq
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        final qx = freq(i), qy = freq(j), idx = i * n + j;
        _qx[idx] = qx;
        _qy[idx] = qy;
        lap[idx] = -(2 * (1 - math.cos(qx * a)) + 2 * (1 - math.cos(qy * a))) / (a * a);
      }
    }
    // 1/r 핵 (원점은 칸 평균 2·1.7627/a), ifftshift 한 배치 그대로
    final pp = pad;
    _kerRe = Float64List(pp * pp);
    _kerIm = Float64List(pp * pp);
    for (var i = 0; i < pp; i++) {
      final x = (i < pp ~/ 2 ? i : i - pp) * a;
      for (var j = 0; j < pp; j++) {
        final y = (j < pp ~/ 2 ? j : j - pp) * a;
        final r = math.sqrt(x * x + y * y);
        _kerRe[i * pp + j] = r > 0 ? 1 / r : 2 * 1.7627 / a;
      }
    }
    _fftPad.transform2d(_kerRe, _kerIm, false);
    _padRe = Float64List(pp * pp);
    _padIm = Float64List(pp * pp);
  }

  double rhoAt(Field f, int idx) => 0.5 * p.mu * p.mu * (f.re[idx] * f.re[idx] + f.im[idx] * f.im[idx]);

  double massOf(Field f) {
    var s = 0.0;
    for (var i = 0; i < ng * ng; i++) {
      s += rhoAt(f, i);
    }
    return s * p.a * p.a;
  }

  /// 두 밀도의 시계 몫 Φ 를 한 번의 복소 FFT 로 (실수 핵이므로 실수부·허수부가 각자의 합성곱)
  void potentials(Field f1, Field? f2, Float64List out1, Float64List? out2) {
    final n = ng, pp = pad;
    _padRe.fillRange(0, pp * pp, 0);
    _padIm.fillRange(0, pp * pp, 0);
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        _padRe[i * pp + j] = rhoAt(f1, i * n + j);
        if (f2 != null) _padIm[i * pp + j] = rhoAt(f2, i * n + j);
      }
    }
    _fftPad.transform2d(_padRe, _padIm, false, rows: n); // 아래쪽 행은 0
    for (var k = 0; k < pp * pp; k++) {
      final r = _padRe[k], im = _padIm[k], kr = _kerRe[k], ki = _kerIm[k];
      _padRe[k] = r * kr - im * ki;
      _padIm[k] = r * ki + im * kr;
    }
    // 역변환: 행 먼저, 열은 필요한 앞쪽 n 열만
    for (var i = 0; i < pp; i++) {
      _fftPad.transform(_padRe, _padIm, i * pp, 1, true);
    }
    for (var j = 0; j < n; j++) {
      _fftPad.transform(_padRe, _padIm, j, pp, true);
    }
    final s = -p.g * p.a * p.a;
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        out1[i * n + j] = s * _padRe[i * pp + j];
        if (out2 != null) out2[i * n + j] = s * _padIm[i * pp + j];
      }
    }
  }

  /// φ ← F⁻¹[F[φ] · e^{c·lap}] (c 가 실수면 허수 시간, 허수면 실제 시간)
  void kinetic(Field f, {double realCoef = 0, double imagCoef = 0}) {
    final (cre, cim) = _kinCache.putIfAbsent((realCoef, imagCoef), () {
      final cr = Float64List(ng * ng), ci = Float64List(ng * ng);
      for (var k = 0; k < ng * ng; k++) {
        final mag = math.exp(realCoef * lap[k]), ang = imagCoef * lap[k];
        cr[k] = mag * math.cos(ang);
        ci[k] = mag * math.sin(ang);
      }
      return (cr, ci);
    });
    _fft.transform2d(f.re, f.im, false);
    for (var k = 0; k < ng * ng; k++) {
      final cr = cre[k], ci = cim[k];
      final r = f.re[k], im = f.im[k];
      f.re[k] = r * cr - im * ci;
      f.im[k] = r * ci + im * cr;
    }
    _fft.transform2d(f.re, f.im, true);
  }

  /// φ ← φ · e^{−i·s·V} (s = 0.5·dt·μ)
  static void phase(Field f, Float64List v, double s) {
    for (var k = 0; k < v.length; k++) {
      final ang = -s * v[k], c = math.cos(ang), sn = math.sin(ang);
      final r = f.re[k], im = f.im[k];
      f.re[k] = r * c - im * sn;
      f.im[k] = r * sn + im * c;
    }
  }

  /// 처음 모양: 폭 2 의 가우스, 질량 M
  Field initialBlob() {
    final f = Field(ng * ng);
    for (var i = 0; i < ng; i++) {
      final x = p.coord(i);
      for (var j = 0; j < ng; j++) {
        final y = p.coord(j);
        f.re[i * ng + j] = math.exp(-(x * x + y * y) / (2 * 2.0 * 2.0));
      }
    }
    normalize(f);
    return f;
  }

  void normalize(Field f) {
    final s = math.sqrt(p.mass / massOf(f));
    for (var k = 0; k < ng * ng; k++) {
      f.re[k] *= s;
      f.im[k] *= s;
    }
  }

  /// 허수 시간 한 단계 (바닥 상태 = 스스로 묶인 모양 찾기)
  void groundStep(Field f, Float64List phiBuf) {
    potentials(f, null, phiBuf, null);
    final h = 0.5 * p.dtau * p.mu;
    for (var k = 0; k < ng * ng; k++) {
      final e = math.exp(-h * phiBuf[k]);
      f.re[k] *= e;
      f.im[k] *= e;
    }
    kinetic(f, realCoef: p.dtau / (2 * p.mu));
    for (var k = 0; k < ng * ng; k++) {
      final e = math.exp(-h * phiBuf[k]);
      f.re[k] *= e;
      f.im[k] *= e;
    }
    normalize(f);
  }

  /// 덩어리를 (dx, dy) 로 옮기고 속도 (vx, vy) 를 줌 (위상 기울기 μv)
  Field shifted(Field f, double dx, double dy, double vx, double vy) {
    final g = Field.copy(f);
    _fft.transform2d(g.re, g.im, false);
    for (var k = 0; k < ng * ng; k++) {
      final ang = -(_qx[k] * dx + _qy[k] * dy), c = math.cos(ang), s = math.sin(ang);
      final r = g.re[k], im = g.im[k];
      g.re[k] = r * c - im * s;
      g.im[k] = r * s + im * c;
    }
    _fft.transform2d(g.re, g.im, true);
    for (var i = 0; i < ng; i++) {
      final x = p.coord(i);
      for (var j = 0; j < ng; j++) {
        final y = p.coord(j), k = i * ng + j;
        final ang = p.mu * (vx * x + vy * y), c = math.cos(ang), s = math.sin(ang);
        final r = g.re[k], im = g.im[k];
        g.re[k] = r * c - im * s;
        g.im[k] = r * s + im * c;
      }
    }
    return g;
  }

  /// 밀도 가중 중심과 폭
  ({double x, double y, double width}) moments(Field f) {
    var w = 0.0, sx = 0.0, sy = 0.0;
    for (var i = 0; i < ng; i++) {
      final x = p.coord(i);
      for (var j = 0; j < ng; j++) {
        final r = rhoAt(f, i * ng + j);
        w += r;
        sx += r * x;
        sy += r * p.coord(j);
      }
    }
    final cx = sx / w, cy = sy / w;
    var s2 = 0.0;
    for (var i = 0; i < ng; i++) {
      final dx = p.coord(i) - cx;
      for (var j = 0; j < ng; j++) {
        final dy = p.coord(j) - cy;
        s2 += rhoAt(f, i * ng + j) * (dx * dx + dy * dy);
      }
    }
    return (x: cx, y: cy, width: math.sqrt(s2 / w));
  }
}

/// 바닥 상태 찾기를 단계별로 (화면에서 진행 표시)
class GroundStateSolver {
  final SlowGravity sim;
  final Field phi;
  final Float64List _buf;
  int n = 0;
  GroundStateSolver(this.sim)
      : phi = sim.initialBlob(),
        _buf = Float64List(sim.ng * sim.ng);

  bool get done => n >= sim.p.groundSteps;

  void advance(int steps) {
    for (var s = 0; s < steps && !done; s++) {
      sim.groundStep(phi, _buf);
      n++;
    }
  }

  /// 바닥 상태 중심의 시계 몫 (가장 깊은 Φ)
  double phiMin() {
    final buf = Float64List(sim.ng * sim.ng);
    sim.potentials(phi, null, buf, null);
    return buf.reduce(math.min);
  }
}

/// 두 덩어리 궤도. mutual = false 면 각 덩어리가 자기 장만 느낌 (대조)
class Binary {
  final SlowGravity sim;
  final bool mutual;
  Field f1, f2;
  final Float64List pot1, pot2, total;
  int n = 0;

  Binary(this.sim, Field ground, {required this.mutual})
      : f1 = sim.shifted(ground, sim.p.r0, 0, 0, sim.p.orbitSpeed),
        f2 = sim.shifted(ground, -sim.p.r0, 0, 0, -sim.p.orbitSpeed),
        pot1 = Float64List(sim.ng * sim.ng),
        pot2 = Float64List(sim.ng * sim.ng),
        total = Float64List(sim.ng * sim.ng) {
    _updatePotentials();
  }

  double get time => n * sim.p.dt;

  void _updatePotentials() {
    sim.potentials(f1, f2, pot1, pot2);
    for (var k = 0; k < total.length; k++) {
      total[k] = pot1[k] + pot2[k];
    }
  }

  void advance(int steps) {
    final s = 0.5 * sim.p.dt * sim.p.mu, kc = sim.p.dt / (2 * sim.p.mu);
    for (var st = 0; st < steps; st++) {
      SlowGravity.phase(f1, mutual ? total : pot1, s);
      SlowGravity.phase(f2, mutual ? total : pot2, s);
      sim.kinetic(f1, imagCoef: kc);
      sim.kinetic(f2, imagCoef: kc);
      _updatePotentials();
      SlowGravity.phase(f1, mutual ? total : pot1, s);
      SlowGravity.phase(f2, mutual ? total : pot2, s);
      n++;
    }
  }

  ({double x, double y, double width}) blob1() => sim.moments(f1);
  ({double x, double y, double width}) blob2() => sim.moments(f2);
}
