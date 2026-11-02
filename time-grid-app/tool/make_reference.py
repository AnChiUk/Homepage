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
import numpy as np
import self_gravity_slow as S
import mode_count_test as MC

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


def slow_config(a, ng):
    """self_gravity_slow 의 격자 전역값을 (a, ng) 로 다시 계산 (원본 식 그대로)"""
    S.A, S.NG = a, ng
    S.c = (np.arange(ng) - ng // 2) * a
    S.X, S.Y = np.meshgrid(S.c, S.c, indexing='ij')
    S.q = 2 * np.pi * np.fft.fftfreq(ng, d=a)
    S.QX, S.QY = np.meshgrid(S.q, S.q, indexing='ij')
    S.LAPQ = -(2 * (1 - np.cos(S.QX * a)) + 2 * (1 - np.cos(S.QY * a))) / a**2
    S.P = 2 * ng
    cp = (np.arange(S.P) - S.P // 2) * a
    XP, YP = np.meshgrid(cp, cp, indexing='ij')
    RP = np.sqrt(XP**2 + YP**2)
    S.KER_Q = np.fft.rfft2(np.fft.ifftshift(np.where(RP > 0, 1 / np.maximum(RP, 1e-12), 2 * 1.7627 / a)))


def slow_evolve(phis, T, dt, mutual, save_every):
    """S.evolve 와 같은 진행 (원본은 그림 저장이 256² 에 묶여 있어 진행 부분만 옮김)"""
    kin = np.exp(1j * dt * S.LAPQ / (2 * S.MU))
    track = []
    nst = int(T / dt)
    for n in range(nst + 1):
        pots = [S.potential(S.rho_of(p)) for p in phis]
        tot = sum(pots)
        if n % save_every == 0:
            track.append(dict(n=n, centers=[[float(v) for v in S.width(p)[1:]] for p in phis]))
        if n == nst:
            break
        new = []
        for j, p in enumerate(phis):
            V = tot if mutual else pots[j]
            p = p * np.exp(-0.5j * dt * S.MU * V)
            p = np.fft.ifft2(np.fft.fft2(p) * kin)
            new.append(p)
        phis = new
        pots = [S.potential(S.rho_of(p)) for p in phis]
        tot = sum(pots)
        phis = [p * np.exp(-0.5j * dt * S.MU * (tot if mutual else pots[j])) for j, p in enumerate(phis)]
    return track


def self_gravity(a, ng, dt, dtau, gsteps, t_end, save_every):
    """동역학 2-c 느린 극한: 바닥 상태와 두 덩어리 궤도 (서로 끌림 켬 / 끔)"""
    slow_config(a, ng)
    GM, r0 = 0.1, 6.0
    M = GM / S.G
    gs = S.ground_state(M, steps=gsteps, dtau=dtau)
    w0, _, _ = S.width(gs)
    phi0 = float(S.potential(S.rho_of(gs)).min())
    v = float(np.sqrt(GM / (4 * r0)))
    tk = 2 * np.pi * r0 / v
    print(a, ng, 'ground', w0, phi0, flush=True)
    out = dict(source='time-grid/self_gravity_slow.py', a=a, ng=ng, mu=S.MU, G=float(S.G), GM=GM, r0=r0, v=v, kepler_period=tk,
               dt=dt, dtau=dtau, ground_steps=gsteps, ground_width=float(w0), ground_phi_min=phi0, t_end=t_end, runs={})
    p1 = S.shift(gs, r0, 0, 0, v); p2 = S.shift(gs, -r0, 0, 0, -v)
    for mutual in (True, False):
        tr = slow_evolve([p1.copy(), p2.copy()], t_end, dt, mutual, save_every)
        out['runs']['mutual' if mutual else 'off'] = tr
        print(a, ng, mutual, tr[-1], flush=True)
    return out


def modes():
    """텐서 2단계 모드 세기: 후보 C1 / C3, 연속 방향과 격자 기호. 고윳값(ω²), 출렁임 속도, 이름표 수, 정적 수"""
    rows = []
    def add(cand, q, label):
        K, V = (MC.C1 if cand == 'C1' else MC.C3)(q)
        w2 = np.sort(np.linalg.eigvals(np.linalg.solve(K, V)).real)
        osc, ng, st, rm = MC.analyze(K, V, q, MC.constraints(q) if cand == 'C3' else None)
        rows.append(dict(candidate=cand, label=label, q=[float(v) for v in q], w2=[float(v) for v in w2],
                         speeds=[float(v) for v in osc], gauge=int(ng), static=int(st)))
    q0 = 0.3 * np.array([1.0, 2.0, 3.0]) / np.sqrt(14)
    add('C1', q0, 'continuum (1,2,3)')
    add('C3', q0, 'continuum (1,2,3)')
    for qa in (0.05, 0.3, 0.8, 1.5):
        for d in ([1, 0, 0], [1, 1, 0], [1, 1, 1]):
            qv = qa * np.array(d, float) / np.linalg.norm(d)
            add('C3', 2 * np.sin(qv / 2), f'lattice qa={qa} dir={d}')
    return dict(source='time-grid/mode_count_test.py', cases=rows)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['relabel', 'deflection_small', 'deflection', 'gravity_small', 'gravity', 'modes']
    if 'relabel' in which:
        json.dump(relabel_1d(), open(os.path.join(OUT, 'relabel_1d.json'), 'w'), indent=1)
    if 'deflection_small' in which:      # 화면용 줄인 격자 (같은 영역, 간격 3배)
        json.dump(deflection_2d(0.12, 256, [2.0, 4.0, 6.0]), open(os.path.join(OUT, 'deflection_2d_small.json'), 'w'), indent=1)
    if 'deflection' in which:            # 원본 크기 (문서의 결과와 같은 설정)
        json.dump(deflection_2d(0.04, 768, [2.0, 4.0, 8.0, 12.0]), open(os.path.join(OUT, 'deflection_2d.json'), 'w'), indent=1)
    if 'gravity_small' in which:         # 화면용: 128², 간격 0.5, dt 1.0, 1.25 케플러 주기 전부
        tk = 2 * np.pi * 6.0 / np.sqrt(0.1 / 24)
        json.dump(self_gravity(0.5, 128, 1.0, 0.2, 375, 1.25 * tk, 10), open(os.path.join(OUT, 'self_gravity_small.json'), 'w'), indent=1)
    if 'modes' in which:
        json.dump(modes(), open(os.path.join(OUT, 'modes.json'), 'w'), indent=1)
    if 'gravity' in which:               # 원본 크기: 256², 간격 0.25, dt 0.1, 원본 바닥 상태 설정. 궤도는 처음 100 시간 단위만
        json.dump(self_gravity(0.25, 256, 0.1, 0.05, 1500, 100.0, 100), open(os.path.join(OUT, 'self_gravity.json'), 'w'), indent=1)
