"""
시간 그리드 사고 실험 — 텐서 2단계: 막 변형 결합 규칙의 모드 세기

막 변형 h_ij (대칭 텐서, 6성분)가 평면파 e^{i(q·x - ωt)} 로 퍼질 때
  운동 에너지 ½ h·K·h (ω²),  위치 에너지 ½ h·V(q)·h
  -> 운동방정식  ω² K h = V(q) h  (일반화 고유값 문제)
모양 하나(고유벡터)마다:
  ω² > 0 : 실제로 출렁이는 모드
  ω² = 0 이고 이름표 바꾸기 h = q⊗ξ + ξ⊗q 와 같으면 : 이름표 모드(관측 불가)
GR은 출렁이는 모드 2개(+, ×), 속도 = 빛.

후보
  C1 성분별 탄성   : K = 1,  V = q² (각 성분이 독립된 파동)
  C2 그리드 밀기   : 그리드가 u 만큼 밀려 h = ½(∂u + ∂uᵀ) (평범한 탄성체, 라메 상수 λ, μ)
  C3 GR형          : 선형화된 아인슈타인-힐베르트 에너지 (시간 게이지 h_0μ = 0)
                     K(h) = h_ij h_ij - h²
                     V(h) = q² h_ij h_ij - 2 (q_i h_ij)(q_k h_kj) + 2 (q_i q_j h_ij) h - q² h²
                     + 구속조건: q_i q_j h_ij - q² h = 0,  q_j h_ij - q_i h = 0
격자: q_i 를 격자 기호 s_i = (2/a) sin(q_i a / 2) 로 바꿔 같은 계산 (이름표 무관성이 격자에서도 정확히 유지됨)
"""
import numpy as np

# 대칭 텐서의 정규직교 기저 (프로베니우스 내적)
BASIS = []
for i in range(3):
    E = np.zeros((3, 3)); E[i, i] = 1; BASIS.append(E)
for i, j in ((0, 1), (1, 2), (0, 2)):
    E = np.zeros((3, 3)); E[i, j] = E[j, i] = 1 / np.sqrt(2); BASIS.append(E)
BASIS = np.array(BASIS)


def form(f):
    """이차 형식 f(h) -> 6x6 대칭 행렬"""
    M = np.zeros((6, 6))
    for A in range(6):
        for B in range(6):
            M[A, B] = 0.25 * (f(BASIS[A] + BASIS[B]) - f(BASIS[A] - BASIS[B]))
    return M


def vec(h):
    return np.array([np.sum(E * h) for E in BASIS])


def C1(q):
    K = form(lambda h: np.sum(h * h))
    V = form(lambda h: (q @ q) * np.sum(h * h))
    return K, V


def C3(q):
    K = form(lambda h: np.sum(h * h) - np.trace(h)**2)
    def pot(h):
        qh = q @ h
        return (q @ q) * np.sum(h * h) - 2 * qh @ qh + 2 * (q @ h @ q) * np.trace(h) - (q @ q) * np.trace(h)**2
    V = form(pot)
    return K, V


def constraints(q):
    """C3 구속조건 행렬 (4 x 6): 해밀토니안 1 + 운동량 3"""
    rows = []
    rows.append([q @ E @ q - (q @ q) * np.trace(E) for E in BASIS])
    for i in range(3):
        rows.append([(E @ q)[i] - q[i] * np.trace(E) for E in BASIS])
    return np.array(rows)


def gauge_space(q):
    """이름표 바꾸기 방향 h = q⊗ξ + ξ⊗q (ξ 3개)"""
    G = []
    for k in range(3):
        xi = np.zeros(3); xi[k] = 1
        G.append(vec(np.outer(q, xi) + np.outer(xi, q)))
    return np.array(G).T          # 6 x 3


def null_space(M, tol=1e-9):
    u, sv, vt = np.linalg.svd(M)
    scale = max(sv.max(), 1e-300)
    return vt[np.sum(sv > tol * scale):].T


