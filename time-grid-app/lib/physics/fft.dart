/// 2의 거듭제곱 크기 복소 FFT (제자리, 반복형 radix-2). numpy.fft 와 같은 부호와 정규화:
///   forward  X_k = Σ x_j e^{−2πi jk/n}
///   inverse  x_j = (1/n) Σ X_k e^{+2πi jk/n}
library;

import 'dart:math' as math;
import 'dart:typed_data';

class Fft {
  final int n;
  final Int32List _rev;
  final Float64List _cos, _sin;

  Fft(this.n)
      : _rev = Int32List(n),
        _cos = Float64List(n ~/ 2),
        _sin = Float64List(n ~/ 2) {
    assert(n > 1 && (n & (n - 1)) == 0, 'n must be a power of two');
    var bits = 0;
    while ((1 << bits) < n) {
      bits++;
    }
    for (var i = 0; i < n; i++) {
      var r = 0;
      for (var b = 0; b < bits; b++) {
        if (i & (1 << b) != 0) r |= 1 << (bits - 1 - b);
      }
      _rev[i] = r;
    }
    for (var i = 0; i < n ~/ 2; i++) {
      _cos[i] = math.cos(2 * math.pi * i / n);
      _sin[i] = math.sin(2 * math.pi * i / n);
    }
  }

  /// 길이 n 의 1D 변환. 원소 k 는 re[off + k*stride].
  void transform(Float64List re, Float64List im, int off, int stride, bool inverse) {
    for (var i = 0; i < n; i++) {
      final j = _rev[i];
      if (j > i) {
        final a = off + i * stride, b = off + j * stride;
        final tr = re[a], ti = im[a];
        re[a] = re[b];
        im[a] = im[b];
        re[b] = tr;
        im[b] = ti;
      }
    }
    final sgn = inverse ? 1.0 : -1.0;
    for (var size = 2; size <= n; size <<= 1) {
      final half = size >> 1, step = n ~/ size;
      for (var start = 0; start < n; start += size) {
        for (var k = 0; k < half; k++) {
          final wr = _cos[k * step], wi = sgn * _sin[k * step];
          final a = off + (start + k) * stride, b = a + half * stride;
          final xr = re[b] * wr - im[b] * wi, xi = re[b] * wi + im[b] * wr;
          re[b] = re[a] - xr;
          im[b] = im[a] - xi;
          re[a] += xr;
          im[a] += xi;
        }
      }
    }
    if (inverse) {
      final s = 1 / n;
      for (var i = 0; i < n; i++) {
        re[off + i * stride] *= s;
        im[off + i * stride] *= s;
      }
    }
  }

  /// n×n 배열 (행 우선, [i*n + j]) 의 2D 변환.
  /// rows: 앞쪽 몇 행만 행 변환 (나머지 행이 0 일 때). cols: 열 변환할 앞쪽 열 수 (그 열만 필요할 때)
  void transform2d(Float64List re, Float64List im, bool inverse, {int? rows, int? cols}) {
    for (var i = 0; i < (rows ?? n); i++) {
      transform(re, im, i * n, 1, inverse);
    }
    for (var j = 0; j < (cols ?? n); j++) {
      transform(re, im, j, n, inverse);
    }
  }
}
