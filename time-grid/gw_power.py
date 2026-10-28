"""
시간 그리드 사고 실험 — 동역학 2-b-2 (가): 방출되는 에너지와 4중극 방출률

2-b-1 (gw_emission.py) 과 같은 격자·원천(보존되는 'bound' 원천)으로 막 변형파를 내보내며 잰다.
  W(t) = ½ ∫ T^TT_ij ḣ_ij d³x       : 원천이 막 변형에 넘겨주는 에너지 (초당)
  F(r) = ∮ -ḣ_ij ∂_r h_ij r² dΩ      : 반지름 r 구면을 지나 나가는 에너지 흐름 (초당)
에너지 정규화: 물질의 막 결합은 시계 몫 N = 1 - h00/2 에서 ½ h·T 이고, 그와 같은 G(=1/32π)를 주는
막 에너지는 ½(ḣ:ḣ - ∇h:∇h) 이다 (문서의 라그랑지안 L = ḣ:ḣ - ... + h·T 의 절반. 운동방정식은 같음).
예측 (4중극 방출률, 같은 G):  P = (32/5) G μ² a⁴ ω⁶,  μ = m/2, a = 2 r0
  문서 식 그대로(절반이 아닌 막 에너지)라면 흐름은 2P 로 나와야 한다.

실행: python gw_power.py [격자 크기] [끝 시각]
출력: gw_power_{격자}_out.txt, viz_data/gw_power_{격자}.json
"""
import json, os, sys, time
import numpy as np

NG_ARG = sys.argv[1] if len(sys.argv) > 1 else '160'
T_ARG = sys.argv[2] if len(sys.argv) > 2 else '240'
sys.argv = ['gw_emission.py', 'bound', NG_ARG, T_ARG]
import gw_emission as E                                   # 같은 격자·원천·흡수층

NG, H, A, DT, G = E.NG, E.H, E.A, E.DT, E.G
M, R0, OMEGA = E.M, E.R0, E.OMEGA
P_PETERS = 32 / 5 * G * (M / 2)**2 * (2 * R0)**4 * OMEGA**6
RADII = [r for r in (24, 32, 40, 48, 56, 64) if r <= H - E.SPONGE - 8]
NPT = 300
# 구면 위 고른 점 (피보나치)
k = np.arange(NPT) + 0.5
th = np.arccos(1 - 2 * k / NPT); ph = np.pi * (1 + 5**0.5) * k
NHAT = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], 1)
WGT = np.array([1, 1, 1, 2, 2, 2], np.float32)             # 6성분 -> h:h 의 비대각 두 번


def shell(h, v, r):
    """반지름 r 구면의 평균 -ḣ:∂_r h  (ḣ 는 반 단계 속도 v)"""
    hp = np.stack([E.trilinear(h[c], (r + 1) * NHAT) for c in range(6)])
    hm = np.stack([E.trilinear(h[c], (r - 1) * NHAT) for c in range(6)])
    vd = np.stack([E.trilinear(v[c], r * NHAT) for c in range(6)])
    dr = (hp - hm) / (2 * A)
    return float(np.mean(-(WGT[:, None] * vd * dr).sum(0))) * 4 * np.pi * r**2


def main():
    t0 = time.time()
    h = np.zeros((6, NG, NG, NG), np.float32); v = np.zeros_like(h)
    gam = E.sponge()
    nst = int(round(float(T_ARG) / DT))
    SRC = E.SRC_EVERY
    tA, SA = 0.0, E.source_tt(0.0); tB, SB = SRC * DT, E.source_tt(SRC * DT)

    def src(t):
        nonlocal tA, SA, tB, SB
        while t > tB + 1e-9:
            tA, SA = tB, SB; tB = tA + SRC * DT; SB = E.source_tt(tB)
        f = np.float32((t - tA) / (tB - tA))
        return SA + f * (SB - SA)

    S = src(0.0)
    ts, Ws, Fs = [], [], {r: [] for r in RADII}
    for n in range(nst):
        t = n * DT
        accel = np.stack([E.laplacian(h[c]) for c in range(6)]) + 0.5 * S
        v = ((1 - 0.5 * DT * gam) * v + DT * accel) / (1 + 0.5 * DT * gam)
        th_ = t + 0.5 * DT                                   # v 는 t + dt/2 의 속도
        Sh = src(th_)
        ts.append(th_)
        Ws.append(float(0.5 * np.sum(WGT[:, None, None, None] * Sh * v) * A**3))
        h_mid = h + 0.5 * DT * v                             # t + dt/2 의 h
        for r in RADII:
            Fs[r].append(shell(h_mid, v, r))
        h += DT * v
        S = src(t + DT)
        if n % 50 == 0:
            print(f"  t = {t:6.1f}  ({time.time() - t0:5.0f} s)", flush=True)
    ts = np.array(ts); Ws = np.array(Ws)
    Tgw = np.pi / OMEGA                                      # 중력파 주기

    def avg(y, t_from):
        sel = ts >= t_from
        nper = int((ts[sel][-1] - ts[sel][0]) / Tgw)        # 온전한 주기 수만큼 평균
        sel2 = sel & (ts < ts[sel][0] + nper * Tgw)
        return float(np.mean(np.asarray(y)[sel2])), nper

    lines = [f"[2-b-2 가] 격자 {NG}³, G = {G:.6f}, m = {M:.2f}, r0 = {R0}, ω = {OMEGA:.4f}, 중력파 주기 {Tgw:.1f}",
             f"   4중극 방출률 예측 P = (32/5)Gμ²a⁴ω⁶ = {P_PETERS:.4e}"]
    Wm, nW = avg(Ws, E.T_RAMP + 10)
    lines.append(f"   원천이 넘겨주는 에너지 W (주기 {nW}번 평균) = {Wm:.4e}  -> W / P = {Wm / P_PETERS:.4f}")
    rows = []
    for r in RADII:
        Fm, nF = avg(Fs[r], E.T_RAMP + r + 15)
        rows.append((r, Fm / P_PETERS, nF))
        lines.append(f"   구면 r = {r:3d} 흐름 (주기 {nF}번 평균) / P = {Fm / P_PETERS:.4f}")
    lines.append(f"   (막 에너지가 문서 식 그대로였다면 위 비율은 모두 2배)")
    lines.append(f"   걸린 시간 {time.time() - t0:.0f} s")
    print('\n'.join(lines))
    with open(f'gw_power_{NG}_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    os.makedirs('viz_data', exist_ok=True)
    stride = 5
    json.dump(dict(grid=NG, G=G, mass=M, r0=R0, omega=OMEGA, P_peters=P_PETERS, ramp=E.T_RAMP,
                   t=np.round(ts[::stride], 3).tolist(), W=np.round(Ws[::stride] / P_PETERS, 5).tolist(),
                   flux={str(r): np.round(np.array(Fs[r])[::stride] / P_PETERS, 5).tolist() for r in RADII},
                   W_mean=Wm / P_PETERS, flux_mean={str(r): x for r, x, _ in rows},
                   note='값은 모두 4중극 방출률 P 로 나눈 것'),
              open(f'viz_data/gw_power_{NG}.json', 'w'))


if __name__ == '__main__':
    main()
