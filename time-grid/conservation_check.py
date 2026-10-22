"""
동역학 2 준비: 격자 저장 파동의 응력-에너지 국소 보존 오차 (3D 격자)

격자 파동 u (m = κ = 1, k = μ²), 6방향 이웃 라플라시안, leapfrog.
연속 극한 응력-에너지:
  T00 = ½u̇² + ½|∇u|² + ½μ²u²,   T0i = -u̇ ∂_i u,   Tij = ∂_i u ∂_j u + δ_ij L,  L = ½u̇² - ½|∇u|² - ½μ²u²
보존식의 남는 값(중심 차분으로 계산):
  에너지:  r0 = ∂_t T00 + ∂_i T0i
  운동량:  ri = ∂_t T0i + ∂_j Tij
상대 오차 = ||r|| / ||∂_t T||.  파수 × 격자 간격(qa)을 바꿔 가며 잰다.
웹 시각화용: viz_data/conservation.json
"""
import json, os
import numpy as np

NG, MU, SIG = 64, 1.0, 5.0


def grad(f):
    return [(np.roll(f, -1, ax) - np.roll(f, 1, ax)) / 2 for ax in range(3)]


def lap(u):
    return sum(np.roll(u, -1, ax) - 2 * u + np.roll(u, 1, ax) for ax in range(3))


def fields(u, v):
    g = grad(u)
    g2 = sum(x * x for x in g)
    L = 0.5 * v * v - 0.5 * g2 - 0.5 * MU**2 * u * u
    T00 = 0.5 * v * v + 0.5 * g2 + 0.5 * MU**2 * u * u
    T0 = [-v * gi for gi in g]
    Tij = [[g[i] * g[j] + (L if i == j else 0) for j in range(3)] for i in range(3)]
    return T00, T0, Tij


def run(qa):
    c = np.arange(NG) - NG // 2
    X, Y, Z = np.meshgrid(c, c, c, indexing='ij')
    n = np.array([1, 1, 1]) / np.sqrt(3)
    qv = qa * n
    om = np.sqrt(MU**2 + sum(4 * np.sin(qi / 2)**2 for qi in qv))
    env = np.exp(-(X**2 + Y**2 + Z**2) / (2 * SIG**2))
    ph = qv[0] * X + qv[1] * Y + qv[2] * Z
    u = env * np.cos(ph); v = om * env * np.sin(ph)
    dt = 0.05
    acc = lambda u: lap(u) - MU**2 * u
    a = acc(u)
    snaps = []
    for k in range(3):                      # t-dt, t, t+dt 시점 저장 (속도는 반 스텝 보정)
        snaps.append((u.copy(), v.copy()))
        v += 0.5 * dt * a; u += dt * v; a = acc(u); v += 0.5 * dt * a
    (u0, v0), (u1, v1), (u2, v2) = snaps
    A0, B0, _ = fields(u0, v0); A1, B1, C1 = fields(u1, v1); A2, B2, _ = fields(u2, v2)
    dT00 = (A2 - A0) / (2 * dt)
    divT0 = sum(grad(B1[i])[i] for i in range(3))
    r0 = dT00 + divT0
    rel_e = np.linalg.norm(r0) / np.linalg.norm(dT00)
    dT0 = [(B2[i] - B0[i]) / (2 * dt) for i in range(3)]
    divT = [sum(grad(C1[i][j])[j] for j in range(3)) for i in range(3)]
    ri = [dT0[i] + divT[i] for i in range(3)]
    rel_p = np.sqrt(sum(np.sum(x * x) for x in ri)) / np.sqrt(sum(np.sum(x * x) for x in dT0))
    return rel_e, rel_p


if __name__ == '__main__':
    os.makedirs('viz_data', exist_ok=True)
    rows = []
    print(f"{'qa':>6}{'에너지 보존 오차':>16}{'운동량 보존 오차':>16}")
    for qa in (0.1, 0.2, 0.4, 0.8):
        e, p = run(qa)
        rows.append(dict(qa=qa, energy=e, momentum=p))
        print(f"{qa:>6}{e:>16.2e}{p:>16.2e}")
    json.dump(dict(note='격자 응력-에너지 국소 보존 오차 (상대값)', rows=rows),
              open('viz_data/conservation.json', 'w'), ensure_ascii=False)
