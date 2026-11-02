import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart';

import '../physics/gw_playback.dart';
import '../physics/modes.dart';
import '../widgets/gw_painters.dart';

/// 화면 4: 중력파. (가) 막 변형 결합 규칙의 모드 세기를 앱 안에서 계산, (나) 3D 격자 중력파의 저장 장면 재생.
class GwScreen extends StatefulWidget {
  const GwScreen({super.key});

  @override
  State<GwScreen> createState() => _GwScreenState();
}

class _Dir {
  final String label;
  final Vec3 v;
  const _Dir(this.label, this.v);
}

const _dirs = [
  _Dir('축 (1,0,0)', [1, 0, 0]),
  _Dir('면대각 (1,1,0)', [1, 1, 0]),
  _Dir('체대각 (1,1,1)', [1, 1, 1]),
  _Dir('임의 (1,2,3)', [1, 2, 3]),
];

class _GwScreenState extends State<GwScreen> with SingleTickerProviderStateMixin {
  // (가) 모드 세기
  Candidate _cand = Candidate.c3;
  int _dir = 3;
  double _qa = 0.3;

  // (나) 재생
  late final Ticker _ticker;
  final Map<String, GwPlayback> _data = {};
  String _pol = 'plus';
  double _t = 0;
  bool _playing = true;
  Duration _last = Duration.zero;
  static const _exaggerate = 300.0;

