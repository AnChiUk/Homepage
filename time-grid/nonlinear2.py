"""
시간 그리드 사고 실험 — 비선형 2: 장 자신의 하중을 끝까지 되먹이면 β_PPN 은 얼마인가

규칙 (기존 규칙에서 바로 나오는 것만 씀):
  1. 상대 변화: 막 변형 U 가 재료값을 바꾸는 양은 그 자리 값에 대한 비율이다 (측정 원칙: 절대 시계가 없으므로
     dN/N = -dU).  -> N = e^{-U},  ψ = e^{γU}   (문서의 "비선형 결합" 지수 꼴)
  2. 정적 장도 그리드 위에서 막을 지나 퍼진다. 그러므로 장 자신의 에너지도 자기가 바꾼 막을 지난다:
     3D 막의 전달 세기 κ = Nψ (모든 파동과 같은 재료값).
        E = (1/8πG) ∫ Nψ |∇U|² d³x + ∫ N ρ d³x        (ρ: 그리드당 질량, 그리드 수는 변하지 않음)
  3. 원천은 한 에너지 함수에서: δE/δU = 0
        ∇²U = -4πG ρ e^{-γU} + ((1-γ)/2) |∇U|²
     |∇U|² 항이 장 자신의 하중이다: 시계 쪽 하중 ρ_f = |∇U|²/8πG 와 공간 쪽 하중(비선형 1의 t_ij 대각합
     Σt_ii = -|∇U|²/8πG)이 ρ_f + γΣt_ii 로 들어간다. γ = 1 이면 정확히 상쇄된다(정적 장은 ρ+Σp = 0).
  예측: 바깥에서 U = m/r + (1-γ)m²/(4r²) + …  ->  -g00 = N² = 1 - 2m/r + 2β m²/r²,  β = (3+γ)/4
        근일점 이동 = (2+2γ-β)/3 × 6πm/p = (5+7γ)/12 × 6πm/p

가. 3D 격자 (간격 0.25, 128³, 자유 경계 FFT 푸아송)에서 되먹임을 반복해 정적 장을 만들고 β 를 잰다.
    시계 몫 N 으로 쓰면 ∇²N = 4πGρN² + |∇N|²/N (γ = 1): 장 자신의 하중 |∇N|²/N 을 한 번씩 되먹일 때마다
    m/r 의 한 차수씩 생긴다. 대조군: 절대 변화(N = 1 - U, U 는 뉴턴 장) -> β = 1/2.
나. 그 장 속 파속 궤도. 그리드 파동의 분산 ω = N √(μ² + k²/ψ²) (동역학 1 의 재료값)에서 나오는 광선 운동으로
    여러 m/p 의 근일점 이동을 재고 m/p -> 0 으로 맞춰 계수를 얻는다.

실행: python nonlinear2.py     결과 nonlinear2_out.txt, viz_data/nonlinear2.json
"""
import json, os
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

G = 1 / (32 * np.pi)                  # 2-b-1과 같은 규칙 값


