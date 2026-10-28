"""
시간 그리드 사고 실험 — 동역학 2-b-3: 원천과 장이 서로 되먹이는 완전 결합 궤도

2-b-2(나)는 잰 방출 세기로 궤도 에너지를 손으로 줄였다(단열 계산). 여기서는 반작용을 넣지 않는다.
두 덩어리와 막 변형파를 한 라그랑지안(규칙 15)으로 함께 진행한다.
    L = Σ_b ½ m v_b² + G m²/d + ½∫(ḣ:ḣ - ∇h:∇h) + w(t) · I,   I = ½ ∫ h_ij T_ij d³x
    T = Σ ρ_b v_b v_b (운동 응력) + t (묶는 장의 응력) + τ (덩어리 내부 조석 응력)   — 2-b-1 의 보존 원천
장:     ḧ = Δ_격자 h + ½ w T^TT                        (gw_emission 과 같은 TT 진행, 흡수층)
덩어리: p_b = (m + w H_b) v_b,   ṗ_b = F_뉴턴 + w [½ v_i v_j ∂H_b,ij/∂X + ∂(I_t + I_τ)/∂X_b]
    H_b,ij = ∫ h_ij ρ_b d³x (덩어리에 걸친 막 변형),  ∂I_t/∂X1_k = -(1/4πG) ∫ h_ij ∂_jΦ2 ∂_i∂_kΦ1
    I_τ = ½ σ² E_ij (H_1 + H_2)_ij,  E = 상대의 조석 텐서 G m (δ - 3nn)/d³
장이 가져간 에너지만큼 궤도 에너지가 빠지면, 4중극 방출에서 d⁴ 가 시간에 대해 직선으로 줄어든다.
    d⁴(t) = d0⁴ - 4 K κ t,   K = (64/5) · 2 G³ m³,  κ = (방출 세기) / (4중극 공식)   [2-b-2: κ = W/P = 0.939]

경우: newton  결합 없음 (적분기 점검, 장 없음)
      bound   보존 원천으로 완전 결합                -> κ_동역학 ≈ 0.94 기대
      kinetic 운동 응력만 결합 (보존 안 되는 원천)   -> 방출 약 1/4, κ_동역학 ≈ 0.23 기대
실행: python coupled_orbit.py newton|bound|kinetic [격자] [끝 시각]
출력: coupled_orbit_{경우}_out.txt, viz_data/coupled_orbit_{경우}.json
"""
import json, os, sys, time
import numpy as np

CASE = sys.argv[1] if len(sys.argv) > 1 else 'bound'
NG_ARG = sys.argv[2] if len(sys.argv) > 2 else '160'
T_ARG = sys.argv[3] if len(sys.argv) > 3 else '150'
sys.argv = ['gw_emission.py', 'bound', NG_ARG, T_ARG]
import gw_emission as E                                   # 같은 격자·기호·흡수층

NG, H, A, DT, G, SIG = E.NG, E.H, E.A, E.DT, E.G, E.SIG
M, R0, V0, OMEGA = E.M, E.R0, E.V_ORB, E.OMEGA
T_END, T_RAMP = float(T_ARG), E.T_RAMP
D_STOP = 3.5                                              # 이보다 가까워지면 덩어리가 겹치므로 멈춤
K4 = 64 / 5 * 2 * G**3 * M**3                             # d⁴ 줄어드는 속도 / (4κ)
KAPPA_2B2 = 0.939
PAIRS, IDX = E.PAIRS, E.IDX
WGT = np.array([1, 1, 1, 2, 2, 2], np.float32)            # 6성분 저장 -> h:T 에서 비대각 두 번
c = E.c
LW = 5                                                    # 덩어리 국소 창 반폭 (칸), 5σ


def ramp(t):
    return 1.0 if t >= T_RAMP else np.sin(0.5 * np.pi * t / T_RAMP)**2


def local(X):
    """덩어리 중심 X 주변 창의 격자 인덱스와 상대 좌표, 정규화된 밀도 ρ_b"""
    i0 = np.round(X / A).astype(int) + H
    sl = [slice(i0[k] - LW, i0[k] + LW + 1) for k in range(3)]
    rel = [c[s] - X[k] for k, s in enumerate(sl)]
    g = [np.exp(-r**2 / (2 * SIG**2)) for r in rel]
    rho = M / ((2 * np.pi)**1.5 * SIG**3) * g[0][:, None, None] * g[1][None, :, None] * g[2][None, None, :]
    return sl, rel, rho


