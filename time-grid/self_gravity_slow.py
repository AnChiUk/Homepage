"""
시간 그리드 사고 실험 — 동역학 2-c (느린 극한): 저장 파동 덩어리의 자기 묶임과 서로 끌림

같은 격자 규칙(m = ψ²/N, κ = N, k = Nψ²μ², N = e^{Φ}, ψ = e^{-Φ})에서 느린 움직임만 남기면
u = Re[φ e^{-iμt}] 의 포락선 φ 가 따르는 방정식:
    i ∂_t φ = -(1/2μ) Δ_격자 φ + μ Φ φ
    Φ(x) = -G ∫ ρ(x') d²x' / |x - x'|,   ρ = ½ μ² |φ|²   (평면 위 물질, 3D 방식 1/r)
G 는 규칙 값 그대로 (G = C_RULE / 8π).  질량과 에너지가 정확히 보존됨 (분할 단계 방법).
격자 라플라시안의 분산 2(1 - cos qa)/a² 를 그대로 씀 -> 격자 규칙의 느린 극한.

2-c-1: 덩어리 하나. 중력 켬/끔에서 폭 비교. 바닥 상태(스스로 묶인 모양)를 허수 시간으로 구함
2-c-2: 바닥 상태 덩어리 둘을 원 궤도 속도로 반대 방향에 놓음
       대조: 각 덩어리는 자기 장만 느낌(서로 끌림 끔) -> 직선으로 멀어져야 함
웹 시각화용: viz_data/slow_{case}.json
"""
import json, os
import numpy as np
from growth_rule_test import solve

