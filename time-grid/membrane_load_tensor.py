"""
시간 그리드 사고 실험 — 텐서 막 규칙 1단계: 저장 파동이 26개 막에 주는 방향별 하중

질문: 한 그리드에 저장된 파동이 연결 방향마다 다른 하중을 주는가?
      그 하중들이 대칭 텐서 하나(성분 6개)로 정확히 묶이는가?  6방향 격자로도 되는가?

막 하중 (연결 방향 e, 단위벡터 n = e/|e|):
  sigma_e = kap_eff < (Δ_e u / |e|)^2 > + < L >
  연속 극한에서 Δ_e u ≈ e·∇u 이므로 sigma_e -> n_i n_j T_ij  (T_ij = kap ∂_i u ∂_j u + δ_ij L)
  -> 하중 13개(± 쌍은 같음)를 n·T·n 으로 최소제곱 맞춤, 남는 오차가 '텐서가 아닌 부분'

평면파 u = cos(q·x - ωt)의 격자 시간 평균은 정확히 계산된다:
  <(Δ_e u)^2> = 1 - cos(q·e),   <L> = 0 (한 모드의 운동/위치 에너지 평균이 같음)
여러 파동이 겹치면(서로 위상이 무관) 하중이 더해진다.
"""
import numpy as np
from itertools import product

dirs26 = [np.array(d) for d in product((-1, 0, 1), repeat=3) if any(d)]
half = []                                   # ± 쌍 중 하나씩 -> 13 방향
for d in dirs26:
    if not any(np.array_equal(-d, h) for h in half):
        half.append(d)
half = np.array(half, float)
face = np.array([d for d in half if np.abs(d).sum() == 1])   # 3
edge = np.array([d for d in half if np.abs(d).sum() == 2])   # 6
corner = np.array([d for d in half if np.abs(d).sum() == 3]) # 4


def kap_eff(links):
    """격자 라플라시안 = kap_eff ∇² 가 되도록 하는 유효 강성 (모든 링크 강성 1)"""
    M = sum(2 * np.outer(e, e) for e in links) / 2        # ± 쌍 포함, 공유 보정
    return M[0, 0]


def loads(links, waves):
    """waves: [(q벡터, 세기)] -> 링크 방향별 하중"""
    ke = kap_eff(links)
    out = []
    for e in links:
        s = sum(w * (1 - np.cos(q @ e)) for q, w in waves)   # <(Δu)^2>
        out.append(ke * s / (e @ e))
    return np.array(out)


def fit_tensor(links, sig):
    n = links / np.linalg.norm(links, axis=1)[:, None]
    A = np.column_stack([n[:, 0]**2, n[:, 1]**2, n[:, 2]**2,
                         2 * n[:, 0] * n[:, 1], 2 * n[:, 1] * n[:, 2], 2 * n[:, 0] * n[:, 2]])
    rank = np.linalg.matrix_rank(A)
    c, *_ = np.linalg.lstsq(A, sig, rcond=None)
    T = np.array([[c[0], c[3], c[5]], [c[3], c[1], c[4]], [c[5], c[4], c[2]]])
    resid = np.linalg.norm(A @ c - sig) / np.linalg.norm(sig)
    return T, rank, resid


def continuum_T(waves, ke):
    return sum(w * ke * 0.5 * np.outer(q, q) for q, w in waves)   # kap <∂u∂u>, <L>=0


def report(name, waves):
    links26 = half
    links6 = face
    T26, r26, e26 = fit_tensor(links26, loads(links26, waves))
    T6, r6, e6 = fit_tensor(links6, loads(links6, waves))
    Tc = continuum_T(waves, kap_eff(links26))
    err = np.linalg.norm(T26 - Tc) / np.linalg.norm(Tc)
    shear = np.abs(Tc[np.triu_indices(3, 1)]).max() / np.abs(Tc).max()
    print(f"{name:<34}{r26:>4}{e26:>10.2e}{err:>10.2e}{r6:>5}{shear:>9.3f}")


if __name__ == '__main__':
    print("13개 막 방향: 면 3 + 모서리 6 + 꼭짓점 4  (26개 연결의 ± 쌍)")
    print(f"{'파동':<34}{'계수':>4}{'맞춤오차':>10}{'T오차':>10}{'6방향계수':>5}{'전단비':>9}")
    for qa in (0.05, 0.2, 0.5):
        print(f"--- 파수 × 격자 간격 = {qa}")
        n = lambda v: np.array(v, float) / np.linalg.norm(v)
        report('빛, x축 방향', [(qa * n([1, 0, 0]), 1.0)])
        report('빛, (1,1,0) 대각 방향', [(qa * n([1, 1, 0]), 1.0)])
        report('빛, (1,2,3) 일반 방향', [(qa * n([1, 2, 3]), 1.0)])
        report('빛, 세 방향 겹침(등방)', [(qa * n(v), 1.0) for v in ([1, 0, 0], [0, 1, 0], [0, 0, 1])])
    print("\n계수: 하중이 담을 수 있는 독립 성분 수 (대칭 텐서는 6)")
    print("맞춤오차: 하중 중 n·T·n 으로 설명되지 않는 비율 (텐서가 아닌 부분)")
    print("T오차: 막 하중에서 복원한 텐서와 연속 응력 텐서의 차이")
    print("전단비: 응력 텐서의 비대각(전단) 성분 크기 / 최대 성분")
