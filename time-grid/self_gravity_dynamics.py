"""
시간 그리드 사고 실험 — 동역학 2-c: 저장 파동이 서로의 장을 느끼며 함께 움직일 때

매 단계 (모두 그리드 규칙):
  1) 저장 파동의 에너지 밀도 ρ = ½u̇² + ½|∇u|² + ½μ²u²  (평면 위 면밀도로 봄)
  2) 텐서 3단계 규칙의 정적 해 (움직임이 느려 정적 풀이로 충분):
     Φ(x) = -G ∫ ρ(x') d²x' / |x - x'|   (물질은 평면, 중력은 3D 방식으로 1/r), Ψ = γΦ, γ = 1
     G 는 규칙의 q²h00 = C_RULE ρ 에서 G = C_RULE / (8π)  (Φ = -h00/2, ∇²Φ = 4πGρ)
  3) 시간 몫 N = e^{Φ}, 공간 몫 ψ = e^{-Ψ} -> 재료값 m = ψ²/N, κ = N, k = Nψ²μ²  (동역학 1과 같음)
  4) 격자 파동 한 단계 진행
2-c-1: 파동 덩어리 하나. 중력 켬/끔에서 폭(RMS 반지름)의 변화 비교
2-c-2: 덩어리 두 개를 원 궤도 속도로 서로 반대 방향에 놓고 궤도 관찰. 중력 끔 대조군과 비교
웹 시각화용: viz_data/self_gravity_{case}.json (프레임마다 시계 몫 지도, 에너지 지도, 덩어리 중심)
"""
import json, os, sys
import numpy as np
from growth_rule_test import solve

C_RULE = solve(np.array([0.1, 0, 0]), -2, 0, 0)[0] * 0.1**2
G_RULE = C_RULE / (8 * np.pi)            # 규칙에서 읽은 중력 세기 (격자 단위)

