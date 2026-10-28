"""
시간 그리드 사고 실험 — 동역학 2-b-3 분석: 궤도 출렁임에 흔들리지 않는 방출 세기

coupled_orbit.py 의 거리 d 맞춤은 원천을 켜는 동안 생긴 작은 이심률(거리의 출렁임)에 흔들린다.
궤도 에너지는 이심 궤도에서도 일정하므로, 그 에너지로 정한 장반경으로 다시 잰다.
    a(t) = G m² / (-2 E_궤도(t))            (같은 질량 둘의 케플러 궤도)
    a⁴(t) = a0⁴ - 4 K κ t                  -> κ_a
    κ_W(t) = (장에 넘겨준 에너지율) / P(a),  P(a) = (32/5) G μ² a⁴ ω⁶ = (64/5) G⁴ m⁵ / a⁵
예측: 보존 원천 κ = 0.939 (2-b-2 잰 방출 세기), 운동 응력만 κ ≈ 0.939 / 4 (진폭 절반 -> 세기 1/4)

실행: python coupled_orbit_analysis.py   (viz_data/coupled_orbit_{bound,kinetic}.json 필요)
"""
import json
import numpy as np


def analyse(case, t_from=50.0):
    d = json.load(open(f'viz_data/coupled_orbit_{case}.json', encoding='utf-8'))
    G, m, K4 = d['G'], d['mass'], d['K4']
    t = np.array(d['t']); E = np.array(d['E_orb']); W = np.array(d['W']); dist = np.array(d['d'])
    a = G * m * m / (-2 * E)
    sel = t >= t_from
    kap_a = -np.polyfit(t[sel], a[sel]**4, 1)[0] / (4 * K4)
    # 넘겨준 에너지율: 누적 W 를 궤도 주기쯤의 창으로 미분해 출렁임을 지움
    P = 64 / 5 * G**4 * m**5 / a**5
    win = 40.0
    rate, kw = [], []
    for i in np.where(sel)[0]:
        j = np.searchsorted(t, t[i] + win)
        if j >= len(t):
            break
        r = (W[j] - W[i]) / (t[j] - t[i]); rate.append(r)
        kw.append(r / np.mean(P[i:j + 1]))
    # 이심률: 한 궤도 주기 창에서 (d_max - d_min) / (d_max + d_min)
    T_orb = 2 * np.pi / np.sqrt(2 * G * m / a**3)
    ecc = []
    for i in np.where(sel)[0]:
        j = np.searchsorted(t, t[i] + T_orb[i])
        if j >= len(t):
            break
        seg = dist[i:j + 1]; ecc.append((seg.max() - seg.min()) / (seg.max() + seg.min()))
    return dict(kap_a=kap_a, kap_W=float(np.mean(kw)), kap_W_spread=float(np.ptp(kw)) if kw else 0.0,
                ecc=float(np.mean(ecc)) if ecc else float('nan'), a0=float(a[sel][0]), a1=float(a[-1]), t1=float(t[-1]),
                dE=float(E[sel][-1] - E[sel][0]), dW=float(W[sel][-1] - W[sel][0]))


if __name__ == '__main__':
    lines = ["[2-b-3 분석] 장반경 a = Gm²/(-2E) 로 잰 방출 세기 (t ≥ 50)"]
    for case, exp in (('bound', 0.939), ('kinetic', 0.939 / 4)):
        r = analyse(case)
        lines.append(f"   {case:8s} κ_a = {r['kap_a']:.4f}   κ_W = {r['kap_W']:.4f} (창 이동 폭 {r['kap_W_spread']:.3f})   기대 {exp:.3f}   "
                     f"평균 이심률 {r['ecc']:.3f}   장반경 {r['a0']:.3f} -> {r['a1']:.3f} (t = {r['t1']:.0f})   -ΔE/ΔW = {-r['dE'] / r['dW']:.3f}")
    print('\n'.join(lines))
    with open('coupled_orbit_analysis_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
