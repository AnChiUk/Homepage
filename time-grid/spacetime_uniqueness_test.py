"""
텐서 3단계 보조: 시공간 이름표 무관성이 맞물림 b1, 시계 에너지 b2, 운동 에너지 비를 정하는가?

시계 몫까지 포함한 변형 h_μν (μ = 0 시간, 1~3 공간, 10성분), 파수 4-벡터 q = (ω, q).
움직이는 이름표(시험 4)를 따르는 이웃 결합 이차 에너지 일반형 (η = diag(-1,1,1,1)로 묶음):
  V4 = c1 (q·q) h:h + c2 (q^μ h_μν)(q_ρ h^ρν) + c3 (q^μ q^ν h_μν) h + c4 (q·q) h²
조건: 아무 변형에 '시공간 밀기' h_μν -> h_μν + q_μ ξ_ν + q_ν ξ_μ 를 더해도 에너지가 그대로
      (ξ_0 = 틱 다시 매기기, ξ_i = 그리드 밀기, 시간에 따라 변하는 밀기 포함)
그다음 정적(ω = 0, h_0i = 0) 으로 줄여서 b1, b2 를, 공간 변형만 시간에 따라 변하는 경우로 줄여서
운동 에너지 비를 읽어 낸다.
"""
import numpy as np

ETA = np.diag([-1.0, 1, 1, 1])
rng = np.random.default_rng(1)


def terms(q, h1, h2):
    """V4 의 네 항 (h1, h2 쌍선형, 대칭화)"""
    qu = ETA @ q                                  # 위첨자 q
    H1u = ETA @ h1 @ ETA; H2u = ETA @ h2 @ ETA
    qq = q @ ETA @ q
    t1 = qq * np.sum(h1 * H2u)
    t2 = (qu @ h1) @ ETA @ (qu @ h2)
    tr1, tr2 = np.trace(ETA @ h1), np.trace(ETA @ h2)
    t3 = 0.5 * ((qu @ h1 @ qu) * tr2 + (qu @ h2 @ qu) * tr1)
    t4 = qq * tr1 * tr2
    return [t1, t2, t3, t4]


def sym(M):
    return M + M.T


rows = []
for _ in range(60):
    q = rng.normal(size=4)
    xi = rng.normal(size=4)
    h1 = sym(rng.normal(size=(4, 4)))
    h2 = np.outer(q, xi) + np.outer(xi, q)        # 시공간 밀기 (아래첨자 q)
    rows.append(terms(q, h1, h2))
A = np.array(rows)
u, s, vt = np.linalg.svd(A)
c = vt[-1] / vt[-1][0]
dim = int(np.sum(s / s.max() < 1e-10))
print(f"시공간 이름표 무관 해: 차원 {dim}, (c1,c2,c3,c4) = {np.round(c, 10)}")


def V4(q, h):
    return sum(ci * ti for ci, ti in zip(c, terms(q, h, h)))


# 정적 축소: ω=0, h_0i=0.  V4 = V(h_s) + b1 h00 R(h_s) + b2 q² h00² 꼴인지 맞춤
qs = np.array([0, *rng.normal(size=3)])
q3 = qs[1:]
def V3(hs):
    return (q3 @ q3) * np.sum(hs * hs) - 2 * (q3 @ hs) @ (q3 @ hs) + 2 * (q3 @ hs @ q3) * np.trace(hs) \
        - (q3 @ q3) * np.trace(hs)**2
X, Y = [], []
for _ in range(20):
    hs = sym(rng.normal(size=(3, 3))); h00 = rng.normal()
    h = np.zeros((4, 4)); h[0, 0] = h00; h[1:, 1:] = hs
    R = q3 @ hs @ q3 - (q3 @ q3) * np.trace(hs)
    X.append([V3(hs), h00 * R, (q3 @ q3) * h00**2]); Y.append(V4(qs, h))
coef, res, *_ = np.linalg.lstsq(np.array(X), np.array(Y), rcond=None)
print(f"정적 축소: V4 = {coef[0]:.6f}·V(공간) + ({coef[1]:+.6f})·h00·R + ({coef[2]:+.6f})·q²·h00²")
print(f"  -> 공간 에너지로 나눈 b1 = {coef[1]/coef[0]:+.6f}, b2 = {coef[2]/coef[0]:+.6f}   (γ = 1 에 필요: b1 = -2)")

# 운동 에너지: q = (ω, 0, 0, 0), h_0μ = 0  ->  V4 = -ω² (a h:h + b h²) 꼴
qt = np.array([1.0, 0, 0, 0])
X, Y = [], []
for _ in range(20):
    hs = sym(rng.normal(size=(3, 3)))
    h = np.zeros((4, 4)); h[1:, 1:] = hs
    X.append([np.sum(hs * hs), np.trace(hs)**2]); Y.append(-V4(qt, h))
k, *_ = np.linalg.lstsq(np.array(X), np.array(Y), rcond=None)
print(f"운동 에너지: ω² ({k[0]:.6f} h:h + ({k[1]:+.6f}) h²)  -> 비 = {k[1]/k[0]:+.6f}   (GR형: -1)")
