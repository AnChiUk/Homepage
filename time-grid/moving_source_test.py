"""
시간 그리드 사고 실험 — 시험 4: 묶이지 않은 압력 (움직이는 파속)

질문 1: (E/M 은 정의상 gamma 와 같으므로 쓰지 않고, 독립값 omega/mu 와 Sigma p/E 로 비교)
        격자 파속의 에너지 E, 운동량 P, 압력 Sigma p 가 '움직이는 이름표'(창발 로런츠 변환)를
        따르는가?  연속 극한 예측: E = gamma M, P = gamma M v, Sigma p = gamma M v^2 (M = 정지 에너지)
질문 2: 원천 후보가 정지 파속과 움직이는 파속에서 일관적인가?
  - U가 스칼라(그리드마다 값 하나)이면, 움직이는 원천의 장 = 정지 원천의 장을 이름표만 바꾼 것.
    스칼라 밀도의 부피 적분은 1/gamma 배가 되어야 함:  int S_움직임 = (1/gamma) int S_정지
    일관성 비 C = int S_움직임 / (M/gamma)  -> 1 이어야 통과
  - U가 텐서(막 방향별 변형)이면, 원천은 응력-에너지 성분 자체 (T00, T0x, Txx) 이고
    E, P, Sigma p 가 텐서로 변환되기만 하면 자동으로 일관적.

1D 격자, m = kappa = 1 (홉 속도 1), k = mu^2. 평평한 배경 (약한 장 1차).
"""
import numpy as np

MU, H, L = 5.0, 0.05, 600.0
SIG = 25.0


def lattice_omega(q):
    return np.sqrt(MU**2 + (4 / H**2) * np.sin(q * H / 2)**2)


def measure(q, periods=6):
    n = int(L / H)
    x = (np.arange(n) - n // 2) * H
    om = lattice_omega(q)
    env = np.exp(-x**2 / (2 * SIG**2))
    u = env * np.cos(q * x)
    v = om * env * np.sin(q * x)          # 오른쪽으로 진행
    dt = 0.4 * 2 / np.sqrt(MU**2 + 4 / H**2)
    nst = int(periods * 2 * np.pi / om / dt) + 1
    acc = lambda u: (np.roll(u, -1) - 2 * u + np.roll(u, 1)) / H**2 - MU**2 * u
    a = acc(u)
    S = np.zeros(3)
    for _ in range(nst):
        v += 0.5 * dt * a
        u += dt * v
        a = acc(u)
        v += 0.5 * dt * a
        ux = (np.roll(u, -1) - u) / H                         # 링크
        ux_node = 0.5 * (ux + np.roll(ux, 1))
        kin, pot, grad = 0.5 * v**2, 0.5 * MU**2 * u**2, 0.5 * ux**2
        E = H * np.sum(kin + pot + grad)
        P = -H * np.sum(v * ux_node)
        Lag = H * np.sum(kin - pot - grad)
        Sp = H * np.sum(2 * grad) + Lag                       # 1D: p_x = kap u_x^2 + L
        S += (E, P, Sp)
    E, P, Sp = S / nst
    return E, P, Sp, om


if __name__ == '__main__':
    print(f"mu={MU}, h={H}  (홉 속도 = 1)")
    print(f"{'q':>6}{'q·h':>6}{'v=P/E':>8}{'v격자':>8}{'ω/μ':>8}{'γ(v)':>8}{'Σp/E':>8}{'v²':>8}"
          f"{'C(ρ)':>8}{'C(ρ+Σp)':>9}{'C(ρ−Σp)':>9}")
    for q in (0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 40.0):
        E, P, Sp, om = measure(q)
        vel = P / E
        vlat = np.sin(q * H) / (H * om)                       # 격자 군속도 dω/dq
        M = np.sqrt(E**2 - P**2)
        gam = 1 / np.sqrt(1 - vel**2)
        rest = M / gam                                          # 스칼라 일관성의 기준
        print(f"{q:>6.1f}{q*H:>6.2f}{vel:>8.4f}{vlat:>8.4f}{om/MU:>8.4f}{gam:>8.4f}{Sp/E:>8.4f}{vel**2:>8.4f}"
              f"{E/rest:>8.3f}{(E+Sp)/rest:>9.3f}{(E-Sp)/rest:>9.3f}")
