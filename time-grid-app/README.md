# 시간 그리드 앱 (Flutter)

[시간 그리드 사고 실험](../time-grid/)을 앱으로 옮겨, 그리드 규칙이 실제로 동작하는 모습을 보여 주는 포트폴리오 프로젝트. 계획은 [Flutter 앱 계획.md](Flutter%20앱%20계획.md), 실험 내용의 기준은 [실험 문서](../time-grid/doc/시간%20그리드%20사고%20실험.md)다.

웹에서 열기: https://anchiuk.github.io/Homepage/time-grid-app/app/

## 화면

| 화면 | 상태 | 계산 | 원본 실험 |
| --- | --- | --- | --- |
| 막의 떨림 (이름표 바꾸기) | 완료 | 앱 안에서 실시간 1D 격자 | `time-grid/relabel_test_1d.py` (시험 1) |
| 빛의 휘어짐 | 완료 | 앱 안에서 실시간 2D 격자 (256², 원본 768²와 같은 영역) | `deflection_dynamics.py` (동역학 1) |
| 두 덩어리 궤도 | 준비 중 | 실시간 2D | `self_gravity_slow.py` |
| 중력파 | 준비 중 | 저장 데이터 재생 + 실시간 행렬 | `gw_free_dynamics.py`, `mode_count_test.py` |

## 구조

```
lib/
  physics/   순수 Dart 계산 (Flutter를 쓰지 않음). 화면은 이것을 불러 쓴다
  screens/   화면
  widgets/   그리기 (CustomPainter)
test/
  reference/ Python 원본이 낸 기준값 (JSON)
tool/
  make_reference.py   기준값 만들기: time-grid/ 의 원본 코드를 그대로 불러 실행
app/         GitHub Pages 에 올리는 웹 빌드 결과
```

## 정확성 확인

Python 실험 코드를 Dart로 옮길 때 부호, 정규화, 격자 미분이 조용히 틀어지기 쉽다. 그래서 화면마다 원본 Python이 낸 값을 기준으로 단위 테스트를 둔다.

- 막의 떨림: 이름표 6가지(균일 두 시간 간격, 거친 격자, 사인, sinh, 변환 안 한 대조)에서 노드 수, 홉 수, 시간 간격, 시계 진동수, 시계비 O1, 신호 시간 O2가 Python과 상대 10⁻⁹ 안에서 같다. 화면이 실제로 돌리는 진행(`LiveExperiment`)을 끝까지 돌린 값도 테스트 측정값과 정확히 같다.

- 빛의 휘어짐: 원본 크기(768², 8경우)와 화면 크기(256², 6경우) 모두에서 휨각 θ가 Python과 상대 10⁻⁸ 안에서 같다. 화면 크기는 같은 속도에서 원본 크기와 1.5% 안이다(그래서 화면의 속도는 격자가 감당하는 q ≤ 6, v ≤ 0.77까지).

## 실행

```
flutter test                      # 기준값 테스트 (원본 크기 2D 는 경우마다 1분 안팎)
flutter run -d chrome             # 개발 실행
python tool/make_reference.py     # 기준값 다시 만들기 (Python, numpy, scipy)
flutter build web --release --base-href /Homepage/time-grid-app/app/ -o <이 폴더의 절대 경로>/app
```

## AI 사용

물리 모형과 실험 설계는 직접 했다. Python→Dart 변환과 일부 구현(화면, 그리기)은 AI(Claude) 도움을 받았고, 정확성은 위의 기준값 테스트로 확인한다.
