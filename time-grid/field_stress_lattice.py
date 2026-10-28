"""
시간 그리드 사고 실험 — 비선형 1-가: 장 자신의 막 하중 (3D 격자, 정적)

규칙: 막 하중 = 그리드를 밀었을 때(막 길이를 바꿨을 때) 에너지가 바뀌는 정도.
물질에 쓴 이 정의를 장(시계 몫 Φ) 자신의 에너지에도 그대로 적용한다.

장의 에너지 (규칙의 뉴턴 극한):  E = (1/8πG) Σ_링크 (Δ_eΦ / a)² a³
축 i 방향 막 길이를 (1+ε) 배로 늘이면  dE/dε = -Σ (1/4πG) [(Δ_iΦ/a)² - ½|∇Φ|²] a³
-> 장의 하중  t_ij = (1/4πG) (∂_iΦ ∂_jΦ - ½ δ_ij |∇Φ|²)   (손으로 넣은 2-b-1의 장 응력과 같은 꼴)

시험: 물질 덩어리 둘의 장에서, 장의 하중 t_ij 의 발산이 물질이 받는 힘 ρ∂_iΦ 를 메우는가
      ∂_j t_ij = ρ ∂_iΦ   (메우면 물질 + 장의 응력이 국소 보존 -> 이름표 무관한 원천)
격자 간격을 줄여 가며(덩어리 폭 / 간격 = 2, 4, 8) 남는 값이 0으로 가는지 본다.
"""
import json, os
import numpy as np

G = 1 / (32 * np.pi)                  # 2-b-1과 같은 규칙 값


def run(res):
    sig = 1.5                          # 덩어리 폭 (물리 단위)
    a = sig / res
    Lbox = 32.0
    N = int(round(Lbox / a))
    c = (np.arange(N) - N // 2) * a
    X, Y, Z = np.meshgrid(c, c, c, indexing='ij')
    rho = np.zeros_like(X)
    for x0, y0 in ((4.0, 0.0), (-4.0, 0.0)):
        rho += np.exp(-((X - x0)**2 + (Y - y0)**2 + Z**2) / (2 * sig**2))
    rho /= (2 * np.pi * sig**2)**1.5
    q = 2 * np.pi * np.fft.fftfreq(N, d=a)
    QX, QY, QZ = np.meshgrid(q, q, q, indexing='ij')
    lap = -(4 / a**2) * (np.sin(QX * a / 2)**2 + np.sin(QY * a / 2)**2 + np.sin(QZ * a / 2)**2)
    rq = np.fft.fftn(rho - rho.mean())
    lap[0, 0, 0] = 1
    Phi = np.real(np.fft.ifftn(4 * np.pi * G * rq / lap))      # 격자 푸아송: L Φ = 4πG(ρ - ρ̄)

    # 링크(반 칸 위치) 차분 -> 노드로 평균 (대칭)
    def dlink(f, ax):
        return (np.roll(f, -1, ax) - f) / a                      # x + a/2 위치
    D = [dlink(Phi, ax) for ax in range(3)]
    def to_node(f, ax):
        return 0.5 * (f + np.roll(f, 1, ax))
    # 노드의 기울기 (중심 차분)
    g = [to_node(D[ax], ax) for ax in range(3)]
    # 장의 하중: 대각은 링크 제곱을 노드 평균 (에너지 정의와 같음), 비대각은 노드 기울기 곱
    sq = [to_node(D[ax]**2, ax) for ax in range(3)]
    grad2 = sum(sq)
    t = [[None] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            t[i][j] = (sq[i] - 0.5 * grad2) / (4 * np.pi * G) if i == j else g[i] * g[j] / (4 * np.pi * G)
    # 발산 (중심 차분) vs 물질이 받는 힘
    def dc(f, ax):
        return (np.roll(f, -1, ax) - np.roll(f, 1, ax)) / (2 * a)
    div = [sum(dc(t[i][j], j) for j in range(3)) for i in range(3)]
    rb = rho - rho.mean()                                      # 주기 상자의 중성 배경 포함
    force = [rb * g[i] for i in range(3)]
    # 덩어리 근처(ρ 가 의미 있는 영역)에서 비교
    mask = rho > 1e-3 * rho.max()
    num = np.sqrt(sum(np.sum((div[i] - force[i])[mask]**2) for i in range(3)))
    den = np.sqrt(sum(np.sum(force[i][mask]**2) for i in range(3)))
    # 덩어리 하나(x>0)가 받는 알짜 힘: 물질 쪽 ∫ρ∂Φ  vs 장의 하중이 경계면으로 전하는 힘
    i0 = N // 2
    right = np.zeros_like(rho, dtype=bool); right[i0:] = True         # x = 0 ~ 상자 끝
    F_mat = np.sum((rb * g[0])[right]) * a**3
    # x = 0 평면을 지나는 장의 하중 흐름 (오른쪽 덩어리를 감싸는 면)
    # 오른쪽 절반의 두 경계면: x = 0 (안쪽) 과 상자 끝(주기 경계로 맞붙은 면)
    F_field = (np.sum(t[0][0][N - 1]) - np.sum(t[0][0][i0 - 1])) * a**2
    return dict(res=res, a=a, N=N, rel_resid=num / den, F_matter=F_mat, F_field=F_field)


if __name__ == '__main__':
    os.makedirs('viz_data', exist_ok=True)
    rows = []
    print(f"{'폭/간격':>8}{'격자':>6}{'국소 균형 남는 값':>18}{'오른쪽 덩어리 힘(물질)':>24}{'(장 하중 면 흐름)':>18}")
    for res in (2, 4, 8):
        r = run(res)
        rows.append(r)
        print(f"{res:>8}{r['N']:>6}{r['rel_resid']:>18.2e}{r['F_matter']:>24.6f}{r['F_field']:>18.6f}", flush=True)
    json.dump(dict(note='장 자신의 막 하중이 물질이 받는 힘을 메우는지 (3D 격자, 정적)', rows=rows),
              open('viz_data/field_stress_lattice.json', 'w'), ensure_ascii=False)
