"""
시간 그리드 사고 실험 — 동역학 2-b-2 (나): 방출이 궤도 에너지를 가져가 궤도가 줄어듦

하나의 에너지 함수(규칙 15)에서 원천이 막 변형에 넘겨준 에너지는 궤도 에너지에서 빠져야 한다.
궤도 에너지 (같은 질량 m 둘, 거리 a):  E = -G m² / (2a)
(가)에서 잰 방출 세기 P_잰값 = κ · P_4중극,  P_4중극 = (32/5) G μ² a⁴ ω⁶,  ω² = 2Gm / a³
  -> da/dt = -(64/5) κ G³ m³ · 2 / a³ ,   a(t) = a0 (1 - t/τ)^{1/4},  τ = a0⁴ / (4·(64/5)·2κ G³ m³)
2-b-1·2-b-2(가)의 궤도(r0 = 3, v = 0.2)에서 κ = 1 과 κ = 잰값을 비교한다.

실행: python inspiral.py [κ]   (κ 는 gw_power 의 W/P 값)
출력: viz_data/inspiral.json
"""
import json, os, sys
import numpy as np
from growth_rule_test import solve

C_RULE = solve(np.array([0.1, 0, 0]), -2, 0, 0)[0] * 0.1**2
G = C_RULE / (8 * np.pi)
R0, V = 3.0, 0.2
OMEGA = V / R0
M = 4 * R0**3 * OMEGA**2 / G
A0 = 2 * R0
kappa = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def tau(k):
    return A0**4 / (4 * (64 / 5) * 2 * k * G**3 * M**3)


def orbit(k, n=400):
    T = tau(k)
    t = np.linspace(0, T * 0.999, n)
    a = A0 * (1 - t / T)**0.25
    w = np.sqrt(2 * G * M / a**3)
    phase = np.concatenate([[0], np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(t))])
    return t, a, w, phase


if __name__ == '__main__':
    P0 = 32 / 5 * G * (M / 2)**2 * A0**4 * OMEGA**6
    E0 = -G * M**2 / (2 * A0)
    print(f"G = {G:.6f}, m = {M:.2f}, 처음 거리 a0 = {A0}, ω = {OMEGA:.4f}, 궤도 주기 {2*np.pi/OMEGA:.1f}")
    print(f"궤도 에너지 {E0:.4f}, 4중극 방출률 {P0:.4e} -> 에너지/방출률 {abs(E0)/P0:.0f}")
    out = {}
    for label, k in (('4중극 공식', 1.0), ('격자에서 잰 값', kappa)):
        t, a, w, ph = orbit(k)
        T = tau(k)
        n_orb = ph[-1] / (2 * np.pi)
        half = np.interp(A0 / 2, a[::-1], t[::-1])
        print(f"{label:<12} κ = {k:.3f}: 합쳐질 때까지 {T:.0f} (궤도 {n_orb:.1f}바퀴), 거리가 절반이 될 때까지 {half:.0f}")
        out[label] = dict(kappa=k, tau=T, t=np.round(t, 3).tolist(), a=np.round(a, 5).tolist(),
                          x=np.round(0.5 * a * np.cos(ph), 4).tolist(), y=np.round(0.5 * a * np.sin(ph), 4).tolist())
    print("※ 거리가 덩어리 크기(폭 1)에 가까워지면 점질량·약한 장 근사가 깨지므로, 그 이후는 그림용 외삽이다.")
    os.makedirs('viz_data', exist_ok=True)
    json.dump(dict(G=G, mass=M, a0=A0, omega0=OMEGA, curves=out), open('viz_data/inspiral.json', 'w'), ensure_ascii=False)
