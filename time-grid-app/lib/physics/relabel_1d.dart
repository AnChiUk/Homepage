/// 시험 1: 이름표 바꾸기 (1D 결합 진동자). 원본: time-grid/relabel_test_1d.py
///
/// 격자 파동:  m u'' = d/dx(κ du/dx) − k u
/// 배경:       U(x) = U0 r0 / sqrt(x² + r0²),  N = e^{−U}, ψ = e^{U}
/// 1D 대응:    m = ψ/N, κ = N/ψ, k = Nψμ²   →  시계 진동수 ω = Nμ, 전달 속도 v = N/ψ
/// 좌표 바꾸기 x → ξ (J = dx/dξ):  m' = mJ,  κ' = κ/J,  k' = kJ
///
/// 관측량 (모두 틱 단위, 좌표값 아님)
///   O1 = 시계 A(우물 중심) 틱 / 시계 B(먼 곳) 틱           → 예측 N_A/N_B
///   O2 = 파속이 B(x = +20)에서 C(x = −20)까지 가는 동안 B 시계 틱 수
library;

import 'dart:math' as math;
import 'dart:typed_data';

const double u0Well = 0.3, r0Well = 2.0, mu = 5.0;
const double lHalf = 60.0, xA = 0.0, xB = 20.0, xC = -20.0;

/// 배경의 시계 몫 N과 공간 몫 ψ.
({double n, double psi}) background(double x) {
  final u = u0Well * r0Well / math.sqrt(x * x + r0Well * r0Well);
  return (n: math.exp(-u), psi: math.exp(u));
}

/// 물리 좌표 x에서의 격자 재료값 (m, κ, k).
({double m, double kap, double k}) paramsX(double x) {
  final b = background(x);
  return (m: b.psi / b.n, kap: b.n / b.psi, k: b.n * b.psi * mu * mu);
}

double _asinh(double x) => math.log(x + math.sqrt(x * x + 1));

double _sinh(double x) => 0.5 * (math.exp(x) - math.exp(-x));

double _cosh(double x) => 0.5 * (math.exp(x) + math.exp(-x));

/// 이름표(좌표) 사상 x(ξ), J(ξ) = dx/dξ, 역사상 ξ(x).
class Mapping {
  final String name;
  final double Function(double) f, jac, inv;
  const Mapping(this.name, this.f, this.jac, this.inv);

  static Mapping uniform() => Mapping('uniform', (s) => s, (s) => 1.0, (x) => x);

  /// x = ξ + ε(XB/π) sin(πξ/XB): x(0) = 0, x(±XB) = ±XB, x(±L) = ±L
  static Mapping sine(double eps) {
    double f(double s) => s + eps * xB / math.pi * math.sin(math.pi * s / xB);
    double jac(double s) => 1 + eps * math.cos(math.pi * s / xB);
    double inv(double x) {
      var s = x;
      for (var i = 0; i < 60; i++) {
        s = s - (f(s) - x) / jac(s);
      }
      return s;
    }

    return Mapping('sine', f, jac, inv);
  }

  static Mapping sinh(double lam) => Mapping(
      'sinh', (s) => lam * _sinh(s / lam), (s) => _cosh(s / lam), (x) => lam * _asinh(x / lam));
}

/// 격자: 노드의 이름표 ξ, 물리 위치 x, 재료값.
class Grid {
  final Float64List s, x, m, k, kap;
  final double hs;
  final Mapping mapping;
  final bool naive;
  Grid._(this.s, this.x, this.m, this.k, this.kap, this.hs, this.mapping, this.naive);

  int get nodes => s.length;

