/// 텐서 2단계: 막 변형 결합 규칙의 모드 세기. 원본: time-grid/mode_count_test.py
///
/// 막 변형 h_ij (대칭 텐서, 6성분)가 평면파로 퍼질 때 ω² K h = V(q) h (일반화 고유값 문제).
///   ω² > 0                         → 실제로 출렁이는 모드
///   ω² = 0 이고 V 의 영공간이 이름표 바꾸기 h = q⊗ξ + ξ⊗q 와 겹침 → 이름표 모드 (관측 불가)
///   나머지                          → 구속 (시간 방향과 맞물린 모드, 스스로 출렁이지 않음)
/// 후보 C1 (성분별 탄성): 6개 모두 출렁임.  C3 (GR형, 유일한 이름표 무관 에너지): 출렁임 2, 이름표 3, 구속 1.
library;

import 'dart:math' as math;

typedef Mat = List<List<double>>;
typedef Vec3 = List<double>;

Mat zeros(int r, int c) => List.generate(r, (_) => List.filled(c, 0.0));

/// 대칭 텐서의 정규직교 기저 6개 (프로베니우스 내적)
final List<Mat> basis = () {
  final out = <Mat>[];
  for (var i = 0; i < 3; i++) {
    final e = zeros(3, 3);
    e[i][i] = 1;
    out.add(e);
  }
  for (final (i, j) in const [(0, 1), (1, 2), (0, 2)]) {
    final e = zeros(3, 3);
    e[i][j] = e[j][i] = 1 / math.sqrt(2);
    out.add(e);
  }
  return out;
}();

double _frob(Mat a, Mat b) {
  var s = 0.0;
  for (var i = 0; i < 3; i++) {
    for (var j = 0; j < 3; j++) {
      s += a[i][j] * b[i][j];
    }
  }
  return s;
}

double _trace(Mat a) => a[0][0] + a[1][1] + a[2][2];

Mat _add(Mat a, Mat b, double s) => [
      for (var i = 0; i < 3; i++) [for (var j = 0; j < 3; j++) a[i][j] + s * b[i][j]]
    ];

/// 이차 형식 f(h) → 6×6 대칭 행렬
Mat form(double Function(Mat) f) {
  final m = zeros(6, 6);
  for (var a = 0; a < 6; a++) {
    for (var b = 0; b < 6; b++) {
      m[a][b] = 0.25 * (f(_add(basis[a], basis[b], 1)) - f(_add(basis[a], basis[b], -1)));
    }
  }
  return m;
}

