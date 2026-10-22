"""
시간 그리드 사고 실험 — 텐서 3단계: 자연 길이 규칙 (하중이 막의 자연 길이를 바꾼다)

변수 (정적, 약한 장): 시계 몫 h00 (시간 몫 N), 막 변형 h_ij (공간 몫 ψ, 6성분)
에너지 (푸리에, 파수 q):
  F = V(h)                      막끼리의 곡률 에너지 (텐서 2단계에서 유일하게 정해진 형태)
    + b1 · h00 · R(h)           시계 몫과 공간 곡률의 맞물림,  R(h) = q_i q_j h_ij - q² tr h
    + b2 · q² · h00²            시계 몫 자체의 에너지
    + K · Σ_e (n_e·h·n_e)²      막 자신이 자연 길이로 돌아가려는 스프링 (13 방향)
    - (h00 ρ + h_ij T_ij)       하중이 자연 길이를 바꾸는 항 (원천 결합)
정적 장: ∂F/∂x = 0.  원천: 정지한 점 물질 (ρ = 1, T_ij = 0 -> 막에 직접 하중 없음)

관측량 (이름표 무관):
  γ_eff = h_zz / h00 at q ⟂ z   (빛은 z 방향, 휘어짐 ∝ h00 + h_zz,  GR 이면 1)
  q² h00 : q 에 무관하면 시계 지연이 1/r (먼 거리까지 이어짐), q→0 에서 0 으로 가면 유카와(끊김)
"""
import numpy as np
from itertools import product
from mode_count_test import BASIS, form, vec, C3

dirs = []
for d in product((-1, 0, 1), repeat=3):
    d = np.array(d, float)
    if any(d) and not any(np.array_equal(-d, e) for e in dirs):
        dirs.append(d)
NS = [d / np.linalg.norm(d) for d in dirs]          # 13 막 방향


def system(q, b1, b2, K):
    _, V = C3(q)                                      # 6x6, 막 곡률 에너지
    Rv = np.array([q @ E @ q - (q @ q) * np.trace(E) for E in BASIS])
    S = form(lambda h: sum((n @ h @ n)**2 for n in NS))
    Q = np.zeros((7, 7))
    Q[1:, 1:] = 2 * V + 2 * K * S                     # F 의 이차항 -> 헤세 행렬
    Q[0, 0] = 2 * b2 * (q @ q)
    Q[0, 1:] = Q[1:, 0] = b1 * Rv
    J = np.zeros(7); J[0] = 1.0                       # ρ = 1, T_ij = 0
    return Q, J


def solve(q, b1, b2, K):
    Q, J = system(q, b1, b2, K)
    x, *_ = np.linalg.lstsq(Q, J, rcond=1e-12)        # 이름표 방향은 해에 영향 없음
    resid = np.linalg.norm(Q @ x - J)
    h00 = x[0]
    h = sum(c * E for c, E in zip(x[1:], BASIS))
    return h00, h[2, 2], resid


def scan(label, b1, b2, K, qs=(0.02, 0.1, 0.5)):
    out = []
    for qm in qs:
        q = np.array([qm, 0, 0])
        h00, hzz, res = solve(q, b1, b2, K)
        out.append((qm, hzz / h00, qm**2 * h00, res))
    g = '  '.join(f"{o[1]:+.3f}" for o in out)
    f = '  '.join(f"{o[2]:+.4f}" for o in out)
    r = max(o[3] for o in out)
    print(f"{label:<34} γ_eff [{g}]   q²·h00 [{f}]   잔차 {r:.0e}")


if __name__ == '__main__':
    print("파수 q = 0.02, 0.1, 0.5 (작을수록 먼 거리)\n")
    print("1) 기준: b1 = -2, b2 = 0, K = 0")
    scan('기준', -2, 0, 0)
    print("\n2) 맞물림 b1 을 바꾸면")
    for b1 in (-1, -3):
        scan(f'b1 = {b1}', b1, 0, 0)
    print("\n3) 시계 몫 자체에 에너지 b2 를 주면")
    for b2 in (0.5, -0.5, 2.0):
        scan(f'b2 = {b2}', -2, b2, 0)
    print("\n4) 막이 자연 길이로 돌아가려는 스프링 K 를 주면")
    for K in (1e-4, 1e-3, 1e-2):
        scan(f'K = {K:g}', -2, 0, K, qs=(0.002, 0.02, 0.1, 0.5))
