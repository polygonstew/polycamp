// ui.js - tiny DOM helper, toasts, modal, confetti, sounds. No framework.
export function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'value') el.value = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(9)) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(kid));
  return el;
}
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export const clear = el => { while (el.firstChild) el.removeChild(el.firstChild); return el; };

export function toast(html, kind = '', ms = 4200) {
  const t = h('div', { class: 'toast ' + kind, html });
  $('#toasts').append(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 400); }, ms);
  return t;
}

export function modal(content, { onclose } = {}) {
  const bg = h('div', { class: 'modal-bg' });
  const box = h('div', { class: 'modal' }, content);
  const close = () => { bg.remove(); onclose && onclose(); };
  bg.addEventListener('click', e => { if (e.target === bg) close(); });
  bg.append(box);
  document.body.append(bg);
  return { close, box };
}

export function lightbox(src) {
  const bg = h('div', { class: 'modal-bg lightbox', onclick: () => bg.remove() }, h('img', { src }));
  document.body.append(bg);
}

// ---- confetti ----
let parts = [], raf = 0;
export function confetti(x = innerWidth / 2, y = innerHeight / 3, n = 90) {
  const c = $('#fx'), g = c.getContext('2d');
  c.width = innerWidth; c.height = innerHeight;
  const cols = ['#e8832a', '#ffb067', '#5fd08a', '#6cb7ff', '#f2c14e', '#ef6b6b', '#a77bf0'];
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, v = 4 + Math.random() * 9;
    parts.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 5, r: 3 + Math.random() * 4, c: cols[i % cols.length], life: 90 + Math.random() * 40, rot: Math.random() * 6 });
  }
  if (raf) return;
  const step = () => {
    g.clearRect(0, 0, c.width, c.height);
    parts = parts.filter(p => p.life-- > 0);
    for (const p of parts) {
      p.x += p.vx; p.y += p.vy; p.vy += .32; p.vx *= .985; p.rot += .2;
      g.save(); g.translate(p.x, p.y); g.rotate(p.rot); g.fillStyle = p.c; g.globalAlpha = Math.min(1, p.life / 30);
      g.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); g.restore();
    }
    raf = parts.length ? requestAnimationFrame(step) : 0;
    if (!raf) g.clearRect(0, 0, c.width, c.height);
  };
  raf = requestAnimationFrame(step);
}

// ---- sound (off by default; Settings > Sound) ----
let ac;
export function beep(kind, enabled) {
  if (!enabled) return;
  try {
    ac = ac || new AudioContext();
    const seq = { task: [[660, .08], [880, .12]], level: [[523, .1], [659, .1], [784, .1], [1046, .25]], bad: [[200, .18]], tick: [[900, .04]] }[kind] || [];
    let t = ac.currentTime;
    for (const [f, d] of seq) {
      const o = ac.createOscillator(), g = ac.createGain();
      o.type = 'triangle'; o.frequency.value = f; g.gain.setValueAtTime(.12, t); g.gain.exponentialRampToValueAtTime(.001, t + d);
      o.connect(g); g.connect(ac.destination); o.start(t); o.stop(t + d); t += d;
    }
  } catch (e) { /* audio not available */ }
}

export const fmtTime = s => s >= 3600 ? (s / 3600).toFixed(1) + ' h' : s >= 60 ? Math.round(s / 60) + ' min' : Math.round(s) + ' s';
export const ago = ts => { const d = Date.now() / 1000 - ts; return d < 90 ? 'just now' : d < 5400 ? Math.round(d / 60) + ' min ago' : d < 129600 ? Math.round(d / 3600) + ' h ago' : Math.round(d / 86400) + ' days ago'; };