C_RULE = solve(np.array([0.1, 0, 0]), -2, 0, 0)[0] * 0.1**2
G = C_RULE / (8 * np.pi)
MU, A, NG = 3.0, 0.25, 256
c = (np.arange(NG) - NG // 2) * A
X, Y = np.meshgrid(c, c, indexing='ij')
q = 2 * np.pi * np.fft.fftfreq(NG, d=A)
QX, QY = np.meshgrid(q, q, indexing='ij')
LAPQ = -(2 * (1 - np.cos(QX * A)) + 2 * (1 - np.cos(QY * A))) / A**2      # 격자 라플라시안

P = 2 * NG
cp = (np.arange(P) - P // 2) * A
XP, YP = np.meshgrid(cp, cp, indexing='ij')
RP = np.sqrt(XP**2 + YP**2)
KER_Q = np.fft.rfft2(np.fft.ifftshift(np.where(RP > 0, 1 / np.maximum(RP, 1e-12), 2 * 1.7627 / A)))


def potential(rho):
    pad = np.zeros((P, P)); pad[:NG, :NG] = rho
    return -G * np.fft.irfft2(np.fft.rfft2(pad) * KER_Q, s=(P, P))[:NG, :NG] * A * A


def rho_of(phi):
    return 0.5 * MU**2 * np.abs(phi)**2


def mass(phi):
    return rho_of(phi).sum() * A * A


def ground_state(M, steps=1500, dtau=0.05):
    """허수 시간으로 질량 M 인 스스로 묶인 바닥 상태를 구함"""
    phi = np.exp(-(X**2 + Y**2) / (2 * 2.0**2)).astype(complex)
    phi *= np.sqrt(M / mass(phi))
    kin = np.exp(dtau * LAPQ / (2 * MU))
    for _ in range(steps):
        Phi = potential(rho_of(phi))
        phi = phi * np.exp(-0.5 * dtau * MU * Phi)
        phi = np.fft.ifft2(np.fft.fft2(phi) * kin)
        phi = phi * np.exp(-0.5 * dtau * MU * Phi)
        phi *= np.sqrt(M / mass(phi))
    return phi


def width(phi, cx=None, cy=None):
    r = rho_of(phi); W = r.sum()
    if cx is None:
        cx, cy = (r * X).sum() / W, (r * Y).sum() / W
    return np.sqrt((r * ((X - cx)**2 + (Y - cy)**2)).sum() / W), cx, cy


def shift(phi, dx, dy, vx, vy):
    """덩어리를 (dx, dy) 로 옮기고 속도 (vx, vy) 를 줌 (위상 기울기 μv)"""
    ph = np.fft.ifft2(np.fft.fft2(phi) * np.exp(-1j * (QX * dx + QY * dy)))
    return ph * np.exp(1j * MU * (vx * X + vy * Y))


def evolve(phis, T, dt, mutual=True, gravity=True, save_every=20, frame_every=80):
    kin = np.exp(1j * dt * LAPQ / (2 * MU))
    track, frames = [], []
    nst = int(T / dt)
    for n in range(nst + 1):
        if gravity:
            pots = [potential(rho_of(p)) for p in phis]
            tot = sum(pots)
        if n % save_every == 0:
            cs, ws = [], []
            for p in phis:
                w, cx, cy = width(p); cs.append([round(float(cx), 4), round(float(cy), 4)]); ws.append(round(float(w), 4))
            track.append(dict(t=round(n * dt, 3), centers=cs, widths=ws, mass=[round(float(mass(p)), 6) for p in phis]))
            if n % frame_every == 0:
                ds = lambda f: f.reshape(64, 4, 64, 4).mean(axis=(1, 3))
                Phi_all = tot if gravity else np.zeros_like(X)
                rr = sum(rho_of(p) for p in phis)
                frames.append(dict(t=round(n * dt, 3), clock=np.round(np.exp(ds(Phi_all)), 6).tolist(),
                                   energy=np.round(ds(rr) / rr.max(), 4).tolist()))
        if n == nst:
            break
        new = []
        for j, p in enumerate(phis):
            V = (tot if mutual else pots[j]) if gravity else 0
            p = p * np.exp(-0.5j * dt * MU * V)
            p = np.fft.ifft2(np.fft.fft2(p) * kin)
            new.append(p)
        phis = new
        if gravity:
            pots = [potential(rho_of(p)) for p in phis]
            tot = sum(pots)
        phis = [p * np.exp(-0.5j * dt * MU * ((tot if mutual else pots[j]) if gravity else 0)) for j, p in enumerate(phis)]
    return track, frames


def save(name, meta, track, frames):
    os.makedirs('viz_data', exist_ok=True)
    with open(f'viz_data/slow_{name}.json', 'w') as f:
        json.dump(dict(meta, track=track, frames=frames), f)


if __name__ == '__main__':
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else 'single'
    print(f"G = {G:.5f} (규칙 값), μ = {MU}, 격자 {NG}², 간격 {A}")
    GM = 0.1
    M = GM / G
    gs = ground_state(M)
    w0, _, _ = width(gs)
    print(f"바닥 상태 (GM = {GM}): 폭 {w0:.3f}, 중심 Φ = {potential(rho_of(gs)).min():+.4f}")
    if part == 'single':
        meta = dict(case='single', G=G, mu=MU, GM=GM, spacing=A, grid=NG)
        for grav in (True, False):
            tr, fr = evolve([gs.copy()], 300.0, 0.1, gravity=grav)
            ws = [t['widths'][0] for t in tr]; ms = [t['mass'][0] for t in tr]
            print(f"중력 {'켬' if grav else '끔'}: 폭 t=0 {ws[0]:.3f} -> t=100 {ws[len(ws)//3]:.3f} -> t=300 {ws[-1]:.3f}, "
                  f"질량 변화 {abs(ms[-1]-ms[0])/ms[0]:.1e}")
            save('single_' + ('on' if grav else 'off'), meta, tr, fr)
    else:
        r0 = 6.0
        v = np.sqrt(GM / (4 * r0))                     # 점질량 원 궤도 속도 (평면, 1/r)
        Tk = 2 * np.pi * r0 / v
        print(f"궤도 반지름 {r0}, 속도 {v:.4f}, 케플러 주기 {Tk:.1f}")
        p1 = shift(gs, r0, 0, 0, v); p2 = shift(gs, -r0, 0, 0, -v)
        meta = dict(case='binary', G=G, mu=MU, GM=GM, r0=r0, v=v, kepler_period=Tk, spacing=A, grid=NG)
        for mutual in (True, False):
            tr, fr = evolve([p1.copy(), p2.copy()], 1.25 * Tk, 0.1, mutual=mutual, save_every=20, frame_every=100)
            cs = np.array([t['centers'] for t in tr]); ts = np.array([t['t'] for t in tr])
            sep = np.linalg.norm(cs[:, 0] - cs[:, 1], axis=1)
            ang = np.unwrap(np.arctan2(cs[:, 0, 1] - cs[:, 1, 1], cs[:, 0, 0] - cs[:, 1, 0]))
            label = '서로 끌림 켬' if mutual else '서로 끌림 끔(대조)'
            print(f"{label}: 거리 {sep[0]:.2f} -> 최소 {sep.min():.2f} / 최대 {sep.max():.2f} -> 끝 {sep[-1]:.2f}, "
                  f"돈 각도 {np.degrees(ang[-1]-ang[0]):.0f}° (케플러 예측 {360*1.25:.0f}°), "
                  f"폭 {tr[0]['widths'][0]:.2f} -> {tr[-1]['widths'][0]:.2f}", flush=True)
            save('binary_' + ('mutual' if mutual else 'nomutual'), meta, tr, fr)
