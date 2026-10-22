"""
시간 그리드 사고 실험 — 동역학 2-b-1: 궤도를 흉내 낸 원천이 막 변형파를 내보내는가

규칙 (텐서 2·3단계, 동역학 2-a와 같음): 시간 게이지에서 막 변형 h_ij 의 라그랑지안
    L = (ḣ:ḣ - ḣ²) - V(h) + h_ij T_ij          (운동 에너지 비 -1, 원천 결합은 정적 에너지 F 그대로)
 -> K ḧ = -V h + ½ T.  두 편광(TT) 부분은 K = 1, V = s² 로 다른 성분과 정확히 분리되므로
    ḧ_TT = Δ_격자 h_TT + ½ T_TT                (Δ_격자 = 7점 라플라시안, 기호 -s²)
 이름표·구속 성분은 TT 측정에 들어가지 않으므로 TT 부분만 진행한다.

정적 G: growth_rule_test 의 규칙 값 G = C_RULE/(8π) (동역학 2-c와 같은 값)
4중극 공식 예측 (원천이 보존될 때): h_TT = (2G/r) Ï_TT(t - r)
    질량 m 둘이 반지름 r0, 각속도 ω 로 돌면 정면(z축) h+, h× 진폭 = 8 G m ω² r0² / r,
    측면(x축) h+ 는 그 절반, h× = 0.

원천 두 가지
  kinetic : 운동 응력만 T_ij = Σ ρ v_i v_j  (보존 안 됨: 서로 끌림의 힘이 응력에 없음) -> 예측 0.5배
  bound   : + 두 덩어리를 묶는 장의 응력 t_ij = (∂_iΦ1 ∂_jΦ2 + ∂_iΦ2 ∂_jΦ1 - δ_ij ∇Φ1·∇Φ2)/(4πG)
            (∂_j t_ij = ρ1∂_iΦ2 + ρ2∂_iΦ1 = 서로 끌림, 운동 응력과 합쳐 보존) -> 예측 1배
  ω 는 같은 G 의 케플러 값 ω² = G m / (4 r0³).

측정 (2ω 성분 진폭, 원천을 켠 뒤 신호가 도착한 구간에서 맞춤)
  - z축, x축 위 여러 반지름의 h+, h× -> r·진폭/예측 (근거리 모양은 gw_emission_theory.py 의 정확한 해와 비교)
  - z = 40 위 고리 표지 16개 (반지름 6, xy 평면): 틱으로 잰 거리의 cos2θ / sin2θ 찌그러짐

실행: python gw_emission.py kinetic|bound [격자 크기] [끝 시각]
출력: gw_emission_{case}_out.txt (격자가 160 이 아니면 _{격자} 를 붙임), viz_data/gw_emission_{case}.json
"""
import json, os, sys, time
import numpy as np
import scipy.fft as sfft
from scipy import ndimage
from growth_rule_test import solve

trapezoid = getattr(np, "trapezoid", None) or np.trapz      # numpy 1.x 와 2.x 모두

C_RULE = solve(np.array([0.1, 0, 0]), -2, 0, 0)[0] * 0.1**2
G = C_RULE / (8 * np.pi)

