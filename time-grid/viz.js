// 시간 그리드 사고 실험: viz_data/의 저장된 프레임을 재생하고 실험 문서를 렌더링한다.
(function () {
  'use strict';

  const DATA = 'viz_data/';
  const DOC = 'doc/' + encodeURIComponent('시간 그리드 사고 실험.md');
  const COL = { accent: '#7dd3fc', warm: '#fbbf24', muted: '#a0a0a0', grid: '#2a2a2a', text: '#e0e0e0' };

  // 파이썬 json은 NaN을 그대로 쓰므로 null로 바꿔서 읽는다.
  async function loadJSON(name) {
    const res = await fetch(DATA + name);
    if (!res.ok) throw new Error(name + ' (' + res.status + ')');
    return JSON.parse((await res.text()).replace(/\bNaN\b/g, 'null'));
  }

  function fail(panel, err) {
    const s = panel.querySelector('.status');
    s.classList.add('err');
    s.textContent = location.protocol === 'file:'
      ? '데이터를 읽으려면 웹 서버로 열어야 합니다 (예: 저장소 폴더에서 python -m http.server).'
      : '데이터를 불러오지 못했습니다: ' + err.message;
  }

  // 캔버스를 화면 해상도에 맞추고, 논리 크기(w, h)로 그릴 수 있는 컨텍스트를 돌려준다.
  function hiDPI(canvas) {
    if (!canvas._w) {
      canvas._w = canvas.width; canvas._h = canvas.height;
      const r = window.devicePixelRatio || 1;
      canvas.width = canvas._w * r; canvas.height = canvas._h * r;
    }
    const ctx = canvas.getContext('2d');
    const r = canvas.width / canvas._w;
    ctx.setTransform(r, 0, 0, r, 0, 0);
    return { ctx, w: canvas._w, h: canvas._h };
  }

  // ── 색 ────────────────────────────────────────────
  function lerp(a, b, t) { return a + (b - a) * t; }
  function ramp(stops, t) {
    t = Math.max(0, Math.min(1, t));
    const n = stops.length - 1, i = Math.min(n - 1, Math.floor(t * n)), f = t * n - i;
    const a = stops[i], b = stops[i + 1];
    return [lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f)];
  }
  const DIVERGING = [[59, 130, 246], [30, 58, 110], [13, 13, 13], [120, 53, 15], [251, 146, 60]];
  const HEAT = [[13, 13, 13], [120, 53, 15], [251, 191, 36], [255, 247, 220]];

  // 2D 배열을 ImageData로 칠한 뒤 늘려 그린다. pick(r, c)는 [x픽셀, y픽셀]을 준다.
  function paintGrid(ctx, rows, cols, colorAt, pick, x, y, w, h) {
    const off = document.createElement('canvas');
    off.width = cols; off.height = rows;
    const oc = off.getContext('2d'), img = oc.createImageData(cols, rows);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const [px, py] = pick(r, c), k = (py * cols + px) * 4, rgb = colorAt(r, c);
        img.data[k] = rgb[0]; img.data[k + 1] = rgb[1]; img.data[k + 2] = rgb[2]; img.data[k + 3] = 255;
      }
    }
    oc.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, x, y, w, h);
  }

  // ── 재생기 ─────────────────────────────────────────
  function makePlayer(panel, render, fps) {
    const btn = panel.querySelector('.play'), scrub = panel.querySelector('.scrub');
    let n = 1, i = 0, playing = false, last = 0, acc = 0;
    function show(k) { i = k; scrub.value = k; render(k); }
    function tick(now) {
      if (!playing) return;
      acc += (now - last) / 1000; last = now;
      if (acc >= 1 / fps) { acc = 0; show((i + 1) % n); }
      requestAnimationFrame(tick);
    }
    btn.addEventListener('click', () => {
      playing = !playing; btn.textContent = playing ? '❚❚' : '▶';
      if (playing) { last = performance.now(); requestAnimationFrame(tick); }
    });
    scrub.addEventListener('input', () => show(+scrub.value));
    return {
      reset(count) { n = count; scrub.max = n - 1; show(Math.min(i, n - 1)); },
      redraw() { render(i); },
    };
  }

  // ── 선 그래프 ──────────────────────────────────────
  function niceTicks(lo, hi, count) {
    const span = hi - lo || 1, step0 = span / count, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => span / s <= count) || 10 * mag;
    const out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  // series: [{name, color, x[], y[], dots?}], opt: {xlab, ylab, ymin, ymax, xmin, xmax, cursor, fmtY}
  function lineChart(canvas, series, opt) {
    const { ctx, w, h } = hiDPI(canvas);
    const m = { l: 52, r: 14, t: 30, b: 40 };
    const pw = w - m.l - m.r, ph = h - m.t - m.b;
    const xs = series.flatMap(s => s.x), ys = series.flatMap(s => s.y).filter(v => v != null);
    const x0 = opt.xmin ?? Math.min(...xs), x1 = opt.xmax ?? Math.max(...xs);
    const y0 = opt.ymin ?? Math.min(...ys), y1 = opt.ymax ?? Math.max(...ys);
    const X = v => m.l + (v - x0) / (x1 - x0) * pw, Y = v => m.t + ph - (v - y0) / (y1 - y0) * ph;

    ctx.clearRect(0, 0, w, h);
    ctx.font = '11px system-ui, sans-serif';
    ctx.lineWidth = 1;
    ctx.fillStyle = COL.muted;
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    for (const v of niceTicks(y0, y1, 4)) {
      ctx.strokeStyle = COL.grid; ctx.beginPath(); ctx.moveTo(m.l, Y(v)); ctx.lineTo(w - m.r, Y(v)); ctx.stroke();
      ctx.fillText(opt.fmtY ? opt.fmtY(v) : String(v), m.l - 6, Y(v));
    }
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    for (const v of niceTicks(x0, x1, 5)) ctx.fillText(String(v), X(v), m.t + ph + 6);
    ctx.fillText(opt.xlab, m.l + pw / 2, h - 14);
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    ctx.fillText(opt.ylab, m.l, 16);

    if (opt.cursor != null) {
      ctx.strokeStyle = '#555'; ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(X(opt.cursor), m.t); ctx.lineTo(X(opt.cursor), m.t + ph); ctx.stroke();
      ctx.setLineDash([]);
    }

    for (const s of series) {
      ctx.strokeStyle = s.color; ctx.fillStyle = s.color; ctx.lineWidth = 2;
      ctx.beginPath();
      let pen = false;
      s.x.forEach((xv, k) => {
        const yv = s.y[k];
        if (yv == null) { pen = false; return; }
        pen ? ctx.lineTo(X(xv), Y(yv)) : ctx.moveTo(X(xv), Y(yv));
        pen = true;
      });
      ctx.stroke();
      if (s.dots) s.x.forEach((xv, k) => { ctx.beginPath(); ctx.arc(X(xv), Y(s.y[k]), 3.5, 0, 7); ctx.fill(); });
    }

    if (opt.legend === false) return;
    // 범례: 오른쪽 위에서 왼쪽으로
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    let lx = w - m.r;
    for (const s of series.slice().reverse()) {
      ctx.fillStyle = COL.text; ctx.fillText(s.name, lx, 16);
      lx -= ctx.measureText(s.name).width + 6;
      ctx.fillStyle = s.color; ctx.fillRect(lx - 12, 14, 12, 3);
      lx -= 26;
    }
  }

  // ── 동역학 2-a 중력파 ───────────────────────────────
  async function initGW(panel) {
    const [plus, cross] = await Promise.all([loadJSON('gw_free_plus.json'), loadJSON('gw_free_cross.json')]);
    const sets = { plus, cross };
    const slice = panel.querySelector('.cv-slice'), ring = panel.querySelector('.cv-ring');
    const baseBox = panel.querySelector('.baseline'), exagEl = panel.querySelector('.exag');
    let pol = 'plus', scale = {};

    // 편광과 기준 모드마다 색 범위와 과장 배율을 한 번 정해 모든 프레임에 같이 쓴다.
    function prepare() {
      const d = sets[pol], base = baseBox.checked ? d.frames[0].ring : null;
      let vmax = 0, dmax = 0;
      for (const f of d.frames) {
        for (const row of f.slice) for (const v of row) vmax = Math.max(vmax, Math.abs(v));
        f.ring.forEach((v, k) => { dmax = Math.max(dmax, Math.abs(v - (base ? base[k] : 0))); });
      }
      const raw = 0.3 * d.ring_radius / dmax, mag = Math.pow(10, Math.floor(Math.log10(raw)));
      scale = { vmax, base, exag: Math.floor(raw / mag) * mag };
      exagEl.textContent = scale.exag.toLocaleString('ko-KR');
    }

    function render(i) {
      const d = sets[pol], f = d.frames[i];
      // 단면: 행 = x, 열 = z(진행 방향) → z를 가로로 그린다
      let { ctx, w, h } = hiDPI(slice);
      const n = f.slice.length;
      paintGrid(ctx, n, n, (r, c) => ramp(DIVERGING, 0.5 + 0.5 * f.slice[r][c] / scale.vmax),
        (r, c) => [c, n - 1 - r], 0, 0, w, h);
      ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = COL.text; ctx.font = '12px system-ui, sans-serif';
      ctx.fillText('z →', w - 34, h - 10); ctx.fillText('x', 8, 16);

      // 고리 표지
      ({ ctx, w, h } = hiDPI(ring));
      ctx.clearRect(0, 0, w, h);
      const cx = w / 2, cy = h / 2, R = 0.32 * w, k = R / d.ring_radius;
      ctx.strokeStyle = '#555'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      const pts = d.ring_angles.map((a, j) => {
        const dl = f.ring[j] - (scale.base ? scale.base[j] : 0);
        const r = (d.ring_radius + dl * scale.exag) * k;
        return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
      });
      ctx.strokeStyle = COL.accent; ctx.lineWidth = 2;
      ctx.beginPath(); pts.forEach(([x, y], j) => j ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.stroke();
      ctx.fillStyle = COL.warm;
      for (const [x, y] of pts) { ctx.beginPath(); ctx.arc(x, y, 4, 0, 7); ctx.fill(); }
      ctx.lineWidth = 1;
      ctx.fillStyle = COL.muted; ctx.font = '12px system-ui, sans-serif';
      ctx.fillText('x →', w - 34, cy - 6); ctx.fillText('y ↑', cx + 6, 16);

      panel.querySelector('.time').textContent = 't = ' + f.t.toFixed(0) + ' / ' + d.frames.at(-1).t.toFixed(0);
    }

    const player = makePlayer(panel, render, 10);
    panel.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
      panel.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b));
      pol = b.dataset.pol; prepare(); player.reset(sets[pol].frames.length);
    }));
    baseBox.addEventListener('change', () => { prepare(); player.redraw(); });
    prepare(); player.reset(plus.frames.length);
  }

  // ── 동역학 2-c-1 자기 묶임 ─────────────────────────
  async function initSingle(panel) {
    const [on, off] = await Promise.all([loadJSON('slow_single_on.json'), loadJSON('slow_single_off.json')]);
    const emax = Math.max(...on.frames[0].energy.flat());
    const width = d => d.track.map(p => p.widths[0]);
    const times = on.track.map(p => p.t);

    function field(canvas, f) {
      const { ctx, w, h } = hiDPI(canvas), n = f.energy.length;
      paintGrid(ctx, n, n, (r, c) => ramp(HEAT, Math.sqrt(f.energy[r][c] / emax)),
        (r, c) => [r, n - 1 - c], 0, 0, w, h);
    }

    function render(i) {
      field(panel.querySelector('.cv-on'), on.frames[i]);
      field(panel.querySelector('.cv-off'), off.frames[i]);
      const t = on.frames[i].t;
      lineChart(panel.querySelector('.cv-chart'), [
        { name: '중력 켬', color: COL.accent, x: times, y: width(on) },
        { name: '중력 끔', color: COL.warm, x: off.track.map(p => p.t), y: width(off) },
      ], { xlab: '시간', ylab: '덩어리 폭', ymin: 0, cursor: t });
      panel.querySelector('.time').textContent = 't = ' + t.toFixed(0) + ' / ' + on.frames.at(-1).t.toFixed(0);
    }

    makePlayer(panel, render, 8).reset(on.frames.length);
  }

  // ── 동역학 2-c-2 두 덩어리 궤도 ────────────────────
  async function initBinary(panel) {
    const status = panel.querySelector('.status');
    const sets = {};
    const [mutual, nomutual] = await Promise.all([loadJSON('slow_binary_mutual.json'), loadJSON('slow_binary_nomutual.json')]);
    sets.mutual = mutual; sets.nomutual = nomutual;
    status.textContent = '';
    let key = 'mutual';
    const canvas = panel.querySelector('.cv-orbit');

    // 분리 벡터의 각도를 이어 붙여 누적 회전각을 구한다.
    for (const d of Object.values(sets)) {
      let prev = null, acc = 0;
      d.emax = Math.max(...d.frames[0].energy.flat());
      d.cmin = Math.min(...d.frames[0].clock.flat());
      for (const p of d.track) {
        const [a, b] = p.centers, ang = Math.atan2(a[1] - b[1], a[0] - b[0]);
        if (prev != null) { let da = ang - prev; da -= 2 * Math.PI * Math.round(da / (2 * Math.PI)); acc += da; }
        prev = ang; p.turn = acc * 180 / Math.PI; p.dist = Math.hypot(a[0] - b[0], a[1] - b[1]);
      }
    }

    function render(i) {
      const d = sets[key], f = d.frames[i], n = f.clock.length, half = n / 2;
      const { ctx, w, h } = hiDPI(canvas);
      const slow = 1 - d.cmin;
      // frame[r][c]는 x = r − 32, y = c − 32 위치의 값이다
      paintGrid(ctx, n, n, (r, c) => {
        const s = (1 - f.clock[r][c]) / slow, e = Math.sqrt(f.energy[r][c] / d.emax);
        const base = [13 + 20 * s, 13 + 60 * s, 13 + 150 * s];
        const hot = ramp(HEAT, e);
        return e > 0.02 ? [Math.max(base[0], hot[0]), Math.max(base[1], hot[1]), Math.max(base[2], hot[2])] : base;
      }, (r, c) => [r, n - 1 - c], 0, 0, w, h);

      const X = x => (x + half + 0.5) / n * w, Y = y => h - (y + half + 0.5) / n * h;
      const upto = d.track.filter(p => p.t <= f.t + 1e-6);
      [COL.accent, '#f472b6'].forEach((color, b) => {
        ctx.strokeStyle = color; ctx.lineWidth = 1.8;
        ctx.beginPath();
        upto.forEach((p, k) => { const [x, y] = p.centers[b]; k ? ctx.lineTo(X(x), Y(y)) : ctx.moveTo(X(x), Y(y)); });
        ctx.stroke();
      });

      const p = upto.at(-1);
      panel.querySelector('.readout').textContent =
        '거리 ' + p.dist.toFixed(2) + ' · 누적 회전 ' + Math.abs(p.turn).toFixed(0) + '° · 케플러 주기의 ' + (f.t / d.kepler_period).toFixed(2) + '배';
      panel.querySelector('.time').textContent = 't = ' + f.t.toFixed(0) + ' / ' + d.frames.at(-1).t.toFixed(0);
    }

    const player = makePlayer(panel, render, 10);
    panel.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
      panel.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b));
      key = b.dataset.case; player.reset(sets[key].frames.length);
    }));
    player.reset(mutual.frames.length);
  }

  // ── 동역학 2-b-1 중력파 방출 ────────────────────────
  async function initEmit(panel) {
    const d = await loadJSON('web_gw_emission.json');
    const half = d.view / 2;
    const ringCv = panel.querySelector('.cv-ring'), exagEl = panel.querySelector('.exag');
    let dmax = 0;
    for (const r of d.rings_bound) for (const v of r) dmax = Math.max(dmax, Math.abs(v));
    const raw = 0.3 * d.ring_radius / dmax, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const exag = Math.floor(raw / mag) * mag;
    exagEl.textContent = exag.toLocaleString('ko-KR');

    function slice(canvas, f, orbit) {
      const { ctx, w, h } = hiDPI(canvas), n = f.length, cell = d.view / n;
      // 진폭이 1/r 로 줄어드므로 중심에서의 거리 r 을 곱해(r·h+ ÷ 예측) 먼 곳 파동도 같은 밝기로 보이게 한다
      paintGrid(ctx, n, n, (r, c) => {
        const x = (r + 0.5) * cell - half, y = (c + 0.5) * cell - half;
        return ramp(DIVERGING, 0.5 + 0.5 * f[r][c] * Math.hypot(x, y));
      }, (r, c) => [r, n - 1 - c], 0, 0, w, h);
      const X = x => (x + half) / d.view * w, Y = y => h - (y + half) / d.view * h;
      if (orbit) {
        ctx.fillStyle = '#ffffff';
        for (const s of [1, -1]) {
          ctx.beginPath(); ctx.arc(X(s * d.r0 * Math.cos(orbit)), Y(s * d.r0 * Math.sin(orbit)), 3, 0, 7); ctx.fill();
        }
      }
      return { ctx, w, h };
    }

    function drawRing(i) {
      const { ctx, w, h } = hiDPI(ringCv);
      ctx.clearRect(0, 0, w, h);
      const cx = w / 2, cy = h / 2, R = 0.32 * w, k = R / d.ring_radius;
      ctx.strokeStyle = '#555'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      const pts = d.ring_angles.map((a, j) => {
        const r = (d.ring_radius + d.rings_bound[i][j] * exag) * k;
        return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
      });
      ctx.strokeStyle = COL.accent; ctx.lineWidth = 2;
      ctx.beginPath(); pts.forEach(([x, y], j) => j ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.stroke();
      ctx.fillStyle = COL.warm;
      for (const [x, y] of pts) { ctx.beginPath(); ctx.arc(x, y, 4, 0, 7); ctx.fill(); }
      ctx.lineWidth = 1;
      ctx.fillStyle = COL.muted; ctx.font = '12px system-ui, sans-serif';
      ctx.fillText('x →', w - 34, cy - 6); ctx.fillText('y ↑', cx + 6, 16);
    }

    const amp = d.amp;
    lineChart(panel.querySelector('.cv-chart'), [
      { name: '정확한 해', color: '#737373', x: amp.theory.r, y: amp.theory.face },
      { name: '보존 원천', color: COL.accent, x: amp.bound_224.r, y: amp.bound_224.face, dots: true },
      { name: '운동 응력만', color: COL.warm, x: amp.kinetic_160.r, y: amp.kinetic_160.face, dots: true },
    ], { xlab: '반지름 r', ylab: 'r·진폭 ÷ 예측', xmin: 10, xmax: 80, ymin: 0, ymax: 1.2, fmtY: v => v.toFixed(1) });

    function render(i) {
      const f = d.frames[i];
      slice(panel.querySelector('.cv-xy'), f.xy, d.omega * f.t);
      const { ctx, w, h } = slice(panel.querySelector('.cv-xz'), f.xz, null);
      ctx.fillStyle = COL.text; ctx.font = '12px system-ui, sans-serif';
      ctx.fillText('z ↑', w / 2 + 6, 16); ctx.fillText('x →', w - 34, h - 10);
      drawRing(i);
      const on = f.t < d.ramp ? ' · 원천 켜는 중' : '';
      panel.querySelector('.time').textContent = 't = ' + f.t.toFixed(0) + ' / ' + d.frames.at(-1).t.toFixed(0) + on;
    }

    makePlayer(panel, render, 8).reset(d.frames.length);
  }

  // ── 비선형 1 장 자신의 하중 ─────────────────────────
  async function initField(panel) {
    const [d, lat] = await Promise.all([loadJSON('field_stress_orbit.json'), loadJSON('field_stress_lattice.json')]);
    const x = d.t.map(t => t / d.period);
    const pick = (arr, k) => arr.map(v => v[k]);
    const series = [
      { name: '필요한 값 ½Ï', color: '#e0e0e0', x, y: pick(d.half_Idd, 0) },
      { name: '물질 응력만', color: COL.warm, x, y: pick(d.Pi, 0) },
      { name: '물질 + 장 자신의 하중', color: COL.accent, x, y: d.Pi.map((p, i) => p[0] + d.t_field[i][0]) },
    ];
    lineChart(panel.querySelector('.cv-chart'), series,
      { xlab: '케플러 주기', ylab: '원천의 회전 성분 (xx−yy)/2', fmtY: v => v.toFixed(2), legend: false });
    panel.querySelector('.legend').innerHTML = series.map(s => '<span style="color:' + s.color + '">━</span> ' + s.name).join('&nbsp;&nbsp; ')
      + '&nbsp;&nbsp; (적분 비: 물질만 ' + d.ratios.matter.toFixed(2) + ', 합 ' + d.ratios.total.toFixed(2) + ')';
    panel.querySelector('.lattice').textContent = lat.rows.map(r => r.rel_resid.toFixed(r.rel_resid < 0.01 ? 4 : 3)).join(' → ');
  }

  // ── 동역학 2-b-2 방출 에너지와 궤도 줄어듦 ───────────
  async function initPower(panel) {
    const [p, ins] = await Promise.all([loadJSON('gw_power_160.json'), loadJSON('inspiral.json')]);
    const radii = Object.keys(p.flux);
    const shades = ['#525252', '#737373', '#a3a3a3', COL.warm];
    const series = [
      ...radii.map((r, k) => ({ name: '구면 r = ' + r + ' 흐름', color: shades[k], x: p.t, y: p.flux[r] })),
      { name: '원천이 넘겨준 에너지', color: COL.accent, x: p.t, y: p.W },
    ];
    lineChart(panel.querySelector('.cv-chart'), series,
      { xlab: '시간 (원천은 t = ' + p.ramp + '까지 켜짐)', ylab: '에너지 흐름 ÷ 4중극 방출률 P', ymin: 0, ymax: 1.3, fmtY: v => v.toFixed(1), legend: false });
    panel.querySelector('.legend').innerHTML = series.map(s => '<span style="color:' + s.color + '">━</span> ' + s.name).join('&nbsp;&nbsp; ');

    // 나선: 두 곡선을 같은 시간축으로 재생한다 (곡선마다 한 덩어리의 x, y, 상대는 반대편)
    const curves = Object.entries(ins.curves).map(([name, c], k) => ({ name, c, color: k ? COL.warm : COL.accent }));
    const tEnd = Math.max(...curves.map(({ c }) => c.t.at(-1)));
    const N = 240, cv = panel.querySelector('.cv-inspiral');
    const idxAt = (c, t) => { let i = 0; while (i < c.t.length - 1 && c.t[i + 1] <= t) i++; return i; };

    function render(f) {
      const t = tEnd * f / (N - 1);
      const { ctx, w, h } = hiDPI(cv);
      ctx.clearRect(0, 0, w, h);
      const R = 0.42 * w / (ins.a0 / 2), cx = w / 2, cy = h / 2;
      ctx.strokeStyle = '#333'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(cx, cy, R * ins.a0 / 2, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      const read = [];
      for (const { name, c, color } of curves) {
        const i = idxAt(c, t);
        for (const s of [1, -1]) {
          ctx.strokeStyle = color; ctx.globalAlpha = 0.55; ctx.lineWidth = 1.4;
          ctx.beginPath();
          for (let j = 0; j <= i; j++) { const X = cx + s * c.x[j] * R, Y = cy - s * c.y[j] * R; j ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); }
          ctx.stroke(); ctx.globalAlpha = 1;
          ctx.fillStyle = color;
          ctx.beginPath(); ctx.arc(cx + s * c.x[i] * R, cy - s * c.y[i] * R, 5, 0, 7); ctx.fill();
        }
        const merged = t >= c.t.at(-1);
        read.push(name + ' 거리 ' + c.a[i].toFixed(2) + (merged ? ' (합쳐짐, τ = ' + c.tau.toFixed(0) + ')' : ''));
      }
      ctx.lineWidth = 1;
      panel.querySelector('.readout').textContent = read.join(' · ');
      panel.querySelector('.time').textContent = 't = ' + t.toFixed(0) + ' / ' + tEnd.toFixed(0);
    }
    makePlayer(panel, render, 20).reset(N);
  }

  // ── 동역학 2-b-3 완전 결합 궤도 ─────────────────────
  async function initCoupled(panel) {
    const names = ['bound', 'kinetic', 'newton'];
    const sets = {};
    (await Promise.all(names.map(n => loadJSON('coupled_orbit_' + n + '.json')))).forEach((d, k) => { sets[names[k]] = d; });
    const color = { bound: COL.accent, kinetic: COL.warm, newton: '#737373' };
    const label = { bound: '보존 원천', kinetic: '운동 응력만', newton: '결합 없음' };
    const semi = d => d.E_orb.map(E => d.G * d.mass * d.mass / (-2 * E));
    // 2-b-2 의 방출 세기로 t = 50 부터 그린 단열 예측 a⁴ = a_s⁴ - 4Kκ(t - t_s)
    const predict = (d, kap) => {
      const a = semi(d), i0 = d.t.findIndex(t => t >= 50), a4 = Math.pow(a[i0], 4);
      return d.t.map(t => t < 50 ? null : (v => v > 0 ? Math.pow(v, 0.25) : null)(a4 - 4 * d.K4 * kap * (t - d.t[i0])));
    };
    let key = 'bound';
    const tEnd = Math.max(...names.map(n => sets[n].t.at(-1)));
    const N = 190;

    function chart(t) {
      const b = sets.bound, k = sets.kinetic, nw = sets.newton;
      lineChart(panel.querySelector('.cv-chart'), [
        { name: '', color: '#a3a3a3', x: b.t, y: predict(b, b.kappa_2b2) },
        { name: '', color: '#a3a3a3', x: k.t, y: predict(k, k.kappa_2b2 / 4) },
        { name: label.newton, color: color.newton, x: nw.t, y: semi(nw) },
        { name: label.kinetic, color: color.kinetic, x: k.t, y: semi(k) },
        { name: label.bound, color: color.bound, x: b.t, y: semi(b) },
      ], { xlab: '시간', ylab: '장반경 a', xmin: 0, xmax: 150, ymin: 3, ymax: 6.4, cursor: t, legend: false, fmtY: v => v.toFixed(1) });
    }

    function render(f) {
      const t = tEnd * f / (N - 1), d = sets[key];
      let i = 0; while (i < d.t.length - 1 && d.t[i + 1] <= t) i++;
      const { ctx, w, h } = hiDPI(panel.querySelector('.cv-orbit'));
      ctx.clearRect(0, 0, w, h);
      const R = 0.4 * w / 3.2, cx = w / 2, cy = h / 2;
      ctx.strokeStyle = '#333'; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(cx, cy, 3 * R, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      for (const P of ['X1', 'X2']) {
        ctx.strokeStyle = color[key]; ctx.globalAlpha = 0.5; ctx.lineWidth = 1.4;
        ctx.beginPath();
        for (let j = 0; j <= i; j++) { const [x, y] = d[P][j]; j ? ctx.lineTo(cx + x * R, cy - y * R) : ctx.moveTo(cx + x * R, cy - y * R); }
        ctx.stroke(); ctx.globalAlpha = 1;
        const [x, y] = d[P][i];
        ctx.fillStyle = color[key]; ctx.beginPath(); ctx.arc(cx + x * R, cy - y * R, 6, 0, 7); ctx.fill();
      }
      ctx.lineWidth = 1;
      chart(t);
      const stopped = t > d.t.at(-1) + 0.5 ? ' (거리 3.5에서 멈춤: 덩어리가 겹치기 직전)' : '';
      panel.querySelector('.readout').textContent = label[key] + ' · 거리 ' + d.d[i].toFixed(2) + ' · 장반경 ' + semi(d)[i].toFixed(2) + stopped;
      panel.querySelector('.time').textContent = 't = ' + t.toFixed(0) + ' / ' + tEnd.toFixed(0);
    }

    const player = makePlayer(panel, render, 15);
    panel.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
      panel.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b));
      key = b.dataset.case; player.redraw();
    }));
    player.reset(N);
  }

  // ── 비선형 2: 근일점 이동 ──────────────────────────
  async function initNonlin2(panel) {
    const d = await loadJSON('nonlinear2.json');
    const byKey = Object.fromEntries(d.orbits.map(o => [o.key, o]));
    const color = { '1': COL.accent, '0': COL.warm, abs: '#737373' };
    const shown = ['1', '0', 'abs'];
    const series = [];
    for (const k of shown) {
      const o = byKey[k];
      series.push({ name: '', color: '#a3a3a3', x: [0, 0.017], y: [o.pred, o.pred] });
      series.push({ name: '', color: color[k], x: o.xs, y: o.ratio_e03, dots: true });
    }
    lineChart(panel.querySelector('.cv-chart'), series,
      { xlab: 'm / p', ylab: '근일점 이동 ÷ 6πm/p', xmin: 0, xmax: 0.017, ymin: 0, ymax: 1.4, legend: false, fmtY: v => v.toFixed(1) });

    function draw(key) {
      const o = byKey[key];
      const { ctx, w, h } = hiDPI(panel.querySelector('.cv-orbit'));
      ctx.clearRect(0, 0, w, h);
      // 궤도는 p 단위. 장미 무늬는 중심 질량에서 원일점 거리 1/(1-e) = 2 안을 채운다
      const e = 0.5, R = 0.46 * w / 2, cx = w / 2, cy = h / 2;
      ctx.strokeStyle = '#444'; ctx.setLineDash([4, 4]); ctx.beginPath();
      for (let k = 0; k <= 200; k++) {
        const f = 2 * Math.PI * k / 200, r = 1 / (1 + e * Math.cos(f));
        const x = cx + r * Math.cos(f) * R, y = cy - r * Math.sin(f) * R;
        k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      }
      ctx.stroke(); ctx.setLineDash([]);
      ctx.strokeStyle = color[key]; ctx.lineWidth = 1.3; ctx.beginPath();
      o.rose.forEach(([x, y], k) => k ? ctx.lineTo(cx + x * R, cy - y * R) : ctx.moveTo(cx + x * R, cy - y * R));
      ctx.stroke(); ctx.lineWidth = 1;
      ctx.fillStyle = COL.text; ctx.beginPath(); ctx.arc(cx, cy, 4, 0, 7); ctx.fill();
      const deg = o.rose_dphi * 180 / Math.PI;
      panel.querySelector('.readout').textContent = o.name + ' · β = ' + o.beta.toFixed(3) + ' · 한 바퀴 ' + deg.toFixed(1) +
        '° 앞섬 · m/p → 0 계수 ' + o.c0_e03.toFixed(4) + ' (예측 ' + o.pred.toFixed(4) + ')';
    }
    panel.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
      panel.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b));
      draw(b.dataset.case);
    }));
    draw('1');
    panel.querySelector('.lattice-beta').textContent = '3D 격자에서 잰 정적 장의 β: ' +
      d.lattice.rows.map(r => r.rule + ' ' + r.beta.toFixed(3) + '(예측 ' + r.beta_pred.toFixed(3) + ')').join(' · ');
  }

  // ── 격자 보존 오차 ─────────────────────────────────
  async function initCons(panel) {
    const d = await loadJSON('conservation.json');
    const qa = d.rows.map(r => r.qa);
    lineChart(panel.querySelector('.cv-chart'), [
      { name: '운동량', color: COL.accent, x: qa, y: d.rows.map(r => r.momentum * 100), dots: true },
      { name: '에너지', color: COL.warm, x: qa, y: d.rows.map(r => r.energy * 100), dots: true },
    ], { xlab: '파수 × 격자 간격 (qa)', ylab: '국소 보존 오차 (%)', xmin: 0, ymin: 0 });
  }

  // ── 실패 기록 ──────────────────────────────────────
  async function initFail(panel) {
    const d = await loadJSON('web_fail_mass.json');
    const colors = ['#737373', '#7dd3fc', '#38bdf8', '#0ea5e9', '#fbbf24', '#f59e0b'];
    const series = d.cases.map((c, k) => ({
      name: c.GM === 0 ? '중력 없음' : (c.case.includes('_eq_') ? 'eq ' : '') + 'GM ' + c.GM,
      color: colors[k], x: c.t, y: c.mass.map(v => v / c.mass[0]),
    }));
    // 계열이 여섯 개라 범례는 그래프 아래에 줄바꿈되는 글로 적는다.
    const canvas = panel.querySelector('.cv-chart');
    lineChart(canvas, series,
      { xlab: '시간', ylab: '처음 대비 질량', xmin: 0, xmax: 300, ymin: 0, ymax: 1.05, fmtY: v => v.toFixed(1), legend: false });
    const legend = document.createElement('p');
    legend.className = 'legend';
    legend.innerHTML = series.map(s => '<span style="color:' + s.color + '">━</span> ' + s.name).join('&nbsp;&nbsp; ');
    canvas.after(legend);
  }

  // ── 실험 문서 ──────────────────────────────────────
  async function initDoc() {
    const el = document.getElementById('doc');
    try {
      const res = await fetch(DOC);
      if (!res.ok) throw new Error(res.status);
      let md = await res.text();
      // 제목과 기준일은 페이지 머리에 이미 있다.
      md = md.replace(/^# .*\n+/, '').replace(/^\d{4}-\d{2}-\d{2} 기준\s*\n/, '');
      // 먼 곳 진동수 기호 ω*의 별표가 굵게 표시와 섞이지 않게 한다.
      md = md.replace(/ω\*/g, 'ω\\*');
      // 문서의 ~ 는 모두 범위(1.00~1.01)이므로 취소선으로 읽히지 않게 한다.
      md = md.replace(/~/g, '\\~');
      marked.use({
        renderer: {
          code(code, lang) {
            if (lang !== 'latex') return false;
            return '<div class="math">' + katex.renderToString(code, { displayMode: true, throwOnError: false, strict: false }) + '</div>';
          },
        },
      });
      el.innerHTML = marked.parse(md);
      el.querySelectorAll('a[href^="http"]').forEach(a => { a.target = '_blank'; a.rel = 'noopener'; });
      const toc = document.getElementById('toc-doc');
      el.querySelectorAll('h2').forEach(h => {
        const a = document.createElement('a');
        a.href = '#' + h.id; a.textContent = h.textContent;
        toc.appendChild(a);
      });
    } catch (err) {
      el.innerHTML = '<p class="status err">' + (location.protocol === 'file:'
        ? '문서를 읽으려면 웹 서버로 열어야 합니다 (예: 저장소 폴더에서 python -m http.server).'
        : '문서를 불러오지 못했습니다: ' + err.message) + '</p>';
    }
  }

  // ── 시작: 패널은 화면 가까이 오면 데이터를 읽는다 ──────
  const loaders = { gw: initGW, single: initSingle, binary: initBinary, emit: initEmit, field: initField, power: initPower, coupled: initCoupled, nonlin2: initNonlin2, cons: initCons, fail: initFail };
  function start(panel) {
    const s = panel.querySelector('.status');
    loaders[panel.dataset.load](panel).then(() => { if (!s.classList.contains('err')) s.textContent = ''; }, err => fail(panel, err));
  }
  const panels = document.querySelectorAll('.panel[data-load]');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { io.unobserve(e.target); start(e.target); }
    }), { rootMargin: '400px' });
    panels.forEach(p => io.observe(p));
  } else {
    panels.forEach(start);
  }
  initDoc();
})();
