import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../physics/relabel_1d.dart';
import '../widgets/membrane_painter.dart';

/// 화면 1: 막의 떨림. 같은 물리를 서로 다른 이름표(격자 노드 배치)로 계산해도 틱으로 잰 값은 같다.
class RelabelScreen extends StatefulWidget {
  const RelabelScreen({super.key});

  @override
  State<RelabelScreen> createState() => _RelabelScreenState();
}

class _Choice {
  final String label, note;
  final Grid Function() build;
  const _Choice(this.label, this.note, this.build);
}

final _choices = <_Choice>[
  _Choice('균일', '노드를 고른 간격으로 둠', () => Grid.build(Mapping.uniform(), 0.05)),
  _Choice('사인 늘이기', '노드 간격을 사인 모양으로 바꾸고 재료값도 같이 변환', () => Grid.build(Mapping.sine(0.5), 0.05)),
  _Choice('sinh 늘이기', '가운데를 촘촘히, 바깥을 성기게 두고 재료값도 변환', () => Grid.build(Mapping.sinh(10.0), 0.02)),
  _Choice('대조: 변환 안 함', '사인 늘이기와 같은 노드, 재료값은 변환하지 않음 (틀린 이름표 바꾸기)',
      () => Grid.build(Mapping.sine(0.5), 0.05, naive: true)),
];

class _RelabelScreenState extends State<RelabelScreen> with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  int _choice = 0;
  late LiveExperiment _exp;
  Measurement? _final;
  final Map<int, Measurement> _done = {};
  bool _running = true;
  double _speed = 6; // 초당 시뮬레이션 시간
  Duration _last = Duration.zero;
  double _debt = 0;

  @override
  void initState() {
    super.initState();
    _exp = LiveExperiment(_choices[_choice].build());
    _ticker = createTicker(_tick)..start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  void _restart(int choice) {
    setState(() {
      _choice = choice;
      _exp = LiveExperiment(_choices[choice].build());
      _final = null;
      _running = true;
      _debt = 0;
    });
  }

  void _tick(Duration now) {
    final dtReal = ((now - _last).inMicroseconds / 1e6).clamp(0.0, 0.1);
    _last = now;
    if (!_running || _exp.done) return;
    _debt += dtReal * _speed / _exp.dt;
    final steps = _debt.floor();
    _debt -= steps;
    _exp.advance(steps);
    if (_exp.done) {
      final m = _exp.result();
      _final = m;
      _done[_choice] = m;
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final c = _choices[_choice];
    final m = _final;
    final clockRunning = _exp.n <= _exp.nClock;
    return Scaffold(
      appBar: AppBar(title: const Text('막의 떨림 · 이름표 바꾸기')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 960),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('그리드 노드에 저장된 파동이 막을 통해 이웃으로 전달된다. 가운데 우물에서는 시계가 느리다. '
                  '노드를 어떻게 배치하든(이름표) 재료값을 같이 바꾸면, 시계 틱과 틱으로 잰 신호 시간은 같아야 한다.',
                  style: t.textTheme.bodyMedium),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  for (var i = 0; i < _choices.length; i++)
                    ChoiceChip(
                      label: Text(_choices[i].label),
                      selected: i == _choice,
                      showCheckmark: false,
                      onSelected: (_) => _restart(i),
                    ),
                ],
              ),
              const SizedBox(height: 4),
              Text('${c.note} · 노드 ${_exp.grid.nodes}개', style: t.textTheme.bodySmall),
              const SizedBox(height: 8),
              AspectRatio(
                aspectRatio: 1.8,
                child: CustomPaint(
                  painter: MembranePainter(_exp, t.colorScheme),
                  child: const SizedBox.expand(),
                ),
              ),
              Row(
                children: [
                  IconButton.filledTonal(
                    tooltip: _running ? '멈춤' : '진행',
                    onPressed: _exp.done ? null : () => setState(() => _running = !_running),
                    icon: Icon(_running ? Icons.pause : Icons.play_arrow),
                  ),
                  IconButton(tooltip: '처음부터', onPressed: () => _restart(_choice), icon: const Icon(Icons.replay)),
                  const SizedBox(width: 8),
                  Text('시각 ${_exp.time.toStringAsFixed(1)} / ${Setup.signalTime.toStringAsFixed(0)}'),
                  Expanded(
                    child: Slider(
                      value: _speed,
                      min: 1,
                      max: 30,
                      label: '×${_speed.toStringAsFixed(0)}',
                      divisions: 29,
                      onChanged: (v) => setState(() => _speed = v),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _Stat(
                    title: '시계 틱',
                    lines: [
                      'A (우물 가운데) ${_exp.ticksA.toStringAsFixed(1)}',
                      'B (먼 곳) ${_exp.ticksB.toStringAsFixed(1)}',
                      if (_exp.ticksB > 0) 'A / B = ${(_exp.ticksA / _exp.ticksB).toStringAsFixed(3)}'
                          '${clockRunning ? '' : ' (측정은 처음 ${Setup.clockTime.toStringAsFixed(0)} 동안)'}',
                    ],
                  ),
                  _Stat(
                    title: '측정값 (끝나면 계산)',
                    lines: m == null
                        ? ['진행 중…']
                        : [
                            '시계비 O1 = ${m.o1.toStringAsFixed(4)}',
                            '신호 B → C 동안 B 틱 O2 = ${m.o2.toStringAsFixed(2)}',
                            'A–B 사이 홉 ${m.hops}개',
                          ],
                  ),
                  _Stat(
                    title: '기준',
                    lines: [
                      '연속 예측 N_A/N_B = ${predictedO1.toStringAsFixed(4)}',
                      'Python 원본 (균일 격자) 0.7734',
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text('이름표별 결과', style: t.textTheme.titleSmall),
              const SizedBox(height: 4),
              Table(
                columnWidths: const {0: FlexColumnWidth(2), 1: FlexColumnWidth(1), 2: FlexColumnWidth(1)},
                children: [
                  _row(t, ['이름표', '시계비 O1', 'B 틱 O2'], header: true),
                  for (var i = 0; i < _choices.length; i++)
                    _row(t, [
                      _choices[i].label,
                      _done[i]?.o1.toStringAsFixed(4) ?? '–',
                      _done[i]?.o2.toStringAsFixed(1) ?? '–',
                    ]),
                ],
              ),
              const SizedBox(height: 4),
              Text('재료값을 같이 바꾼 이름표들은 시계비가 0.02% 안에서 같다. 변환하지 않은 대조는 시계비가 1.3%, '
                  '신호 시간이 31% 달라진다. 신호 시간의 작은 차이(약 1~5%)는 파속이 격자 간격에 따라 조금씩 퍼지는 몫이다.',
                  style: t.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }

  TableRow _row(ThemeData t, List<String> cells, {bool header = false}) => TableRow(
        children: [
          for (final s in cells)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Text(s, style: header ? t.textTheme.labelMedium : t.textTheme.bodyMedium),
            ),
        ],
      );
}

class _Stat extends StatelessWidget {
  final String title;
  final List<String> lines;
  const _Stat({required this.title, required this.lines});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Container(
      constraints: const BoxConstraints(minWidth: 220),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: t.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: t.textTheme.labelMedium),
          const SizedBox(height: 4),
          for (final l in lines) Text(l, style: t.textTheme.bodyMedium),
        ],
      ),
    );
  }
}
