# 저가 IR 페이스·바디 트래커 기획 정리

2026-10-28 기준

## 목표와 문제 정의

목표는 페이스·바디 트래커를 **소비자가 50만 원 이하**로 판매해 VR·VTuber 사용자에게 대중화하는 것이에요. 방향은 저가 적외선 카메라 모듈 2대와 몸에 두르는 패턴 밴드로, 드리프트 없는 광학 추적을 이 가격에 넣는 거예요.

지금 트래커가 비싼 이유는 세 가지로 정리했어요.

- **외부 장비**: 라이트하우스 방식은 베이스스테이션(1대 약 33만 원)이 2대 이상 필요해요.
- **정밀 부품과 소량 생산**: 수요층이 좁아 대량생산 효과가 약해요.
- **처리 성능 부담**: 카메라 영상을 PC에서 AI로 처리하면 "카메라는 싸도 GPU가 비싼" 문제가 생겨요.

저가 대안 중 IMU 센서 방식은 싸지만 시간이 지나면 위치가 틀어지는 드리프트가 있고, 카메라 한 대 방식은 깊이와 가림에 약해요.

## 시장 가격 조사

소비자 시장은 IMU(45만~51만 원)와 라이트하우스(116만 원 이상)가 차지하고, 광학 마커 방식은 수백만 원대 전문가용에만 있어요. 그래서 40만~50만 원대 광학 추적 제품은 비어 있는 자리예요. 가격은 1달러 ≈ 1,450원, 100엔 ≈ 900원으로 환산했고 일부는 출시가예요.

