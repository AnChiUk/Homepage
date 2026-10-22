"""
시간 그리드 사고 실험 — 동역학 1: 물질이 만든 장 속에서 파속이 휘는가

흐름 (모두 그리드 규칙):
  1) 무거운 물질 덩어리(가우스, 반지름 RS)의 에너지 ρ 가 텐서 3단계 규칙으로 시계 몫 h00 과
     막 변형 h_ij 를 만든다.  규칙에서 읽은 값: q² h00 = C_RULE ρ(q),  h_zz/h00 = γ_RULE
     -> Φ = -h00/2,  Ψ = γ Φ  (3D 점 원천: Φ(r) = -GM erf(r/(√2 RS)) / r)
  2) 시간 몫 N = e^{Φ}, 공간 몫 ψ = e^{-Ψ} 가 그리드 재료값을 바꾼다 (빛이 지나는 평면 위 2D 격자):
     m = ψ²/N,  κ = N,  k = N ψ² μ²     (2D 에서 √-g g^{μν} 대응. 국소 분산은 3D 와 같아 궤적이 같음)
  3) 그 격자 위로 속도 v 인 시험 파속을 충돌 거리 b 로 보내고, 지나간 뒤 휨각 θ = ΔP_x / P_z 를 잰다.
예측 (약한 장): θ = (2GM / b v²) (1 + γ v²)
  -> θ v² / (2GM/b) 를 v² 에 대해 그리면 절편 1 (뉴턴 끌림), 기울기 γ (공간 몫, 빛의 2배)
"""
import numpy as np
from scipy.special import erf
from growth_rule_test import solve

C_RULE = solve(np.array([0.1, 0, 0]), -2, 0, 0)[0] * 0.1**2      # q² h00 / ρ
GAMMA_RULE = (lambda r: r[1] / r[0])(solve(np.array([0.1, 0, 0]), -2, 0, 0))

MU, A, NG = 4.0, 0.04, 768            # 시계 진동수, 격자 간격, 격자 수 (한 변)
L = A * NG
RS, B, GM = 1.5, 6.0, 0.06            # 원천 반지름, 충돌 거리, 원천 세기
SIG = 2.0                              # 시험 파속 폭
Z0 = -12.0


def fields(gamma):
    c = (np.arange(NG) - NG // 2) * A
    X, Z = np.meshgrid(c, c, indexing='ij')                     # X: 옆(휨 방향), Z: 진행 방향
    r = np.sqrt(X**2 + Z**2) + 1e-12
    Phi = -GM * erf(r / (np.sqrt(2) * RS)) / r
    N, psi = np.exp(Phi), np.exp(-gamma * Phi)
    m = psi**2 / N
    k = N * psi**2 * MU**2
    kap_x = 0.5 * (N + np.roll(N, -1, 0))                       # 링크 값 (평균)
    kap_z = 0.5 * (N + np.roll(N, -1, 1))
    return X, Z, m, k, kap_x, kap_z


def run(q, gamma):
    X, Z, m, k, kx, kz = fields(gamma)
    om = np.sqrt(MU**2 + (4 / A**2) * np.sin(q * A / 2)**2)      # 먼 곳 격자 분산
    vg = np.sin(q * A) / (A * om)
    env = np.exp(-((X - B)**2 + (Z - Z0)**2) / (2 * SIG**2))
    u = env * np.cos(q * (Z - Z0))
    v = om * env * np.sin(q * (Z - Z0))                          # +z 로 진행
    dt = 0.35 * 2 / np.sqrt(np.max((k + 4 * (kx + kz) / A**2) / m))
    T = 2 * abs(Z0) / vg
    nst = int(T / dt)

    def acc(u):
        fx = kx * (np.roll(u, -1, 0) - u) / A**2
        fz = kz * (np.roll(u, -1, 1) - u) / A**2
        return (fx - np.roll(fx, 1, 0) + fz - np.roll(fz, 1, 1) - k * u) / m

    def momentum(u, v):
        ux = (np.roll(u, -1, 0) - np.roll(u, 1, 0)) / (2 * A)
        uz = (np.roll(u, -1, 1) - np.roll(u, 1, 1)) / (2 * A)
        return -np.sum(m * v * ux), -np.sum(m * v * uz)

    Px0, Pz0 = momentum(u, v)
    a = acc(u)
    for _ in range(nst):
        v += 0.5 * dt * a
        u += dt * v
        a = acc(u)
        v += 0.5 * dt * a
    Px1, Pz1 = momentum(u, v)
    theta = -(Px1 - Px0) / Pz1          # 양수 = 물질 쪽으로 휨(끌림)
    return vg, theta


if __name__ == '__main__':
    print(f"규칙에서 읽은 값: q²h00/ρ = {C_RULE:.4f}, γ = {GAMMA_RULE:.4f}")
    print(f"격자 {NG}x{NG}, 간격 {A}, μ = {MU}, 원천 GM = {GM}, 충돌 거리 b = {B}")
    print(f"{'경우':<16}{'q':>6}{'v':>8}{'θ(rad)':>10}{'θv²/(2GM/b)':>14}{'예측':>9}")
    import sys
    cases = [(g, q) for g in (GAMMA_RULE, 0.0) for q in (2.0, 4.0, 8.0, 12.0)]
    if len(sys.argv) > 1:
        cases = cases[:int(sys.argv[1])]
    res = {}
    for g, q in cases:
        vg, th = run(q, g)
        norm = th * vg**2 / (2 * GM / B)
        res.setdefault(g, []).append((vg**2, norm))
        label = '규칙 (γ=1)' if g == GAMMA_RULE else '대조 (γ=0)'
        print(f"{label:<16}{q:>6.1f}{vg:>8.4f}{th:>10.5f}{norm:>14.4f}{1 + g * vg**2:>9.4f}", flush=True)
    for g, pts in res.items():
        if len(pts) >= 2:
            x, y = np.array(pts).T
            s, i = np.polyfit(x, y, 1)
            label = '규칙' if g == GAMMA_RULE else '대조'
            print(f"{label}: 맞춤 θv²/(2GM/b) = {i:.3f} + {s:.3f}·v²  ->  잰 γ = 기울기/절편 = {s/i:.3f}  (기대 {g:.0f})")
    print("절편이 1에서 벗어나는 것은 유한한 경로(±12)와 휘면서 가까워지는 효과로, 모든 속도에 비슷하게 걸림")
