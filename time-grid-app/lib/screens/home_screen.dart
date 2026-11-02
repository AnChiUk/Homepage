import 'package:flutter/material.dart';

class _Entry {
  final String title, subtitle;
  final IconData icon;
  final String? route;
  const _Entry(this.title, this.subtitle, this.icon, this.route);
}

const _entries = <_Entry>[
  _Entry('막의 떨림', '그리드와 막, 시계 틱, 틱으로 잰 홉. 이름표를 바꿔도 잰 값은 같다', Icons.graphic_eq, '/relabel'),
  _Entry('빛의 휘어짐', '물질 쪽으로 휘는 파속. 휨이 속도에 따라 1 + γv²로 커짐 (γ = 1 / 0 비교)', Icons.flare, '/deflection'),
  _Entry('두 덩어리 궤도', '자기 중력으로 묶인 파동 덩어리 둘이 서로 끌려 도는 궤도 (끌림 켬/끔 비교)', Icons.blur_circular, '/orbit'),
  _Entry('중력파', '모양 6가지 중 + / × 두 편광만 출렁임, 고리 표지의 찌그러짐 재생', Icons.waves, '/gw'),
];

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('시간 그리드 사고 실험')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('시간, 공간, 빛, 중력을 그리드 사이의 에너지 전달 하나로 설명할 수 있는지 시험하는 사고 실험. '
                  '화면마다 앱 안에서 직접 계산하며, 계산은 Python 원본 실험과 같은 값이 나오는지 테스트로 확인했다.',
                  style: t.textTheme.bodyMedium),
              const SizedBox(height: 16),
              for (final e in _entries)
                Card(
                  child: ListTile(
                    enabled: e.route != null,
                    leading: Icon(e.icon),
                    title: Text(e.title),
                    subtitle: Text(e.subtitle),
                    trailing: e.route != null ? const Icon(Icons.chevron_right) : null,
                    onTap: e.route == null ? null : () => Navigator.of(context).pushNamed(e.route!),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
