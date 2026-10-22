"""
시간 그리드 사고 실험 — 동역학 2-a: 자유 중력파 전파 (3D 격자, 막 변형만)

막 변형 h_ij 를 텐서 2·3단계에서 정해진 에너지로 시간 진행한다 (시계 몫 h_0μ = 0 로 둔 시간 게이지).
  운동: ½(ḣ:ḣ - ḣ²),  위치: ½ V(h) (유일한 이름표 무관 형태),  격자 기호 s_i = 2 sin(q_i a/2)/a
  -> 파수마다  K ḧ = -V(s) h  (6x6),  leapfrog 로 진행 (모든 파수를 한꺼번에)

초기 상태 = (1) z 방향으로 가는 + 편광 또는 × 편광 중력파 펄스
          + (2) 같은 크기의 '이름표 성분' (그리드를 가우스 모양으로 밀어 놓은 것, h = ∂ξ + ∂ξᵀ)
측정 (틱으로 잰 홉 = 시간 게이지에서 고정 좌표 표지 사이의 고유 거리):
  - 펄스 중심의 위치 -> 전파 속도
  - xy 평면의 고리 표지 16개까지의 거리 -> + / × 모양 찌그러짐
  - 이름표 성분은 고리를 고정된 모양으로만 바꾸고 출렁이지 않아야 함

웹 시각화용 출력: viz_data/gw_free_{pol}.json
  frames: 시각 t, xz 단면의 TT 진폭(32x32로 줄임), 고리 반지름 16개
"""
import json, os
import numpy as np
from mode_count_test import BASIS

NG, A = 96, 1.0
AMP, SIG_Z, LAM = 1e-3, 5.0, 10.0        # 펄스 진폭, 길이 폭, 파장
Z0 = -24.0                               # 펄스 출발 위치 (고리는 z = 0)
W_XY = 14.0                              # 펄스 가로 폭 (평면파에 가깝게)
GAUGE_AMP, GAUGE_SIG = 1e-3 * 4.0, 4.0   # 이름표 성분 크기
R_RING, N_RING = 6.0, 16
Z_RING = 0.0
DT, T_END, SAVE_EVERY = 0.25, 48.0, 4