MU, A, NG = 3.0, 0.25, 192
L = A * NG
c = (np.arange(NG) - NG // 2) * A
X, Y = np.meshgrid(c, c, indexing='ij')

# 3D 방식 1/r 핵 (두 배 크기 0 채움으로 주기 영상 제거)
P = 2 * NG
cp = (np.arange(P) - P // 2) * A
XP, YP = np.meshgrid(cp, cp, indexing='ij')
RP = np.sqrt(XP**2 + YP**2)
KER = np.where(RP > 0, 1 / np.maximum(RP, 1e-12), 2 * 1.7627 / A)   # 칸 평균 1/r (정사각형 칸)
KER_Q = np.fft.rfft2(np.fft.ifftshift(KER))


def potential(rho, G):
    if G == 0:
        return np.zeros_like(rho)
    pad = np.zeros((P, P)); pad[:NG, :NG] = rho
    conv = np.fft.irfft2(np.fft.rfft2(pad) * KER_Q, s=(P, P))[:NG, :NG] * A * A
    return -G * conv


def energy_density(u, v):
    gx = (np.roll(u, -1, 0) - np.roll(u, 1, 0)) / (2 * A)
    gy = (np.roll(u, -1, 1) - np.roll(u, 1, 1)) / (2 * A)
    return 0.5 * v * v + 0.5 * (gx * gx + gy * gy) + 0.5 * MU**2 * u * u


def source(u, ud, Phi):
    """에너지 함수 L = ½m u̇² - ½κ|∇u|² - ½k u²,  m = e^{-3Φ}, κ = e^{Φ}, k = e^{-Φ}μ² 에서
    원천 σ = -∂L/∂Φ  (시간 평균하면 ρ 와 같음)"""
    gx = (np.roll(u, -1, 0) - np.roll(u, 1, 0)) / (2 * A)
    gy = (np.roll(u, -1, 1) - np.roll(u, 1, 1)) / (2 * A)
    return 1.5 * np.exp(-3 * Phi) * ud * ud + 0.5 * np.exp(Phi) * (gx * gx + gy * gy) - 0.5 * np.exp(-Phi) * MU**2 * u * u


def material(Phi):
    N, psi = np.exp(Phi), np.exp(-Phi)        # γ = 1
    m = psi**2 / N; k = N * psi**2 * MU**2
    kx = 0.5 * (N + np.roll(N, -1, 0)); ky = 0.5 * (N + np.roll(N, -1, 1))
    return m, k, kx, ky


def blob(x0, y0, sig, vx, vy, amp):
    """정지 진동(물질) 파동 덩어리, 속도 (vx, vy) 의 위상 기울기"""
    qx, qy = MU * vx, MU * vy
    om = np.sqrt(MU**2 + qx**2 + qy**2)
    env = amp * np.exp(-((X - x0)**2 + (Y - y0)**2) / (2 * sig**2))
    ph = qx * (X - x0) + qy * (Y - y0)
    return env * np.cos(ph), om * env * np.sin(ph)


def mass_of(u, v):
    return np.sum(energy_density(u, v)) * A * A


def run(case, G, T, blobs, save_every):
    u = np.zeros_like(X); v = np.zeros_like(X)
    for b in blobs:
        du, dv = blob(*b); u += du; v += dv
    dt = 0.35 * 2 / np.sqrt(MU**2 * 1.5 + 8 / A**2)
    nst = int(T / dt)
    frames, track = [], []
    cents = [np.array([b[0], b[1]]) for b in blobs]

    TAU = 2 * (2 * np.pi / MU)                      # 원천 평균 시간 = 빠른 떨림 주기의 2배
    state = {}

    def solve_phi(u, pi, Phi, first=False):
        """정적 근사는 느린 원천에만 성립: 원천 σ 를 시간 평균(지수 이동 평균)한 값으로 장을 풂"""
        ud = pi / np.exp(-3 * Phi)
        sig_now = source(u, ud, Phi)
        if first:
            state['avg'] = energy_density(u, ud)       # 시작값: 평균하면 σ = ρ
        else:
            state['avg'] += (dt / TAU) * (sig_now - state['avg'])
        return potential(state['avg'], G)

    def force(u, Phi):
        kx = 0.5 * (np.exp(Phi) + np.roll(np.exp(Phi), -1, 0))
        ky = 0.5 * (np.exp(Phi) + np.roll(np.exp(Phi), -1, 1))
        fx = kx * (np.roll(u, -1, 0) - u) / A**2
        fy = ky * (np.roll(u, -1, 1) - u) / A**2
        return fx - np.roll(fx, 1, 0) + fy - np.roll(fy, 1, 1) - np.exp(-Phi) * MU**2 * u

    Phi = np.zeros_like(u)
    pi = v.copy()                                   # 처음 Φ = 0 근처에서 m ≈ 1
    Phi = solve_phi(u, pi, Phi, first=True)
    pi = np.exp(-3 * Phi) * v
    for n in range(nst + 1):
        if n % save_every == 0:
            ud = pi / np.exp(-3 * Phi)
            rho = energy_density(u, ud)
            if len(cents) > 1:
                d = np.stack([(X - cc[0])**2 + (Y - cc[1])**2 for cc in cents])
                own = np.argmin(d, 0)
            else:
                own = np.zeros_like(X, dtype=int)
            new, widths = [], []
            for j in range(len(cents)):
                w = rho * (own == j)
                W = w.sum()
                cx, cy = (w * X).sum() / W, (w * Y).sum() / W
                new.append(np.array([cx, cy]))
                widths.append(float(np.sqrt((w * ((X - cx)**2 + (Y - cy)**2)).sum() / W)))
            cents = new
            t = n * dt
            H = np.sum(0.5 * pi * pi / np.exp(-3 * Phi) + 0.5 * MU**2 * np.exp(-Phi) * u * u) * A * A
            track.append(dict(t=round(t, 3), centers=[[round(float(p[0]), 4), round(float(p[1]), 4)] for p in cents],
                              widths=[round(x, 4) for x in widths], mass=round(float(rho.sum() * A * A), 5),
                              phi_min=round(float(Phi.min()), 5)))
            if n % (save_every * 4) == 0:
                ds = lambda f: f.reshape(48, 4, 48, 4).mean(axis=(1, 3))
                frames.append(dict(t=round(t, 3), clock=np.round(np.exp(ds(Phi)), 6).tolist(),
                                   energy=np.round(ds(rho) / rho.max(), 4).tolist()))
        pi += 0.5 * dt * force(u, Phi)
        u += dt * pi / np.exp(-3 * Phi)
        Phi = solve_phi(u, pi, Phi)
        pi += 0.5 * dt * force(u, Phi)
    return dict(case=case, G=G, mu=MU, grid=NG, spacing=A, track=track, frames=frames)


def save(d):
    os.makedirs('viz_data', exist_ok=True)
    with open(f"viz_data/self_gravity_{d['case']}.json", 'w') as f:
        json.dump(d, f)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'single'
    print(f"규칙에서 읽은 G = {G_RULE:.5f} (격자 단위), μ = {MU}, 격자 {NG}², 간격 {A}")
    if which == 'single':
        sig = 1.5
        u, v = blob(0, 0, sig, 0, 0, 1.0)
        M1 = mass_of(u, v)
        for GM in (0.0, 0.05, 0.1, 0.2):
            # G 는 규칙 값 그대로 두고, 덩어리에 저장된 파동의 양(진폭)으로 질량을 맞춤
            amp = 1.0 if GM == 0 else np.sqrt(GM / (G_RULE * M1))
            G = 0 if GM == 0 else G_RULE
            d = run(f'single_GM{GM}', G, 80.0, [(0, 0, sig, 0, 0, amp)], 40)
            save(d)
            ws = [tr['widths'][0] for tr in d['track']]
            ts = [tr['t'] for tr in d['track']]
            print(f"GM = {GM:<5} 폭: t=0 {ws[0]:.2f}, t=20 {ws[len(ws)//4]:.2f}, t=40 {ws[len(ws)//2]:.2f}, "
                  f"t=80 {ws[-1]:.2f}   (최대 {max(ws):.2f}, 최소 {min(ws):.2f})", flush=True)
