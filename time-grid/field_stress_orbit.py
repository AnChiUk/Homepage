"""
시간 그리드 사고 실험 — 비선형 1-나: 실제 궤도에서 방출 원천이 저절로 맞는가

2-c 의 스스로 묶인 두 덩어리 궤도(느린 극한, 손으로 넣은 응력 없음)를 다시 돌리며 매 순간 잰다:
  ½Ï_ij      : 덩어리 분포의 2차 모멘트 I_ij = ∫ρ x_i x_j 를 시간으로 두 번 미분한 것 (4중극 방출에 필요한 값)
  ∫Π_ij      : 물질(저장 파동)의 응력. 운동 + 덩어리를 퍼지게 하는 내부 압력 포함
               느린 극한에서 ∫Π_ij = ½ Re∫ ∂_iφ* ∂_jφ   (격자 미분 s = 2 sin(qa/2)/a)
  ∫t_ij      : 장 자신의 막 하중 (1-가에서 정의). 평면 물질의 3D 장을 평면 푸리에로 정확히 적분
               ∫t_ij d³x = (1/4πG)(1/L²) Σ_k (k_i k_j - ½δ_ij k²) |Φ̂(k)|² / k ,  Φ̂ = -(2πG/k) ρ̂
  대조       : -∫ x_i ρ ∂_jΦ (대칭화)  — ∂_j t_ij = ρ∂_iΦ 이면 ∫t 와 같아야 함
비교는 회전하며 방출하는 부분(대각합 없는 성분 (xx-yy)/2, xy)으로 한다.
보존되는 원천이면 ∫(Π + t) = ½Ï,  물질 응력만이면 약 절반.
웹 시각화용: viz_data/field_stress_orbit.json
"""
import json, os
import numpy as np
from scipy.signal import savgol_filter
import self_gravity_slow as S

A, NG, MU, G = S.A, S.NG, S.MU, S.G
X, Y = S.X, S.Y
qN = 2 * np.pi * np.fft.fftfreq(NG, d=A)
QX, QY = np.meshgrid(qN, qN, indexing='ij')
SX, SY = 2 * np.sin(QX * A / 2) / A, 2 * np.sin(QY * A / 2) / A
P = S.P
qP = 2 * np.pi * np.fft.fftfreq(P, d=A)
KX, KY = np.meshgrid(qP, qP, indexing='ij')
KK = np.sqrt(KX**2 + KY**2); KK[0, 0] = 1.0          # k = 0 칸은 아래에서 0으로 둠


def tl(m):                    # 대각합 없는 두 성분
    return np.array([(m[0, 0] - m[1, 1]) / 2, m[0, 1]])


def measure(phis):
    phi = sum(phis)
    rho = S.rho_of(phi)
    I = np.array([[np.sum(rho * X * X), np.sum(rho * X * Y)], [np.sum(rho * X * Y), np.sum(rho * Y * Y)]]) * A * A
    ph = np.fft.fft2(phi) * A * A
    L2 = (NG * A)**2
    w = np.abs(ph)**2 / L2
    Pi = 0.5 * np.array([[np.sum(SX * SX * w), np.sum(SX * SY * w)], [np.sum(SX * SY * w), np.sum(SY * SY * w)]])
    pad = np.zeros((P, P)); pad[:NG, :NG] = rho
    rq = np.fft.fft2(pad) * A * A
    Ph2 = (2 * np.pi * G / KK)**2 * np.abs(rq)**2 / (P * A)**2
    Ph2[0, 0] = 0.0
    t = np.array([[np.sum((KX * KX - 0.5 * KK**2) * Ph2 / KK), np.sum(KX * KY * Ph2 / KK)],
                  [np.sum(KX * KY * Ph2 / KK), np.sum((KY * KY - 0.5 * KK**2) * Ph2 / KK)]]) / (4 * np.pi * G)
    Phi = S.potential(rho)
    gx = (np.roll(Phi, -1, 0) - np.roll(Phi, 1, 0)) / (2 * A)
    gy = (np.roll(Phi, -1, 1) - np.roll(Phi, 1, 1)) / (2 * A)
    vxx = -np.sum(X * rho * gx); vyy = -np.sum(Y * rho * gy)
    vxy = -0.5 * np.sum(X * rho * gy + Y * rho * gx)
    vir = np.array([[vxx, vxy], [vxy, vyy]]) * A * A
    return tl(I), tl(Pi), tl(t), tl(vir)


