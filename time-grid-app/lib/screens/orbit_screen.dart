import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../physics/self_gravity_2d.dart';
import '../widgets/orbit_painter.dart';

/// 화면 3: 두 덩어리 궤도. 저장 파동 덩어리가 자기 중력으로 묶이고, 둘이 서로 끌려 궤도를 돈다.
class OrbitScreen extends StatefulWidget {
  const OrbitScreen({super.key});

  @override
  State<OrbitScreen> createState() => _OrbitScreenState();
}

class _OrbitScreenState extends State<OrbitScreen> with SingleTickerProviderStateMixin {
  static const params = SlowGravityParams.small;
  static SlowGravity? _sim;
  static Field? _ground; // 한 번 구한 바닥 상태는 다시 쓴다

  late final Ticker _ticker;
  GroundStateSolver? _solver;
  Binary? _binary;
  bool _mutual = true, _running = true;
  final List<Offset> _trail1 = [], _trail2 = [];
  double _angle = 0, _lastRaw = 0, _sep = 0, _width = 0;
  double _rhoMax = 1;
  ui.Image? _image;
  bool _imageBusy = false, _imageDirty = false;
  ColorScheme? _cs;

  SlowGravity get sim => _sim ??= SlowGravity(params);

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_tick)..start();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final first = _cs == null;
    _cs = Theme.of(context).colorScheme;
    if (first) {
      if (_ground == null) {
        _solver = GroundStateSolver(sim);
      } else {
        _startBinary();
      }
    }
    _renderImage();
  }

  @override
  void dispose() {
    _ticker.dispose();
    _image?.dispose();
    super.dispose();
  }

  void _startBinary() {
    final b = Binary(sim, _ground!, mutual: _mutual);
    _binary = b;
    _trail1.clear();
    _trail2.clear();
    _angle = 0;
    _rhoMax = 0;
    for (var k = 0; k < b.f1.re.length; k++) {
      _rhoMax = math.max(_rhoMax, sim.rhoAt(b.f1, k) + sim.rhoAt(b.f2, k));
    }
    _record(first: true);
    _running = true;
  }

  void _record({bool first = false}) {
    final b = _binary!;
    final c1 = b.blob1(), c2 = b.blob2();
    _trail1.add(Offset(c1.x, c1.y));
    _trail2.add(Offset(c2.x, c2.y));
    final raw = math.atan2(c1.y - c2.y, c1.x - c2.x);
    if (!first) {
      var d = raw - _lastRaw;
      if (d > math.pi) d -= 2 * math.pi;
      if (d < -math.pi) d += 2 * math.pi;
      _angle += d;
    }
    _lastRaw = raw;
    _sep = math.sqrt(math.pow(c1.x - c2.x, 2) + math.pow(c1.y - c2.y, 2));
    _width = c1.width;
  }

  /// 원본과 같이 1.25 케플러 주기 동안 (단계 수 int(T/dt))
  int get _nEnd => (1.25 * params.keplerPeriod / params.dt).floor();
  bool get _orbitDone => _binary != null && _binary!.n >= _nEnd;

  void _tick(Duration _) {
    if (!_running) return;
    final sw = Stopwatch()..start();
    final solver = _solver;
    if (solver != null) {
      while (sw.elapsedMilliseconds < 14 && !solver.done) {
        solver.advance(1);
      }
      if (solver.done) {
        _ground = solver.phi;
        _solver = null;
        _startBinary();
      }
    } else if (_binary != null && !_orbitDone) {
      while (sw.elapsedMilliseconds < 14 && !_orbitDone) {
        _binary!.advance(1);
        _record(); // 매 단계 기록 (프레임마다 기록하면 각도 추적이 회전을 놓침)
      }
    } else {
      return;
    }
    _renderImage();
    setState(() {});
  }

  /// 시계 지도 e^{Φ}(배경) + 저장 파동 밀도
  void _renderImage() {
    if (_cs == null) return;
    if (_imageBusy) {
      _imageDirty = true;
      return;
    }
    _imageBusy = true;
    _imageDirty = false;
    final ng = params.ng, cs = _cs!;
    final solver = _solver, b = _binary;
    final rho = Float64List(ng * ng), clock = Float64List(ng * ng);
    if (solver != null) {
      for (var k = 0; k < ng * ng; k++) {
        rho[k] = sim.rhoAt(solver.phi, k);
      }
    } else if (b != null) {
      for (var k = 0; k < ng * ng; k++) {
        rho[k] = sim.rhoAt(b.f1, k) + sim.rhoAt(b.f2, k);
        clock[k] = b.total[k]; // 두 덩어리가 만든 시계 몫 (대조에서도 장은 있음, 서로 느끼지 않을 뿐)
      }
    }
    var rMax = solver != null ? rho.reduce(math.max) : _rhoMax;
    if (rMax <= 0) rMax = 1;
    final view = _viewHalf;
    final iLo = ((params.ng ~/ 2) - view / params.a).round(), iHi = ((params.ng ~/ 2) + view / params.a).round();
    final side = iHi - iLo;
    final img = Uint8List(side * side * 4);
    const slowMax = 0.2; // Φ = −0.2 근처에서 가장 진하게 (바닥 상태 가운데 −0.105, 두 덩어리 겹친 곳은 더 깊음)
    for (var ii = 0; ii < side; ii++) {
      final i = iLo + ii;
      for (var jj = 0; jj < side; jj++) {
        final j = iLo + jj, k = i * ng + j;
        final slow = (-clock[k] / slowMax).clamp(0.0, 1.0) * 0.45;
        final w = math.sqrt((rho[k] / rMax).clamp(0.0, 1.0));
        double ch(double bg, double sl, double wv) => ((bg * (1 - slow) + sl * slow) * (1 - w) + wv * w) * 255;
        // 화면: 가로 = x(i), 세로 = y(j), 위쪽이 +y
        final o = ((side - 1 - jj) * side + ii) * 4;
        img[o] = ch(cs.surface.r, cs.primary.r, cs.tertiary.r).round().clamp(0, 255);
        img[o + 1] = ch(cs.surface.g, cs.primary.g, cs.tertiary.g).round().clamp(0, 255);
        img[o + 2] = ch(cs.surface.b, cs.primary.b, cs.tertiary.b).round().clamp(0, 255);
        img[o + 3] = 255;
      }
    }
    ui.decodeImageFromPixels(img, side, side, ui.PixelFormat.rgba8888, (im) {
      _imageBusy = false;
      if (!mounted) {
        im.dispose();
        return;
      }
      setState(() {
        _image?.dispose();
        _image = im;
      });
      if (_imageDirty) _renderImage();
    });
  }

  /// 보이는 영역의 반 너비: 서로 끌림이면 궤도 근처, 끄면 상자 전체
  double get _viewHalf => _mutual ? 16.0 : 32.0;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final b = _binary, solver = _solver;
    final tk = params.keplerPeriod;
    final status = solver != null
        ? '스스로 묶인 모양 찾는 중 ${(100 * solver.n / params.groundSteps).toStringAsFixed(0)}% (허수 시간 진행)'
        : b == null
            ? ''
            : '시각 ${b.time.toStringAsFixed(0)} = ${(b.time / tk).toStringAsFixed(2)} 케플러 주기'
                '${_orbitDone ? ' · 끝' : ''}';
    final picture = AspectRatio(
      aspectRatio: 1,
      child: CustomPaint(
        painter: OrbitPainter(
          image: _image,
          trail1: _trail1,
          trail2: _trail2,
          viewHalf: _viewHalf,
          r0: params.r0,
          showKepler: _mutual,
          cs: t.colorScheme,
        ),
        child: const SizedBox.expand(),
      ),
    );
    final stats = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(status, style: t.textTheme.titleSmall),
        const SizedBox(height: 8),
        if (b != null) ...[
          _line(t, '두 덩어리를 잇는 선이 돈 각도', '${(_angle * 180 / math.pi).toStringAsFixed(0)}°'),
          _line(t, '케플러 예측 (같은 시각)', '${(360 * b.time / tk).toStringAsFixed(0)}°'),
          _line(t, '거리 (처음 ${(2 * params.r0).toStringAsFixed(0)})', _sep.toStringAsFixed(2)),
          _line(t, '덩어리 폭', _width.toStringAsFixed(2)),
        ] else
          _line(t, '덩어리 폭', solver == null ? '' : sim.moments(solver.phi).width.toStringAsFixed(3)),
        const SizedBox(height: 12),
        Text(
          _mutual
              ? '두 덩어리는 각자 자기 중력으로 묶인 채(폭이 거의 그대로) 서로 끌려 돈다. 원본 Python(256²)은 1.25주기 동안 486°(케플러 450°), '
                  '이 앱(128²)은 493°. 덩어리가 공이 아니라 퍼진 파동이라 점질량 케플러보다 조금 빨리 돈다.'
              : '대조: 각 덩어리가 자기 장만 느끼면 처음 속도 그대로 직선으로 멀어진다. 상자는 주기 경계라 끝에서 반대편으로 다시 들어온다.',
          style: t.textTheme.bodySmall,
        ),
      ],
    );
    return Scaffold(
      appBar: AppBar(title: const Text('두 덩어리 궤도')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1080),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('저장 파동이 만든 시계 몫(시간이 느려짐)이 다시 파동을 끌어당겨, 파동 덩어리가 스스로 묶인다. '
                  '그런 덩어리 둘을 원 궤도 속도로 반대 방향에 놓으면 서로 끌려 궤도를 돈다. 손으로 넣은 힘은 없다: 같은 격자 규칙의 느린 극한이다.',
                  style: t.textTheme.bodyMedium),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  for (final (m, label) in const [(true, '서로 끌림 켬'), (false, '대조: 서로 끌림 끔')])
                    ChoiceChip(
                      label: Text(label),
                      selected: _mutual == m,
                      showCheckmark: false,
                      onSelected: (_) => setState(() {
                        _mutual = m;
                        if (_ground != null) _startBinary();
                        _renderImage();
                      }),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              LayoutBuilder(builder: (context, c) {
                if (c.maxWidth < 720) return Column(children: [picture, const SizedBox(height: 12), stats]);
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [Expanded(child: picture), const SizedBox(width: 16), Expanded(child: stats)],
                );
              }),
              Row(
                children: [
                  IconButton.filledTonal(
                    tooltip: _running ? '멈춤' : '진행',
                    onPressed: _orbitDone ? null : () => setState(() => _running = !_running),
                    icon: Icon(_running ? Icons.pause : Icons.play_arrow),
                  ),
                  IconButton(
                    tooltip: '처음부터',
                    onPressed: _ground == null ? null : () => setState(_startBinary),
                    icon: const Icon(Icons.replay),
                  ),
                ],
              ),
              Text('배경이 진할수록 시계가 느린 곳(두 덩어리의 시계 몫), 밝은 덩어리는 저장 파동의 밀도, 선은 두 덩어리 중심의 궤적, 점선 원은 반지름 6의 케플러 원 궤도. '
                  '이 앱의 계산은 원본 Python과 같은 크기(256²)와 화면 크기(128²) 모두에서 중심 위치가 10⁻⁷ 안에서 같다.',
                  style: t.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }

  Widget _line(ThemeData t, String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(children: [Expanded(child: Text(k, style: t.textTheme.bodyMedium)), Text(v, style: t.textTheme.titleMedium)]),
      );
}
