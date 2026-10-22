"""
텐서 2단계 보조: 이웃 막 결합(2계 미분) 이차 에너지 중 '그리드를 밀어도 에너지 0'(이름표 무관)을
만족하는 것이 유일한가?

일반형 V = c1 q² h:h + c2 (q·h)·(q·h) + c3 (q·h·q) tr h + c4 q² (tr h)²
조건 (약): 밀기만 한 변형 h = q⊗ξ + ξ⊗q 의 에너지가 0
조건 (완전): 아무 변형 h 에 밀기를 더해도 에너지가 그대로, 즉 교차항 V(h, 밀기) = 0
-> c 에 대한 선형 방정식. 해 공간의 차원과 방향을 구한다. (GR형 C3 = (1, -2, 2, -1))
"""
import numpy as np
rng = np.random.default_rng(0)
rows = []
for _ in range(40):
    q = rng.normal(size=3); xi = rng.normal(size=3); eta = rng.normal(size=3)
    # V 는 이차형식이므로 h1, h2 교차항까지 조건에 넣음 (밀기 공간 전체에서 0)
    for a, b in ((xi, xi), (xi, eta), (eta, eta)):
        h1 = np.outer(q, a) + np.outer(a, q)
        h2 = np.outer(q, b) + np.outer(b, q)
        rows.append([(q @ q) * np.sum(h1 * h2),
                     (q @ h1) @ (q @ h2),
                     0.5 * ((q @ h1 @ q) * np.trace(h2) + (q @ h2 @ q) * np.trace(h1)),
                     (q @ q) * np.trace(h1) * np.trace(h2)])
A_weak = np.array(rows)
rows2 = list(rows)
for _ in range(40):
    q = rng.normal(size=3); xi = rng.normal(size=3)
    M = rng.normal(size=(3, 3)); h1 = M + M.T                    # 아무 변형
    h2 = np.outer(q, xi) + np.outer(xi, q)                       # 밀기
    rows2.append([(q @ q) * np.sum(h1 * h2),
                  (q @ h1) @ (q @ h2),
                  0.5 * ((q @ h1 @ q) * np.trace(h2) + (q @ h2 @ q) * np.trace(h1)),
                  (q @ q) * np.trace(h1) * np.trace(h2)])
for label, A in (('약한 조건', A_weak), ('완전한 조건', np.array(rows2))):
    u, s, vt = np.linalg.svd(A)
    dim = int(np.sum(s / s.max() < 1e-10))
    sol = vt[-1] / vt[-1][0]
    print(f"{label}: 해 공간 차원 {dim}, 해 (c1,c2,c3,c4) = {np.round(sol, 10)}")
print("GR형 C3 = (1, -2, 2, -1)")
raise SystemExit
u, s, vt = np.linalg.svd(A)
print("특잇값:", np.round(s / s.max(), 12))
sol = vt[-1] / vt[-1][0]
print("이름표 무관 해의 차원:", int(np.sum(s / s.max() < 1e-10)))
print("해 (c1, c2, c3, c4) =", np.round(sol, 10), "  GR형 C3 = (1, -2, 2, -1)")
