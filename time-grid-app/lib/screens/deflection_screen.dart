import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../physics/deflection_2d.dart';
import '../widgets/deflection_chart.dart';
import '../widgets/deflection_painter.dart';

/// 화면 2: 빛의 휘어짐. 규칙이 만든 장 속 2D 격자로 파속을 보내 휨각을 잰다.
class DeflectionScreen extends StatefulWidget {
  const DeflectionScreen({super.key});

  @override
  State<DeflectionScreen> createState() => _DeflectionScreenState();
}

class _DeflectionScreenState extends State<DeflectionScreen> with SingleTickerProviderStateMixin {
  static const params = DeflectionParams.small;
  static const qs = [2.0, 4.0, 6.0];

  late final Ticker _ticker;
  double _gamma = 1;
  int _qi = 1;
  late Deflection2D _sim;
  final List<Offset> _trail = [];
  final List<AppPoint> _points = [];
  ui.Image? _image;
  bool _imageBusy = false, _imageDirty = false;
  ColorScheme? _cs;
  double _eMax = 1;
  bool _running = true;

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
      _reset();
    } else {
      _renderImage();
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    _image?.dispose();
    super.dispose();
  }

  void _reset() {
    _sim = Deflection2D(params, _gamma, qs[_qi]);
    _trail.clear();
    _eMax = 0;
    final size = params.ng * params.ng;
    for (var i = 0; i < size; i++) {
      final e = _sim.m[i] * _sim.v[i] * _sim.v[i] + _sim.k[i] * _sim.u[i] * _sim.u[i];
      if (e > _eMax) _eMax = e;
    }
    _running = true;
    _addTrail();
    _renderImage();
  }

  void _addTrail() {
    final c = _sim.centroid();
    _trail.add(Offset(c.z, c.x));
  }

  void _tick(Duration _) {
    if (!_running || _sim.done) return;
    // 한 프레임에 약 12 ms 만 계산 (브라우저에서는 Isolate 가 없으므로 나눠서)
    final sw = Stopwatch()..start();
    while (sw.elapsedMilliseconds < 12 && !_sim.done) {
      _sim.advance(2);
    }
    _addTrail();
    if (_sim.done) {
      final th = _sim.theta();
      _points.removeWhere((p) => p.gamma == _gamma && p.q == _sim.q);
      _points.add(AppPoint(_gamma, _sim.q, _sim.vg, th, _sim.normalized(th)));
    }
    _renderImage();
    setState(() {});
  }

  /// 시계 지도(배경) + 파속 에너지 밀도를 한 장의 그림으로
  void _renderImage() {
    if (_imageBusy) {
      _imageDirty = true; // 그리는 중이면 끝난 뒤 한 번 더 (마지막 장면을 놓치지 않게)
      return;
    }
    _imageBusy = true;
    _imageDirty = false;
    final ng = params.ng;
    final px = Uint8List(ng * ng * 4);
    final cs = _cs!;
    final bg = cs.surface, slow = cs.primary, wave = cs.tertiary;
    // 화면: 가로 = 진행 방향 z(j), 세로 = 휨 방향 x(i), 위쪽이 +x
    for (var i = 0; i < ng; i++) {
      final row = (ng - 1 - i) * ng;
      for (var j = 0; j < ng; j++) {
        final idx = i * ng + j;
        final s = ((1 - _sim.nClock[idx]) / (1 - phiNMin)).clamp(0.0, 1.0) * 0.35;
        final e = (_sim.m[idx] * _sim.v[idx] * _sim.v[idx] + _sim.k[idx] * _sim.u[idx] * _sim.u[idx]) / _eMax;
        final w = (e > 0 ? e : 0.0).clamp(0.0, 1.0);
        final ww = w < 1 ? (w * (2 - w)) : 1.0;
        double ch(double b, double sl, double wv) => ((b * (1 - s) + sl * s) * (1 - ww) + wv * ww) * 255;
        final o = (row + j) * 4;
        px[o] = ch(bg.r, slow.r, wave.r).round().clamp(0, 255);
        px[o + 1] = ch(bg.g, slow.g, wave.g).round().clamp(0, 255);
        px[o + 2] = ch(bg.b, slow.b, wave.b).round().clamp(0, 255);
        px[o + 3] = 255;
      }
    }
    ui.decodeImageFromPixels(px, ng, ng, ui.PixelFormat.rgba8888, (img) {
      _imageBusy = false;
      if (!mounted) {
        img.dispose();
        return;
      }
      setState(() {
        _image?.dispose();
        _image = img;
      });
      if (_imageDirty) _renderImage();
    });
  }

  /// 덩어리 중심(가장 느린 곳)의 시계 몫
  static final double phiNMin = math.exp(phiAt(params, 1e-12));

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final sim = _sim;
    final last = _points.where((p) => p.gamma == _gamma && p.q == sim.q).firstOrNull;
    final field = AspectRatio(
      aspectRatio: 1,
      child: CustomPaint(
        painter: DeflectionPainter(_image, _trail, params, t.colorScheme),
        child: const SizedBox.expand(),
      ),
    );
    final chart = AspectRatio(aspectRatio: 1.25, child: DeflectionChart(points: _points));
    return Scaffold(
      appBar: AppBar(title: const Text('빛의 휘어짐')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1080),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('가운데 덩어리가 규칙대로 시계 몫(시간이 느려짐)과 공간 몫(그리드 간격이 늘어남)을 만들고, 그 값이 격자의 재료값이 된다. '
                  '그 격자 위로 파속을 보내면 물질 쪽으로 휜다. 휨은 속도에 따라 1 + γv²로 커지고, γ = 1이면 빛의 극한에서 뉴턴 값의 2배가 된다.',
                  style: t.textTheme.bodyMedium),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  for (final (g, label) in const [(1.0, '규칙 γ = 1'), (0.0, '대조 γ = 0 (시간 몫만)')])
                    ChoiceChip(
                      label: Text(label),
                      selected: _gamma == g,
                      showCheckmark: false,
                      onSelected: (_) => setState(() {
                        _gamma = g;
                        _reset();
                      }),
                    ),
                  const SizedBox(width: 8),
                  for (var i = 0; i < qs.length; i++)
                    ChoiceChip(
                      label: Text('v = ${params.groupVelocity(qs[i]).toStringAsFixed(2)}'),
                      selected: _qi == i,
                      showCheckmark: false,
                      onSelected: (_) => setState(() {
                        _qi = i;
                        _reset();
                      }),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              LayoutBuilder(builder: (context, c) {
                if (c.maxWidth < 720) {
                  return Column(children: [field, const SizedBox(height: 12), chart]);
                }
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: field),
                    const SizedBox(width: 16),
                    Expanded(child: chart),
                  ],
                );
              }),
              Row(
                children: [
                  IconButton.filledTonal(
                    tooltip: _running ? '멈춤' : '진행',
                    onPressed: sim.done ? null : () => setState(() => _running = !_running),
                    icon: Icon(_running ? Icons.pause : Icons.play_arrow),
                  ),
                  IconButton(tooltip: '처음부터', onPressed: () => setState(_reset), icon: const Icon(Icons.replay)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      sim.done && last != null
                          ? '휨각 θ = ${last.theta.toStringAsFixed(4)} rad · θv²/(2GM/b) = ${last.normalized.toStringAsFixed(3)} '
                              '(예측 ${(1 + _gamma * sim.vg * sim.vg).toStringAsFixed(3)})'
                          : '진행 ${(100 * sim.n / sim.nSteps).toStringAsFixed(0)}% · 격자 ${params.ng}², 시각 ${sim.time.toStringAsFixed(1)}',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text('왼쪽: 배경이 진할수록 시계가 느린 곳, 점선은 휘지 않았을 때의 직선, 실선은 파속 에너지 중심의 궤적. '
                  '오른쪽: 속도별로 잰 휨을 뉴턴 값(2GM/bv²)으로 나눈 값. 빈 점은 원본 Python(768² 격자), 찬 점은 이 앱에서 방금 잰 값(256² 격자, 같은 속도에서 원본과 1.5% 안). '
                  '원본 결과: 규칙은 기울기 γ = 1.04, 대조는 0.02. 절편이 1보다 조금 작은 것은 유한한 경로(±12)의 효과.',
                  style: t.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}
