"""
시간 그리드 사고 실험 — 동역학 2-b-4: 저장 파동 덩어리의 완전 결합 궤도

2-b-3 의 남은 단순화를 걷어 낸다.
  - 덩어리: 모양이 고정된 가우스 -> 2-c 의 저장 파동(느린 극한 ψ, 3D)이 자기 중력으로 묶인 것. 모양과 내부 응력이 저절로 정해진다.
  - 원천: 손으로 넣던 조석 응력 τ 와 "상대 덩어리의 장" 구분을 없앤다. 원천은 파동 자신의 응력과 전체 장의 하중뿐이다.
        T_ij = (1/μ) Re(∂_iψ* ∂_jψ) + (1/4πG) ∂_iΦ ∂_jΦ        (TT 부분만 남으므로 대각합 항은 빠짐)
  - 반작용: 한 라그랑지안 (규칙 15)
        L = ∫ Re(iψ*ψ̇) - (1/2μ)(δ - w h):∂ψ*∂ψ - μΦ|ψ|² - (1/8πG)(δ - w h):∂Φ∂Φ + ½(ḣ:ḣ - ∇h:∇h)
     ψ:  iψ̇ = -(1/2μ)∇²ψ + (w/2μ) ∂_i(h_ij ∂_jψ) + μ(Φ + wχ)ψ,   ∇²Φ = 4πGρ,  ∇²χ = ∂_i(h_ij ∂_jΦ),  ρ = μ|ψ|²
     h:  ḧ = Δh + ½ w T^TT                         (2-b-3 와 같은 격자·흡수층)
    시계 몫(뉴턴 부분)은 규칙상 자기 에너지가 없는 구속(제약)이므로 즉시 풀린다(2-b-3 과 같음, 아래 문서 참고).
  격자 두 겹: ψ 와 Φ 는 고운 격자(64³, 간격 0.25, 자유 경계 푸아송), h 는 거친 격자(160³, 간격 1).
    거친 <-> 고운: 등방 가우스 필터와 그 수반 (아래 restrict / prolong). 서로 수반이라 결합 에너지가 한 식으로 맞는다.

결과 (실패, 문서 2-b-4): 반작용을 끄면 넘겨준 에너지가 4중극 공식과 맞지만(bound 0.99~1.05), 덩어리가 막 변형을 느끼면
  궤도가 너무 빨리 준다(bound κ = 1.68, kinetic 0.34). rigid 점검: kinetic 0.240(맞음), bound 1.39(여전히 넘침).

경우: newton  결합 없음 (덩어리 둘의 궤도만)
      bound   파동 응력 + 장 하중으로 완전 결합        -> 2-b-2/2-b-3 의 방출 세기 κ ≈ 0.94 기대
      kinetic 파동 응력만 결합 (장 하중 없음)          -> 약 1/4 기대
실행: python wave_orbit.py newton|bound|kinetic [끝 시각] [binary|single|moving|nobr|rigid]   (점검 결과 wave_orbit_checks_out.txt)
출력: wave_orbit_{경우}_out.txt, viz_data/wave_orbit_{경우}.json
"""
import json, os, sys, time
import numpy as np
import scipy.fft as sfft

CASE = sys.argv[1] if len(sys.argv) > 1 else 'bound'
T_ARG = sys.argv[2] if len(sys.argv) > 2 else '150'
INIT = sys.argv[3] if len(sys.argv) > 3 else 'binary'       # 점검용: single(정지 덩어리 하나), moving(등속 덩어리 하나), nobr(반작용 끔: 덩어리는 장을 느끼지 않음),
                                                          #         rigid(덩어리 안은 장을 느끼지 않고, 중심만 H = P²/2M - (w/2M) h̄:PP + 알짜 힘으로 결합)
sys.argv = ['gw_emission.py', 'bound', '160', T_ARG]
import gw_emission as E                                   # 같은 거친 격자·기호·흡수층

NG, H, A, DT, G = E.NG, E.H, E.A, E.DT, E.G
M, R0, V0 = E.M, E.R0, E.V_ORB
T_END, T_RAMP = float(T_ARG), E.T_RAMP
PAIRS, IDX = E.PAIRS, E.IDX
WGT = np.array([1, 1, 1, 2, 2, 2], np.float32)
K4 = 64 / 5 * 2 * G**3 * M**3
D_STOP = 3.5
MU = 3.0                                                  # 저장 파동의 μ (바닥 상태 반질량 반지름 0.94)
NF, AF = 64, 0.25                                         # 고운 격자
NSUB = 8                                                  # 거친 한 단계(0.4)당 고운 단계
DTF = DT / NSUB
W = 8

