/// 동역학 1: 물질이 만든 장 속에서 파속이 휘는가. 원본: time-grid/deflection_dynamics.py
///
/// 1) 무거운 덩어리(가우스, 반지름 RS)가 규칙으로 시계 몫 Φ = −GM erf(r/(√2 RS))/r 와 공간 몫 Ψ = γΦ 를 만든다.
/// 2) N = e^{Φ}, ψ = e^{−Ψ} 가 빛이 지나는 평면 위 2D 격자의 재료값을 바꾼다:  m = ψ²/N,  κ = N,  k = Nψ²μ²
/// 3) 속도 v 인 시험 파속을 충돌 거리 b 로 보내고, 지나간 뒤 휨각 θ = −ΔP_x / P_z 를 잰다.
/// 예측 (약한 장): θ = (2GM / b v²)(1 + γv²)  → θv²/(2GM/b) 의 절편 1(뉴턴 끌림), 기울기 γ(공간 몫)
library;

import 'dart:math' as math;
import 'dart:typed_data';

/// erf: |x| < 2.5 는 테일러 급수, 그 위는 erfc 연분수 (상대 오차 약 1e-15)
double erf(double x) {
  final ax = x.abs();
  double r;
  if (ax < 2.5) {
    var term = ax, sum = ax;
    final x2 = ax * ax;
    for (var n = 1; n < 80; n++) {
      term *= -x2 / n;
      final add = term / (2 * n + 1);
      sum += add;
      if (add.abs() < 1e-17 * sum.abs()) break;
    }
    r = 2 / math.sqrt(math.pi) * sum;
  } else if (ax > 6.5) {
    r = 1.0;
  } else {
    // erfc(x) = exp(−x²)/√π · 1/(x + 1/2/(x + 1/(x + 3/2/(x + ...))))  (뒤에서부터)
    var f = 0.0;
    for (var n = 60; n >= 1; n--) {
      f = (n / 2) / (ax + f);
    }
    r = 1 - math.exp(-ax * ax) / math.sqrt(math.pi) / (ax + f);
  }
  return x < 0 ? -r : r;
}

class DeflectionParams {
  final double mu, a, rs, b, gm, sig, z0;
  final int ng;
  const DeflectionParams({
    this.mu = 4.0,
    this.a = 0.04,
    this.ng = 768,
    this.rs = 1.5,
    this.b = 6.0,
    this.gm = 0.06,
    this.sig = 2.0,
    this.z0 = -12.0,
  });

  /// 화면용: 같은 영역(한 변 30.72), 격자 간격 3배. 같은 속도에서 휨은 원본과 1.5% 안 (q ≤ 6, qa ≤ 0.72)
  static const small = DeflectionParams(a: 0.12, ng: 256);

  double get length => a * ng;
  double coord(int i) => (i - ng ~/ 2) * a;

  /// 먼 곳 격자 분산의 진동수와 군속도
  double omega(double q) => math.sqrt(mu * mu + (4 / (a * a)) * math.pow(math.sin(q * a / 2), 2));
  double groupVelocity(double q) => math.sin(q * a) / (a * omega(q));
}

/// 시계 몫 Φ(r) (덩어리 중심에서 거리 r)
double phiAt(DeflectionParams p, double r) => -p.gm * erf(r / (math.sqrt(2) * p.rs)) / r;

/// 2D 격자 위 파속 하나. 배열은 [i * ng + j], i = X(옆, 휨 방향), j = Z(진행 방향), 주기 경계.
class Deflection2D {
  final DeflectionParams p;
  final double gamma, q;
  final int ng;
  late final Float64List m, k, kx, kz, nClock, u, v, acc, _fx, _fz;
  late final double dt, vg, px0;
  late final int nSteps;
  int n = 0;