CASE = sys.argv[1] if len(sys.argv) > 1 else 'bound'
NG = int(sys.argv[2]) if len(sys.argv) > 2 else 160
T_END = float(sys.argv[3]) if len(sys.argv) > 3 else 240.0
A = 1.0
R0, SIG = 3.0, 1.0                     # 궤도 반지름, 덩어리 폭
V_ORB = 0.2                            # 궤도 속도 -> ω = v / r0
OMEGA = V_ORB / R0
M = 4 * R0**3 * OMEGA**2 / G           # 케플러: ω² = G m / (4 r0³)
T_RAMP = 40.0                          # 원천을 부드럽게 켜는 시간
DT = 0.4
SPONGE = 24 if NG <= 160 else 32      # 흡수층 두께 (칸)
RADII = list(range(16, NG // 2 - SPONGE - 7, 8))   # 흡수층에서 8칸 이상 떨어진 반지름
TAG = CASE if NG == 160 else f"{CASE}_{NG}"
RING_Z, RING_R, N_RING = 40.0, 6.0, 16
SAVE_EVERY = 10                        # 4 시간 단위마다 그림 저장
SRC_EVERY = 2
WORKERS = 8

H = NG // 2
c = (np.arange(NG) - H) * A
q = 2 * np.pi * sfft.fftfreq(NG, d=A)
qr = 2 * np.pi * sfft.rfftfreq(NG, d=A)
QX, QY, QZ = np.meshgrid(q, q, qr, indexing='ij')
SV = [2 * np.sin(Qc * A / 2) / A for Qc in (QX, QY, QZ)]          # 격자 기호 s_i
S2 = SV[0]**2 + SV[1]**2 + SV[2]**2
ZERO = S2 == 0
S2_safe = np.where(ZERO, 1.0, S2).astype(np.float32)
SH = [(s / np.sqrt(S2_safe)).astype(np.float32) for s in SV]       # 단위 파수 방향 n (격자 기호로)
GRAD = [(1j * Qc).astype(np.complex64) for Qc in (QX, QY, QZ)]      # 매끄러운 장의 기울기
del QX, QY, QZ, SV
PAIRS = [(0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (0, 2)]
IDX = {(i, j): k for k, (i, j) in enumerate(PAIRS)}
IDX.update({(j, i): k for k, (i, j) in enumerate(PAIRS)})

rfft = lambda f: sfft.rfftn(f, workers=WORKERS)
irfft = lambda f: sfft.irfftn(f, s=(NG, NG, NG), workers=WORKERS).astype(np.float32)


def sponge():
    d = np.maximum(np.abs(c) - (H - SPONGE), 0) / SPONGE
    g1 = d**2
    gam = 0.25 * (g1[:, None, None] + g1[None, :, None] + g1[None, None, :])
    return np.minimum(gam, 0.25).astype(np.float32)


def blob(cx, cy, m):
    gx = np.exp(-(c - cx)**2 / (2 * SIG**2)); gy = np.exp(-(c - cy)**2 / (2 * SIG**2)); gz = np.exp(-c**2 / (2 * SIG**2))
    norm = m / ((2 * np.pi)**1.5 * SIG**3)
    return (norm * gx[:, None, None] * gy[None, :, None] * gz[None, None, :]).astype(np.float32)


def ramp(t):
    return 1.0 if t >= T_RAMP else np.sin(0.5 * np.pi * t / T_RAMP)**2


def source_tt(t):
    """시각 t 의 원천 응력 T_ij 의 TT 부분 (실공간, 6성분)"""
    w = ramp(t)
    ang = OMEGA * t
    cs, sn = np.cos(ang), np.sin(ang)
    centers = [(R0 * cs, R0 * sn), (-R0 * cs, -R0 * sn)]
    vels = [(-V_ORB * sn, V_ORB * cs), (V_ORB * sn, -V_ORB * cs)]
    rhos = [blob(cx, cy, w * M) for cx, cy in centers]
    Tq = [np.zeros(S2.shape, np.complex64) for _ in range(6)]
    for rho, (vx, vy) in zip(rhos, vels):
        rq = rfft(rho)
        Tq[IDX[0, 0]] += rq * np.float32(vx * vx)
        Tq[IDX[1, 1]] += rq * np.float32(vy * vy)
        Tq[IDX[0, 1]] += rq * np.float32(vx * vy)
    if CASE == 'bound':
        grads = []
        for rho in rhos:
            phiq = np.float32(-4 * np.pi * G) * rfft(rho) / S2_safe
            phiq[ZERO] = 0
            grads.append([irfft(g * phiq) for g in GRAD])
        g1, g2 = grads
        dot = g1[0] * g2[0] + g1[1] * g2[1] + g1[2] * g2[2]
        k4 = np.float32(1 / (4 * np.pi * G))
        for k, (i, j) in enumerate(PAIRS):
            tij = g1[i] * g2[j] + g2[i] * g1[j] - (dot if i == j else 0)
            Tq[k] += rfft(tij * k4)
        # 덩어리 내부의 조석 응력: 상대의 끌림이 덩어리 안에서 고르지 않은 만큼(조석)을 버텨 모양을 유지
        #   τ_b = σ² ρ_b ∂_i∂_jΦ_상대(중심),  ∂_j τ_b = 끌림의 조석 편차 (가우스 덩어리에서 정확, 선형 조석)
        d = 2 * R0
        nn = np.array([cs, sn, 0.0])
        tidal = G * w * M * (np.eye(3) - 3 * np.outer(nn, nn)) / d**3
        rq_sum = rfft(rhos[0] + rhos[1])
        for k, (i, j) in enumerate(PAIRS):
            if tidal[i, j] != 0:
                Tq[k] += rq_sum * np.float32(SIG**2 * tidal[i, j])
    # TT 투영 (n = 격자 파수 방향):  PTP - ½ P tr(PT),  P = 1 - n n
    #   = T_ij - n_i u_j - u_i n_j + n_i n_j w - ½ (δ_ij - n_i n_j)(tr T - w),  u = T·n,  w = n·T·n
    n = SH
    u = [sum(Tq[IDX[i, k]] * n[k] for k in range(3)) for i in range(3)]
    w = n[0] * u[0] + n[1] * u[1] + n[2] * u[2]
    trw = Tq[0] + Tq[1] + Tq[2] - w
    out = np.empty((6, NG, NG, NG), np.float32)
    for k, (i, j) in enumerate(PAIRS):
        tt = Tq[k] - n[i] * u[j] - u[i] * n[j] + n[i] * n[j] * w - 0.5 * ((1.0 if i == j else 0.0) - n[i] * n[j]) * trw
        tt[ZERO] = 0
        out[k] = irfft(tt)
    return out


def laplacian(f):
    """7점 격자 라플라시안 (주기 경계), 기호 -s²"""
    return ndimage.laplace(f, mode='wrap') / A**2


def trilinear(f, pts):
    idx = pts / A + H
    i0 = np.floor(idx).astype(int); fr = idx - i0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                wgt = (fr[:, 0] if dx else 1 - fr[:, 0]) * (fr[:, 1] if dy else 1 - fr[:, 1]) * (fr[:, 2] if dz else 1 - fr[:, 2])
                out = out + wgt * f[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz]
    return out


TH = np.linspace(0, 2 * np.pi, N_RING, endpoint=False)
SS = np.linspace(0, RING_R, 13)


def ring(h, center, e1, e2):
    """고리 표지까지 틱으로 잰 거리 변화 ΔL = ½ ∫ n·h·n ds (각도 16개)"""
    out = []
    for th in TH:
        n = np.cos(th) * e1 + np.sin(th) * e2
        pts = center + SS[:, None] * n
        nhn = sum(n[i] * n[j] * trilinear(h[IDX[i, j]], pts) for i in range(3) for j in range(3))
        out.append(0.5 * trapezoid(nhn, SS))
    return np.array(out)


def main():
    t0 = time.time()
    h = np.zeros((6, NG, NG, NG), np.float32)
    v = np.zeros_like(h)
    gam = sponge()
    nst = int(round(T_END / DT))
    probes = {r: dict(z=[], x=[]) for r in RADII}
    ts, rings_face, rings_edge, frames = [], [], [], []
    amp_pred = 8 * G * M * OMEGA**2 * R0**2                # r · 진폭 (정면, 보존 원천)
    zc = np.array([0, 0, RING_Z]); xc = np.array([RING_Z, 0, 0])
    ex, ey, ez = np.eye(3)
    # 원천은 SRC_EVERY 단계마다 계산하고 사이는 선형 보간 (위상 변화 2ω·0.8 = 0.11 rad, 진폭 오차 ~0.1%)
    tA, SA = 0.0, source_tt(0.0)
    tB, SB = SRC_EVERY * DT, source_tt(SRC_EVERY * DT)

    def src(t):
        nonlocal tA, SA, tB, SB
        while t > tB + 1e-9:
            tA, SA = tB, SB
            tB = tA + SRC_EVERY * DT
            SB = source_tt(tB)
        f = np.float32((t - tA) / (tB - tA))
        return SA + f * (SB - SA)

    S = src(0.0)
    for n in range(nst + 1):
        t = n * DT
        ts.append(t)
        for r in RADII:
            hz = h[:, H, H, H + r]; hx = h[:, H + r, H, H]
            probes[r]['z'].append([0.5 * float(hz[0] - hz[1]), float(hz[3])])      # 정면: h+ = ½(xx-yy), h× = xy
            probes[r]['x'].append([0.5 * float(hx[1] - hx[2]), float(hx[4])])      # 측면: h+ = ½(yy-zz), h× = yz
        if n % SAVE_EVERY == 0:
            rings_face.append(ring(h, zc, ex, ey))
            rings_edge.append(ring(h, xc, ey, ez))
            hp_xy = 0.5 * (h[0, :, :, H] - h[1, :, :, H])
            hp_xz = 0.5 * (h[0, :, H, :] - h[1, :, H, :])
            crop = lambda f: f[H - 64:H + 64, H - 64:H + 64].reshape(64, 2, 64, 2).mean(axis=(1, 3))
            frames.append(dict(t=round(t, 2), xy=np.round(crop(hp_xy) / amp_pred, 4).tolist(),
                               xz=np.round(crop(hp_xz) / amp_pred, 4).tolist()))
            print(f"  t = {t:6.1f}  ({time.time() - t0:5.0f} s)", flush=True)
        if n == nst:
            break
        # 감쇠 있는 도약 개구리: v_{n+½}, h_{n+1}
        accel = np.stack([laplacian(h[k]) for k in range(6)]) + 0.5 * S
        v = ((1 - 0.5 * DT * gam) * v + DT * accel) / (1 + 0.5 * DT * gam)
        h += DT * v
        S = src(t + DT)

    ts = np.array(ts)
    Om = 2 * OMEGA

    def amp(series, t_from):
        y = np.asarray(series); sel = ts >= t_from
        tt = ts[sel]
        X = np.stack([np.ones_like(tt), tt, tt**2, np.cos(Om * tt), np.sin(Om * tt)], 1)
        coef, *_ = np.linalg.lstsq(X, y[sel], rcond=None)
        return np.hypot(coef[3], coef[4])

    expect = 0.5 if CASE == 'kinetic' else 1.0
    lines = [f"[{CASE}] G = {G:.6f} (규칙 값 = 1/(32π) {1/(32*np.pi):.6f}), 격자 {NG}³, 간격 {A}, dt {DT}",
             f"   두 덩어리 m = {M:.2f}, 궤도 반지름 {R0}, 속도 {V_ORB}, ω = {OMEGA:.4f}, 중력파 파장 {np.pi / OMEGA:.1f}, 폭 {SIG}",
             f"   예측 (4중극 공식, 같은 G): 정면 r·h = {amp_pred:.5f}; 이 원천의 기대 비율 {expect}",
             "   반지름   정면 h+   정면 h×   측면 h+/정면   측면 h×/정면   (정면은 r·진폭/예측)"]
    rh = []
    for r in RADII:
        t_from = T_RAMP + r + 20
        zp = amp([p[0] for p in probes[r]['z']], t_from); zx = amp([p[1] for p in probes[r]['z']], t_from)
        xp = amp([p[0] for p in probes[r]['x']], t_from); xx = amp([p[1] for p in probes[r]['x']], t_from)
        rh.append([r * zp / amp_pred, r * zx / amp_pred])
        lines.append(f"   {r:4d}     {r*zp/amp_pred:.4f}    {r*zx/amp_pred:.4f}    {xp/zp:.4f}         {xx/zp:.2e}")
    rh = np.array(rh)
    # r·h 는 kr ≲ 8 에서 푸리에 TT 투영 때문에 출렁이며 다가가므로 단순 외삽하지 않는다 (gw_emission_theory.py)
    lines.append("   근거리 모양 비교: python gw_emission_theory.py viz_data/gw_emission_" + TAG + ".json")
    rf = np.array(rings_face); re_ = np.array(rings_edge)
    tr = ts[::SAVE_EVERY][:len(rf)]
    t_from = T_RAMP + RING_Z + 20
    c2 = rf @ np.cos(2 * TH) * 2 / N_RING; s2 = rf @ np.sin(2 * TH) * 2 / N_RING
    sel = tr >= t_from
    lines.append(f"   고리 (z = {RING_Z:.0f}, 반지름 {RING_R:.0f}): cos2θ 출렁임 {np.ptp(c2[sel]):.2e}, sin2θ {np.ptp(s2[sel]):.2e}  "
                 f"(예측 ½·h·R 진폭의 두 배 = {2 * 0.5 * expect * amp_pred / RING_Z * RING_R:.2e})")
    lines.append(f"   걸린 시간 {time.time() - t0:.0f} s")
    print('\n'.join(lines))
    with open(f'gw_emission_{TAG}_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    os.makedirs('viz_data', exist_ok=True)
    out = dict(case=CASE, G=G, grid=NG, spacing=A, mass=M, r0=R0, omega=OMEGA, v=V_ORB, ramp=T_RAMP,
               amp_pred=amp_pred, expect=expect, radii=RADII, rh=np.round(rh, 5).tolist(),
               view=128, view_cells=64,
               ring_z=RING_Z, ring_radius=RING_R, ring_angles=np.round(TH, 5).tolist(),
               rings_face=np.round(rf, 8).tolist(), rings_edge=np.round(re_, 8).tolist(), frames=frames)
    with open(f'viz_data/gw_emission_{TAG}.json', 'w') as f:
        json.dump(out, f)


if __name__ == '__main__':
    main()
