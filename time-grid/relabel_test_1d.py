"""
시간 그리드 사고 실험 — 시험 1: 이름표 바꾸기 (1D 결합 진동자)

질문: 같은 물리 상황을 서로 다른 이름표(시간 스텝 dt, 격자 간격 h,
비균일 좌표 x = x(xi))로 표현했을 때, 틱/홉으로 잰 값이 같은가?

격자 파동:  m u'' = d/dx(kappa du/dx) - k u
배경:       U(x) = U0 r0 / sqrt(x^2 + r0^2),  N = e^{-U}, psi = e^{U}  (alpha = beta = 1, N psi = 1)
1D 대응:    m = psi/N, kappa = N/psi, k = N psi mu^2   ->  omega_s = N mu,  v = N/psi

좌표 바꾸기 x -> xi (J = dx/dxi):  m' = m J,  kappa' = kappa / J,  k' = k J
(연속 극한에서 정확한 변환. 격자에서 얼마나 지켜지는지가 시험 대상)

관측량 (모두 틱 단위, 좌표값 아님)
  O1 = 시계 A(우물 중심) 틱 / 시계 B(먼 곳) 틱          -> 예측 N_A / N_B
  O2 = 파속이 B(x=+20)에서 C(x=-20)까지 가는 동안 B 시계 틱 수
"""
import numpy as np
from scipy.signal import hilbert

U0, R0, MU = 0.3, 2.0, 5.0
L, XA, XB, XC = 60.0, 0.0, 20.0, -20.0


def background(x):
    U = U0 * R0 / np.sqrt(x**2 + R0**2)
    N, psi = np.exp(-U), np.exp(U)
    return N, psi


def params_x(x):
    N, psi = background(x)
    return psi / N, N / psi, N * psi * MU**2      # m, kappa, k


# ---------- 좌표 사상 x(xi), J(xi), 역사상 ----------
def map_uniform():
    return (lambda s: s), (lambda s: np.ones_like(s)), (lambda x: x)


def map_sine(eps):
    # x = xi + eps*(XB/pi) sin(pi xi / XB): x(0)=0, x(+-XB)=+-XB, x(+-L)=+-L
    f = lambda s: s + eps * XB / np.pi * np.sin(np.pi * s / XB)
    J = lambda s: 1 + eps * np.cos(np.pi * s / XB)

    def inv(x):
        s = np.array(x, float)
        for _ in range(60):
            s = s - (f(s) - x) / J(s)
        return s
    return f, J, inv


def map_sinh(lam):
    f = lambda s: lam * np.sinh(s / lam)
    J = lambda s: np.cosh(s / lam)
    inv = lambda x: lam * np.arcsinh(np.asarray(x) / lam)
    return f, J, inv


# ---------- 격자 구성 ----------
def build(mapping, h, naive=False):
    f, J, inv = mapping
    s_end = inv(L)
    M = int(round(2 * s_end / h)) + 1
    s = np.linspace(-s_end, s_end, M)
    hs = s[1] - s[0]
    x = f(s)
    s_link = 0.5 * (s[1:] + s[:-1])
    m, _, k = params_x(x)
    _, kap, _ = params_x(f(s_link))
    if not naive:                       # 올바른 변환
        m = m * J(s)
        k = k * J(s)
        kap = kap / J(s_link)
    # naive: 노드는 옮기고 파라미터는 변환하지 않음 (틀린 이름표 바꾸기)
    return dict(s=s, x=x, hs=hs, m=m, kap=kap, k=k, inv=inv)


def omega_max(g):
    lap = (np.r_[g['kap'], 0] + np.r_[0, g['kap']]) / g['hs']**2
    return np.sqrt(np.max((g['k'] + 2 * lap) / g['m']))


def accel(u, g):
    du = np.diff(u)
    flux = g['kap'] * du / g['hs']**2
    a = np.zeros_like(u)
    a[1:-1] = (flux[1:] - flux[:-1] - g['k'][1:-1] * u[1:-1]) / g['m'][1:-1]
    return a                            # 양 끝 고정