  Deflection2D(this.p, this.gamma, this.q) : ng = p.ng {
    final size = ng * ng;
    m = Float64List(size);
    k = Float64List(size);
    kx = Float64List(size);
    kz = Float64List(size);
    nClock = Float64List(size);
    u = Float64List(size);
    v = Float64List(size);
    acc = Float64List(size);
    _fx = Float64List(size);
    _fz = Float64List(size);
    final a = p.a, mu2 = p.mu * p.mu;
    for (var i = 0; i < ng; i++) {
      final x = p.coord(i);
      for (var j = 0; j < ng; j++) {
        final z = p.coord(j);
        final r = math.sqrt(x * x + z * z) + 1e-12;
        final phi = phiAt(p, r);
        final nn = math.exp(phi), psi = math.exp(-gamma * phi);
        final idx = i * ng + j;
        nClock[idx] = nn;
        m[idx] = psi * psi / nn;
        k[idx] = nn * (psi * psi) * mu2;
      }
    }
    for (var i = 0; i < ng; i++) {
      final ip = (i + 1) % ng;
      for (var j = 0; j < ng; j++) {
        final jp = (j + 1) % ng;
        kx[i * ng + j] = 0.5 * (nClock[i * ng + j] + nClock[ip * ng + j]);
        kz[i * ng + j] = 0.5 * (nClock[i * ng + j] + nClock[i * ng + jp]);
      }
    }
    final om = p.omega(q);
    vg = p.groupVelocity(q);
    final s2 = 2 * p.sig * p.sig;
    for (var i = 0; i < ng; i++) {
      final dx = p.coord(i) - p.b;
      for (var j = 0; j < ng; j++) {
        final dz = p.coord(j) - p.z0;
        final env = math.exp(-(dx * dx + dz * dz) / s2);
        u[i * ng + j] = env * math.cos(q * dz);
        v[i * ng + j] = om * env * math.sin(q * dz); // +z 로 진행
      }
    }
    var best = 0.0;
    final a2 = a * a;
    for (var idx = 0; idx < size; idx++) {
      best = math.max(best, (k[idx] + 4 * (kx[idx] + kz[idx]) / a2) / m[idx]);
    }
    dt = 0.35 * 2 / math.sqrt(best);
    nSteps = (2 * p.z0.abs() / vg / dt).floor();
    px0 = momentum().px;
    _accel();
  }

  bool get done => n >= nSteps;
  double get time => n * dt;

  void _accel() {
    final a2 = p.a * p.a, last = ng - 1;
    for (var i = 0; i < ng; i++) {
      final ip = (i == last ? 0 : i + 1) * ng, row = i * ng;
      for (var j = 0; j < last; j++) {
        final idx = row + j, ui = u[idx];
        _fx[idx] = kx[idx] * (u[ip + j] - ui) / a2;
        _fz[idx] = kz[idx] * (u[idx + 1] - ui) / a2;
      }
      final idx = row + last;
      _fx[idx] = kx[idx] * (u[ip + last] - u[idx]) / a2;
      _fz[idx] = kz[idx] * (u[row] - u[idx]) / a2;
    }
    for (var i = 0; i < ng; i++) {
      final im = (i == 0 ? last : i - 1) * ng, row = i * ng;
      acc[row] = (_fx[row] - _fx[im] + _fz[row] - _fz[row + last] - k[row] * u[row]) / m[row];
      for (var j = 1; j < ng; j++) {
        final idx = row + j;
        acc[idx] = (_fx[idx] - _fx[im + j] + _fz[idx] - _fz[idx - 1] - k[idx] * u[idx]) / m[idx];
      }
    }
  }

  void advance(int steps) {
    final h = 0.5 * dt, size = ng * ng;
    for (var s = 0; s < steps && !done; s++) {
      for (var idx = 0; idx < size; idx++) {
        v[idx] += h * acc[idx];
        u[idx] += dt * v[idx];
      }
      _accel();
      for (var idx = 0; idx < size; idx++) {
        v[idx] += h * acc[idx];
      }
      n++;
    }
  }

  /// 파속 운동량 (P_x, P_z) = −Σ m v ∇u
  ({double px, double pz}) momentum() {
    var px = 0.0, pz = 0.0;
    final inv = 1 / (2 * p.a);
    for (var i = 0; i < ng; i++) {
      final ip = ((i + 1) % ng) * ng, im = ((i - 1 + ng) % ng) * ng, row = i * ng;
      for (var j = 0; j < ng; j++) {
        final idx = row + j;
        final ux = (u[ip + j] - u[im + j]) * inv;
        final uz = (u[row + (j + 1) % ng] - u[row + (j - 1 + ng) % ng]) * inv;
        px -= m[idx] * v[idx] * ux;
        pz -= m[idx] * v[idx] * uz;
      }
    }
    return (px: px, pz: pz);
  }

  /// 휨각 (양수 = 물질 쪽으로 휨, 끌림)
  double theta() {
    final mo = momentum();
    return -(mo.px - px0) / mo.pz;
  }

  /// 파속 에너지 무게중심 (궤적 그리기용, 관측 가능한 위치)
  ({double x, double z}) centroid() {
    var w = 0.0, sx = 0.0, sz = 0.0;
    for (var i = 0; i < ng; i++) {
      final x = p.coord(i);
      for (var j = 0; j < ng; j++) {
        final idx = i * ng + j;
        final e = m[idx] * v[idx] * v[idx] + k[idx] * u[idx] * u[idx];
        w += e;
        sx += e * x;
        sz += e * p.coord(j);
      }
    }
    return (x: sx / w, z: sz / w);
  }

  /// 정규화한 휨: θv²/(2GM/b). 예측 1 + γv²
  double normalized(double theta) => theta * vg * vg / (2 * p.gm / p.b);
}
