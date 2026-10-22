"""
시간 그리드 사고 실험 — 동역학 2-b-1 웹 시각화 데이터 만들기

gw_emission.py 의 결과(viz_data/gw_emission_{kinetic,bound,bound_224}.json, 각 10 MB, 저장소에는 올리지 않음)에서
웹에서 재생할 만큼만 뽑아 viz_data/web_gw_emission.json 으로 저장한다.
  frames : 224³ 보존 원천(bound)의 xy 평면(z = 0), xz 평면(y = 0) h+ 단면 64x64, 4 시간 단위마다
           값 = h+ / (r·h 예측 상수), ±2 에서 자름
  rings  : z = 40 고리 표지 16개의 거리 변화 (bound 224³)
  amp    : 반지름별 r·진폭/예측 (시뮬레이션) 과 같은 규칙의 정확한 해 곡선 (gw_emission_theory.py)
"""
import json
import numpy as np
from gw_emission_theory import profile

load = lambda name: json.load(open(f'viz_data/{name}.json', encoding='utf-8'))
B, A, B160 = load('gw_emission_bound_224'), load('gw_emission_kinetic'), load('gw_emission_bound')

clip = lambda f: np.round(np.clip(np.array(f), -2, 2), 3).tolist()
frames = [dict(t=f['t'], xy=clip(f['xy']), xz=clip(f['xz'])) for f in B['frames']]

Om = 2 * B['omega']
rr = np.arange(12, 81, 2)
theory = profile(rr, Om)

out = dict(
    note='동역학 2-b-1: 궤도를 흉내 낸 원천의 막 변형파 방출. 값은 4중극 공식(같은 G) 대비.',
    G=B['G'], omega=B['omega'], r0=B['r0'], v=B['v'], mass=B['mass'], ramp=B['ramp'],
    wavelength=round(np.pi / B['omega'], 2), amp_pred=B['amp_pred'],
    view=B['view'], frame_every=4.0,
    ring_z=B['ring_z'], ring_radius=B['ring_radius'], ring_angles=B['ring_angles'],
    rings_bound=B['rings_face'],
    amp=dict(
        theory=dict(r=rr.tolist(), face=np.round(theory[:, 0], 4).tolist()),
        bound_224=dict(r=B['radii'], face=[round(x[0], 4) for x in B['rh']], grid=224),
        bound_160=dict(r=B160['radii'], face=[round(x[0], 4) for x in B160['rh']], grid=160),
        kinetic_160=dict(r=A['radii'], face=[round(x[0], 4) for x in A['rh']], grid=160),
    ),
    frames=frames,
)
with open('viz_data/web_gw_emission.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
print('저장: viz_data/web_gw_emission.json')
