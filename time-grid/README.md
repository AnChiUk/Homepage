# 시간 그리드 사고 실험 — 시뮬레이션 코드와 데이터

2026-10-22 기준. 실험 전체 내용과 결과는 `doc/시간 그리드 사고 실험.md`에 있다.

## 실행 환경

- Python 3.10 이상
- `pip install numpy scipy matplotlib`
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

## 다른 PC에서

- 압축을 풀고 이 폴더에서 바로 실행하면 된다.
- 프로젝트 문서의 최신본은 claude.ai 프로젝트 "Time grid 사고 실험"에도 있다.
- GitHub 저장소(chiuki010.github.io의 time-grid 폴더)에 올릴 계획이면 이 폴더를 그대로 올리면 된다.
