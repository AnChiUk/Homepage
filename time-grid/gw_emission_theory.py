"""
시간 그리드 사고 실험 — 동역학 2-b-1 분석: 시뮬레이션 진폭을 같은 규칙의 정확한 해와 비교

규칙의 TT 방정식 ḧ = ∇²h + ½ T_TT (푸리에 TT 투영) 에서 점 4중극 원천 T = Q δ(x) e^{-iΩt} 의
나가는 정확한 해 (연속 극한):
    h_ij = ½[Q_ij F0 + Q_kj ∂i∂k F2 + Q_ik ∂k∂j F2 - ½δ_ij Q_kl ∂k∂l F2 + ½ Q_kl ∂i∂j∂k∂l F4]
    F0 = e^{iΩr}/(4πr),  F2 = (e^{iΩr} - 1)/(4πΩ²r),  F4 = (e^{iΩr} - 1)/(4πΩ⁴r) + r/(8πΩ²)
(푸리에 TT 투영의 n̂n̂/q², n̂n̂n̂n̂/q⁴ 항을 부분분수로 풀어 얻음. 미분은 4차 유한차분)
먼 곳에서 r·h 는 4중극 공식 값으로 가지만, kr ≲ 8 에서는 투영 때문에 ±5% 이상 출렁이며 다가간다.
-> 시뮬레이션 r·h/예측 을 이 정확한 모양과 반지름마다 비교한다 (흡수층 근처는 제외).

실행: python gw_emission_theory.py [viz_data/gw_emission_*.json ...]
"""
import json, sys
import numpy as np

D = 0.25
ST2 = [(-2, -1 / 12), (-1, 4 / 3), (0, -5 / 2), (1, 4 / 3), (2, -1 / 12)]
ST1 = [(-2, 1 / 12), (-1, -2 / 3), (1, 2 / 3), (2, -1 / 12)]
E3 = np.eye(3)


def d1(f, i):
    return lambda x: sum(w * f(x + s * D * E3[i]) for s, w in ST1) / D


def d2(f, i, j):
    if i == j:
        return lambda x: sum(w * f(x + s * D * E3[i]) for s, w in ST2) / D**2
    return d1(d1(f, i), j)


def field(x, Q, Om):
    F0 = lambda r: np.exp(1j * Om * r) / (4 * np.pi * r)
    F2 = lambda r: (np.exp(1j * Om * r) - 1) / (4 * np.pi * Om**2 * r)
    F4 = lambda r: (np.exp(1j * Om * r) - 1) / (4 * np.pi * Om**4 * r) + r / (8 * np.pi * Om**2)
    rad = lambda F: (lambda y: F(np.linalg.norm(y)))
    f0, f2, f4 = rad(F0), rad(F2), rad(F4)
    D2 = np.array([[d2(f2, i, j)(x) for j in range(3)] for i in range(3)])
    g = lambda y: sum(Q[k, l] * d2(f4, k, l)(y) for k in range(3) for l in range(3) if Q[k, l] != 0)
    D4 = np.array([[d2(g, i, j)(x) for j in range(3)] for i in range(3)])
    return 0.5 * (Q * f0(x) + Q.T @ D2 + D2 @ Q - 0.5 * np.eye(3) * np.einsum('kl,kl->', Q, D2) + 0.5 * D4)


def profile(radii, Om):
    """정면(z축) r|h+| 와 측면(x축) h+/정면, 둘 다 먼 곳 값 대비"""
    Q = np.diag([1.0, -1.0, 0.0])
    far = 0.5 / (4 * np.pi)
    out = []
    for r in radii:
        hz = field(np.array([0, 0, r], float), Q, Om)
        hx = field(np.array([r, 0, 0], float), Q, Om)
        face = abs(0.5 * (hz[0, 0] - hz[1, 1])); edge = abs(0.5 * (hx[1, 1] - hx[2, 2]))
        out.append((r * face / far, edge / face))
    return np.array(out)


if __name__ == '__main__':
    files = sys.argv[1:] or ['viz_data/gw_emission_kinetic.json', 'viz_data/gw_emission_bound.json']
    for fn in files:
        d = json.load(open(fn, encoding='utf-8'))
        Om = 2 * d['omega']
        th = profile(d['radii'], Om)
        rh = np.array(d['rh'])
        print(f"[{fn}]  원천 {d['case']}, 격자 {d['grid']}³, 기대 비율 {d['expect']}")
        print("   반지름   kr     정확한 해   시뮬 h+   시뮬 h×   h+ ÷ (정확한 해 × 기대)   h× ÷ (…)")
        for r, (t, _), (p, x) in zip(d['radii'], th, rh):
            print(f"   {r:4d}   {Om * r:5.2f}   {t:.4f}     {p:.4f}    {x:.4f}    {p / (t * d['expect']):.4f}                  {x / (t * d['expect']):.4f}")
