"""
시간 그리드 사고 실험 — 동역학 2-b-4 진단: 덩어리 내부 떨림의 4중극 방출

결합 없는 궤도(newton)에서 덩어리마다 중심에 대한 내부 2차 모멘트 Q_b,ij = ∫_b ρ (x-X_b)_i (x-X_b)_j 를 매 0.4 마다 잰다.
같은 G 의 4중극 공식으로 내부 떨림의 방출률 P_내부 = (G/5) ⟨Q⃛^TF : Q⃛^TF⟩ (두 덩어리 합)을 궤도 방출률 P 와 비교한다.
궤도 전체의 4중극 I = Σ_b [M_b X_b X_b + Q_b] 로도 같은 계산을 해 P_전체 를 얻는다.
실행: python wave_orbit_diag.py [끝 시각]     결과 wave_orbit_diag_out.txt
"""
import sys, time
T_END = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
sys.argv = ['wave_orbit.py', 'newton', str(T_END)]
import numpy as np
import wave_orbit as Wo

G, MU, AF, XF, M = Wo.G, Wo.MU, Wo.AF, Wo.XF, Wo.M


def moments(psi, Xprev):
    rho = MU * np.abs(psi)**2
    n = Xprev[0] - Xprev[1]; mid = 0.5 * (Xprev[0] + Xprev[1])
    side = ((XF[0] - mid[0]) * n[0] + (XF[1] - mid[1]) * n[1] + (XF[2] - mid[2]) * n[2]) > 0
    out = []
    for s in (side, ~side):
        Mb = rho[s].sum() * AF**3
        X = np.array([(rho * XF[i])[s].sum() for i in range(3)]) * AF**3 / Mb
        Q = np.array([[(rho * (XF[i] - X[i]) * (XF[j] - X[j]))[s].sum() for j in range(3)] for i in range(3)]) * AF**3
        out.append((X, Q, Mb))
    return out


def tf(Q):
    return Q - np.trace(Q, axis1=-2, axis2=-1)[..., None, None] * np.eye(3) / 3


def main():
    t0 = time.time()
    psi0 = np.load(f'wave_orbit_ground_mu{MU:g}.npy')
    sh = int(round(Wo.R0 / AF))
    psi = (np.roll(psi0, sh, 0) * np.exp(1j * MU * Wo.V0 * XF[1]) +
           np.roll(psi0, -sh, 0) * np.exp(-1j * MU * Wo.V0 * XF[1]))
    Phi = Wo.poisson_free(4 * np.pi * G * MU * np.abs(psi)**2)
    Xc = [np.array([Wo.R0, 0, 0.]), np.array([-Wo.R0, 0, 0.])]
    ts, Qint, Itot, dd = [], [], [], []
    nst = int(round(T_END / Wo.DT))
    for n in range(nst + 1):
        (X1, Q1, M1), (X2, Q2, M2) = moments(psi, Xc)
        Xc = [X1, X2]
        ts.append(n * Wo.DT); Qint.append([Q1, Q2]); dd.append(np.linalg.norm(X1 - X2))
        Itot.append(M1 * np.outer(X1, X1) + M2 * np.outer(X2, X2) + Q1 + Q2)
        for _ in range(Wo.NSUB):
            psi *= np.exp(-0.5j * MU * Wo.DTF * Phi)
            psi = Wo.ifft(Wo.fft(psi) * np.exp(-0.5j * Wo.DTF * Wo.K2F / MU))
            Phi = Wo.poisson_free(4 * np.pi * G * MU * np.abs(psi)**2)
            psi *= np.exp(-0.5j * MU * Wo.DTF * Phi)
            psi *= Wo.DAMP
    ts = np.array(ts); Qint = np.array(Qint); Itot = np.array(Itot); dd = np.array(dd)
    dt = Wo.DT
    d3 = lambda f: (f[4:] - 2 * f[3:-1] + 2 * f[1:-3] - f[:-4]) / (2 * dt**3)      # 중심 차분 3계 미분
    Pint = G / 5 * sum(np.sum(d3(tf(Qint[:, b]))**2, axis=(1, 2)) for b in range(2))
    Ptot = G / 5 * np.sum(d3(tf(Itot))**2, axis=(1, 2))
    a = dd[2:-2] / 1.0
    Porb = 64 / 5 * G**4 * M**5 / dd[2:-2]**5
    lines = [f"[2-b-4 진단] 결합 없는 궤도, 덩어리 내부 4중극 떨림의 방출률 (같은 G 의 4중극 공식, 0.4 간격 3계 미분)"]
    for t1, t2 in ((0, 20), (20, 40), (40, 60), (60, T_END)):
        s = (ts[2:-2] >= t1) & (ts[2:-2] < t2)
        lines.append(f"   t {t1:3.0f}~{t2:3.0f}: P_내부 / P_궤도 = {Pint[s].mean() / Porb[s].mean():.3f}   P_전체(궤도 + 내부) / P_궤도 = {Ptot[s].mean() / Porb[s].mean():.3f}")
    # 내부 떨림의 주된 진동수
    q = tf(Qint[:, 0])[:, 0, 0] - tf(Qint[:, 0])[:, 1, 1]
    q = q - q.mean()
    sp = np.abs(np.fft.rfft(q * np.hanning(len(q))))
    fr = 2 * np.pi * np.fft.rfftfreq(len(q), dt)
    k = np.argmax(sp[3:]) + 3
    lines.append(f"   덩어리 1 내부 4중극(xx-yy) 떨림의 주된 각진동수 {fr[k]:.2f} (궤도 2ω = {2 * Wo.V0 / Wo.R0:.3f}), 진폭 {np.ptp(q) / 2:.3f} (궤도 4중극 진폭 {M * Wo.R0**2:.1f})")
    lines.append(f"   걸린 시간 {time.time() - t0:.0f} s")
    print('\n'.join(lines))
    with open('wave_orbit_diag_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