def H_and_grad(h, X):
    """H_ij = ∫h_ij ρ dV,  dH_ij/dX_k = ∫h_ij ρ (x-X)_k/σ² dV   (3x3, 3x3x3)"""
    sl, rel, rho = local(X)
    Hm = np.zeros((3, 3)); dH = np.zeros((3, 3, 3))
    w = [rho * rel[0][:, None, None], rho * rel[1][None, :, None], rho * rel[2][None, None, :]]
    for (i, j), k6 in IDX.items():
        hw = h[k6][sl[0], sl[1], sl[2]].astype(np.float64)
        Hm[i, j] = np.sum(hw * rho) * A**3
        for k in range(3):
            dH[i, j, k] = np.sum(hw * w[k]) * A**3 / SIG**2
    return Hm, dH


def tidal(D):
    """상대의 조석 텐서 E (둘 다 같음)와 dE_ij/dD_k,  D = X1 - X2"""
    d = np.linalg.norm(D); I3 = np.eye(3)
    Et = G * M * (I3 / d**3 - 3 * np.outer(D, D) / d**5)
    dE = G * M * (-3 * I3[:, :, None] * D[None, None, :] / d**5
                  - 3 * (I3[:, None, :] * D[None, :, None] + D[:, None, None] * I3[None, :, :]) / d**5
                  + 15 * D[:, None, None] * D[None, :, None] * D[None, None, :] / d**7)
    return Et, dE


def position_fields(X1, X2):
    """위치만으로 정해지는 것: 밀도의 푸리에, 장 기울기 g_b, 헤세 Φ_b,ik (실공간)"""
    rhos = [E.blob(X[0], X[1], M) for X in (X1, X2)]
    rq = [E.rfft(r) for r in rhos]
    out = []
    for q in rq:
        phiq = np.float32(-4 * np.pi * G) * q / E.S2_safe
        phiq[E.ZERO] = 0
        g = [E.irfft(gr * phiq) for gr in E.GRAD]
        hess = {(i, k): E.irfft(E.GRAD[i] * E.GRAD[k] * phiq) for i in range(3) for k in range(i, 3)}
        out.append((g, hess))
    return rq, out


def tt_project(Tq):
    n = E.SH
    u = [sum(Tq[IDX[i, k]] * n[k] for k in range(3)) for i in range(3)]
    w = n[0] * u[0] + n[1] * u[1] + n[2] * u[2]
    trw = Tq[0] + Tq[1] + Tq[2] - w
    out = np.empty((6, NG, NG, NG), np.float32)
    for k, (i, j) in enumerate(PAIRS):
        tt = Tq[k] - n[i] * u[j] - u[i] * n[j] + n[i] * n[j] * w - 0.5 * ((1.0 if i == j else 0.0) - n[i] * n[j]) * trw
        tt[E.ZERO] = 0
        out[k] = E.irfft(tt)
    return out


def source(rq, fields, X1, X2, V1, V2):
    """원천 T 의 TT 부분 (6성분 실공간)"""
    Tq = [np.zeros(E.S2.shape, np.complex64) for _ in range(6)]
    for q, Vb in zip(rq, (V1, V2)):
        for k, (i, j) in enumerate(PAIRS):
            if Vb[i] * Vb[j] != 0:
                Tq[k] += q * np.float32(Vb[i] * Vb[j])
    if CASE == 'bound':
        (g1, _), (g2, _) = fields
        dot = g1[0] * g2[0] + g1[1] * g2[1] + g1[2] * g2[2]
        k4 = np.float32(1 / (4 * np.pi * G))
        for k, (i, j) in enumerate(PAIRS):
            Tq[k] += E.rfft((g1[i] * g2[j] + g2[i] * g1[j] - (dot if i == j else 0)) * k4)
        Et, _ = tidal(X1 - X2)
        for k, (i, j) in enumerate(PAIRS):
            Tq[k] += (rq[0] + rq[1]) * np.float32(SIG**2 * Et[i, j])
    return tt_project(Tq)


def coupling_forces(h, fields, X1, X2, V1, V2):
    """∂I/∂X_b (b = 1, 2) 와 H_b.  I = ½∫h·T"""
    H1, dH1 = H_and_grad(h, X1); H2, dH2 = H_and_grad(h, X2)
    F = [0.5 * np.einsum('i,j,ijk->k', V, V, dH) for V, dH in ((V1, dH1), (V2, dH2))]
    if CASE == 'bound':
        (g1, hs1), (g2, hs2) = fields
        hess = lambda hs, i, k: hs[(min(i, k), max(i, k))]
        for b, (gother, hs) in enumerate(((g2, hs1), (g1, hs2))):
            # ∂I_t/∂X_b,k = -(1/4πG) ∫ h_ij g_other,j Φ_b,ik
            u = [sum(h[IDX[i, j]] * gother[j] for j in range(3)) for i in range(3)]
            for k in range(3):
                F[b][k] += -float(sum(np.sum(u[i] * hess(hs, i, k), dtype=np.float64) for i in range(3))) * A**3 / (4 * np.pi * G)
        Et, dE = tidal(X1 - X2)
        Hs = H1 + H2
        dI_dD = 0.5 * SIG**2 * np.einsum('ijk,ij->k', dE, Hs)
        F[0] += dI_dD + 0.5 * SIG**2 * np.einsum('ij,ijk->k', Et, dH1)
        F[1] += -dI_dD + 0.5 * SIG**2 * np.einsum('ij,ijk->k', Et, dH2)
    return F, (H1, H2)


