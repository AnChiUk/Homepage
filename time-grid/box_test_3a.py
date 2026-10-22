"""
시간 그리드 사고 실험 — 시험 3-a: 상자 변환 (3D 구대칭, Z 벽 + 벽 하중 측정)

질문: 같은 에너지(먼 곳 틱 기준)를 담은 '물질 상자'와 '빛 상자'의 먼 곳 시간 몫이 같은가?
      그리고 그러려면 벽 응력이 필요한가?

격자 (반지름 방향, 유한 부피):
  m_i V_i u_i'' = kap A (u_{i+1}-u_i)/h - kap A (u_i-u_{i-1})/h - k_i V_i u_i
벽: r > R 에서 m, kappa, k 를 모두 F 배 (시험 2의 숨은 방향 = 임피던스만 키움, 속도·시계 그대로)

응력-에너지 (L = 1/2 m u_t^2 - 1/2 kap u_r^2 - 1/2 k u^2):
  rho = 1/2 m u_t^2 + 1/2 kap u_r^2 + 1/2 k u^2
  p_r = kap u_r^2 + L,  p_t = L,  Sigma p = kap u_r^2 + 3L

약한 장에서 먼 곳 장(1/r 계수) = 원천의 부피 적분. 후보:
  (가) rho              (나) rho + Sigma p (파동만)       (나') rho + Sigma p (파동 + 벽)
벽 응력은 힘 평형(라플라스 식)에서:  int Sigma p_wall dV = -3 V P,  P = 벽이 받는 압력
"""
import numpy as np
from scipy.linalg import eigh_tridiagonal

R, MU, F = 1.0, 20.0, 1.0e4
H = R / 1000.0
R_OUT = R + 0.05


def build():
    n_in = int(round(R / H))
    n = int(round(R_OUT / H)) + 1
    r = np.arange(n) * H                     # 노드
    rl = (np.arange(n - 1) + 0.5) * H        # 링크
    Rw = (n_in + 0.5) * H                    # 벽 위치(노드 사이)
    V = 4 * np.pi / 3 * ((r + H / 2)**3 - np.clip(r - H / 2, 0, None)**3)
    A = 4 * np.pi * rl**2
    f_node = np.where(r < Rw, 1.0, F)
    f_link = np.where(rl < Rw, 1.0, F)
    m, k, kap = f_node, MU**2 * f_node, f_link
    return dict(r=r, rl=rl, Rw=Rw, V=V, A=A, m=m, k=k, kap=kap, n=n)


def modes(g, omega_lo, omega_hi):
    """일반화 고유문제 K u = w^2 M u (끝 노드 고정) -> 대칭화 후 삼중대각 고유분해"""
    n = g['n'] - 1                           # 마지막 노드 고정(u=0)
    M = g['m'][:n] * g['V'][:n]
    c = g['kap'] * g['A'] / H                # 링크 강성
    diag = g['k'][:n] * g['V'][:n] + c[:n] + np.r_[0, c[:n - 1]]
    off = -c[:n - 1]
    s = 1 / np.sqrt(M)
    w2, vec = eigh_tridiagonal(diag * s * s, off * s[:-1] * s[1:],
                               select='v', select_range=(omega_lo**2, omega_hi**2))
    u = vec * s[:, None]
    u = np.vstack([u, np.zeros(u.shape[1])])
    return np.sqrt(w2), u


def inside_fraction(g, u, w):
    e = 0.5 * g['m'] * g['V'] * (w**2 + MU**2) * u**2      # 대략적 노드 에너지
    return e[g['r'] < g['Rw']].sum() / e.sum()