| 제품 | 방식 | 구성 | 가격(원화) |
| --- | --- | --- | --- |
| [SlimeVR](https://slimevr.dev/buy) | IMU | 풀바디 세트 | 약 51만 원 |
| SlimeVR 호환 수제 | IMU | 트래커 5~7개 | 약 24만~33만 원 |
| [HaritoraX 2](https://shop.shiftall.net/en-us/collections/all?page=2) | IMU | 본체 | 약 43만 원 |
| [Sony mocopi](https://www.gdm.or.jp/pressrelease/2022/1129/466481) | IMU | 6개 센서 | 약 45만 원 |
| [Vive Ultimate Tracker](https://shop-us.vive.com/products/21048355) | 카메라 내장 | 3개 + 동글 | 약 100만 원 |
| [Vive Tracker 3.0](https://roadtovr.com/htc-vive-facial-tracker-3-0-announcement-release-date-price/) + [베이스스테이션 2.0](https://shop-us.vive.com/products/2104005) | 라이트하우스 | 트래커 3개 + 베이스 2대 | 약 116만 원 이상 |
| [Rokoko Smartsuit Pro II](https://mocaponline.com/blogs/mocap-news/mocap-suit-price-guide) | IMU 수트 | 수트만 | 약 362만 원 |
| [OptiTrack](https://mocaponline.com/blogs/mocap-news/mocap-suit-price-guide) | 광학 마커 | 카메라 4대 최소 | 약 725만 원부터 |
| [Vive Focus 페이셜 트래커](https://knoxlabs.com/products/vive-facial-tracker) | 입 카메라 | 단품 | 약 14만 원 |
| [NARE FACIAL TRACKER](https://www.moguravr.com/?p=317592) | 눈·입 카메라 | 단품 | 약 29만 원 |

NARE는 한국 Nare Motion사가 설계한 제품이라, 국내에 비슷한 방향의 경쟁자가 있다는 뜻이에요.

## 기술 방향

핵심은 저가 적외선 센서 3개를 한 모듈에 넣고, 모듈 안에서 점 좌표까지 처리해 PC에는 좌표만 보내는 구조예요. OptiTrack 같은 전문 장비와 같은 원리를 저가 부품으로 구현하는 거예요.

<figure class="diagram">
<svg viewBox="0 0 760 236" role="img" aria-label="모듈 안에서 점 좌표만 뽑아 PC로 보낸다" font-size="13">
<defs><marker id="pipe-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="d-edge-fill"/></marker></defs>
<text x="24" y="34" font-size="15" font-weight="600" class="d-ink">모듈 안에서 점 좌표만 뽑아 PC로 보낸다</text>
<text x="24" y="56" font-size="11.5" class="d-quiet">카메라 모듈 1개의 내부 구조</text>
<g fill="none" class="d-edge" stroke-width="1.25"><path d="M174 122H214" marker-end="url(#pipe-arrow)"/><path d="M364 122H404" marker-end="url(#pipe-arrow)"/><path d="M554 122H594" marker-end="url(#pipe-arrow)"/></g>
<rect x="24" y="84" width="150" height="76" rx="8" fill="none" class="d-edge" stroke-width="1.25"/>
<text x="99" y="114" text-anchor="middle" font-weight="600" class="d-ink">트리거 회로</text>
<text x="99" y="134" text-anchor="middle" font-size="11.5" class="d-quiet">셔터를 1/180초씩</text>
<text x="99" y="150" text-anchor="middle" font-size="11.5" class="d-quiet">엇갈려 열기</text>
<rect x="214" y="84" width="150" height="76" rx="8" fill="none" class="d-edge" stroke-width="1.25"/>
<text x="289" y="114" text-anchor="middle" font-weight="600" class="d-ink">IR 센서 3개</text>
<text x="289" y="134" text-anchor="middle" font-size="11.5" class="d-quiet">글로벌 셔터 60fps</text>
<text x="289" y="150" text-anchor="middle" font-size="11.5" class="d-quiet">간격 6cm, 850nm 필터</text>
<rect x="404" y="84" width="150" height="76" rx="8" class="d-main" stroke-width="2"/>
<text x="479" y="114" text-anchor="middle" font-weight="600" class="d-ink">처리 칩(FPGA)</text>
<text x="479" y="134" text-anchor="middle" font-size="11.5" class="d-quiet">밝은 점 찾기</text>
<text x="479" y="150" text-anchor="middle" font-size="11.5" class="d-quiet">→ 중심 좌표 계산</text>
<rect x="594" y="84" width="150" height="76" rx="8" fill="none" class="d-edge" stroke-width="1.25"/>
<text x="669" y="114" text-anchor="middle" font-weight="600" class="d-ink">PC·VR 기기</text>
<text x="669" y="134" text-anchor="middle" font-size="11.5" class="d-quiet">삼각측량·밴드 판별</text>
<text x="669" y="150" text-anchor="middle" font-size="11.5" class="d-quiet">→ 아바타 동작</text>
<text x="384" y="188" text-anchor="middle" font-size="11.5" class="d-quiet">영상 180프레임/초</text>
<text x="574" y="188" text-anchor="middle" font-size="11.5" class="d-quiet">점 좌표만 (USB)</text>
<text x="24" y="212" font-size="11.5" class="d-quiet">전송 데이터가 수천 분의 1로 줄어 고성능 GPU가 필요 없다</text>
</svg>
<figcaption>카메라 모듈 처리 흐름 · 4단계</figcaption>
</figure>

- **다중 카메라**: 여러 각도에서 보면 삼각측량으로 3D 위치를 구하고, 한 카메라가 가려져도 다른 카메라가 보완해요. IMU와 달리 드리프트가 없어요.
- **엇갈림 촬영**: 60fps 센서 3개의 셔터를 1/180초씩 엇갈리면 모듈 하나가 초당 180번 관측해요. 단, 모션 블러는 줄지 않아 짧은 노출과 강한 IR LED가 따로 필요해요.
- **모듈 단독 스테레오**: 센서 사이 간격을 이용하면 모듈 하나로도 깊이를 구할 수 있어요. 오차는 2대 교차보다 크다는 점이 한계예요.
- **부품 조건**: 하드웨어 트리거를 지원하는 **글로벌 셔터** 센서(예: OV9281 계열)가 필요해요. OV2640 같은 초저가 모듈은 동기화가 어렵고, 롤링 셔터는 빠른 동작에서 마커가 늘어져 보여요.
- **저가 IR 카메라 시세**: 라즈베리파이 NoIR V2가 [약 2.6만 원](https://www.devicemart.co.kr/goods/view?no=1289483), OV2640 모듈은 약 8달러예요. 시제품은 카메라 1대당 1만~3만 원으로 가능해요.

개발은 세 단계로 나눠요. 먼저 트리거만 마이크로컨트롤러로 만들고 처리는 PC에서 검증해요. 다음에 점 찾기를 FPGA 개발보드로 옮기고, 마지막에 전용 기판으로 통합해 원가를 낮춰요.

## 마커 방식

첫 제품은 **패턴 밴드**로 가고, 패턴 옷은 나중에 고급 옵션으로 두는 것이 낫다고 봤어요. 밴드는 둘레 어디서든 점이 보여 가림에 강하고, 모양을 아는 점 3개만 보여도 한 모듈로 위치와 방향을 계산(PnP)할 수 있어요.

| 방식 | 가림 | 정확도 | 원가 | 착용·내구성 | 판단 |
| --- | --- | --- | --- | --- | --- |
| 반사 구슬 (부위당 1개) | 약함 | 좋음, 사방에서 같은 원 | 낮음 | 붙이기 번거로움 | 비교 기준 |
| 피부에 칠하기 | 점이 많으면 강함 | 낮음, 비스듬하면 사라짐 | 거의 0 | 매번 칠하고 지워야 함 | 비현실적 |
| 패턴 밴드 | 강함 | 좋음, 잘 안 밀림 | 밴드당 수백~수천 원(추정) | 벨크로, 사이즈 하나 | **1단계 제품** |
| 패턴 옷(수트) | 가장 강함 | 보통, 옷이 밀림 | 높음, 체형별 사이즈 | 세탁에 약함 | 고급 옵션 |

밴드는 가슴·허리·양팔·양허벅지·양발목 8곳에 감아요.

**밴드 구분 원리**

- 점을 위·아래 두 줄로 찍고, 칸마다 "위 / 아래 / 둘 다" 중 하나로 코드를 만들어요.
- 어느 방향에서 보든 **이웃한 3칸**의 조합이 다른 밴드와 겹치지 않게 설계해요. 밴드를 거꾸로 봐도 헷갈리지 않아요.
- 좌우 밴드는 같은 패턴을 쓰고 몸 구조(발목은 무릎 아래)로 구분하면 필요한 패턴이 5종으로 줄어요. 8종 모두 다르게 해도 3칸으로 구분돼요.
- 한 번 판별한 뒤에는 직전 위치로 따라가므로, 판별은 가려졌다 다시 나타날 때만 필요해요.

## 시뮬레이터 결과

**패턴 밴드를 쓰면 카메라 모듈 2대를 몸 앞쪽에만 두어도 추적 커버리지가 99~100%예요.** 반사 구슬은 같은 배치에서 79~85%에 그쳤어요. 사용자가 방 앞뒤에 카메라를 따로 설치하지 않아도 돼서 설치 난이도가 크게 낮아져요.

[IR 트래커 설계 시뮬레이터](simulator.html)는 캡슐 13개로 만든 3D 몸에 서 있기·걷기·팔 휘두르기·쪼그려 앉기·춤 동작을 넣고, 몸을 10°씩 360° 돌리며 각 부위가 추적되는지 계산해요. 기준 설정은 모듈 높이 2m, 거리 2.2m, 화각 90°, 가로 1,280px예요.

| 배치 | 반사 구슬 추적 | 패턴 밴드 추적 | 밴드 판별 |
| --- | --- | --- | --- |
| 정면 1대 | 59~65% | 90~95% | 74~77% |
| 정면 2대 | 79~85% | 99~100% | 88~89% |
| 앞뒤·대각 2대 | 97~100% | 99~100% | 93~99% |
| 사방 4대 | 100% | — | — |

판별률은 추적된 순간 중 이웃한 3칸을 읽어 어느 밴드인지 맞힌 비율이에요. 직전 프레임 정보를 쓰지 않은 최악 조건이라 실사용은 이보다 좋을 거예요. 가장 약한 부위는 둘레가 작은 발목 밴드(약 72%)예요.

**판별률을 좌우하는 것 (정면 2대, 걷기)**

- **해상도가 결정적**: 640px이면 29%, 1,280px이면 89%, 1,920px이면 95%.
- **점이 크면 오히려 나빠요**: 점 지름 2.5cm에 줄 간격 3cm면 위아래 점이 붙어 보여 0%, 1cm면 95%.
- 칸 간격은 3.5cm 근처가 가장 좋았어요.

**첫 시제품 밴드 규격 제안 (1,280px 기준)**: 점 지름 1cm, 줄 간격 3cm, 칸 간격 3.5cm.

한계도 있어요. 몸과 동작은 손으로 만든 근사이고, 한 모듈 단독 추적의 깊이 오차는 약 1~2cm로 2대 교차(약 1mm)보다 훨씬 커요.

## 원가·사업성

직판으로 팔고, 부품 원가를 20만 원 이하로 맞추고, 인건비까지 회수하려면 약 2,000~8,000대를 팔아야 50만 원 이하가 현실적이에요. 아래 부품 단가는 모두 추정이고, 실제 견적으로 확인해야 해요.

**소비자가 50만 원의 분해 (온라인 직판)**

| 항목 | 금액 |
| --- | --- |
| 부가세 10% | 약 4.5만 원 |
| 결제·플랫폼 수수료 | 약 4만~5만 원 |
| 배송·고객지원·불량 대응 | 약 3만 원 |
| 마케팅 | 약 3만~5만 원 |
| **남는 금액 (원가 + 개발비 회수 + 이익)** | **약 33만~35만 원** |

유통사를 거치면 마진으로 30% 안팎이 더 빠져 50만 원은 거의 불가능해요. 자사몰·크라우드펀딩 직판이 전제예요.

**부품 원가 추정 (모듈 1개)**

| 부품 | 추정 단가 |
| --- | --- |
| 센서 3개 + 렌즈 + IR 필터 | 1.5만~4.5만 원 |
| 처리 칩(저가 FPGA) | 1만~3만 원 |
| USB·제어 칩, IR LED | 0.6만~2만 원 |
| 기판 제작·조립 | 0.5만~1.5만 원 |
| 케이스·거치대·케이블 | 0.5만~1.5만 원 |
| **모듈 1개 합계** | **4만~12만 원** |

모듈 2개에 밴드·포장까지 더하면 총 약 10만~28만 원이에요. 목표는 15만~20만 원 이하로, 이때 대당 13만~20만 원이 개발비 회수와 이익으로 남아요. 지름 1cm 점 밴드는 구슬 마커보다 싸서 원가에도 유리해요.

**개발비와 손익분기**: 기판 시제품 반복, 전파 인증(KC, 해외는 FCC·CE), 케이스 금형, 소프트웨어를 합치면 인건비 제외 약 1억~3억 원이고, 인건비까지 넣으면 약 3억~8억 원으로 봐요(아래 표). 대당 10만~15만 원씩 회수하면 2,000~8,000대가 손익분기예요. Tundra Tracker는 크라우드펀딩 후원자에게만 11,000대를 출하했고 SlimeVR은 한 번 배송에 3,400세트 넘게 보냈어요. 크라우드펀딩으로 개발비를 먼저 모으는 것이 이 시장의 검증된 방식이에요.

| 개발비 항목 | 가정 | 추정 금액 |
| --- | --- | --- |
| 인건비 | 3~4명(하드웨어, FPGA·펌웨어, 추적 소프트웨어, 기구·제품) × 12~18개월, 1인 연 6,000만~8,000만 원 | 약 2억~5억 원 |
| 기판 시제품 반복 | 3~5회 제작·조립 | 약 0.3억~1억 원 |
| 전파 인증 | KC, 해외 판매 시 FCC·CE | 약 0.3억~1억 원 |
| 케이스 금형 | 모듈 케이스·거치대 | 약 0.3억~0.8억 원 |
| 장비·기타 | 개발보드, 계측 장비, 테스트 밴드 | 약 0.1억~0.2억 원 |
| **합계** | | **약 3억~8억 원** |

인건비가 전체의 3분의 2쯤 돼요. 인원과 기간은 가정이라 실제 팀 구성이 정해지면 바꿔 넣어야 해요. 인건비를 줄이는 방법으로는 창업자가 설계·코딩을 직접 맡고 기판 배선과 금형만 외주를 주는 구성이 있어요.

시뮬레이터 아래쪽 원가 계산기에 실제 견적을 넣으면 모듈 수에 따른 손익분기 판매량을 바로 볼 수 있어요.

## 페이스 트래커 방향

**첫 제품은 바디 트래커만 내고, 페이스 트래커는 그다음 단계 제품으로 개발해요.** 아래는 그때를 위한 방향이에요.

얼굴은 몸과 따로, 헤드셋에 다는 가까운 카메라와 점 없는 AI 추적으로 가는 것이 맞아 보여요. 멀리 둔 저가 카메라로는 미세한 표정을 잡기 어렵고, VR 헤드셋을 쓰면 윗얼굴은 가려져요.

- 입 주변은 가까운 IR 카메라 1대로 충분하고, 오픈소스 Project Babble 같은 마커리스 추적이 이미 쓰이고 있어요.
- 기존 제품 가격은 Vive Focus 페이셜 트래커 약 14만 원, NARE FACIAL TRACKER 약 29만 원이에요.
- 바디 모듈과 같은 저가 IR 센서·처리 칩을 공유하면 부품 구매 단가를 함께 낮출 수 있어요.

얼굴 쪽은 아직 시뮬레이터로 검증하지 않았고, 바디 제품 출시 뒤에 검토해요.

## 다음 단계와 남은 위험

다음은 실제 움직임 데이터로 시뮬레이터를 검증하고, 핵심 부품 견적을 받아 원가표를 확정하는 거예요.

- [ ] 실제 모션캡처 데이터를 시뮬레이터에 넣어 커버리지·판별률 재확인
- [ ] 글로벌 셔터 IR 센서와 저가 FPGA 실제 견적 받기
- [ ] 점 지름 1cm·줄 간격 3cm·칸 간격 3.5cm 밴드 시편 제작
- [ ] 웹캠 2~3대 + PC 처리로 밴드 판별 실측 (개발 1단계)
- [ ] 견적 기준으로 원가표 확정 후 크라우드펀딩 가격 결정

**남은 위험**

- 한 모듈 단독 추적의 깊이 오차(1~2cm)가 VR에서 눈에 띄는 수준일 수 있어요.
- 발목 밴드 판별률(약 72%)이 가장 낮아요.
- 한국 발 경쟁자(Nare Motion)가 이미 있어요.
- 글로벌 셔터 센서와 FPGA 단가가 추정보다 높으면 모듈당 원가가 12만 원을 넘어요.

## 출처

- [SlimeVR 구매 페이지](https://slimevr.dev/buy)
- [Shiftall 스토어 – HaritoraX 2](https://shop.shiftall.net/en-us/collections/all?page=2)
- [GDM – Sony mocopi 발표](https://www.gdm.or.jp/pressrelease/2022/1129/466481)
- [VIVE 공식몰 – Ultimate Tracker 3+1 키트](https://shop-us.vive.com/products/21048355)
- [VIVE 공식몰 – Base Station 2.0](https://shop-us.vive.com/products/2104005)
- [Road to VR – Vive Tracker 3.0·Facial Tracker](https://roadtovr.com/htc-vive-facial-tracker-3-0-announcement-release-date-price/)
- [Road to VR – Tundra Tracker 가격](https://roadtovr.com/?p=101057)
- [Mixed News – Tundra 가격 인상과 출하량](https://mixed-news.com/en/tundra-tracker-vr-trackers-launch-with-higher-price/)
- [Crowd Supply – SlimeVR 출하 소식](https://www.crowdsupply.com/slimevr/slimevr-full-body-tracker/updates/in-stock-at-crowd-supply)
- [MoCap Online – 모션캡처 가격 가이드](https://mocaponline.com/blogs/mocap-news/mocap-suit-price-guide)
- [Knox Labs – Vive Focus Facial Tracker](https://knoxlabs.com/products/vive-facial-tracker)
- [Mogura VR – NARE FACIAL TRACKER](https://www.moguravr.com/?p=317592)
- [디바이스마트 – 라즈베리파이 NoIR V2](https://www.devicemart.co.kr/goods/view?no=1289483)