def coupling_energy(h, rq, fields, X1, X2, V1, V2):
    """I = ½ ∫ h_ij T_ij (힘 공식 점검용, T 는 투영 전)"""
    Tq = [np.zeros(E.S2.shape, np.complex64) for _ in range(6)]
    for q, Vb in zip(rq, (V1, V2)):
        for k, (i, j) in enumerate(PAIRS):
            Tq[k] += q * np.float32(Vb[i] * Vb[j])
    if CASE == 'bound':
        (g1, _), (g2, _) = fields
        dot = g1[0] * g2[0] + g1[1] * g2[1] + g1[2] * g2[2]
        for k, (i, j) in enumerate(PAIRS):
            Tq[k] += E.rfft((g1[i] * g2[j] + g2[i] * g1[j] - (dot if i == j else 0)) / (4 * np.pi * G))
        Et, _ = tidal(X1 - X2)
        for k, (i, j) in enumerate(PAIRS):
            Tq[k] += (rq[0] + rq[1]) * np.float32(SIG**2 * Et[i, j])
    T = np.stack([E.irfft(x) for x in Tq])
    return 0.5 * float(np.sum(WGT[:, None, None, None] * h * T, dtype=np.float64)) * A**3


def check_forces():
    """힘 공식이 결합 에너지의 정확한 미분인지 유한차분으로 확인 (임의의 TT 비슷한 매끄러운 h)"""
    rng = np.random.default_rng(1)
    hq = np.zeros((6,) + E.S2.shape, np.complex64)
    kmask = (E.S2 < 0.15**2).astype(np.float32)
    for k in range(6):
        hq[k] = (rng.normal(size=E.S2.shape) + 1j * rng.normal(size=E.S2.shape)).astype(np.complex64) * kmask
    h = np.stack([E.irfft(x) for x in hq])
    h -= (h[0] + h[1] + h[2]) / 3 * np.array([1, 1, 1, 0, 0, 0], np.float32)[:, None, None, None]  # 대각합 0
    h *= np.float32(0.02 / np.abs(h).max())
    X1 = np.array([2.7, 1.1, 0.0]); X2 = -X1 + np.array([0.3, -0.2, 0.0])
    V1 = np.array([-0.07, 0.19, 0.0]); V2 = -V1
    rq, fields = position_fields(X1, X2)
    F, _ = coupling_forces(h, fields, X1, X2, V1, V2)
    eps = 0.02
    print('  힘 점검 (해석식 vs 유한차분 dI/dX):')
    for b in range(2):
        for k in range(2):
            Xp = [X1.copy(), X2.copy()]; Xm = [X1.copy(), X2.copy()]
            Xp[b][k] += eps; Xm[b][k] -= eps
            Ip = coupling_energy(h, *position_fields(*Xp), *Xp, V1, V2)
            Im = coupling_energy(h, *position_fields(*Xm), *Xm, V1, V2)
            fd = (Ip - Im) / (2 * eps)
            print(f"    덩어리 {b + 1}, 축 {'xy'[k]}: 해석 {F[b][k]:+.5e}  유한차분 {fd:+.5e}  비 {F[b][k] / fd:.4f}")


