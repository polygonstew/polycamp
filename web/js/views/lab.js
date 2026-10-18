// lab.js - Texture Lab. Make a tileable texture (procedural, ComfyUI on the CPU, or your own picture),
// derive PBR maps, preview them lit, then send them to Blender or export to Godot/Kiln.
import { h, toast, clear, fmtTime } from '../ui.js';
import { S, api } from '../api.js';
import * as P_ from '../proc.js';

const P = { seamless: true, blend: 2.2, h_contrast: 1.4, h_smooth: 1, h_invert: false, n_strength: 3, r_base: .65, r_contrast: .8, r_invert: false,
  ao_radius: 6, ao_strength: 2.5, inc_height: true, inc_normal: true, inc_roughness: true, inc_ao: true, tiling: 2, bump: .2, nstr_b: 1 };
const G = { A: '#8a5a2b', B: '#d9a566', scale: 1, seed: 7, kind: 'planks', mode: 'proc', denoise: .55 };

export default async function (root) {
  const T = { raw: null, hgt: null, tileable: false, maps: {}, albedo: null };
  const presets = (await api('tex/presets'));
  const comfy = await api('comfy/status');
  let preview = 'tile2', job = null, pollT = 0, lx = .4, ly = -.5;
  const stage = h('canvas', { width: 512, height: 512 });
  const mapsEl = h('div', { class: 'maps' });
  const setsEl = h('div', { class: 'row' });
  const status = h('div', { class: 'dim', style: { fontSize: '.85rem' } });
  const nameIn = h('input', { type: 'text', value: 'my-texture', style: { width: '100%' } });
  const prompt = h('textarea', { rows: 4, style: { width: '100%' }, placeholder: 'seamless texture, top down, flat lighting…' }, presets.presets[0].prompt);

  // ---------------- pipeline ----------------
  const rebuild = () => {
    if (!T.raw) return;
    const W = T.raw.width, H = T.raw.height;
    const albedo = (P.seamless && !T.tileable) ? P_.seamless(T.raw, P.blend) : T.raw;
    const L = P_.luminance(albedo);
    const hgt = T.hgt && T.tileable ? T.hgt : P_.heightMap(L, W, H, { contrast: P.h_contrast, smoothing: P.h_smooth, invert: P.h_invert });
    T.albedo = albedo;
    const normal = P_.normalMap(hgt, W, H, P.n_strength);
    T.maps = { base_color: P_.toCanvas(albedo), height: P_.toCanvas(P_.grayImage(hgt, W, H)), normal: P_.toCanvas(normal),
      roughness: P_.toCanvas(P_.roughnessMap(L, W, H, { base: P.r_base, contrast: P.r_contrast, invert: P.r_invert })),
      ao: P_.toCanvas(P_.aoMap(hgt, W, H, { radius: P.ao_radius, strength: P.ao_strength })) };
    T.normalData = normal;
    drawMaps(); drawStage();
  };
  let pend = 0;
  const later = () => { cancelAnimationFrame(pend); pend = requestAnimationFrame(rebuild); };

  const drawMaps = () => {
    clear(mapsEl);
    for (const k of ['base_color', 'height', 'normal', 'roughness', 'ao']) {
      const c = document.createElement('canvas'); c.width = c.height = 160;
      c.getContext('2d').drawImage(T.maps[k], 0, 0, 160, 160);
      mapsEl.append(h('div', { class: 'mapc' }, c, h('label', {}, k.replace('_', ' '))));
    }
  };
  const drawStage = () => {
    if (!T.raw) return;
    const g = stage.getContext('2d'), s = 512;
    stage.width = stage.height = s;
    if (preview === 'relief') {
      const r = P_.relief(P_.imageDataOf(T.maps.base_color), T.normalData, lx, ly);
      const c = P_.toCanvas(r); g.drawImage(c, 0, 0, s, s);
    } else {
      const n = preview === 'tile1' ? 1 : preview === 'tile2' ? 2 : 3;
      for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) g.drawImage(T.maps.base_color, x * s / n, y * s / n, s / n, s / n);
      if (n > 1) { g.strokeStyle = 'rgba(255,255,255,.18)'; for (let i = 1; i < n; i++) { g.beginPath(); g.moveTo(i * s / n, 0); g.lineTo(i * s / n, s); g.moveTo(0, i * s / n); g.lineTo(s, i * s / n); g.stroke(); } }
    }
  };
  stage.addEventListener('mousemove', e => {
    if (preview !== 'relief') return;
    const r = stage.getBoundingClientRect(); lx = (e.clientX - r.left) / r.width * 2 - 1; ly = (e.clientY - r.top) / r.height * 2 - 1;
    cancelAnimationFrame(pend); pend = requestAnimationFrame(drawStage);
  });

  const setRaw = (img, tileable, hgt = null) => { T.raw = img; T.tileable = tileable; T.hgt = hgt; rebuild(); };
  const loadUrl = url => new Promise((res, rej) => { const im = new Image(); im.crossOrigin = 'anonymous'; im.onload = () => res(im); im.onerror = rej; im.src = url; });
  const fromImage = async (im, tileable = false) => {
    const side = Math.min(im.naturalWidth, im.naturalHeight, 1024);
    const c = document.createElement('canvas'); c.width = c.height = side;
    c.getContext('2d').drawImage(im, (im.naturalWidth - side) / 2, (im.naturalHeight - side) / 2, side, side, 0, 0, side, side);
    setRaw(c.getContext('2d').getImageData(0, 0, side, side), tileable);
  };

  // ---------------- sources ----------------
  const runProc = () => {
    const side = +S.settings.comfy_side >= 512 ? 512 : 384;
    const { img, hgt } = P_.generate(G.kind, side, { A: G.A, B: G.B, scale: G.scale, seed: G.seed });
    setRaw(img, true, hgt);
  };
  const cook = async (init) => {
    if (!comfy.ok) return toast(comfy.error, 'bad', 6000);
    const speed = speedSel.value;
    const body = { prompt: prompt.value, speed, side: +S.settings.comfy_side, seed: Math.floor(Math.random() * 1e9) };
    if (init) { body.init = T.maps.base_color.toDataURL('image/png'); body.denoise = G.denoise; }
    const r = await api('tex/generate', body);
    if (!r.ok) return toast(r.error, 'bad', 5000);
    job = r.job; poll();
  };
  const poll = async () => {
    clearTimeout(pollT);
    if (!job) return;
    const j = await api('tex/job?id=' + job);
    if (j.status === 'running') {
      status.innerHTML = `⏳ Cooking on your CPU… <b>${fmtTime(j.elapsed)}</b> (${j.steps || '?'} steps at ${j.side || '?'} px). ComfyUI is slow here, so go model something and come back.`;
      pollT = setTimeout(poll, 2000);
    } else if (j.status === 'done') {
      status.textContent = '✔ Done in ' + fmtTime(j.elapsed); job = null;
      await fromImage(await loadUrl(j.image + '?t=' + Date.now()), false);
      toast('Texture ready. Check the 2×2 tile preview for seams.', 'good');
    } else { status.innerHTML = `<span class="bad">${j.error || 'failed'}</span>`; job = null; }
  };

  // ---------------- UI pieces ----------------
  const slider = (label, obj, key, min, max, step, onchange = later) => {
    const v = h('span', { class: 'v' }, obj[key]);
    const inp = h('input', { type: 'range', min, max, step, value: obj[key], oninput: e => { obj[key] = +e.target.value; v.textContent = obj[key]; onchange(); } });
    return [h('label', {}, label), inp, v];
  };
  const check = (label, obj, key) => h('label', { class: 'row' }, h('input', { type: 'checkbox', checked: obj[key], onchange: e => { obj[key] = e.target.checked; later(); } }), label);
  const speedSel = h('select', {}, [['fast', 'Fast (LCM, 5 steps)'], ['normal', 'Normal (LCM, 8 steps)'], ['quality', 'Quality (16 steps, slow!)']].map(([v, t]) => h('option', { value: v }, t)));
  const kindChips = h('div', { class: 'chips' });
  const drawKinds = () => {
    clear(kindChips);
    presets.presets.forEach(p => kindChips.append(h('span', { class: 'chip' + (G.kind === p.proc && prompt.value === p.prompt ? ' on' : ''), onclick: () => {
      G.kind = p.proc; prompt.value = p.prompt; nameIn.value = p.id;
      const pal = { wood: ['#7a4a22', '#d6a363'], stone: ['#6e6a62', '#b3ad9f'], cobble: ['#59585a', '#a9a59b'], rust: ['#4a2a1a', '#c9702d'], roof: ['#3d2a1e', '#8a6246'], grass: ['#2c5a22', '#8bc34a'], leather: ['#4a2b17', '#9a6234'], plaster: ['#a49a8a', '#e6dccb'] }[p.id];
      if (pal) { G.A = pal[0]; G.B = pal[1]; colA.value = G.A; colB.value = G.B; }
      drawKinds();
      if (G.mode === 'proc') runProc();
    } }, p.name)));
  };
  const colA = h('input', { type: 'color', value: G.A, oninput: e => G.A = e.target.value }), colB = h('input', { type: 'color', value: G.B, oninput: e => G.B = e.target.value });
  const fileIn = h('input', { type: 'file', accept: 'image/*', style: { display: 'none' }, onchange: e => e.target.files[0] && loadFile(e.target.files[0]) });
  const loadFile = f => { const u = URL.createObjectURL(f); loadUrl(u).then(im => fromImage(im, false)); };
  addEventListener('paste', pasteH);
  function pasteH(e) { const it = [...(e.clipboardData || {}).items || []].find(i => i.type.startsWith('image/')); if (it) loadFile(it.getAsFile()); }

  const tabs = h('div', { class: 'chips', style: { marginBottom: '8px' } });
  const srcBody = h('div');
  const drawSrc = () => {
    clear(tabs); clear(srcBody);
    [['proc', 'Procedural (instant)'], ['ai', 'ComfyUI (AI, slow)'], ['pic', 'My picture']].forEach(([m, t]) => tabs.append(h('span', { class: 'chip' + (G.mode === m ? ' on' : ''), onclick: () => { G.mode = m; drawSrc(); } }, t)));
    if (G.mode === 'proc') srcBody.append(h('div', { class: 'row' }, h('label', {}, 'colours'), colA, colB), h('div', { class: 'sliders', style: { margin: '8px 0' } }, slider('scale', G, 'scale', .4, 3, .1, () => { }), slider('seed', G, 'seed', 1, 99, 1, () => { })),
      h('button', { class: 'pri', onclick: runProc }, '✨ Generate'), h('p', { class: 'faint', style: { fontSize: '.8rem' } }, 'Pure maths, tiles perfectly, and teaches you what Noise and Voronoi nodes do in Blender.'));
    if (G.mode === 'ai') srcBody.append(prompt,
      h('div', { class: 'row', style: { margin: '8px 0' } }, speedSel),
      comfy.ok ? h('div', { class: 'good', style: { fontSize: '.82rem' } }, `ComfyUI ${comfy.version} online · ${comfy.ckpt}${comfy.busy ? ' · busy' : ''}`) : h('div', { class: 'bad', style: { fontSize: '.82rem' } }, comfy.error),
      h('div', { class: 'row', style: { marginTop: '8px' } }, h('button', { class: 'pri', onclick: () => cook(false) }, '🍳 Cook texture'), h('button', { onclick: () => api('tex/cancel', {}).then(() => { job = null; status.textContent = 'cancelled'; }) }, 'Cancel')),
      h('div', { class: 'sliders', style: { marginTop: '8px' } }, slider('variation', G, 'denoise', .2, .9, .05, () => { })),
      h('button', { class: 'sm', style: { marginTop: '6px' }, onclick: () => T.raw ? cook(true) : toast('Make or load a texture first', 'bad') }, '🎲 Variation of current (img2img)'),
      h('p', { class: 'faint', style: { fontSize: '.8rem' } }, 'About 30 s per step at 512 px on this CPU. The result is made seamless for you afterwards.'));
    if (G.mode === 'pic') srcBody.append(h('div', { class: 'row' }, h('button', { onclick: () => fileIn.click() }, '📁 Choose image'), fileIn), h('p', { class: 'dim', style: { fontSize: '.85rem' } }, 'Or drop a file on the preview, or paste (Ctrl+V). Photos of walls, floors and bark work great.'));
  };
  stage.addEventListener('dragover', e => e.preventDefault());
  stage.addEventListener('drop', e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) loadFile(f); });

  const previewBar = h('div', { class: 'chips' }, [['tile1', '1×'], ['tile2', '2×2 tile'], ['tile3', '3×3 tile'], ['relief', '💡 Relief (move mouse)']].map(([k, t]) => h('span', { class: 'chip' + (preview === k ? ' on' : ''), onclick: e => { preview = k; [...previewBar.children].forEach(c => c.classList.remove('on')); e.target.classList.add('on'); drawStage(); } }, t)));

  // ---------------- saving & sending ----------------
  const payload = () => {
    const m = {};
    for (const [k, c] of Object.entries(T.maps)) {
      if (k === 'height' && !P.inc_height) continue;
      if (k === 'normal' && !P.inc_normal) continue;
      if (k === 'roughness' && !P.inc_roughness) continue;
      if (k === 'ao' && !P.inc_ao) continue;
      m[k] = c.toDataURL('image/png');
    }
    return m;
  };
  const save = async () => {
    if (!T.raw) { toast('Make a texture first', 'bad'); return null; }
    const r = await api('tex/save', { name: nameIn.value || 'texture', maps: payload(), meta: { kind: G.kind, prompt: prompt.value } });
    loadSets();
    return r.set;
  };
  const toBlender = async () => {
    const set = await save(); if (!set) return;
    const r = await api('tex/to_blender', { set, apply: 'selected', tiling: [P.tiling, P.tiling], normal_strength: P.nstr_b, bump_strength: P.bump });
    toast(r.msg || r.error || 'Sent', r.ok === false || r.error ? 'bad' : 'good', 5000);
  };
  const toGodot = async () => {
    const set = await save(); if (!set) return;
    const r = await api('tex/export_godot', { set });
    toast(r.ok ? `Exported to <code>${r.folder}</code> with a StandardMaterial3D .tres` : r.error, r.ok ? 'good' : 'bad', 6000);
  };
  const loadSets = async () => {
    const { sets } = await api('tex/list');
    clear(setsEl);
    sets.slice(0, 12).forEach(s => setsEl.append(h('div', { class: 'mapc', style: { width: '84px' } }, h('img', { src: s.thumb, style: { width: '100%', borderRadius: '6px', cursor: 'pointer' }, title: 'Load ' + s.name, onclick: async () => { nameIn.value = s.name; fromImage(await loadUrl(s.thumb + '?t=' + Date.now()), false); } }), h('label', {}, s.name),
      h('a', { href: '#', onclick: async e => { e.preventDefault(); await api('tex/delete', { set: s.name }); loadSets(); } }, '✕'))));
    if (!sets.length) setsEl.append(h('span', { class: 'faint' }, 'No saved sets yet.'));
  };

  root.append(h('div', { class: 'row' }, h('h1', { style: { margin: 0 } }, '🧱 Texture Lab'), h('span', { class: 'dim' }, 'albedo → height → normal → roughness → AO, tileable, CPU friendly')),
    h('div', { class: 'lab', style: { marginTop: '14px' } },
      h('div', { class: 'col' },
        h('div', { class: 'card' }, h('h4', {}, '1 · Source'), kindChips, h('div', { style: { height: '8px' } }), tabs, srcBody, status),
        h('div', { class: 'card' }, h('h4', {}, 'Seamless'), check('Make seamless (offset blend)', P, 'seamless'), h('div', { class: 'sliders' }, slider('blend', P, 'blend', 1, 5, .1)), h('p', { class: 'faint', style: { fontSize: '.78rem' } }, 'Procedural textures already tile; AI and photos need this.'))),
      h('div', { class: 'col' }, h('div', { class: 'stage' }, stage), previewBar, h('div', { class: 'card' }, h('h4', {}, '2 · Maps'), mapsEl)),
      h('div', { class: 'col' },
        h('div', { class: 'card' }, h('h4', {}, 'Map tuning'),
          h('div', { class: 'sliders' }, slider('height ×', P, 'h_contrast', .5, 3, .05), slider('smooth', P, 'h_smooth', 0, 6, 1), slider('normal', P, 'n_strength', .5, 12, .25),
            slider('rough base', P, 'r_base', 0, 1, .05), slider('rough ×', P, 'r_contrast', 0, 2, .05), slider('AO radius', P, 'ao_radius', 1, 24, 1), slider('AO power', P, 'ao_strength', 0, 8, .25)),
          h('div', { class: 'row', style: { marginTop: '6px' } }, check('invert height', P, 'h_invert'), check('invert rough', P, 'r_invert'))),
        h('div', { class: 'card' }, h('h4', {}, '3 · Use it'), h('label', {}, 'Set name'), nameIn,
          h('div', { class: 'row', style: { margin: '8px 0' } }, check('height', P, 'inc_height'), check('normal', P, 'inc_normal'), check('rough', P, 'inc_roughness'), check('AO', P, 'inc_ao')),
          h('div', { class: 'sliders' }, slider('tiling', P, 'tiling', 1, 8, 1, () => { }), slider('bump', P, 'bump', 0, 1, .05, () => { })),
          h('div', { class: 'row', style: { marginTop: '10px' } }, h('button', { onclick: save }, '💾 Save set'), h('button', { class: 'pri', onclick: toBlender }, '→ Blender (selected objects)'), h('button', { onclick: toGodot }, '→ Godot / Kiln')),
          h('p', { class: 'faint', style: { fontSize: '.78rem' } }, S.bridge.connected ? 'Blender is linked: select a mesh there first.' : 'Link Blender to send directly.')),
        h('div', { class: 'card' }, h('h4', {}, 'Saved sets'), setsEl))));
  drawKinds(); drawSrc(); loadSets();
  runProc();           // start with something on screen
  return () => { clearTimeout(pollT); removeEventListener('paste', pasteH); };
}