xf = (np.arange(NF) - NF // 2) * AF
XF = np.meshgrid(xf, xf, xf, indexing='ij')
kf = 2 * np.pi * sfft.fftfreq(NF, d=AF)
KF = np.meshgrid(kf, kf, kf, indexing='ij')
K2F = KF[0]**2 + KF[1]**2 + KF[2]**2
fft = lambda f: sfft.fftn(f, workers=W)
ifft = lambda f: sfft.ifftn(f, workers=W)

# 자유 경계 푸아송 (2NF 상자 그린 함수)
_m = 2 * NF
_k = np.minimum(np.arange(_m), _m - np.arange(_m)) * AF
_R = np.sqrt(_k[:, None, None]**2 + _k[None, :, None]**2 + _k[None, None, :]**2)
_R[0, 0, 0] = AF / 2.380077
GK = sfft.rfftn(-1 / (4 * np.pi * _R)) * AF**3
del _k, _R


def poisson_free(S):
    P = np.zeros((_m,) * 3); P[:NF, :NF, :NF] = S
    return sfft.irfftn(sfft.rfftn(P, workers=W) * GK, s=P.shape, workers=W)[:NF, :NF, :NF]


# 거친 <-> 고운: 폭 SIGK 의 등방 가우스 필터 K 와 그 수반.
#   제한  (R f)(x_c) = Σ_f K(x_c - x_f) f a_f³        (고운 격자에서 걸러 4칸마다 뽑음, 거친 칸 -8..7)
#   보간  (P h)(x_f) = Σ_c K(x_f - x_c) h_c a_c³       (R 의 수반 -> 결합 에너지가 한 식)
#   삼선형 제한은 덩어리가 칸을 지날 때 격자 비등방성을 만든다. 덩어리 내부 응력은 궤도 응력의 약 10배라
#   그 비등방성이 가짜 TT 원천이 된다(첫 시도: κ = 1.88). 등방 필터는 구대칭 응력을 구대칭으로 남긴다.
SIGK = 1.0
KFILT = np.exp(-0.5 * K2F * SIGK**2)
STEP = int(round(A / AF))
SLC = slice(H - NF // (2 * STEP), H + NF // (2 * STEP))


def restrict(ff):
    return np.real(ifft(fft(ff) * KFILT))[::STEP, ::STEP, ::STEP]


def prolong(fc_local):
    F = np.zeros((NF, NF, NF)); F[::STEP, ::STEP, ::STEP] = fc_local * (A / AF)**3
    return np.real(ifft(fft(F) * KFILT))


# 장 하중은 고운 격자의 정확한 Φ 로 (덩어리 자신의 장 하중이 내부 파동 응력과 고운 격자에서 상쇄되도록).
# 고운 상자 가장자리 쪽은 창 WIN 으로 줄이고, 그 바깥은 거친 격자의 장 하중으로 채운다.
def _taper(x, a=5.0, b=7.0):
    u = np.clip((np.abs(x) - a) / (b - a), 0, 1)
    return np.cos(0.5 * np.pi * u)**2
WIN = _taper(XF[0]) * _taper(XF[1]) * _taper(XF[2])
_wc = _taper(E.c)
WIN_C = (1 - _wc[:, None, None] * _wc[None, :, None] * _wc[None, None, :]).astype(np.float32)   # 거친 격자 몫


def dcen(f, ax):
    return (np.roll(f, -1, ax) - np.roll(f, 1, ax)) / (2 * AF)


# 고운 격자 가장자리 흡수 (튀어나간 파동이 주기 경계로 돌아오지 않게)
_edge = np.maximum(np.abs(np.stack(XF)).max(0) - 6.5, 0) / 1.5
DAMP = np.exp(-0.5 * _edge**2 * DTF)


def grad(psi):
    ph = fft(psi)
    return [ifft(1j * KF[i] * ph) for i in range(3)]


def ground_state():
    Nn = M / MU
    r2 = XF[0]**2 + XF[1]**2 + XF[2]**2
    psi = np.exp(-r2 / 2).astype(complex)
    for it in range(3000):
        psi *= np.sqrt(Nn / (np.sum(np.abs(psi)**2) * AF**3))
        Phi = poisson_free(4 * np.pi * G * MU * np.abs(psi)**2)
        psi *= np.exp(-MU * Phi * 0.01)
        psi = ifft(fft(psi) * np.exp(-K2F / (2 * MU) * 0.02))
        psi *= np.exp(-MU * Phi * 0.01)
    psi *= np.sqrt(Nn / (np.sum(np.abs(psi)**2) * AF**3))
    return psi


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


def coarse_phi_grad(rho_f):
    rc = np.zeros((NG, NG, NG), np.float32); rc[SLC, SLC, SLC] = restrict(rho_f)
    phiq = np.float32(-4 * np.pi * G) * E.rfft(rc) / E.S2_safe
    phiq[E.ZERO] = 0
    return [E.irfft(g * phiq) for g in E.GRAD]


def source(psi, Phi, gc):
    """T 의 TT 부분 (거친 격자 6성분): 고운 격자의 파동 응력 (+ bound: 장 하중)을 걸러 제한, 바깥은 거친 격자 장 하중"""
    D = grad(psi)
    gf = [dcen(Phi, ax) for ax in range(3)] if CASE == 'bound' else None
    Tq = []
    for k, (i, j) in enumerate(PAIRS):
        tf = np.real(np.conj(D[i]) * D[j]) / MU
        if CASE == 'bound':
            tf = tf + WIN * gf[i] * gf[j] / (4 * np.pi * G)
        tc = np.zeros((NG, NG, NG), np.float32)
        tc[SLC, SLC, SLC] = restrict(tf)
        if CASE == 'bound':
            tc += WIN_C * gc[i] * gc[j] / np.float32(4 * np.pi * G)
        Tq.append(E.rfft(tc))
    return tt_project(Tq)


def chi_fine(hf, Phi):
    """I_t = (w/8πG) Σ WIN h_ij ∂_iΦ ∂_jΦ 의 ρ 미분 -> χ: ∇²χ = ∂_i(WIN h_ij ∂_jΦ) (고운 격자, 같은 중심 차분)"""
    gf = [dcen(Phi, ax) for ax in range(3)]
    div = sum(dcen(WIN * sum(hf[IDX[i, j]] * gf[j] for j in range(3)), i) for i in range(3))
    return poisson_free(div)


def Kh(psi, hf, w):
    D = grad(psi)
    out = 0
    for i in range(3):
        u = sum(hf[IDX[i, j]] * D[j] for j in range(3))
        out = out + ifft(1j * KF[i] * fft(u))
    return (w / (2 * MU)) * out


def rigid_kick(psi, hf, chf, w, Xprev, dt):
    """덩어리마다 완전 결합의 알짜 힘(에렌페스트) F_b = ∫_b (w/2) ∂_k h_ij T^kin_ij - w ρ ∂_k χ 를 균일한 속도 변화로 준다"""
    rho = MU * np.abs(psi)**2
    n = Xprev[0] - Xprev[1]; mid = 0.5 * (Xprev[0] + Xprev[1])
    side = ((XF[0] - mid[0]) * n[0] + (XF[1] - mid[1]) * n[1] + (XF[2] - mid[2]) * n[2]) > 0
    D = grad(psi)
    hT = [np.real(np.conj(D[i]) * D[j]) / MU * (1.0 if i == j else 2.0) for (i, j) in PAIRS]
    hk = [fft(hf[k]) for k in range(6)]
    f = [0.5 * w * sum(np.real(ifft(1j * KF[ax] * hk[k])) * hT[k] for k in range(6)) for ax in range(3)]
    if not np.isscalar(chf):
        f = [f[ax] - w * rho * dcen(chf, ax) for ax in range(3)]
    jd = [np.imag(np.conj(psi) * D[i]) for i in range(3)]
    out = 0
    for s in (side, ~side):
        Mb = rho[s].sum() * AF**3
        P = np.array([jd[ax][s].sum() for ax in range(3)]) * AF**3
        hb = np.array([[(rho * hf[IDX[i, j]])[s].sum() for j in range(3)] for i in range(3)]) * AF**3 / Mb
        dv = np.array([f[ax][s].sum() for ax in range(3)]) * AF**3 / Mb * dt
        dx = -w * hb @ P / Mb * dt                         # 중심 속도도 Ẋ = (δ - w h̄) P / M  (운동 결합이 속도-운동량 관계를 바꿈)
        pb = np.where(s, psi * np.exp(1j * MU * (dv[0] * XF[0] + dv[1] * XF[1] + dv[2] * XF[2])), 0)
        out = out + ifft(fft(pb) * np.exp(-1j * (KF[0] * dx[0] + KF[1] * dx[1] + KF[2] * dx[2])))
    return out


def blobs(psi, Xprev):
    """두 덩어리: 직전 중심을 잇는 선의 수직 이등분면으로 나눔. 중심, 운동량, 질량"""
    rho = MU * np.abs(psi)**2
    n = Xprev[0] - Xprev[1]; mid = 0.5 * (Xprev[0] + Xprev[1])
    side = ((XF[0] - mid[0]) * n[0] + (XF[1] - mid[1]) * n[1] + (XF[2] - mid[2]) * n[2]) > 0
    D = grad(psi)
    jd = [np.imag(np.conj(psi) * D[i]) for i in range(3)]
    out = []
    for s in (side, ~side):
        Mb = rho[s].sum() * AF**3
        X = np.array([(rho * XF[i])[s].sum() for i in range(3)]) * AF**3 / Mb
        P = np.array([jd[i][s].sum() for i in range(3)]) * AF**3
        out.append((X, P / Mb, Mb))
    return out


def main():
    t0 = time.time()
    cache = f'wave_orbit_ground_mu{MU:g}.npy'                  # 바닥 상태 저장 (약 3분, 저장소에는 올리지 않음)
    if os.path.exists(cache):
        psi0 = np.load(cache)
    else:
        psi0 = ground_state(); np.save(cache, psi0)
    print(f"  바닥 상태 ({time.time() - t0:.0f} s)", flush=True)
    sh = int(round(R0 / AF))
    psi = (np.roll(psi0, sh, 0) * np.exp(1j * MU * V0 * XF[1]) +
           np.roll(psi0, -sh, 0) * np.exp(-1j * MU * V0 * XF[1]))
    if INIT not in ('binary', 'nobr', 'rigid'):
        psi = psi0 * (np.exp(1j * MU * 0.05 * XF[0]) if INIT == 'moving' else 1)
    field = CASE != 'newton'
    if field:
        h = np.zeros((6, NG, NG, NG), np.float32); vf = np.zeros_like(h)
        gam = E.sponge()
    hf = np.zeros((6, NF, NF, NF)); chf = 0.0
    rec = dict(t=[], X1=[], X2=[], d=[], E_orb=[], W=[], mass_ratio=[], frames=[], frame_t=[])
    Xc = [np.array([R0, 0, 0.]), np.array([-R0, 0, 0.])]
    W_cum = 0.0
    nst = int(round(T_END / DT))
    Phi = poisson_free(4 * np.pi * G * MU * np.abs(psi)**2)
    for n in range(nst + 1):
        t = n * DT
        w = E.ramp(t) if field else 0.0
        if INIT not in ('binary', 'nobr', 'rigid'):
            rho_ = MU * np.abs(psi)**2; M1 = rho_.sum() * AF**3
            X1 = np.array([(rho_ * XF[i]).sum() for i in range(3)]) * AF**3 / M1; V1 = np.zeros(3)
            X2, V2, M2 = X1 - np.array([10.0, 0, 0]), np.zeros(3), M1
        else:
            (X1, V1, M1), (X2, V2, M2) = blobs(psi, Xc)
        Xc = [X1, X2]
        d = float(np.linalg.norm(X1 - X2))
        E_orb = 0.5 * M1 * V1 @ V1 + 0.5 * M2 * V2 @ V2 - G * M1 * M2 / d
        if field:
            rho = MU * np.abs(psi)**2
            gc = coarse_phi_grad(rho) if CASE == 'bound' else None
            S = source(psi, Phi, gc)
            accel = np.stack([E.laplacian(h[k]) for k in range(6)]) + np.float32(0.5 * w) * S
            vf_old = vf
            vf = ((1 - 0.5 * DT * gam) * vf + DT * accel) / (1 + 0.5 * DT * gam)
            W_cum += DT * 0.5 * w * float(np.sum(WGT[:, None, None, None] * S * 0.5 * (vf + vf_old), dtype=np.float64)) * A**3
            h_loc_old = h[:, SLC, SLC, SLC].copy()
            h += DT * vf
            # 덩어리가 t_n -> t_n+1 동안 느끼는 막 변형은 가운데 시각 값 (h_n + h_n+1)/2.
            # 끝 값 h_n+1 을 쓰면 반 단계 어긋남이 강한 근거리 장에 가짜 소산력을 만든다(첫 두 시도: κ = 1.88, 1.64).
            hm = 0.5 * (h_loc_old + h[:, SLC, SLC, SLC])
            hf = np.stack([prolong(hm[k]) for k in range(6)])
            chf = chi_fine(hf, Phi) if CASE == 'bound' else 0.0
        if n % 2 == 0:
            rec['t'].append(round(t, 3)); rec['X1'].append(np.round(X1[:2], 5).tolist()); rec['X2'].append(np.round(X2[:2], 5).tolist())
            rec['d'].append(round(d, 6)); rec['E_orb'].append(round(float(E_orb), 7)); rec['W'].append(round(W_cum, 7))
            rec['mass_ratio'].append(round(float(M1 + M2) / (2 * M), 6))
        if n % 10 == 0:
            col = (MU * np.abs(psi)**2).sum(2) * AF
            rec['frames'].append(np.round(col[8:56, 8:56] / 40 * 255).clip(0, 255).astype(int).tolist()); rec['frame_t'].append(round(t, 2))
        if n % 25 == 0:
            print(f"  t = {t:6.1f}  d = {d:.4f}  E_orb = {E_orb:+.5f}  W 누적 = {W_cum:.5f}  질량 {(M1 + M2) / (2 * M):.4f}  ({time.time() - t0:5.0f} s)", flush=True)
        if d < D_STOP:
            print(f"  d < {D_STOP} 에서 멈춤 (t = {t:.1f})")
            break
        # 고운 격자 진행 (스트랭 분할, h 결합항은 운동 단계 가운데)
        wm = 0.0 if INIT in ('nobr', 'rigid') else w             # 덩어리 안이 느끼는 결합
        if INIT == 'rigid' and w:
            psi = rigid_kick(psi, hf, chf, w, Xc, 0.5 * DT)
        for _ in range(NSUB):
            psi *= np.exp(-0.5j * MU * DTF * (Phi + wm * chf))
            ph = fft(psi) * np.exp(-0.25j * DTF * K2F / MU)
            psi = ifft(ph)
            if wm:
                k1 = Kh(psi, hf, wm)
                psi = psi - 1j * DTF * k1 - 0.5 * DTF**2 * Kh(k1, hf, wm)
            psi = ifft(fft(psi) * np.exp(-0.25j * DTF * K2F / MU))
            Phi = poisson_free(4 * np.pi * G * MU * np.abs(psi)**2)
            psi *= np.exp(-0.5j * MU * DTF * (Phi + wm * chf))
            psi *= DAMP
        if INIT == 'rigid' and w:
            psi = rigid_kick(psi, hf, chf, w, Xc, 0.5 * DT)

    t_arr = np.array(rec['t']); E_arr = np.array(rec['E_orb']); W_arr = np.array(rec['W']); d_arr = np.array(rec['d'])
    lines = [f"[2-b-4 {CASE}] 거친 격자 {NG}³ (간격 {A}), 고운 격자 {NF}³ (간격 {AF}), μ = {MU}, G = {G:.6f}, m = {M:.2f}, 처음 거리 {2 * R0}, 속도 {V0}"]
    a = G * M * M / (-2 * E_arr)
    sel = t_arr >= T_RAMP + 10
    if sel.sum() > 20:
        kap = -np.polyfit(t_arr[sel], a[sel]**4, 1)[0] / (4 * K4)
        dE = E_arr[sel][-1] - E_arr[sel][0]; dW = W_arr[sel][-1] - W_arr[sel][0]
        lines.append(f"   장반경 a = Gm²/(-2E) 의 a⁴ 기울기 -> κ = {kap:.4f}   (2-b-2 잰 방출 세기 0.939)")
        if dW:
            lines.append(f"   궤도 에너지 변화 {dE:+.5f}, 장에 넘겨준 에너지 {dW:+.5f}, -ΔE/ΔW = {-dE / dW:.4f}")
        lines.append(f"   장반경 {a[sel][0]:.3f} -> {a[-1]:.3f}, 거리 {d_arr[sel][0]:.3f} -> {d_arr[-1]:.3f} (t = {t_arr[-1]:.1f}), 질량 비 {rec['mass_ratio'][-1]:.4f}")
    lines.append(f"   걸린 시간 {time.time() - t0:.0f} s")
    print('\n'.join(lines))
    if INIT in ('nobr', 'rigid'):
        a = G * M * M / (-2 * E_arr); P = 64 / 5 * G**4 * M**5 / a**5
        for t1, t2 in ((50, 65), (65, 80)):
            s_ = (t_arr >= t1) & (t_arr <= t2)
            print(f"   점검 {INIT} {CASE} t {t1}~{t2}: 넘겨준 에너지율 / P = {np.polyfit(t_arr[s_], W_arr[s_], 1)[0] / P[s_].mean():.3f}")
        return
    if INIT != 'binary':
        print(f"   점검 {INIT}: 장에 넘겨준 누적 에너지 {W_cum:+.5f}, 중심 {X1.round(3)}")
        return
    with open(f'wave_orbit_{CASE}_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    os.makedirs('viz_data', exist_ok=True)
    json.dump(dict(case=CASE, G=G, mass=M, mu=MU, r0=R0, v=V0, ramp=T_RAMP, K4=K4, frame_box=[-6, 6], **rec),
              open(f'viz_data/wave_orbit_{CASE}.json', 'w'))


if __name__ == '__main__':
    main()