double _dot(Vec3 a, Vec3 b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

Vec3 _qh(Vec3 q, Mat h) => [for (var j = 0; j < 3; j++) q[0] * h[0][j] + q[1] * h[1][j] + q[2] * h[2][j]];

enum Candidate { c1, c3 }

/// (K, V): C1 성분별 탄성, C3 선형화된 아인슈타인-힐베르트 (시간 게이지)
(Mat, Mat) operators(Candidate c, Vec3 q) {
  final q2 = _dot(q, q);
  if (c == Candidate.c1) {
    return (form((h) => _frob(h, h)), form((h) => q2 * _frob(h, h)));
  }
  final k = form((h) => _frob(h, h) - math.pow(_trace(h), 2));
  final v = form((h) {
    final qh = _qh(q, h), tr = _trace(h);
    return q2 * _frob(h, h) - 2 * _dot(qh, qh) + 2 * _dot(qh, q) * tr - q2 * tr * tr;
  });
  return (k, v);
}

/// 이름표 바꾸기 방향 h = q⊗ξ + ξ⊗q (ξ 3개) → 6×3
Mat gaugeSpace(Vec3 q) {
  final g = zeros(6, 3);
  for (var k = 0; k < 3; k++) {
    final h = zeros(3, 3);
    for (var i = 0; i < 3; i++) {
      h[i][k] += q[i];
      h[k][i] += q[i];
    }
    for (var a = 0; a < 6; a++) {
      g[a][k] = _frob(basis[a], h);
    }
  }
  return g;
}

/// 대칭 행렬의 야코비 고유분해 → (고윳값, 열이 고유벡터인 행렬)
(List<double>, Mat) jacobiEigen(Mat input) {
  final n = input.length;
  final a = [for (final r in input) List<double>.from(r)];
  final v = zeros(n, n);
  for (var i = 0; i < n; i++) {
    v[i][i] = 1;
  }
  for (var sweep = 0; sweep < 100; sweep++) {
    var off = 0.0;
    for (var p = 0; p < n; p++) {
      for (var q = p + 1; q < n; q++) {
        off += a[p][q] * a[p][q];
      }
    }
    if (off < 1e-30) break;
    for (var p = 0; p < n; p++) {
      for (var q = p + 1; q < n; q++) {
        if (a[p][q].abs() < 1e-300) continue;
        final theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        final t = (theta >= 0 ? 1 : -1) / (theta.abs() + math.sqrt(theta * theta + 1));
        final c = 1 / math.sqrt(t * t + 1), s = t * c;
        for (var k = 0; k < n; k++) {
          final akp = a[k][p], akq = a[k][q];
          a[k][p] = c * akp - s * akq;
          a[k][q] = s * akp + c * akq;
        }
        for (var k = 0; k < n; k++) {
          final apk = a[p][k], aqk = a[q][k];
          a[p][k] = c * apk - s * aqk;
          a[q][k] = s * apk + c * aqk;
        }
        for (var k = 0; k < n; k++) {
          final vkp = v[k][p], vkq = v[k][q];
          v[k][p] = c * vkp - s * vkq;
          v[k][q] = s * vkp + c * vkq;
        }
      }
    }
  }
  return ([for (var i = 0; i < n; i++) a[i][i]], v);
}

/// 특잇값 (AᵀA 의 고윳값 제곱근)
List<double> singularValues(Mat a) {
  final rows = a.length, cols = a[0].length;
  final ata = zeros(cols, cols);
  for (var i = 0; i < cols; i++) {
    for (var j = 0; j < cols; j++) {
      var s = 0.0;
      for (var k = 0; k < rows; k++) {
        s += a[k][i] * a[k][j];
      }
      ata[i][j] = s;
    }
  }
  return [for (final e in jacobiEigen(ata).$1) math.sqrt(math.max(e, 0))];
}

/// 대칭 행렬 m 의 영공간 (numpy SVD 방식: 특잇값 ≤ tol·최댓값)
Mat nullSpace(Mat m, {double tol = 1e-9}) {
  final (e, v) = jacobiEigen(m);
  final scale = math.max(e.map((x) => x.abs()).reduce(math.max), 1e-300);
  final cols = [for (var k = 0; k < e.length; k++) if (e[k].abs() <= tol * scale) k];
  return [
    for (var i = 0; i < m.length; i++) [for (final k in cols) v[i][k]]
  ];
}

int rank(Mat a, double tol) => singularValues(a).where((s) => s > tol).length;

/// 일반 실수 행렬의 고윳값 (평형화 → 헤센베르크 → 이동 QR, Numerical Recipes 방식). 실수부만 반환
List<double> eigenvaluesReal(Mat input) {
  final n = input.length;
  final a = [for (final r in input) List<double>.from(r)];
  // 평형화
  const radix = 2.0, sqrdx = radix * radix;
  var done = false;
  while (!done) {
    done = true;
    for (var i = 0; i < n; i++) {
      var r = 0.0, c = 0.0;
      for (var j = 0; j < n; j++) {
        if (j != i) {
          c += a[j][i].abs();
          r += a[i][j].abs();
        }
      }
      if (c != 0 && r != 0) {
        var g = r / radix, f = 1.0;
        final s = c + r;
        while (c < g) {
          f *= radix;
          c *= sqrdx;
        }
        g = r * radix;
        while (c > g) {
          f /= radix;
          c /= sqrdx;
        }
        if ((c + r) / f < 0.95 * s) {
          done = false;
          g = 1 / f;
          for (var j = 0; j < n; j++) {
            a[i][j] *= g;
          }
          for (var j = 0; j < n; j++) {
            a[j][i] *= f;
          }
        }
      }
    }
  }
  // 헤센베르크 (가우스 소거)
  for (var m = 1; m < n - 1; m++) {
    var x = 0.0;
    var i = m;
    for (var j = m; j < n; j++) {
      if (a[j][m - 1].abs() > x.abs()) {
        x = a[j][m - 1];
        i = j;
      }
    }
    if (i != m) {
      for (var j = m - 1; j < n; j++) {
        final t = a[i][j];
        a[i][j] = a[m][j];
        a[m][j] = t;
      }
      for (var j = 0; j < n; j++) {
        final t = a[j][i];
        a[j][i] = a[j][m];
        a[j][m] = t;
      }
    }
    if (x != 0) {
      for (i = m + 1; i < n; i++) {
        var y = a[i][m - 1];
        if (y != 0) {
          y /= x;
          a[i][m - 1] = y;
          for (var j = m; j < n; j++) {
            a[i][j] -= y * a[m][j];
          }
          for (var j = 0; j < n; j++) {
            a[j][m] += y * a[j][i];
          }
        }
      }
    }
  }
  for (var i = 2; i < n; i++) {
    for (var j = 0; j < i - 1; j++) {
      a[i][j] = 0;
    }
  }
  // 이동 QR (hqr)
  final wr = List<double>.filled(n, 0);
  var anorm = 0.0;
  for (var i = 0; i < n; i++) {
    for (var j = math.max(i - 1, 0); j < n; j++) {
      anorm += a[i][j].abs();
    }
  }
  var nn = n - 1;
  var t = 0.0;
  double p = 0, q = 0, r = 0, s = 0, w = 0, x = 0, y = 0, z = 0;
  while (nn >= 0) {
    var its = 0;
    int l;
    do {
      for (l = nn; l > 0; l--) {
        s = a[l - 1][l - 1].abs() + a[l][l].abs();
        if (s == 0) s = anorm;
        if (a[l][l - 1].abs() + s == s) {
          a[l][l - 1] = 0;
          break;
        }
      }
      x = a[nn][nn];
      if (l == nn) {
        wr[nn--] = x + t;
      } else {
        y = a[nn - 1][nn - 1];
        w = a[nn][nn - 1] * a[nn - 1][nn];
        if (l == nn - 1) {
          p = 0.5 * (y - x);
          q = p * p + w;
          z = math.sqrt(q.abs());
          x += t;
          if (q >= 0) {
            z = p + (p >= 0 ? z.abs() : -z.abs());
            wr[nn - 1] = wr[nn] = x + z;
            if (z != 0) wr[nn] = x - w / z;
          } else {
            wr[nn - 1] = wr[nn] = x + p; // 복소 쌍: 실수부만
          }
          nn -= 2;
        } else {
          if (its == 60) throw StateError('hqr: too many iterations');
          if (its == 10 || its == 20) {
            t += x;
            for (var i = 0; i <= nn; i++) {
              a[i][i] -= x;
            }
            s = a[nn][nn - 1].abs() + a[nn - 1][nn - 2].abs();
            y = x = 0.75 * s;
            w = -0.4375 * s * s;
          }
          ++its;
          int m;
          for (m = nn - 2; m >= l; m--) {
            z = a[m][m];
            r = x - z;
            s = y - z;
            p = (r * s - w) / a[m + 1][m] + a[m][m + 1];
            q = a[m + 1][m + 1] - z - r - s;
            r = a[m + 2][m + 1];
            s = p.abs() + q.abs() + r.abs();
            p /= s;
            q /= s;
            r /= s;
            if (m == l) break;
            final u = a[m][m - 1].abs() * (q.abs() + r.abs());
            final v = p.abs() * (a[m - 1][m - 1].abs() + z.abs() + a[m + 1][m + 1].abs());
            if (u + v == v) break;
          }
          for (var i = m; i < nn - 1; i++) {
            a[i + 2][i] = 0;
            if (i != m) a[i + 2][i - 1] = 0;
          }
          for (var k = m; k < nn; k++) {
            if (k != m) {
              p = a[k][k - 1];
              q = a[k + 1][k - 1];
              r = 0;
              if (k + 1 != nn) r = a[k + 2][k - 1];
              if ((x = p.abs() + q.abs() + r.abs()) != 0) {
                p /= x;
                q /= x;
                r /= x;
              }
            }
            final sq = math.sqrt(p * p + q * q + r * r);
            s = p >= 0 ? sq : -sq;
            if (s != 0) {
              if (k == m) {
                if (l != m) a[k][k - 1] = -a[k][k - 1];
              } else {
                a[k][k - 1] = -s * x;
              }
              p += s;
              x = p / s;
              y = q / s;
              z = r / s;
              q /= p;
              r /= p;
              for (var j = k; j <= nn; j++) {
                p = a[k][j] + q * a[k + 1][j];
                if (k + 1 != nn) {
                  p += r * a[k + 2][j];
                  a[k + 2][j] -= p * z;
                }
                a[k + 1][j] -= p * y;
                a[k][j] -= p * x;
              }
              final mmin = nn < k + 3 ? nn : k + 3;
              for (var i = l; i <= mmin; i++) {
                p = x * a[i][k] + y * a[i][k + 1];
                if (k + 1 != nn) {
                  p += z * a[i][k + 2];
                  a[i][k + 2] -= p * r;
                }
                a[i][k + 1] -= p * q;
                a[i][k] -= p;
              }
            }
          }
        }
      }
    } while (l < nn - 1);
  }
  return wr..sort();
}

/// K⁻¹V (가우스 소거, 부분 피벗)
Mat solve(Mat k, Mat v) {
  final n = k.length;
  final a = [for (var i = 0; i < n; i++) [...k[i], ...v[i]]];
  for (var c = 0; c < n; c++) {
    var piv = c;
    for (var r = c + 1; r < n; r++) {
      if (a[r][c].abs() > a[piv][c].abs()) piv = r;
    }
    final tmp = a[c];
    a[c] = a[piv];
    a[piv] = tmp;
    for (var r = 0; r < n; r++) {
      if (r == c) continue;
      final f = a[r][c] / a[c][c];
      for (var j = c; j < 2 * n; j++) {
        a[r][j] -= f * a[c][j];
      }
    }
  }
  return [
    for (var i = 0; i < n; i++) [for (var j = 0; j < n; j++) a[i][n + j] / a[i][i]]
  ];
}

class ModeCount {
  final List<double> w2, speeds; // ω² 전부, 출렁이는 모드의 속도 (빛 = 1)
  final int gauge, staticModes;
  const ModeCount(this.w2, this.speeds, this.gauge, this.staticModes);
  int get oscillating => speeds.length;
  int get constraint => 6 - oscillating - gauge - staticModes;
}

/// mode_count_test.analyze 와 같은 분류
ModeCount analyze(Candidate c, Vec3 q) {
  final (k, v) = operators(c, q);
  final q2 = _dot(q, q);
  final w2 = eigenvaluesReal(solve(k, v));
  final speeds = [for (final w in w2) if (w > 1e-7 * q2) math.sqrt(w / q2)]..sort();
  final nv = nullSpace(v);
  final dimN = nv[0].length;
  final g = gaugeSpace(q);
  final int dimNG;
  if (dimN == 0) {
    dimNG = 3;
  } else {
    final stacked = [for (var i = 0; i < 6; i++) [...nv[i], ...g[i]]];
    dimNG = rank(stacked, 1e-7);
  }
  final nGauge = dimN + 3 - dimNG;
  return ModeCount(w2, speeds, nGauge, dimN - nGauge);
}

/// 격자 기호 s_i = 2 sin(q_i a / 2) (간격 a = 1)
Vec3 latticeSymbol(Vec3 q) => [for (final x in q) 2 * math.sin(x / 2)];
