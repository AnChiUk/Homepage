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
  const loaders = { gw: initGW, single: initSingle, binary: initBinary, cons: initCons, fail: initFail };
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
