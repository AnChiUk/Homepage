"""
시간 그리드 사고 실험 — 시험 2: 관측 가능한 조합 찾기 (1D 결합 진동자)

m = e^{aU}, kappa = e^{-bU}, k = mu^2 e^{cU}
  N   = sqrt(k/m)      = e^{-alpha U},  alpha = (a-c)/2
  v   = sqrt(kappa/m)  = e^{-(a+b)U/2}
  psi = N/v            = e^{beta U},    beta  = (b+c)/2
  Z   = sqrt(kappa m)  = e^{(a-b)U/2}

숨은 방향 (a,b,c) -> (a+t, b-t, c+t): alpha, beta 그대로, Z 만 e^{tU} 배.
질문: 이 방향은 틱/틱으로 잰 홉 측정에서 안 보이는가? (안 보이면 이름표, 보이면 물리량)
대조: alpha 를 바꾸면 보여야 한다.

측정
  O1 = 시계 A(중심) / 시계 B(x=20) 틱 비
  O2 = 파속이 B -> C(x=-20) 가는 동안 B 시계 틱 수
  R  = 우물에서 되돌아온 반사파 진폭 / 입사 진폭 (임피던스 기울기에서만 생김)
"""
import numpy as np
from scipy.signal import hilbert
from relabel_test_1d import (U0, R0, MU, L, XA, XB, XC, run, clock_freq, peak_time)


def Ufield(x):
    return U0 * R0 / np.sqrt(x**2 + R0**2)


def build_abc(a, b, c, h=0.05):
    M = int(round(2 * L / h)) + 1
    x = np.linspace(-L, L, M)
    hs = x[1] - x[0]
    xl = 0.5 * (x[1:] + x[:-1])
    m = np.exp(a * Ufield(x))
    k = MU**2 * np.exp(c * Ufield(x))
    kap = np.exp(-b * Ufield(xl))
    return dict(s=x, x=x, hs=hs, m=m, kap=kap, k=k, inv=lambda y: y)


def omega_max(g):
    lap = (np.r_[g['kap'], 0] + np.r_[0, g['kap']]) / g['hs']**2
    return np.sqrt(np.max((g['k'] + 2 * lap) / g['m']))


def local_omega(g, x0, q):
    i = int(np.argmin(np.abs(g['x'] - x0)))
    return np.sqrt((g['kap'][i] * q**2 + g['k'][i]) / g['m'][i])


def packet(g, x0, q, sig):
    x = g['x']
    env = np.exp(-(x - x0)**2 / (2 * sig**2))
    om = local_omega(g, x0, q)
    return env * np.cos(q * (x - x0)), -om * env * np.sin(q * (x - x0))


def observables(g, dt_frac=0.25):
    dt = dt_frac * 2 / omega_max(g)
    x = g['x']
    f = {}
    for name, xc in (('A', XA), ('B', XB)):
        u0 = np.exp(-(x - xc)**2 / (2 * 1.5**2))
        t, r = run(g, u0, np.zeros_like(x), 30.0, dt, [xc])
        f[name] = clock_freq(t, r[:, 0])
    u0, v0 = packet(g, XB, 6.0, 3.0)
    t, r = run(g, u0, v0, 95.0, dt, [XB, XC])
    O2 = (peak_time(t, r[:, 1]) - peak_time(t, r[:, 0])) * f['B']
    return f['A'] / f['B'], O2


def reflection(g, q, x0=8.0, sig=3.0, dt_frac=0.25):
    """x0 에서 왼쪽으로 쏜 파속이 우물에서 반사돼 x0 로 돌아오는 진폭 비"""
    dt = dt_frac * 2 / omega_max(g)
    om = local_omega(g, x0, q)
    vg = g['kap'][0] / g['m'][0] * q / om          # 먼 곳 군속도 근사
    T = 2 * x0 / vg + 6 * sig / vg
    u0, v0 = packet(g, x0, q, sig)
    t, r = run(g, u0, v0, T, dt, [x0 + 0.0])
    env = np.abs(hilbert(r[:, 0]))
    inc = env[0]
    late = t > (2 * x0 - 3 * sig) / vg               # 반사파가 돌아올 구간
    return np.max(env[late]) / inc


if __name__ == '__main__':
    base = (2.0, 2.0, 0.0)          # alpha = beta = 1, Z 일정 (시험 1과 같은 배경)
    cases = [('기준 (2, 2, 0)', base)]
    for t in (-2.0, -1.0, 1.0, 2.0):
        cases.append((f'숨은 방향 t={t:+.0f}', (2 + t, 2 - t, t)))
    cases.append(('alpha 1.2 (2.4, 2, 0)', (2.4, 2.0, 0.0)))

    print(f"{'경우':<24}{'alpha':>6}{'beta':>6}{'Z 지수':>7}{'O1':>10}{'O2':>10}")
    res = []
    for name, (a, b, c) in cases:
        g = build_abc(a, b, c)
        O1, O2 = observables(g)
        res.append((name, O1, O2))
        print(f"{name:<24}{(a-c)/2:>6.2f}{(b+c)/2:>6.2f}{(a-b)/2:>7.2f}{O1:>10.5f}{O2:>10.3f}")
    b0 = res[0]
    print('\n기준 대비')
    for name, O1, O2 in res[1:]:
        print(f"{name:<24} O1 {100*(O1/b0[1]-1):+8.3f}%   O2 {100*(O2/b0[2]-1):+8.3f}%")

    print('\n반사 진폭 비 R (파장별)')
    print(f"{'q':>6}{'q*r0':>7}" + ''.join(f"{'t='+format(t,'+.0f'):>11}" for t in (0, 1, 2, 4)))
    for q in (0.5, 1.0, 2.0, 6.0):
        row = [reflection(build_abc(2 + t, 2 - t, t), q) for t in (0.0, 1.0, 2.0, 4.0)]
        print(f"{q:>6.1f}{q*R0:>7.1f}" + ''.join(f"{v:>11.2e}" for v in row))
