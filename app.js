// 다국어 딕셔너리
const i18n = {
  ko: {
    title: "나는 금을 만들고 싶었다",
    subtitle: "파동 공명과 공간 압축을 통한 원자 재배열 시뮬레이터",
    m1_title: "[모듈 1] 망치 vs 열쇠",
    m1_desc: "무작정 출력과 정밀한 위상/주파수 공명의 차이",
    m1_info: "에너지만 높이면 쿨롱 장벽에 막혀 열이 발생하지만, 위상을 일치시키면 양자 터널링 현상이 일어납니다.",
    m1_pwr: "출력 에너지",
    m1_res: "위상 공명도",
    m2_title: "[모듈 2] 공간 압축 도파관",
    m2_desc: "채널 간격 수축에 따른 고조파(HHG) 주파수 변환",
    m2_info: "입구보다 출구가 좁아지는 테이퍼드 관 내부에서 파동의 파장이 압축되어 고에너지 감마선(HHG)으로 변환됩니다.",
    m2_gap: "도파관 간격",
    m3_title: "[모듈 3] 미시 우주 컴파일러",
    m3_desc: "수소 이온화 및 파동 촉매를 이용한 중원소 합성",
    m3_info: "파동 촉매 축소에 따라 79개의 수소 이온(Proton)이 나선형으로 집속·융합되어 금(Au) 원자핵이 합성되는 3D 과정을 관찰하세요.",
    m4_title: "[모듈 4] 미시-거시 우주 스케일 줌",
    m4_desc: "펨토미터 양자 파동부터 거시 우주 결정화까지의 대칭성",
    m4_info: "미시 양자 파동의 간섭 패턴과 거시 우주 거시 구조(Cosmic Web)의 결정화망은 동일한 대칭성을 가집니다.",
    m4_scale: "시공간 스케일"
  },
  en: {
    title: "I Wanted to Make Gold",
    subtitle: "Atomic Transmutation Simulator via Wave Resonance & Space Compression",
    m1_title: "[Module 1] Hammer vs Key",
    m1_desc: "Brute Force Power vs Precise Phase/Frequency Resonance",
    m1_info: "High energy without resonance causes thermal decay, whereas phase-locking enables quantum tunneling through the Coulomb barrier.",
    m1_pwr: "Output Power",
    m1_res: "Phase Resonance",
    m2_title: "[Module 2] Space Compression Waveguide",
    m2_desc: "Harmonic (HHG) Frequency Shift via Channel Gap Contraction",
    m2_info: "Wavelengths compress inside the tapered waveguide as the exit gap narrows, triggering High-Order Harmonic Generation (HHG).",
    m2_gap: "Channel Gap",
    m3_title: "[Module 3] Micro-Cosmos Compiler",
    m3_desc: "Heavy Element Synthesis via Hydrogen Ionization & Wave Catalysts",
    m3_info: "Observe the 3D process of 79 protons spiraling and fusing into a Gold (Au) nucleus under wave catalysis.",
    m4_title: "[Module 4] Micro-Macro Cosmic Zoom",
    m4_desc: "Symmetry from Femtometer Quantum Waves to Cosmic Crystallization",
    m4_info: "Quantum wave interference patterns mirror the macro-scale structure of the Cosmic Web.",
    m4_scale: "Spacetime Scale"
  },
  ja: {
    title: "金を作りたかった",
    subtitle: "波動共鳴と空間圧縮による原子再配列シミュレーター",
    m1_title: "[モジュール 1] ハンマー vs 鍵",
    m1_desc: "無闇な出力と精密な位相・周波数共鳴の違い",
    m1_info: "出力を上げるだけではクーロン障壁に阻まれ発熱しますが、位相を合わせることで量子トンネル効果が起こります。",
    m1_pwr: "出力エネルギー",
    m1_res: "位相共鳴度",
    m2_title: "[モジュール 2] 空間圧縮導波管",
    m2_desc: "チャネル間隔収縮に伴う高調波(HHG)周波数変換",
    m2_info: "出口が狭まるテーパー管内部で波長が強固に圧縮され、高エネルギーガンマ線領域(HHG)へと周波数変換されます。",
    m2_gap: "導波管間隔",
    m3_title: "[モジュール 3] ミクロ宇宙コンパイラ",
    m3_desc: "水素イオン化と波動触媒を用いた重元素合成",
    m3_info: "波動触媒の収縮に伴い79個の水素イオンが螺旋状に集束・融合し、金(Au)原子核が合成される3D過程を観察できます。",
    m4_title: "[モジュール 4] ミクロ・マクロ宇宙スケールズーム",
    m4_desc: "フェムトメートル量子波動からマクロ宇宙結晶化までの対称性",
    m4_info: "ミクロな量子波動の干渉パターンとマクロな宇宙大規模構造(Cosmic Web)は同じ対称性を持ちます。",
    m4_scale: "時空スケール"
  }
};