  /// naive = true: 노드는 옮기고 재료값은 변환하지 않음 (틀린 이름표 바꾸기, 대조군)
  factory Grid.build(Mapping mp, double h, {bool naive = false}) {
    final sEnd = mp.inv(lHalf);
    final count = (2 * sEnd / h).round() + 1;
    final s = Float64List(count);
    final step = 2 * sEnd / (count - 1);
    for (var i = 0; i < count; i++) {
      s[i] = -sEnd + i * step; // numpy linspace 와 같은 식 (끝점은 정확히 sEnd)
    }
    s[count - 1] = sEnd;
    final hs = s[1] - s[0];
    final x = Float64List(count), m = Float64List(count), k = Float64List(count);
    final kap = Float64List(count - 1);
    for (var i = 0; i < count; i++) {
      x[i] = mp.f(s[i]);
      final p = paramsX(x[i]);
      m[i] = naive ? p.m : p.m * mp.jac(s[i]);
      k[i] = naive ? p.k : p.k * mp.jac(s[i]);
    }
    for (var i = 0; i < count - 1; i++) {
      final sl = 0.5 * (s[i + 1] + s[i]);
      final p = paramsX(mp.f(sl));
      kap[i] = naive ? p.kap : p.kap / mp.jac(sl);
    }
    return Grid._(s, x, m, k, kap, hs, mp, naive);
  }

  double omegaMax() {
    var best = 0.0;
    final h2 = hs * hs;
    for (var i = 0; i < nodes; i++) {
      final lap = ((i < nodes - 1 ? kap[i] : 0.0) + (i > 0 ? kap[i - 1] : 0.0)) / h2;
      best = math.max(best, (k[i] + 2 * lap) / m[i]);
    }
    return math.sqrt(best);
  }

  /// 물리 위치 xp를 노드 사이 선형 보간 (왼쪽 노드 번호, 가중치)로.
  ({int i, double w}) probe(double xp) {
    final sp = mapping.inv(xp);
    var lo = 0, hi = nodes; // 첫 s[j] >= sp 찾기 (numpy searchsorted)
    while (lo < hi) {
      final mid = (lo + hi) >> 1;
      if (s[mid] < sp) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }
    final i = lo - 1;
    return (i: i, w: (sp - s[i]) / (s[i + 1] - s[i]));
  }
}

/// 격자 위 막의 떨림 하나 (leapfrog, 양 끝 고정).
class Chain {
  final Grid g;
  final Float64List u, v, a;
  double t = 0;
  Chain(this.g, Float64List u0, Float64List v0)
      : u = Float64List.fromList(u0),
        v = Float64List.fromList(v0),
        a = Float64List(u0.length) {
    _accel();
  }

  void _accel() {
    final n = u.length, h2 = g.hs * g.hs;
    var fluxPrev = g.kap[0] * (u[1] - u[0]) / h2;
    a[0] = 0;
    for (var i = 1; i < n - 1; i++) {
      final flux = g.kap[i] * (u[i + 1] - u[i]) / h2;
      a[i] = (flux - fluxPrev - g.k[i] * u[i]) / g.m[i];
      fluxPrev = flux;
    }
    a[n - 1] = 0;
  }

  void step(double dt) {
    final n = u.length;
    for (var i = 0; i < n; i++) {
      v[i] += 0.5 * dt * a[i];
      u[i] += dt * v[i];
    }
    _accel();
    for (var i = 0; i < n; i++) {
      v[i] += 0.5 * dt * a[i];
    }
    t += dt;
  }

  double sample(({int i, double w}) p) => u[p.i] * (1 - p.w) + u[p.i + 1] * p.w;
}

/// 관측 실험 세 개(시계 A, 시계 B, B→C 신호)의 처음 상태.
class Setup {
  static const double clockWidth = 1.5, signalK = 6.0, signalWidth = 3.0;
  static const double clockTime = 30.0, signalTime = 95.0;

  static Chain clock(Grid g, double xc) {
    final u0 = Float64List(g.nodes);
    for (var i = 0; i < g.nodes; i++) {
      final d = g.x[i] - xc;
      u0[i] = math.exp(-d * d / (2 * clockWidth * clockWidth));
    }
    return Chain(g, u0, Float64List(g.nodes));
  }

