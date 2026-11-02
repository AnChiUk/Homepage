"""
Python 기준값 만들기: time-grid/ 의 원본 실험 코드를 그대로 불러 test/reference/*.json 에 저장한다.
Dart 변환이 맞는지는 test/ 의 단위 테스트가 이 값과 비교해 확인한다.
실행: python tool/make_reference.py   (time-grid-app 폴더에서)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'time-grid'))
import relabel_test_1d as R
import deflection_dynamics as D

OUT = os.path.join(HERE, '..', 'test', 'reference')


def relabel_1d():
    cases = [
        ('uniform', R.map_uniform(), 0.05, 0.5, False),
        ('uniform', R.map_uniform(), 0.05, 0.25, False),
        ('uniform', R.map_uniform(), 0.10, 0.5, False),
        ('sine', R.map_sine(0.5), 0.05, 0.5, False),
        ('sinh', R.map_sinh(10.0), 0.02, 0.5, False),
        ('sine', R.map_sine(0.5), 0.05, 0.5, True),
    ]
    rows = []
    for name, mp, h, dtf, naive in cases:
        g = R.build(mp, h, naive)
        r = R.measure(g, dtf)
        rows.append(dict(mapping=name, h=h, dt_frac=dtf, naive=naive, nodes=int(r['nodes']), hops=int(r['hops']),
                         dt=float(r['dt']), fB=float(r['fB']), O1=float(r['O1']), O2=float(r['O2'])))
        print(rows[-1])
    NA, _ = R.background(0.0); NB, _ = R.background(R.XB)
    return dict(source='time-grid/relabel_test_1d.py', predicted_O1=float(NA / NB), cases=rows)


def deflection_2d(a, ng, qs):
    """동역학 1 파속 휨. 원본은 모듈 전역(A, NG)을 읽으므로 바꿔서 줄인 격자도 같은 코드로 잰다"""
    D.A, D.NG = a, ng
    D.L = a * ng
    rows = []
    for g in (D.GAMMA_RULE, 0.0):
        for q in qs:
            vg, th = D.run(q, g)
            rows.append(dict(gamma=float(g), q=q, vg=float(vg), theta=float(th)))
            print(a, ng, rows[-1], flush=True)
    return dict(source='time-grid/deflection_dynamics.py', a=a, ng=ng, mu=D.MU, rs=D.RS, b=D.B, gm=D.GM, sig=D.SIG, z0=D.Z0,
                gamma_rule=float(D.GAMMA_RULE), cases=rows)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['relabel', 'deflection_small', 'deflection']
    if 'relabel' in which:
        json.dump(relabel_1d(), open(os.path.join(OUT, 'relabel_1d.json'), 'w'), indent=1)
    if 'deflection_small' in which:      # 화면용 줄인 격자 (같은 영역, 간격 3배)
        json.dump(deflection_2d(0.12, 256, [2.0, 4.0, 6.0]), open(os.path.join(OUT, 'deflection_2d_small.json'), 'w'), indent=1)
    if 'deflection' in which:            # 원본 크기 (문서의 결과와 같은 설정)
        json.dump(deflection_2d(0.04, 768, [2.0, 4.0, 8.0, 12.0]), open(os.path.join(OUT, 'deflection_2d.json'), 'w'), indent=1)