if __name__ == '__main__':
    GM = 0.1
    gs = S.ground_state(GM / G)
    r0 = 6.0
    v = np.sqrt(GM / (4 * r0))
    Tk = 2 * np.pi * r0 / v
    phis = [S.shift(gs, r0, 0, 0, v), S.shift(gs, -r0, 0, 0, -v)]
    dt, every = 0.1, 10
    nst = int(1.25 * Tk / dt)
    kin = np.exp(1j * dt * S.LAPQ / (2 * MU))
    recs = []
    pots = [S.potential(S.rho_of(p)) for p in phis]; tot = sum(pots)
    for n in range(nst + 1):
        if n % every == 0:
            recs.append((n * dt, *measure(phis)))
            if n % (every * 100) == 0:
                print(f"t = {n*dt:.0f} / {nst*dt:.0f}", flush=True)
        phis = [p * np.exp(-0.5j * dt * MU * tot) for p in phis]
        phis = [np.fft.ifft2(np.fft.fft2(p) * kin) for p in phis]
        pots = [S.potential(S.rho_of(p)) for p in phis]; tot = sum(pots)
        phis = [p * np.exp(-0.5j * dt * MU * tot) for p in phis]
    ts = np.array([r[0] for r in recs])
    I = np.array([r[1] for r in recs]); Pi = np.array([r[2] for r in recs])
    t = np.array([r[3] for r in recs]); vir = np.array([r[4] for r in recs])
    h = ts[1] - ts[0]
    win = int(round(40 / h)) | 1
    Idd = savgol_filter(I, win, 4, deriv=2, delta=h, axis=0)
    half = 0.5 * Idd
    sl = slice(win, len(ts) - win)                     # 끝부분(미분 불안정) 제외
    Pis = savgol_filter(Pi, win, 4, axis=0); tss = savgol_filter(t, win, 4, axis=0)

    def ratio(src):
        a, b = src[sl].ravel(), half[sl].ravel()
        return float(a @ b / (b @ b)), float(np.linalg.norm(a - (a @ b / (b @ b)) * b) / np.linalg.norm(a))

    rk, ek = ratio(Pis); rt, et = ratio(Pis + tss); rf, ef = ratio(tss)
    vr = float(np.linalg.norm(t[sl] - vir[sl]) / np.linalg.norm(t[sl]))
    print(f"\n궤도 반지름 {r0}, 케플러 주기 {Tk:.0f}, 측정 {len(ts)}점, 평활 창 {win*h:.0f}")
    print(f"물질 응력만        ∫Π     / ½Ï = {rk:.3f}   (모양 어긋남 {ek:.2f})")
    print(f"장 자신의 하중만   ∫t     / ½Ï = {rf:.3f}   (모양 어긋남 {ef:.2f})")
    print(f"물질 + 장          ∫(Π+t) / ½Ï = {rt:.3f}   (모양 어긋남 {et:.2f})")
    print(f"대조: ∫t 와 -∫xρ∂Φ 의 차이 {vr:.2e}")
    os.makedirs('viz_data', exist_ok=True)
    json.dump(dict(t=ts.tolist(), half_Idd=half.tolist(), Pi=Pis.tolist(), t_field=tss.tolist(),
                   ratios=dict(matter=rk, field=rf, total=rt), period=Tk, r0=r0,
                   note='성분 0 = (xx-yy)/2, 성분 1 = xy. 회전하며 방출하는 부분'),
              open('viz_data/field_stress_orbit.json', 'w'))
