# 시간 그리드 사고 실험 — 시뮬레이션 코드와 데이터

2026-10-23 기준. 실험 전체 내용과 결과는 `doc/시간 그리드 사고 실험.md`에 있다.

## 실행 환경

- Python 3.10 이상
- `pip install numpy scipy matplotlib`
- `gw_free_dynamics.py`는 `np.trapezoid`를 써서 numpy 2 이상이 필요하다. `gw_emission.py`는 numpy 1.x와 2.x 모두에서 돈다.
- 모든 코드는 이 폴더를 작업 폴더로 두고 실행한다 (서로 import 함: `relabel_test_1d.py`, `mode_count_test.py`, `growth_rule_test.py`를 다른 파일이 불러 씀).

## 파일과 실험 대응

| 파일 | 실험 | 비고 |
| --- | --- | --- |
| `relabel_test_1d.py`, `relabel_convergence.py` | 시험 1 이름표 바꾸기 | 1D |
| `hidden_direction_test_1d.py`, `hidden_direction_reflection.py` | 시험 2 숨은 방향(임피던스) | 1D |
| `box_test_3a.py`, `box_test_3a_h.py` | 시험 3-a 상자 변환 | 3D 구대칭, 약 2분 |
| `moving_source_test.py` | 시험 4 움직이는 파속 | 1D |
| `membrane_load_tensor.py` | 텐서 1단계 막 하중 | 해석 계산 |
| `mode_count_test.py`, `uniqueness_test.py` | 텐서 2단계 모드 세기, 유일성 | 해석 계산 |
| `growth_rule_test.py`, `spacetime_uniqueness_test.py` | 텐서 3단계 자연 길이 규칙 | 해석 계산 |
| `deflection_dynamics.py` | 동역학 1 파속 휨 | 2D 768², 약 11분. 결과 `deflection_out.txt` |
| `gw_free_dynamics.py` | 동역학 2-a 자유 중력파 | 3D 96³, 약 6분. 결과 `gw_out.txt` |
| `conservation_check.py` | 격자 보존 오차 | 3D |
| `self_gravity_dynamics.py` | 동역학 2-c 실제 파동 시도 | 실패 기록용 (에너지 누수) |
| `self_gravity_slow.py` | 동역학 2-c 느린 극한 | `python3 self_gravity_slow.py single` / `binary` (binary 약 10분). 결과 `binary_out.txt` |
| `gw_emission.py` | 동역학 2-b-1 궤도 원천의 방출 | `python gw_emission.py kinetic\|bound [격자] [끝 시각]`. 160³ 약 17~20분, 224³ 약 41분(메모리 약 3.5 GB). 결과 `gw_emission_{kinetic,bound,bound_224}_out.txt` |
| `gw_emission_theory.py` | 동역학 2-b-1 분석 | 같은 규칙의 정확한 해(점 4중극, 푸리에 TT)와 반지름별 비교 |
| `gw_emission_web.py` | 동역학 2-b-1 웹 데이터 | 원본 결과에서 `viz_data/web_gw_emission.json`을 만듦 |

## 웹 시각화 데이터 (`viz_data/`)

| 파일 | 내용 |
| --- | --- |
| `gw_free_plus.json`, `gw_free_cross.json` | 동역학 2-a 프레임: xz 단면 TT 진폭(32×32), 고리 표지 16개 반지름 |
| `gw_ring_preview.png` | 고리 찌그러짐 미리보기 |
| `conservation.json` | 격자 보존 오차 |
| `slow_single_on.json`, `slow_single_off.json` | 동역학 2-c-1 덩어리 하나, 중력 켬/끔 |
| `slow_binary_mutual.json`, `slow_binary_nomutual.json` | 동역학 2-c-2 두 덩어리 궤도와 대조군. track(중심, 폭, 질량), frames(시계 지도, 에너지 지도 64×64) |
| `binary_preview.png` | 궤도 미리보기 |
| `self_gravity_*.json` | 동역학 2-c 실제 파동 시도(실패 기록). 여러 판에서 덮어씌워졌으므로 최종 판(원천 평균)의 결과임 |
| `web_fail_mass.json` | 동역학 2-c 실패 기록의 질량 곡선만 뽑은 웹 차트용 요약 |
| `web_gw_emission.json` | 동역학 2-b-1: xy·xz 단면 r·h+ 프레임(224³), 고리 표지, 반지름별 진폭과 정확한 해. 원본 `gw_emission_*.json`(각 10 MB)은 저장소에 올리지 않으며 `gw_emission.py`로 다시 만든다 |

## 문서와 저장소

- 실험 문서의 최신본은 이 폴더의 `doc/시간 그리드 사고 실험.md`다. 웹페이지(`index.html`)가 이 파일을 그대로 읽어 보여 준다. claude.ai 쪽 문서는 2026-10-22 판에서 멈췄다.
- 저장소: [AnChiUk/Homepage](https://github.com/AnChiUk/Homepage)의 `time-grid` 폴더.
- 웹페이지를 로컬에서 보려면 저장소 폴더에서 `python -m http.server`로 연다(데이터를 fetch로 읽음).