let currentLang = 'ko';
let time = 0;

// 모듈 3 플레이어 상태
let isPlaying3 = false;
let progress3 = 0; // 0.0 ~ 1.0

function updateLanguage(lang) {
  currentLang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (i18n[lang][key]) el.textContent = i18n[lang][key];
  });
}

function setupCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  return canvas;
}

function renderAll() {
  time += 0.08;

  // 모듈 3 자동 재생 연산
  if (isPlaying3) {
    progress3 += 0.003;
    if (progress3 > 1.0) progress3 = 0.0; // 반복 재생

    const timeline = document.getElementById('timeline3');
    const timeVal = document.getElementById('timeVal3');
    if (timeline) timeline.value = progress3 * 100;
    if (timeVal) timeVal.innerText = `${(progress3 * 100).toFixed(1)}%`;
  }

  // [모듈 1] 3D
  const c1 = document.getElementById('canvas1');
  if (c1) {
    const pwr = parseFloat(document.getElementById('slider1-1').value);
    const res = parseFloat(document.getElementById('slider1-2').value);
    Module1.draw(null, c1.width, c1.height, time, pwr, res);
  }

  // [모듈 2] 3D
  const c2 = document.getElementById('canvas2');
  if (c2) {
    const gap = parseFloat(document.getElementById('slider2').value);
    Module2.draw(null, c2.width, c2.height, time, gap);
  }

  // [모듈 3] 3D 플레이어
  const c3 = document.getElementById('canvas3');
  if (c3) {
    Module3.draw(null, c3.width, c3.height, time, progress3);
  }

  // [모듈 4] 2D
  const c4 = document.getElementById('canvas4');
  if (c4) {
    const exp = parseInt(document.getElementById('slider4').value);
    Module4.draw(c4.getContext('2d'), c4.width, c4.height, time, exp);
  }

  requestAnimationFrame(renderAll);
}

window.addEventListener('load', () => {
  ['canvas4'].forEach(id => setupCanvas(id));

  // 3D 모듈 초기화 (1, 2, 3)
  Module1.init('canvas1');
  Module2.init('canvas2');
  Module3.init('canvas3');

  // 모듈 3 플레이어 버튼/슬라이더 이벤트
  const btnPlay3 = document.getElementById('btnPlay3');
  const timeline3 = document.getElementById('timeline3');
  const timeVal3 = document.getElementById('timeVal3');

  if (btnPlay3) {
    btnPlay3.addEventListener('click', () => {
      isPlaying3 = !isPlaying3;
      btnPlay3.innerText = isPlaying3 ? '❚❚' : '▶';
    });
  }

  if (timeline3) {
    timeline3.addEventListener('input', (e) => {
      progress3 = parseFloat(e.target.value) / 100;
      if (timeVal3) timeVal3.innerText = `${e.target.value}%`;
    });
  }

  // 기본 슬라이더 이벤트
  document.getElementById('langSelect').addEventListener('change', (e) => updateLanguage(e.target.value));
  document.getElementById('slider1-1').addEventListener('input', (e) => document.getElementById('val1-1').innerText = e.target.value);
  document.getElementById('slider1-2').addEventListener('input', (e) => document.getElementById('val1-2').innerText = e.target.value);
  document.getElementById('slider2').addEventListener('input', (e) => document.getElementById('val2').innerText = e.target.value);
  document.getElementById('slider4').addEventListener('input', (e) => document.getElementById('val4').innerText = `10^${e.target.value} m`);

  window.addEventListener('resize', () => {
    Module1.resize('canvas1');
    Module2.resize('canvas2');
    Module3.resize('canvas3');
    setupCanvas('canvas4');
  });

  updateLanguage('ko');
  renderAll();
});