  @override
  void initState() {
    super.initState();
    for (final pol in ['plus', 'cross']) {
      rootBundle.loadString('assets/viz_data/gw_free_$pol.json').then((s) {
        if (!mounted) return;
        setState(() => _data[pol] = GwPlayback.fromJson(jsonDecode(s) as Map<String, dynamic>));
      });
    }
    _ticker = createTicker(_tick)..start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  void _tick(Duration now) {
    final dt = ((now - _last).inMicroseconds / 1e6).clamp(0.0, 0.1);
    _last = now;
    final g = _data[_pol];
    if (!_playing || g == null) return;
    setState(() {
      _t += dt * 8; // 초당 8 시간 단위
      if (_t > g.tEnd) _t = 0;
    });
  }

  ModeCount get _modes {
    final d = _dirs[_dir].v;
    final n = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    final q = [for (final x in d) _qa * x / n];
    return analyze(_cand, latticeSymbol(q));
  }

  /// 격자 파수 qa 기준 속도 (원본 표와 같은 정의)
  List<double> _latticeSpeeds(ModeCount m) {
    final d = _dirs[_dir].v;
    final n = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    final s = latticeSymbol([for (final x in d) _qa * x / n]);
    final sn = math.sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2]);
    return [for (final v in m.speeds) v * sn / _qa];
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final m = _modes;
    final speeds = _latticeSpeeds(m);
    final g = _data[_pol];
    final kinds = [
      for (var i = 0; i < m.oscillating; i++) (ModeKind.oscillating, '출렁임\n속도 ${speeds[i].toStringAsFixed(4)}'),
      for (var i = 0; i < m.gauge; i++) (ModeKind.gauge, '이름표\n(관측 불가)'),
      for (var i = 0; i < m.staticModes; i++) (ModeKind.fixed, '정적'),
      for (var i = 0; i < m.constraint; i++) (ModeKind.constraint, '구속\n(시간과 맞물림)'),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('중력파')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1080),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('막 변형은 방향을 가진 텐서(모양 6가지)다. 그중 몇 가지가 파동으로 출렁이는지는 막끼리의 결합 규칙이 정한다.',
                  style: t.textTheme.bodyMedium),
              const SizedBox(height: 16),
              Text('모양 6가지 중 출렁이는 것 (앱 안에서 계산)', style: t.textTheme.titleMedium),
              const SizedBox(height: 8),
              Wrap(spacing: 8, runSpacing: 4, children: [
                for (final (c, label) in const [(Candidate.c3, 'C3 이름표 무관 결합 (규칙)'), (Candidate.c1, 'C1 성분별 탄성 (대조)')])
                  ChoiceChip(
                    label: Text(label),
                    selected: _cand == c,
                    showCheckmark: false,
                    onSelected: (_) => setState(() => _cand = c),
                  ),
              ]),
              const SizedBox(height: 4),
              Wrap(spacing: 8, runSpacing: 4, children: [
                for (var i = 0; i < _dirs.length; i++)
                  ChoiceChip(
                    label: Text(_dirs[i].label),
                    selected: _dir == i,
                    showCheckmark: false,
                    onSelected: (_) => setState(() => _dir = i),
                  ),
              ]),
              Row(children: [
                Text('파수 × 격자 간격 ${_qa.toStringAsFixed(2)}'),
                Expanded(
                  child: Slider(value: _qa, min: 0.05, max: 1.5, onChanged: (v) => setState(() => _qa = v)),
                ),
              ]),
              ModeCells(kinds: kinds),
              const SizedBox(height: 6),
              Text(
                _cand == Candidate.c3
                    ? '규칙(이름표 바꾸기와 무관한 유일한 결합)에서는 + / × 두 모양만 출렁이고, 셋은 그리드를 밀어 놓은 것(이름표), 하나는 시간 방향과 맞물린 구속이다. '
                        '일반상대성이론과 같은 구조다. 속도는 긴 파장에서 1(빛과 같음), 파장이 격자에 가까워지면 조금 느려진다.'
                    : '대조: 성분마다 따로 출렁이게 하면 6가지가 모두 출렁인다. 그리드를 밀어 놓기만 한 것(이름표)까지 파동이 되어, 관측할 수 없는 것이 출렁이는 셈이다.',
                style: t.textTheme.bodySmall,
              ),
              const Divider(height: 40),
              Text('중력파가 고리 표지를 지나갈 때 (3D 격자 96³, 저장된 장면 재생)', style: t.textTheme.titleMedium),
              const SizedBox(height: 8),
              Wrap(spacing: 8, children: [
                for (final (p, label) in const [('plus', '+ 편광'), ('cross', '× 편광')])
                  ChoiceChip(
                    label: Text(label),
                    selected: _pol == p,
                    showCheckmark: false,
                    onSelected: (_) => setState(() => _pol = p),
                  ),
              ]),
              const SizedBox(height: 8),
              if (g == null)
                const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
              else
                LayoutBuilder(builder: (context, c) {
                  final slice = AspectRatio(
                    aspectRatio: 1,
                    child: CustomPaint(painter: SlicePainter(g.sliceAt(_t), t.colorScheme), child: const SizedBox.expand()),
                  );
                  final ring = AspectRatio(
                    aspectRatio: 1,
                    child: CustomPaint(
                      painter: RingPainter(
                        radius: g.ringRadius,
                        angles: g.ringAngles,
                        now: g.ringAt(_t),
                        start: g.frames.first.ring,
                        exaggerate: _exaggerate,
                        cs: t.colorScheme,
                      ),
                      child: const SizedBox.expand(),
                    ),
                  );
                  if (c.maxWidth < 720) return Column(children: [slice, const SizedBox(height: 12), ring]);
                  return Row(children: [Expanded(child: slice), const SizedBox(width: 16), Expanded(child: ring)]);
                }),
              if (g != null)
                Row(children: [
                  IconButton.filledTonal(
                    onPressed: () => setState(() => _playing = !_playing),
                    icon: Icon(_playing ? Icons.pause : Icons.play_arrow),
                  ),
                  Expanded(
                    child: Slider(
                      value: _t.clamp(0, g.tEnd),
                      max: g.tEnd,
                      onChanged: (v) => setState(() {
                        _t = v;
                        _playing = false;
                      }),
                    ),
                  ),
                  Text('t = ${_t.toStringAsFixed(1)}'),
                ]),
              Text('왼쪽: 막 변형의 ${_pol == 'plus' ? '+' : '×'} 성분 xz 단면. 펄스가 왼쪽(z = −24)에서 오른쪽으로 지나가고, 세로 점선이 고리가 있는 z = 0이다. '
                  '오른쪽: z = 0 평면의 고리 표지 16개까지 틱으로 잰 거리(${_exaggerate.toStringAsFixed(0)}배 과장). 흐린 점은 처음 모양: '
                  '그리드를 밀어 놓은 이름표 성분 때문에 처음부터 찌그러져 있지만 그 모양은 출렁이지 않는다. 진한 점은 지금 모양: '
                  '파동이 지나갈 때만 ${_pol == 'plus' ? '+ 모양(가로세로)' : '× 모양(대각선)'}으로 늘었다 줄었다 한다. 잰 전파 속도 ${g?.speed.toStringAsFixed(3) ?? ''}(격자 예측 0.951).',
                  style: t.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}
