"""시험 2-b: 숨은 방향(임피던스)이 만드는 반사 — 격자 방정식의 정상 상태 산란으로 정확히 계산
왼쪽 끝에 왼쪽으로 나가는 투과파만 두고 오른쪽으로 적분한 뒤,
오른쪽 끝에서 들어오는 파(B)와 반사파(A)로 분해: R = |A/B|
"""
import numpy as np
from hidden_direction_test_1d import build_abc, Ufield
from relabel_test_1d import R0


def refl(g, omega):
    x, h, m, kap, k = g['x'], g['hs'], g['m'], g['kap'], g['k']

    def qloc(i, il):
        s2 = (m[i] * omega**2 - k[i]) * h**2 / (4 * kap[il])
        return 2 * np.arcsin(np.sqrt(s2)) / h
    q0 = qloc(0, 0)
    u = np.zeros(len(x), complex)
    u[0], u[1] = np.exp(-1j * q0 * x[0]), np.exp(-1j * q0 * x[1])
    for i in range(1, len(x) - 1):
        rhs = (k[i] - m[i] * omega**2) * u[i] * h**2
        u[i + 1] = u[i] + (rhs + kap[i - 1] * (u[i] - u[i - 1])) / kap[i]
    n = len(x) - 1
    q = qloc(n, n - 1)
    M = np.array([[np.exp(1j*q*x[n-1]), np.exp(-1j*q*x[n-1])],
                  [np.exp(1j*q*x[n]),   np.exp(-1j*q*x[n])]])
    A, B = np.linalg.solve(M, u[n-1:n+1])
    return abs(A / B)


MU = 5.0
print(f"{'q(먼곳)':>8}{'q*r0':>7}" + ''.join(f"{'t='+format(t,'+.0f'):>11}" for t in (0, 1, 2, 4)))
for q in (0.25, 0.5, 1.0, 2.0, 4.0, 6.0):
    omega = np.sqrt(MU**2 + q**2)
    row = [refl(build_abc(2 + t, 2 - t, t, h=0.025), omega) for t in (0, 1, 2, 4)]
    print(f"{q:>8.2f}{q*R0:>7.1f}" + ''.join(f"{v:>11.2e}" for v in row))