c = (np.arange(NG) - NG // 2) * A
X, Y, Z = np.meshgrid(c, c, c, indexing='ij')
qv = 2 * np.pi * np.fft.fftfreq(NG, d=A)
QX, QY, QZ = np.meshgrid(qv, qv, qv, indexing='ij')
S = np.stack([2 * np.sin(Q * A / 2) / A for Q in (QX, QY, QZ)], -1)     # (n,n,n,3)


def to_vec(h33):
    """(...,3,3) -> (...,6) 정규직교 기저 성분"""
    return np.stack([np.sum(h33 * E, axis=(-2, -1)) for E in BASIS], -1)


def to_mat(v6):
    return np.einsum('...a,aij->...ij', v6, BASIS)


def operators():
    """파수마다 K, V (6x6).  K(h) = h:h - (tr h)^2,  V(h) = s²h:h - 2|s·h|² + 2(s·h·s)tr h - s²(tr h)²"""
    E = BASIS
    trE = np.trace(E, axis1=1, axis2=2)
    K = np.einsum('aij,bij->ab', E, E) - np.outer(trE, trE)
    s2 = np.sum(S**2, -1)[..., None, None]
    EE = np.einsum('aij,bij->ab', E, E)
    sE = np.einsum('...i,aij->...aj', S, E)                    # (s·E_a)_j
    t2 = np.einsum('...aj,...bj->...ab', sE, sE)
    sEs = np.einsum('...aj,...j->...a', sE, S)
    t3 = sEs[..., :, None] * trE[None, None, None, None, :] + sEs[..., None, :] * trE[:, None]
    V = s2 * EE - 2 * t2 + t3 - s2 * np.outer(trE, trE)
    return K, V


def initial(pol):
    env = AMP * np.exp(-(Z - Z0)**2 / (2 * SIG_Z**2) - (X**2 + Y**2) / (2 * W_XY**2))
    kz = 2 * np.pi / LAM
    e = np.zeros((3, 3))
    if pol == 'plus':
        e[0, 0], e[1, 1] = 1, -1
    else:
        e[0, 1] = e[1, 0] = 1
    wave = env * np.cos(kz * (Z - Z0))
    h = wave[..., None, None] * e
    # +z 로 가도록: ḣ = -∂_z h (속도 1)
    dz = np.gradient(wave, A, axis=2)
    hd = (-dz)[..., None, None] * e
    # 이름표 성분: ξ = 가우스 (정지).  시뮬레이션과 같은 격자 미분으로 h_g = s⊗ξ + ξ⊗s (푸리에)
    g = GAUGE_AMP * np.exp(-((X - 8)**2 + (Y + 4)**2 + Z**2) / (2 * GAUGE_SIG**2))
    xi = np.stack([g, 0.6 * g, -0.4 * g], -1)
    xiq = np.fft.fftn(xi, axes=(0, 1, 2))
    hgq = 1j * (S[..., :, None] * xiq[..., None, :] + xiq[..., :, None] * S[..., None, :])
    hg = np.real(np.fft.ifftn(hgq, axes=(0, 1, 2)))
    # 펄스를 순수 TT(두 편광) 성분으로 거름: 격자 기호 s 로 만든 TT 투영
    s2 = np.sum(S**2, -1); s2[s2 == 0] = 1
    sh = S / np.sqrt(s2)[..., None]
    P = np.eye(3) - sh[..., :, None] * sh[..., None, :]
    def tt(f):
        fq = np.fft.fftn(f, axes=(0, 1, 2))
        gq = 0.5 * (np.einsum('...ik,...jl,...kl->...ij', P, P, fq) * 2
                    - P * np.einsum('...kl,...kl->...', P, fq)[..., None, None])
        return np.real(np.fft.ifftn(gq, axes=(0, 1, 2)))
    h, hd = tt(h), tt(hd)
    return to_vec(h), to_vec(hd), to_vec(hg)


def ring_radii(h_real):
    """중심에서 고리 표지까지 반지름 방향 고유 거리 L = ∫ (1 + ½ n·h·n) ds"""
    th = np.linspace(0, 2 * np.pi, N_RING, endpoint=False)
    s = np.linspace(0, R_RING, 49)
    out = []
    for t in th:
        n = np.array([np.cos(t), np.sin(t), 0.0])
        pts = s[:, None] * n
        idx = pts / A + NG // 2
        i0 = np.floor(idx).astype(int); f = idx - i0
        val = 0.0
        acc = np.zeros(len(s))
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    wgt = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                    hh = h_real[(i0[:, 0] + dx) % NG, (i0[:, 1] + dy) % NG, (i0[:, 2] + dz) % NG]
                    acc += wgt * np.einsum('ki,kij,kj->k', np.tile(n, (len(s), 1)), hh, np.tile(n, (len(s), 1)))
        out.append(R_RING + 0.5 * np.trapezoid(acc, s))
    return np.array(out)


def run(pol, with_wave=True, with_gauge=True):
    K, V = operators()
    Kinv = np.linalg.inv(K)
    M = np.einsum('ab,...bc->...ac', Kinv, V)                   # ḧ = -M h
    h0, hd0, hg = initial(pol)
    hv = (h0 if with_wave else 0 * h0) + (hg if with_gauge else 0 * hg)
    vv = hd0 if with_wave else 0 * hd0
    hq = np.fft.fftn(hv, axes=(0, 1, 2)); vq = np.fft.fftn(vv, axes=(0, 1, 2))
    acc = lambda h: -np.einsum('...ab,...b->...a', M, h)
    a = acc(hq)
    frames = []
    nst = int(T_END / DT)
    for n in range(nst + 1):
        if n % SAVE_EVERY == 0:
            hr = np.real(np.fft.ifftn(hq, axes=(0, 1, 2)))
            h33 = to_mat(hr)
            hp = 0.5 * (h33[..., 0, 0] - h33[..., 1, 1]); hx = h33[..., 0, 1]
            tt = np.sqrt(hp**2 + hx**2)
            prof = tt[NG // 2, NG // 2, :]                       # z 축 위 TT 크기
            zpk = float(np.sum(c * prof**2) / np.sum(prof**2))   # 파동 묶음 무게중심
            sl = (hp if pol == 'plus' else hx)[:, NG // 2, :]    # xz 단면
            sl32 = sl.reshape(32, 3, 32, 3).mean(axis=(1, 3))
            frames.append(dict(t=round(n * DT, 3), z_peak=float(zpk),
                               slice=np.round(sl32 / AMP, 4).tolist(),
                               ring=np.round(ring_radii(h33) - R_RING, 8).tolist()))
        vq += 0.5 * DT * a
        hq += DT * vq
        a = acc(hq)
        vq += 0.5 * DT * a
    return frames


if __name__ == '__main__':
    os.makedirs('viz_data', exist_ok=True)
    th = np.linspace(0, 2 * np.pi, N_RING, endpoint=False)
    for pol in ('plus', 'cross'):
        fr = run(pol)
        fg = run(pol, with_wave=False)                           # 이름표 성분만
        # 전파 속도: 펄스가 고리를 지나기 전후 z_peak 선형 맞춤 (t = 4 ~ 20)
        ts = np.array([f['t'] for f in fr]); zs = np.array([f['z_peak'] for f in fr])
        sel = (ts > 4) & (ts < 44)
        vel = np.polyfit(ts[sel], zs[sel], 1)[0]
        # 고리 찌그러짐: 각 시각 반지름 변화의 cos2θ, sin2θ 성분
        rings = np.array([f['ring'] for f in fr]); rg = np.array([f['ring'] for f in fg])
        c2 = rings @ np.cos(2 * th) * 2 / N_RING; s2 = rings @ np.sin(2 * th) * 2 / N_RING
        g_c2 = rg @ np.cos(2 * th) * 2 / N_RING; g_s2 = rg @ np.sin(2 * th) * 2 / N_RING
        q0 = 2 * np.pi / LAM
        print(f"[{pol}] 전파 속도 {vel:.3f}  (격자 예측 cos(qa/2) = {np.cos(q0 * A / 2):.3f}, 연속 극한 = 1)")
        print(f"   고리 + 모양(cos2θ) 진폭 최대 {np.max(np.abs(c2 - c2[0])):.2e},  × 모양(sin2θ) 최대 {np.max(np.abs(s2 - s2[0])):.2e}")
        print(f"   이름표 성분만: 고리 변화의 시간 변동 cos2θ {np.ptp(g_c2):.1e}, sin2θ {np.ptp(g_s2):.1e}, "
              f"전체 반지름 {np.ptp(rg, axis=0).max():.1e}  (출렁이지 않으면 0)")
        out = dict(pol=pol, grid=NG, dt_frame=DT * SAVE_EVERY, amp=AMP, ring_radius=R_RING,
                   ring_angles=np.round(th, 5).tolist(), speed=round(float(vel), 4), frames=fr)
        with open(f'viz_data/gw_free_{pol}.json', 'w') as fobj:
            json.dump(out, fobj)
        print(f"   저장: viz_data/gw_free_{pol}.json ({os.path.getsize(f'viz_data/gw_free_{pol}.json')/1e6:.1f} MB)")