def main():
    t0 = time.time()
    if CASE != 'newton':
        check_forces()
    X = [np.array([R0, 0.0, 0.0]), np.array([-R0, 0.0, 0.0])]
    Vv = [np.array([0.0, V0, 0.0]), np.array([0.0, -V0, 0.0])]
    fN = lambda X1, X2: (lambda D: -G * M * M * D / np.linalg.norm(D)**3)(X1 - X2)
    F0 = fN(*X)
    p = [M * Vv[0] - 0.5 * DT * F0, M * Vv[1] + 0.5 * DT * F0]  # p_{-½}
    field = CASE != 'newton'
    if field:
        h = np.zeros((6, NG, NG, NG), np.float32); vf = np.zeros_like(h)
        gam = E.sponge()
    Hs = (np.zeros((3, 3)), np.zeros((3, 3)))
    vel = lambda pb, Hb, w: np.linalg.solve(M * np.eye(3) + w * Hb, pb)
    rec = dict(t=[], X1=[], X2=[], d=[], E_orb=[], W=[], H=[])
    nst = int(round(T_END / DT))
    W_cum = 0.0
    for n in range(nst + 1):
        t = n * DT
        w = ramp(t) if field else 0.0
        v_prev = [vel(p[b], Hs[b], w) for b in range(2)]            # v_{n-½}
        F = [fN(X[0], X[1]), -fN(X[0], X[1])]
        if field:
            rq, fields = position_fields(X[0], X[1])
            Fc, Hs = coupling_forces(h, fields, X[0], X[1], *v_prev)
            F = [F[b] + w * Fc[b] for b in range(2)]
        p_new = [p[b] + DT * F[b] for b in range(2)]                # p_{n+½}
        v_new = [vel(p_new[b], Hs[b], w) for b in range(2)]
        v_now = [0.5 * (v_prev[b] + v_new[b]) for b in range(2)]   # v_n
        d = float(np.linalg.norm(X[0] - X[1]))
        E_orb = sum(0.5 * M * float(v @ v) for v in v_now) - G * M * M / d
        Wn = 0.0
        if field:
            S = source(rq, fields, X[0], X[1], *v_now)
            accel = np.stack([E.laplacian(h[k]) for k in range(6)]) + np.float32(0.5 * w) * S
            vf_old = vf
            vf = ((1 - 0.5 * DT * gam) * vf + DT * accel) / (1 + 0.5 * DT * gam)
            Wn = 0.5 * w * float(np.sum(WGT[:, None, None, None] * S * 0.5 * (vf + vf_old), dtype=np.float64)) * A**3
            h += DT * vf
        W_cum += Wn * DT
        if n % 2 == 0:
            rec['t'].append(round(t, 3)); rec['X1'].append(np.round(X[0][:2], 5).tolist()); rec['X2'].append(np.round(X[1][:2], 5).tolist())
            rec['d'].append(round(d, 6)); rec['E_orb'].append(round(E_orb, 7)); rec['W'].append(round(W_cum, 7))
            rec['H'].append(round(float(np.linalg.norm(Hs[0])) / M, 6))      # 막 변형이 덩어리 관성에 더하는 비율
        if n % 25 == 0:
            print(f"  t = {t:6.1f}  d = {d:.4f}  E_orb = {E_orb:+.5f}  W 누적 = {W_cum:.5f}  ({time.time() - t0:5.0f} s)", flush=True)
        if d < D_STOP:
            print(f"  d < {D_STOP} 에서 멈춤 (t = {t:.1f})")
            break
        X = [X[b] + DT * v_new[b] for b in range(2)]
        p = p_new

    t_arr = np.array(rec['t']); d_arr = np.array(rec['d']); E_arr = np.array(rec['E_orb']); W_arr = np.array(rec['W'])
    lines = [f"[2-b-3 {CASE}] 격자 {NG}³, G = {G:.6f}, m = {M:.2f}, 처음 거리 {2 * R0}, 속도 {V0}, dt {DT}, 원천 켜는 시간 {T_RAMP}",
             f"   4중극 공식 d⁴ 감소율 4K = {4 * K4:.4e} (κ = 1)"]
    # d⁴ 직선 맞춤: 원천을 다 켠 뒤, 이심 출렁임은 궤도 주기 평균으로 지움
    sel = t_arr >= T_RAMP + 10
    if sel.sum() > 20:
        ts, d4 = t_arr[sel], d_arr[sel]**4
        slope = np.polyfit(ts, d4, 1)[0]
        kap = -slope / (4 * K4)
        lines.append(f"   d⁴ 기울기 {slope:+.4e} (t ≥ {T_RAMP + 10:.0f}) -> κ_동역학 = {kap:.4f}   (2-b-2 잰 방출 세기 κ = {KAPPA_2B2})")
        dE = E_arr[sel][-1] - E_arr[sel][0]; dW = W_arr[sel][-1] - W_arr[sel][0]
        lines.append(f"   같은 구간 궤도 에너지 변화 {dE:+.5f}, 장에 넘겨준 에너지 {dW:+.5f}, 비 -ΔE/ΔW = {-dE / dW if dW else float('nan'):.4f}")
        lines.append(f"   거리 {d_arr[sel][0]:.3f} -> {d_arr[-1]:.3f} (t = {t_arr[-1]:.1f})")
    lines.append(f"   걸린 시간 {time.time() - t0:.0f} s")
    print('\n'.join(lines))
    with open(f'coupled_orbit_{CASE}_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    os.makedirs('viz_data', exist_ok=True)
    json.dump(dict(case=CASE, grid=NG, G=G, mass=M, r0=R0, v=V0, ramp=T_RAMP, K4=K4, kappa_2b2=KAPPA_2B2, **rec),
              open(f'viz_data/coupled_orbit_{CASE}.json', 'w'))


if __name__ == '__main__':
    main()
