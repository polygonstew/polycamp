// uv.js - UV Lab: pull an object's UV layout out of Blender, paint colour blocks over it, optionally let ComfyUI
// (img2img) add detail, then push the result back as that object's texture.
import { h, toast, clear, fmtTime } from '../ui.js';
import { S, api, on } from '../api.js';
import * as P_ from '../proc.js';

export default async function (root) {
  const SZ = 1024;
  const paint = h('canvas', { width: SZ, height: SZ, style: { width: '100%', touchAction: 'none', cursor: 'crosshair' } });
  const over = h('canvas', { width: SZ, height: SZ, style: { position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', mixBlendMode: 'screen', opacity: .75 } });
  const g = paint.getContext('2d', { willReadFrequently: true }), go = over.getContext('2d');
  const T = { tool: 'brush', color: '#d9a566', size: 28, alpha: 1, undo: [], obj: '', stats: null, job: null };
  g.fillStyle = '#7a6a58'; g.fillRect(0, 0, SZ, SZ);
  const statsEl = h('div', { class: 'kv' });
  const msg = h('div', { class: 'dim', style: { fontSize: '.85rem' } });
  const objIn = h('input', { type: 'text', placeholder: '(active object)', style: { width: '100%' } });
  const sizeSel = h('select', {}, [512, 1024, 2048].map(n => h('option', { value: n, selected: n === 1024 }, n + ' px')));
  const prompt = h('textarea', { rows: 3, style: { width: '100%' } }, 'hand painted wooden lantern surface, detailed texture, flat lighting');
  const setSel = h('select', {}, h('option', { value: '' }, 'solid colour'));

  const snap = () => { T.undo.push(g.getImageData(0, 0, SZ, SZ)); if (T.undo.length > 8) T.undo.shift(); };
  let drawing = false, last = null;
  const pos = e => { const r = paint.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * SZ, (e.clientY - r.top) / r.height * SZ]; };
  const stroke = (a, b) => {
    g.save();
    g.lineCap = g.lineJoin = 'round'; g.lineWidth = T.size;
    if (T.tool === 'erase') { g.globalCompositeOperation = 'destination-out'; g.strokeStyle = 'rgba(0,0,0,1)'; }
    else { g.globalAlpha = T.alpha; g.strokeStyle = T.color; }
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1] + .01); g.stroke(); g.restore();
  };
  paint.addEventListener('pointerdown', e => {
    if (T.tool === 'fill') { snap(); g.fillStyle = T.color; g.globalAlpha = T.alpha; g.fillRect(0, 0, SZ, SZ); g.globalAlpha = 1; return; }
    snap(); drawing = true; last = pos(e); stroke(last, last); paint.setPointerCapture(e.pointerId);
  });
  paint.addEventListener('pointermove', e => { if (!drawing) return; const p = pos(e); stroke(last, p); last = p; });
  paint.addEventListener('pointerup', () => { drawing = false; });

  const loadOverlay = async name => {
    const im = new Image();
    await new Promise(r => { im.onload = r; im.src = '/files/uv/' + name + '?t=' + Date.now(); });
    go.clearRect(0, 0, SZ, SZ); go.drawImage(im, 0, 0, SZ, SZ);
  };
  const showStats = s => {
    clear(statsEl);
    if (!s) return;
    statsEl.append(h('b', {}, 'Object'), h('span', {}, s.object), h('b', {}, 'Faces'), h('span', {}, s.faces),
      h('b', {}, 'Covered'), h('span', { class: s.coverage < .35 ? 'bad' : 'good' }, Math.round(s.coverage * 100) + '% of the tile'),
      h('b', {}, 'Overlap'), h('span', { class: s.overlap > .01 ? 'bad' : 'good' }, Math.round(s.overlap * 1000) / 10 + '%'),
      h('b', {}, 'Outside'), h('span', { class: s.oob > 0 ? 'bad' : 'good' }, Math.round(s.oob * 100) + '% of loops'));
  };
  const fetchUV = async () => {
    if (!S.bridge.connected) return toast('Link Blender first.', 'bad');
    msg.textContent = 'Asking Blender…';
    const r = await api('uv/request', { object: objIn.value || undefined, size: +sizeSel.value });
    if (r.ok === false) { msg.textContent = ''; return toast(r.msg || r.error, 'bad', 6000); }
    msg.textContent = r.msg || '';
    T.obj = r.data && r.data.object || objIn.value;
  };
  const offUV = on('uv', async m => { await loadOverlay(m.name); T.stats = m.stats; showStats(m.stats); T.obj = m.stats.object; msg.textContent = 'Layout loaded. Paint on it!'; });

  const useSet = async () => {
    if (!setSel.value) return;
    const im = new Image();
    await new Promise(r => { im.onload = r; im.src = `/files/textures/${setSel.value}/base_color.png`; });
    snap();
    const n = +tileN.value;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) g.drawImage(im, x * SZ / n, y * SZ / n, SZ / n, SZ / n);
  };
  const tileN = h('input', { type: 'number', min: 1, max: 8, value: 2, style: { width: '60px' } });
  api('tex/list').then(({ sets }) => sets.forEach(s => setSel.append(h('option', { value: s.name }, s.name))));

  const style = async () => {
    const r = await api('tex/generate', { prompt: prompt.value, speed: 'fast', side: +S.settings.comfy_side, init: paint.toDataURL('image/png'), denoise: +denoise.value });
    if (!r.ok) return toast(r.error, 'bad', 6000);
    T.job = r.job;
    const poll = async () => {
      const j = await api('tex/job?id=' + T.job);
      if (j.status === 'running') { msg.textContent = 'ComfyUI is repainting: ' + fmtTime(j.elapsed); setTimeout(poll, 2000); }
      else if (j.status === 'done') {
        const im = new Image(); await new Promise(res => { im.onload = res; im.src = j.image + '?t=' + Date.now(); });
        snap(); g.drawImage(im, 0, 0, SZ, SZ); msg.textContent = 'Repainted in ' + fmtTime(j.elapsed);
      } else msg.textContent = j.error || 'failed';
    };
    poll();
  };
  const denoise = h('input', { type: 'range', min: .2, max: .8, step: .05, value: .45 });

  const send = async () => {
    const name = 'uv-' + (T.obj || 'paint').replace(/[^\w.-]/g, '_');
    const sv = await api('tex/save', { name, maps: { base_color: paint.toDataURL('image/png') } });
    const r = await api('tex/to_blender', { set: sv.set, apply: T.obj || 'active', tiling: [1, 1] });
    toast(r.msg || r.error || 'Sent', r.ok === false || r.error ? 'bad' : 'good', 5000);
  };

  const btn = (t, tool) => h('button', { class: 'sm', onclick: e => { T.tool = tool; [...e.target.parentNode.children].forEach(c => c.classList.remove('pri')); e.target.classList.add('pri'); } }, t);
  root.append(h('div', { class: 'row' }, h('div', {}, h('div', { class: 'sheet' }, 'Workshop'), h('h1', { style: { margin: 0 } }, 'UV lab')), h('span', { class: 'dim', style: { fontFamily: 'var(--serif)' } }, 'See the layout, paint on it, send it back.')),
    h('div', { class: 'uvgrid', style: { marginTop: '14px' } },
      h('div', {}, h('div', { class: 'uvstage', style: { position: 'relative' } }, paint, over),
        h('p', { class: 'faint', style: { fontSize: '.82rem' } }, 'Teal = covered, red = overlapping islands (usually a mistake), white = edges. The picture’s top edge is V = 1, like Blender’s UV Editor.')),
      h('div', { class: 'col', style: { display: 'flex', flexDirection: 'column', gap: '12px' } },
        h('div', { class: 'card' }, h('h4', { style: { margin: '0 0 8px' } }, '1 · Layout from Blender'), objIn, h('div', { class: 'row', style: { margin: '8px 0' } }, sizeSel, h('button', { class: 'pri', onclick: fetchUV }, 'Get UV layout')), statsEl, msg),
        h('div', { class: 'card' }, h('h4', { style: { margin: '0 0 8px' } }, '2 · Paint'),
          h('div', { class: 'row' }, btn('Brush', 'brush'), btn('Eraser', 'erase'), btn('Fill', 'fill'), h('input', { type: 'color', value: T.color, oninput: e => T.color = e.target.value })),
          h('div', { class: 'sliders', style: { marginTop: '8px' } }, h('label', {}, 'size'), h('input', { type: 'range', min: 4, max: 160, value: T.size, oninput: e => T.size = +e.target.value }), h('span'),
            h('label', {}, 'opacity'), h('input', { type: 'range', min: .05, max: 1, step: .05, value: 1, oninput: e => T.alpha = +e.target.value }), h('span'),
            h('label', {}, 'UV lines'), h('input', { type: 'range', min: 0, max: 1, step: .05, value: .75, oninput: e => over.style.opacity = e.target.value }), h('span')),
          h('div', { class: 'row', style: { marginTop: '8px' } }, h('label', {}, 'start from'), setSel, h('label', {}, '×'), tileN, h('button', { class: 'sm', onclick: useSet }, 'Tile it')),
          h('div', { class: 'row', style: { marginTop: '8px' } }, h('button', { class: 'sm', onclick: () => { const u = T.undo.pop(); if (u) g.putImageData(u, 0, 0); } }, '↶ Undo'))),
        h('div', { class: 'card' }, h('h4', { style: { margin: '0 0 8px' } }, '3 · Add detail (ComfyUI, optional)'), prompt,
          h('div', { class: 'row', style: { marginTop: '6px' } }, h('label', {}, 'how much AI'), denoise), h('button', { class: 'sm', style: { marginTop: '6px' }, onclick: style }, 'Repaint with img2img')),
        h('div', { class: 'card' }, h('h4', { style: { margin: '0 0 8px' } }, '4 · Back to Blender'), h('button', { class: 'pri', onclick: send }, '→ Apply as this object’s texture'),
          h('p', { class: 'faint', style: { fontSize: '.78rem' } }, 'Creates a material with this image as Base Color on the object.')))));
  return () => offUV();
}