# ── 가. 3D 격자 정적 장 ─────────────────────────────────────────
class Lattice:
    def __init__(self, n=128, a=0.25, sig=1.0, GM=0.5):
        self.n, self.a = n, a
        c = (np.arange(n) - n // 2) * a
        X, Y, Z = np.meshgrid(c, c, c, indexing='ij')
        self.r = np.sqrt(X**2 + Y**2 + Z**2)
        rho = np.exp(-self.r**2 / (2 * sig**2))
        self.rho = rho / (rho.sum() * a**3) * (GM / G)          # 그리드당 질량 합 = GM/G
        # 자유 경계 그린 함수 -1/(4πr) 를 2n 상자에 깔고 FFT 합성곱 (원점 칸은 정육면체 평균 2.380/a)
        m = 2 * n
        k = np.arange(m); k = np.minimum(k, m - k) * a
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        R = np.sqrt(KX**2 + KY**2 + KZ**2)
        R[0, 0, 0] = a / 2.380077
        self.gk = np.fft.rfftn(-1 / (4 * np.pi * R)) * a**3

    def poisson(self, S):
        """∇²U = S 의 자유 경계 해 (무한대에서 0)"""
        n = self.n
        P = np.zeros((2 * n,) * 3); P[:n, :n, :n] = S
        U = np.fft.irfftn(np.fft.rfftn(P) * self.gk, s=P.shape)
        return U[:n, :n, :n]                                      # 2n 상자라 서로 감기지 않음

    def grad2(self, U):
        """링크 차분 제곱을 노드로 평균 (비선형 1 의 장 에너지 정의와 같음). 가장자리 링크는 버림"""
        a, g2 = self.a, np.zeros_like(U)
        for ax in range(3):
            d = np.diff(U, axis=ax) / a
            sq = d**2
            pad_lo = [(0, 0)] * 3; pad_lo[ax] = (1, 0)
            pad_hi = [(0, 0)] * 3; pad_hi[ax] = (0, 1)
            g2 += 0.5 * (np.pad(sq, pad_lo) + np.pad(sq, pad_hi))
        return g2

    def solve_rule(self, gamma, tol=1e-12, it_max=60):
        U = np.zeros_like(self.rho); hist = []
        for it in range(it_max):
            S = -4 * np.pi * G * self.rho * np.exp(-gamma * U) + 0.5 * (1 - gamma) * self.grad2(U)
            Un = self.poisson(S)
            ch = np.abs(Un - U).max(); U = Un; hist.append(ch)
            if ch < tol:
                break
        return U, hist

    def bootstrap_N(self, orders=4):
        """γ = 1 을 시계 몫 N 으로: ∇²N = 4πGρN² + |∇N|²/N. 장 자신의 하중을 한 번씩 되먹인다"""
        N = np.ones_like(self.rho); out = [N.copy()]
        for _ in range(orders):
            S = 4 * np.pi * G * self.rho * N**2 + self.grad2(N) / N
            N = 1 + self.poisson(S); out.append(N.copy())
        return out


def fit_beta(r, N2, r_lo=6.0, r_hi=14.0):
    """N² = c0 + b1/r + b2/r² + b3/r³ 를 맞춰 m = -b1/(2c0), β = c0·b2/(2·(b1/2)²) (먼 곳 N 을 1 로 다시 잼)"""
    sel = (r >= r_lo) & (r <= r_hi)
    x = 1 / r[sel]
    A = np.vstack([np.ones_like(x), x, x**2, x**3]).T
    c = np.linalg.lstsq(A, N2[sel], rcond=None)[0]
    m = -c[1] / (2 * c[0])
    beta = (c[2] / c[0]) / (2 * m**2)
    return m, beta


def part_lattice():
    L = Lattice()
    rows, prof = [], {}
    rr = L.r.ravel()
    axis = L.r[L.n // 2:, L.n // 2, L.n // 2]
    for gamma in (1.0, 0.5, 0.0):
        U, hist = L.solve_rule(gamma)
        N2 = np.exp(-2 * U).ravel()
        m, beta = fit_beta(rr, N2)
        rows.append(dict(rule=f'규칙 γ = {gamma:g}', gamma=gamma, m=m, beta=beta, beta_pred=(3 + gamma) / 4,
                         iters=len(hist)))
        prof[f'g{gamma:g}'] = U[L.n // 2:, L.n // 2, L.n // 2].tolist()
    # 대조군: 절대 변화 N = 1 - U_뉴턴
    Ulin = L.poisson(-4 * np.pi * G * L.rho)
    m, beta = fit_beta(rr, ((1 - Ulin)**2).ravel())
    rows.append(dict(rule='대조: 절대 변화 N = 1 - U', gamma=1.0, m=m, beta=beta, beta_pred=0.5, iters=1))
    # 되먹임 차수별 (γ = 1, 시계 몫 N)
    boot = []
    for k, N in enumerate(L.bootstrap_N(5)):
        if k == 0:
            continue
        m, beta = fit_beta(rr, (N**2).ravel())
        boot.append(dict(order=k, m=m, beta=beta, N_axis=N[L.n // 2:, L.n // 2, L.n // 2].tolist()))
    return dict(rows=rows, boot=boot, r_axis=axis.tolist(), U_axis=prof)


# ── 나. 파속 궤도의 근일점 이동 ─────────────────────────────────
def field(rule, m):
    """(N, N', ψ, ψ') 를 r 의 함수로. 규칙 장은 바깥 정확해: e^{-kU/2} = 1 - k m/(2r), k = 1-γ"""
    if rule == 'abs':
        return lambda r: (1 - m / r, m / r**2, 1 + m / r, -m / r**2)
    g = float(rule); k = 1 - g

    def f(r):
        if k == 0:
            U, Up = m / r, -m / r**2
        else:
            U = -2 / k * np.log1p(-k * m / (2 * r)); Up = -(m / r**2) / (1 - k * m / (2 * r))
        N, psi = np.exp(-U), np.exp(g * U)
        return N, -Up * N, psi, g * Up * psi
    return f


def precession(rule, m, p, e, n_orb=12, keep=False):
    f = field(rule, m)
    rp, ra = p / (1 + e), p / (1 - e)

    def V(r, L):
        N, _, psi, _ = f(r)
        return N * np.sqrt(1 + (L / (r * psi))**2)
    L0 = np.sqrt(m * p)
    L = brentq(lambda L: V(rp, L) - V(ra, L), 0.5 * L0, 2.0 * L0, xtol=1e-15, rtol=1e-15)

    def rhs(t, y):
        r, phi, pr = y
        N, Np, psi, psip = f(r)
        q2 = pr**2 + (L / r)**2
        S = np.sqrt(1 + q2 / psi**2)
        dr = N * pr / (psi**2 * S)
        dphi = N * L / (r**2 * psi**2 * S)
        dpr = -(Np * S + N / (2 * S) * (-2 * L**2 / (r**3 * psi**2) - 2 * q2 * psip / psi**3))
        return [dr, dphi, dpr]

    peri = lambda t, y: y[2]
    peri.direction = 1
    T = 2 * np.pi * np.sqrt((0.5 * (rp + ra))**3 / m)                 # 뉴턴 주기 (μ = 1, 시험 입자)
    sol = solve_ivp(rhs, (0, (n_orb + 0.5) * T), [rp, 0.0, 0.0], method='DOP853', rtol=1e-12, atol=1e-14,
                    events=peri, dense_output=keep)
    te = sol.t_events[0]
    ph = np.concatenate([[0.0], sol.y_events[0][te > 0.5 * T, 1]])     # 출발점(t = 0)의 근일점은 빼고
    dphi = np.mean(np.diff(ph)) - 2 * np.pi
    out = dict(dphi=dphi, ratio=dphi / (6 * np.pi * m / p))
    if keep:
        t = np.linspace(0, sol.t[-1], 3000)
        r, phi, _ = sol.sol(t)
        out['xy'] = np.round(np.vstack([r * np.cos(phi), r * np.sin(phi)]).T / p, 4).tolist()
    return out


def part_orbit():
    rules = [('1', 1.0, '규칙 γ = 1'), ('0.5', 0.5, '규칙 γ = 0.5'), ('0', 0.0, '규칙 γ = 0'), ('abs', 1.0, '대조: 절대 변화')]
    xs = [0.001, 0.002, 0.004, 0.008, 0.016]
    res = []
    for key, g, name in rules:
        beta = 0.5 if key == 'abs' else (3 + g) / 4
        pred = (2 + 2 * g - beta) / 3
        ratios = {}
        for e in (0.3, 0.6):
            ratios[e] = [precession(key, x, 1.0, e)['ratio'] for x in xs]
        # m/p -> 0 맞춤 (2차)
        c03 = np.polyfit(xs, ratios[0.3], 2)[-1]
        c06 = np.polyfit(xs, ratios[0.6], 2)[-1]
        rose = precession(key, 0.03, 1.0, 0.5, n_orb=6, keep=True)
        res.append(dict(key=key, name=name, gamma=g, beta=beta, pred=pred, xs=xs,
                        ratio_e03=ratios[0.3], ratio_e06=ratios[0.6], c0_e03=c03, c0_e06=c06,
                        rose=rose['xy'], rose_dphi=rose['dphi']))
    return res


if __name__ == '__main__':
    os.makedirs('viz_data', exist_ok=True)
    lat = part_lattice()
    orb = part_orbit()
    lines = ['[비선형 2-가] 3D 격자 128³ (간격 0.25, 가우스 폭 1, GM = 0.5) 정적 장의 β (N² 를 6 ≤ r ≤ 14 에서 맞춤)']
    for r in lat['rows']:
        lines.append(f"   {r['rule']:24s} m = {r['m']:.4f}   β = {r['beta']:.4f}   예측 {r['beta_pred']:.3f}   반복 {r['iters']}")
    lines.append('   γ = 1, 시계 몫 N 으로 장 자신의 하중을 한 번씩 되먹일 때:')
    for b in lat['boot']:
        lines.append(f"     되먹임 {b['order'] - 1}회  β = {b['beta']:.4f}")
    lines.append('[비선형 2-나] 파속 궤도 근일점 이동 / (6πm/p), m/p = 0.001 ~ 0.016, m/p -> 0 맞춤')
    for o in orb:
        lines.append(f"   {o['name']:16s} β = {o['beta']:.3f}  예측 (2+2γ-β)/3 = {o['pred']:.4f}   "
                     f"맞춤 e=0.3: {o['c0_e03']:.4f}  e=0.6: {o['c0_e06']:.4f}   "
                     f"(m/p = 0.001 에서 {o['ratio_e03'][0]:.4f})")
    print('\n'.join(lines))
    with open('nonlinear2_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    with open('viz_data/nonlinear2.json', 'w', encoding='utf-8') as f:
        json.dump(dict(G=G, lattice=lat, orbits=orb), f, ensure_ascii=False)