  /// B에서 왼쪽(C 쪽)으로 가는 파속
  static Chain signal(Grid g) {
    final p = paramsX(xB);
    final om = math.sqrt((p.kap * signalK * signalK + p.k) / p.m);
    final u0 = Float64List(g.nodes), v0 = Float64List(g.nodes);
    for (var i = 0; i < g.nodes; i++) {
      final d = g.x[i] - xB;
      final env = math.exp(-d * d / (2 * signalWidth * signalWidth));
      u0[i] = env * math.cos(signalK * d);
      v0[i] = -om * env * math.sin(signalK * d);
    }
    return Chain(g, u0, v0);
  }
}

/// leapfrog 진행하며 탐침 위치의 u(t)를 기록. 반환: 시각, 탐침별 기록.
({Float64List t, List<Float64List> rec}) run(Chain c, double tEnd, double dt, List<double> probes) {
  final ps = [for (final xp in probes) c.g.probe(xp)];
  final nsteps = (tEnd / dt).ceil();
  final t = Float64List(nsteps + 1);
  final rec = [for (final _ in probes) Float64List(nsteps + 1)];
  for (var j = 0; j < ps.length; j++) {
    rec[j][0] = c.sample(ps[j]);
  }
  for (var n = 0; n < nsteps; n++) {
    c.step(dt);
    t[n + 1] = (n + 1) * dt;
    for (var j = 0; j < ps.length; j++) {
      rec[j][n + 1] = c.sample(ps[j]);
    }
  }
  return (t: t, rec: rec);
}

/// 영점 교차(선형 보간)로 잰 평균 진동수. 틱 하나 = 한 주기.
double clockFreq(List<double> t, List<double> y) {
  final tz = <double>[];
  for (var i = 0; i < y.length - 1; i++) {
    final a = y[i].sign, b = y[i + 1].sign;
    if (a * b < 0) {
      tz.add(t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i]));
    }
  }
  if (tz.length < 2) return double.nan;
  return (tz.length - 1) / (2 * (tz.last - tz.first));
}

/// scipy.signal.hilbert 와 같은 해석 신호의 크기(포락선). 길이 그대로의 DFT.
Float64List hilbertEnvelope(List<double> y) {
  final n = y.length;
  final cosT = Float64List(n), sinT = Float64List(n);
  for (var j = 0; j < n; j++) {
    cosT[j] = math.cos(2 * math.pi * j / n);
    sinT[j] = math.sin(2 * math.pi * j / n);
  }
  // 해석 신호 가중치: 0과 (짝수일 때) n/2 는 1, 양의 진동수는 2, 음의 진동수는 0 → 0..kMax 만 계산
  final kMax = n ~/ 2;
  final re = Float64List(kMax + 1), im = Float64List(kMax + 1);
  for (var k = 0; k <= kMax; k++) {
    var sr = 0.0, si = 0.0, idx = 0;
    for (var j = 0; j < n; j++) {
      sr += y[j] * cosT[idx];
      si -= y[j] * sinT[idx];
      idx += k;
      if (idx >= n) idx -= n;
    }
    final hk = (k == 0 || (n.isEven && k == kMax)) ? 1.0 : 2.0;
    re[k] = sr * hk;
    im[k] = si * hk;
  }
  final env = Float64List(n);
  for (var j = 0; j < n; j++) {
    var sr = 0.0, si = 0.0, idx = 0;
    for (var k = 0; k <= kMax; k++) {
      sr += re[k] * cosT[idx] - im[k] * sinT[idx];
      si += re[k] * sinT[idx] + im[k] * cosT[idx];
      idx += j;
      if (idx >= n) idx -= n;
    }
    env[j] = math.sqrt(sr * sr + si * si) / n;
  }
  return env;
}

/// 포락선 꼭대기 시각 (포물선 보간).
double peakTime(List<double> t, List<double> y) {
  final env = hilbertEnvelope(y);
  var j = 0;
  for (var i = 1; i < env.length; i++) {
    if (env[i] > env[j]) j = i;
  }
  j = j.clamp(1, env.length - 2);
  final y0 = env[j - 1], y1 = env[j], y2 = env[j + 1];
  return t[j] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (t[1] - t[0]);
}