def analyze(K, V, q, cons=None):
    """출렁임 = ω²≠0 인 모드 수, 정적 = V 의 영공간 중 이름표가 아닌 차원, 이름표 = 영공간 ∩ 이름표 공간"""
    q2 = q @ q
    w2 = np.linalg.eigvals(np.linalg.solve(K, V)).real
    osc = sorted(np.sqrt(w / q2) for w in w2 if w > 1e-7 * q2)
    Nv = null_space(V)
    G = gauge_space(q)
    dimN = Nv.shape[1]
    dimNG = np.linalg.matrix_rank(np.hstack([Nv, G]), tol=1e-7) if dimN else 3
    n_gauge = dimN + 3 - dimNG          # 영공간과 이름표 공간의 교집합 차원
    static = dimN - n_gauge
    removed = None
    if cons is not None and static:
        # 이름표가 아닌 정적 방향이 진공 구속조건에서 0으로 강제되는가
        Pg = G @ np.linalg.pinv(G)
        rest = Nv - Pg @ Nv
        rest = rest[:, np.linalg.norm(rest, axis=0) > 1e-6]
        removed = np.linalg.matrix_rank(cons @ rest, tol=1e-7 * q2) if rest.size else 0
    return osc, n_gauge, static, removed


def summarize(name, K, V, q, cons=None):
    osc, ng, st, rm = analyze(K, V, q, cons)
    sp = ', '.join(f'{s:.3f}' for s in osc) if osc else '-'
    extra = '' if rm is None else f'   (정적 {st}개 중 구속조건이 없애는 수: {rm})'
    print(f"{name:<22}{len(osc):>6}{ng:>7}{st:>7}   속도(빛=1): {sp}{extra}")


def C2_modes(q, lam=1.0, mu=1.0):
    """평범한 탄성체: 변위 u 3성분 -> 모드 3개. 그 변형 h=½(qu+uq)가 C3 에너지에서 얼마인지"""
    qn = q / np.linalg.norm(q)
    t1 = np.cross(qn, [0, 0, 1.0] if abs(qn[2]) < 0.9 else [1.0, 0, 0]); t1 /= np.linalg.norm(t1)
    t2 = np.cross(qn, t1)
    _, V3 = C3(q)
    rows = []
    for name, u, w2 in (('종파(압축)', qn, (lam + 2 * mu) * (q @ q)),
                        ('횡파 1', t1, mu * (q @ q)), ('횡파 2', t2, mu * (q @ q))):
        h = vec(0.5 * (np.outer(q, u) + np.outer(u, q)))
        curv = h @ V3 @ h / (q @ q)**2
        rows.append((name, np.sqrt(w2 / (q @ q)), curv))
    return rows


if __name__ == '__main__':
    q = 0.3 * np.array([1.0, 2.0, 3.0]) / np.sqrt(14)          # 임의 방향, 연속 극한
    print("연속 극한, 진행 방향 (1,2,3)")
    print(f"{'후보':<22}{'출렁임':>6}{'이름표':>7}{'정적':>7}")
    summarize('C1 성분별 탄성', *C1(q), q)
    summarize('C3 GR형', *C3(q), q, constraints(q))

    print("\nC2 그리드 밀기 (라메 λ=μ=1): 모드 3개, 각 모드의 막 변형이 C3 에너지(곡률)에서 갖는 값")
    for name, sp, curv in C2_modes(q):
        print(f"  {name:<12} 속도 {sp:.3f}   GR형 에너지/|q|⁴ = {curv:.1e}")

    print("\n격자 위 C3 (s_i = (2/a)sin(q_i a/2)): 출렁임 개수, 속도 / 이름표 개수")
    print(f"{'파수×격자간격':>12}{'축(1,0,0)':>18}{'면대각(1,1,0)':>18}{'체대각(1,1,1)':>18}")
    for qa in (0.05, 0.3, 0.8, 1.5):
        row = []
        for d in ([1, 0, 0], [1, 1, 0], [1, 1, 1]):
            qv = qa * np.array(d, float) / np.linalg.norm(d)
            sv = 2 * np.sin(qv / 2)
            osc, ng, st, rm = analyze(*C3(sv), sv, constraints(sv))
            v = [o * np.linalg.norm(sv) / qa for o in osc]          # 격자 파수 qa 기준 속도
            row.append(f"{len(osc)}개 {np.mean(v):.4f} / {ng}")
        print(f"{qa:>12}" + ''.join(f"{c:>18}" for c in row))