def run_and_average(g, u0, omega, periods=40):
    """정지 모드에서 출발해 leapfrog 로 시간 진행, 시간 평균 응력-에너지 측정"""
    M = g['m'] * g['V']
    c = g['kap'] * g['A'] / H
    om_max = np.sqrt(np.max((g['k'] * g['V'] + 2 * np.r_[c, 0] + 2 * np.r_[0, c]) / M))
    dt = 0.4 * 2 / om_max
    T = periods * 2 * np.pi / omega
    nst = int(T / dt)

    def acc(u):
        fl = c * np.diff(u)
        a = np.r_[fl, 0] - np.r_[0, fl] - g['k'] * g['V'] * u
        a = a / M
        a[-1] = 0.0
        return a
    u, v = u0.copy(), np.zeros_like(u0)
    a = acc(u)
    S = dict(kin=0.0, pot=0.0, grad=0.0, pr_wall=0.0)
    iw = int(np.searchsorted(g['rl'], g['Rw'])) - 1          # 벽 바로 안쪽 링크
    cnt = 0
    for _ in range(nst):
        v += 0.5 * dt * a
        u += dt * v
        a = acc(u)
        v += 0.5 * dt * a
        ur = np.diff(u) / H
        kin = 0.5 * g['m'] * v**2                         # 노드 밀도
        pot = 0.5 * g['k'] * u**2
        grad = 0.5 * g['kap'] * ur**2                     # 링크 밀도
        S['kin'] += np.sum(kin * g['V'])
        S['pot'] += np.sum(pot * g['V'])
        S['grad'] += np.sum(grad * g['A'] * H)
        # 벽 바로 안쪽 링크의 p_r = kap u_r^2 + L
        Lnode = kin - pot
        Lw = 0.5 * (Lnode[iw] + Lnode[iw + 1]) - grad[iw]
        S['pr_wall'] += 2 * grad[iw] + Lw
        cnt += 1
    for kk in S:
        S[kk] /= cnt
    E = S['kin'] + S['pot'] + S['grad']
    int_L = S['kin'] - S['grad'] - S['pot']
    int_sigp = 2 * S['grad'] + 3 * int_L                 # kap u_r^2 = 2*grad
    Vbox = 4 * np.pi / 3 * g['Rw']**3
    P = S['pr_wall']
    return dict(E=E, sigp=int_sigp, P=P, wall=-3 * Vbox * P, dt=dt, steps=nst)


if __name__ == '__main__':
    g = build()
    boxes = []
    # 물질 상자: 가장 낮은 모드 (정지 진동, 압력 거의 0)
    w, U = modes(g, MU * 0.99, MU * 1.2)
    fr = [inside_fraction(g, U[:, j], w[j]) for j in range(len(w))]
    j = int(np.argmax(fr))
    boxes.append(('물질 상자 (최저 모드)', w[j], U[:, j], fr[j]))
    # 빛 상자: q ~ 10 mu 인 높은 모드 (진행파의 겹침, Sigma p ~ rho)
    q_t = 10 * MU
    wt = np.sqrt(MU**2 + q_t**2)
    w, U = modes(g, wt * 0.995, wt * 1.005)
    fr = [inside_fraction(g, U[:, j], w[j]) for j in range(len(w))]
    j = int(np.argmax(fr))
    boxes.append(('빛 상자 (q≈10μ 모드)', w[j], U[:, j], fr[j]))

    print(f"R={R}, mu={MU}, 벽 임피던스 비 F={F:g}, h={H}")
    print(f"{'상자':<22}{'ω':>8}{'안쪽비율':>10}{'Σp/ρ(파동)':>12}{'3VP/E':>9}{'(가)':>8}{'(나)':>8}{'(나′)':>8}")
    for name, om, u0, frac in boxes:
        r = run_and_average(g, u0, om)
        E = r['E']
        sp = r['sigp'] / E
        wl = r['wall'] / E
        print(f"{name:<22}{om:>8.2f}{frac:>10.6f}{sp:>12.4f}{-wl:>9.4f}"
              f"{1.0:>8.3f}{1+sp:>8.3f}{1+sp+wl:>8.3f}")
    print("\n(가) rho만, (나) rho+Σp 파동만, (나′) rho+Σp 파동+벽 : 먼 곳 장 세기, E=1로 정규화")