class Measurement {
  final double o1, o2, fB, dt;
  final int hops, nodes;
  const Measurement(this.o1, this.o2, this.fB, this.dt, this.hops, this.nodes);
}

/// O1(시계 A/B 틱 비)와 O2(B→C 신호 동안 B 틱). relabel_test_1d.measure 와 같은 절차.
Measurement measure(Grid g, double dtFrac) {
  final dt = dtFrac * 2 / g.omegaMax();
  final fA = clockFromRun(g, xA, dt), fB = clockFromRun(g, xB, dt);
  final r = run(Setup.signal(g), Setup.signalTime, dt, const [xB, xC]);
  final tB = peakTime(r.t, r.rec[0]), tC = peakTime(r.t, r.rec[1]);
  final hops = ((g.mapping.inv(xB) - g.mapping.inv(xA)).abs() / g.hs).round();
  return Measurement(fA / fB, (tC - tB) * fB, fB, dt, hops, g.nodes);
}

double clockFromRun(Grid g, double xc, double dt) {
  final r = run(Setup.clock(g, xc), Setup.clockTime, dt, [xc]);
  return clockFreq(r.t, r.rec[0]);
}

double get predictedO1 => background(xA).n / background(xB).n;

/// 화면용: 세 실험(시계 A, 시계 B, 신호)을 같은 격자에서 한 단계씩 함께 진행.
/// 끝까지 돌리면 [measure]와 똑같은 기록이 쌓이므로 결과도 같다 (테스트로 확인).
class LiveExperiment {
  final Grid grid;
  final double dt;
  final Chain clockA, clockB, signal;
  final ({int i, double w}) _pA, _pB, _pC;
  final int nClock, nSignal;
  final List<double> t = [0], recA = [], recB = [], sigB = [], sigC = [];
  int n = 0, _zA = 0, _zB = 0;

  LiveExperiment(this.grid, {double dtFrac = 0.5})
      : dt = dtFrac * 2 / grid.omegaMax(),
        clockA = Setup.clock(grid, xA),
        clockB = Setup.clock(grid, xB),
        signal = Setup.signal(grid),
        _pA = grid.probe(xA),
        _pB = grid.probe(xB),
        _pC = grid.probe(xC),
        nClock = (Setup.clockTime / (dtFrac * 2 / grid.omegaMax())).ceil(),
        nSignal = (Setup.signalTime / (dtFrac * 2 / grid.omegaMax())).ceil() {
    _record();
  }

  bool get done => n >= nSignal;
  double get time => n * dt;

  /// 지금까지 센 틱 (영점 교차 두 번 = 한 틱)
  double get ticksA => _zA / 2;
  double get ticksB => _zB / 2;

  void _record() {
    recA.add(clockA.sample(_pA));
    recB.add(clockB.sample(_pB));
    sigB.add(signal.sample(_pB));
    sigC.add(signal.sample(_pC));
    if (recA.length > 1) {
      if (recA[recA.length - 2].sign * recA.last.sign < 0) _zA++;
      if (recB[recB.length - 2].sign * recB.last.sign < 0) _zB++;
    }
  }

  void advance(int steps) {
    for (var s = 0; s < steps && !done; s++) {
      clockA.step(dt);
      clockB.step(dt);
      signal.step(dt);
      n++;
      t.add(n * dt);
      _record();
    }
  }

  /// 끝난 뒤의 관측량: O1(시계비), O2(B→C 신호 동안 B 틱). 시계는 처음 [Setup.clockTime] 동안만 씀.
  Measurement result() {
    final tc = t.sublist(0, nClock + 1);
    final fA = clockFreq(tc, recA.sublist(0, nClock + 1));
    final fB = clockFreq(tc, recB.sublist(0, nClock + 1));
    final tB = peakTime(t, sigB), tC = peakTime(t, sigC);
    final hops = ((grid.mapping.inv(xB) - grid.mapping.inv(xA)).abs() / grid.hs).round();
    return Measurement(fA / fB, (tC - tB) * fB, fB, dt, hops, grid.nodes);
  }
}