def run(g, u0, v0, T, dt, probes):
    """leapfrog. probes: 물리 좌표 x 목록 -> 선형 보간으로 u(x,t) 기록"""
    s = g['s']
    idx, w = [], []
    for xp in probes:
        sp = float(g['inv'](xp))
        i = np.searchsorted(s, sp) - 1
        idx.append(i)
        w.append((sp - s[i]) / (s[i + 1] - s[i]))
    nsteps = int(np.ceil(T / dt))
    rec = np.zeros((nsteps + 1, len(probes)))
    u, v = u0.copy(), v0.copy()
    a = accel(u, g)

    def sample(u):
        return [u[i] * (1 - wi) + u[i + 1] * wi for i, wi in zip(idx, w)]
    rec[0] = sample(u)
    for n in range(nsteps):
        v += 0.5 * dt * a
        u += dt * v
        a = accel(u, g)
        v += 0.5 * dt * a
        rec[n + 1] = sample(u)
    t = np.arange(nsteps + 1) * dt
    return t, rec


# ---------- 측정 ----------
def clock_freq(t, y):
    """영점 교차 (선형 보간)으로 평균 진동수"""
    sgn = np.sign(y)
    i = np.where(sgn[:-1] * sgn[1:] < 0)[0]
    tz = t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i])
    return (len(tz) - 1) / (2 * (tz[-1] - tz[0]))


def peak_time(t, y):
    env = np.abs(hilbert(y))
    j = int(np.clip(np.argmax(env), 1, len(env) - 2))
    y0, y1, y2 = env[j - 1], env[j], env[j + 1]
    return t[j] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (t[1] - t[0])


def measure(g, dt_frac):
    dt = dt_frac * 2 / omega_max(g)
    x = g['x']
    # 시계: 넓은 정지 덩어리의 진동 (A, B 각각)
    sig_c = 1.5
    freqs = {}
    for name, xc in (('A', XA), ('B', XB)):
        u0 = np.exp(-(x - xc)**2 / (2 * sig_c**2))
        t, r = run(g, u0, np.zeros_like(x), 30.0, dt, [xc])
        freqs[name] = clock_freq(t, r[:, 0])
    # 신호: B에서 왼쪽(C 쪽)으로 가는 파속
    q0, sig_s = 6.0, 3.0
    mB, kapB, kB = params_x(np.array([XB]))
    om = np.sqrt((kapB * q0**2 + kB) / mB)[0]
    env = np.exp(-(x - XB)**2 / (2 * sig_s**2))
    u0 = env * np.cos(q0 * (x - XB))
    v0 = -om * env * np.sin(q0 * (x - XB))
    t, r = run(g, u0, v0, 95.0, dt, [XB, XC])
    tB = peak_time(t, r[:, 0])
    tC = peak_time(t, r[:, 1])
    hops_AB = int(round(abs(float(g['inv'](XB)) - float(g['inv'](XA))) / g['hs']))
    return dict(O1=freqs['A'] / freqs['B'], O2=(tC - tB) * freqs['B'],
                fB=freqs['B'], hops=hops_AB, nodes=len(x), dt=dt)


if __name__ == '__main__':
    NA, _ = background(np.array(XA)); NB, _ = background(np.array(XB))
    cases = [
        ('기준: 균일 h=0.05, dt=0.5', map_uniform(), 0.05, 0.5, False),
        ('dt 절반 (0.25)',            map_uniform(), 0.05, 0.25, False),
        ('dt 1/4 (0.125)',            map_uniform(), 0.05, 0.125, False),
        ('격자 거칠게 h=0.1',          map_uniform(), 0.10, 0.5, False),
        ('격자 촘촘히 h=0.025',        map_uniform(), 0.025, 0.5, False),
        ('사인 늘이기 eps=0.5',        map_sine(0.5), 0.05, 0.5, False),
        ('sinh 늘이기 lam=10',         map_sinh(10.0), 0.02, 0.5, False),
        ('대조군: 사인 늘이기, 변환 안 함', map_sine(0.5), 0.05, 0.5, True),
    ]
    print(f'예측 O1 = N_A/N_B = {NA/NB:.5f}')
    print(f"{'경우':<30}{'노드':>7}{'A-B 홉':>8}{'O1 시계비':>11}{'O2 B틱':>10}")
    res = []
    for name, mp, h, dtf, naive in cases:
        g = build(mp, h, naive)
        r = measure(g, dtf)
        res.append((name, r))
        print(f"{name:<30}{r['nodes']:>7}{r['hops']:>8}{r['O1']:>11.5f}{r['O2']:>10.3f}")
    base = res[0][1]
    print('\n기준 대비 상대 차이')
    for name, r in res[1:]:
        print(f"{name:<30} O1 {100*(r['O1']/base['O1']-1):+8.3f}%   O2 {100*(r['O2']/base['O2']-1):+8.3f}%")
