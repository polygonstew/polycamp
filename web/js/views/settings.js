// settings.js - layout, theme, version notes, ComfyUI, Godot/Kiln folder, reset.
import { h, toast } from '../ui.js';
import { S, api, saveSetting } from '../api.js';

const VOICE_KIND = { af: 'US woman', am: 'US man', bf: 'UK woman', bm: 'UK man' };
const voiceLabel = v => `${v.slice(3).replace(/^./, c => c.toUpperCase())} (${VOICE_KIND[v.slice(0, 2)]})`;

export default async function (root) {
  const s = S.settings;
  const kiln = await api('kiln/info');
  const comfy = await api('comfy/status');
  const vs = await api('voice/status');
  const voices = (vs.voices || []).filter(v => VOICE_KIND[v.slice(0, 2)]).sort((a, b) => (b === 'af_heart') - (a === 'af_heart') || a.localeCompare(b));
  const prog = h('div', { class: 'faint', style: { fontSize: '.82rem', marginTop: '6px' } });
  const showProg = st => {
    const b = st.batch;
    prog.textContent = b.total && b.left ? `Preparing ${b.label}: ${b.done} of ${b.total} segments done` + (st.job_s ? `, about ${Math.max(1, Math.round(b.left * st.job_s / 60))} min left` : '')
      : b.total ? `Last batch: ${b.done} made${b.failed ? ', ' + b.failed + ' failed' : ''}.` : '';
    prog.textContent += ` Stored: ${st.cache.files} files, ${st.cache.mb} MB.` + (st.rtf ? ` Speed on this PC: ${st.rtf}× real time.` : '');
  };
  showProg(vs);
  const timer = setInterval(async () => showProg(await api('voice/status')), 2500);
  const preview = (key, el) => async () => {
    el.disabled = true;
    const old = el.textContent;
    el.textContent = 'Making a sample…';
    const r = await api('voice/preview', { voice: S.settings[key] });
    if (r.key) await new Audio(`/voice/${r.key}.ogg`).play().catch(() => toast('The sample could not be played.', 'bad'));
    el.disabled = false;
    el.textContent = old;
  };
  const voicePick = key => {
    const b = h('button', { class: 'sm' }, 'Hear it');
    b.onclick = preview(key, b);
    return h('div', { class: 'row' }, h('select', { onchange: e => saveSetting({ [key]: e.target.value }) },
      (voices.includes(s[key]) || !voices.length ? voices : [s[key], ...voices]).map(v => h('option', { value: v, selected: s[key] === v }, voiceLabel(v)))), b);
  };
  const chk = (key, extra) => h('input', { type: 'checkbox', checked: s[key], onchange: e => saveSetting({ [key]: e.target.checked }) });
  const voiceRows = !vs.installed
    ? [h('label', {}, 'Voice engine'), h('div', {}, h('span', { class: 'bad' }, 'Not installed. '), 'Run ', h('code', {}, 'python3 tools/install_voice.py'), ' on the PC that runs Polycamp (about 400 MB, no GPU needed), then reload this page.')]
    : [
      h('label', {}, 'Narrator voice'), voicePick('voice_narrator'),
      h('label', {}, 'Cubby’s voice'), voicePick('voice_cubby'),
      h('label', {}, 'Speed'), h('select', { onchange: e => saveSetting({ voice_speed: +e.target.value }) }, [0.85, 1, 1.15, 1.3, 1.5, 1.75].map(v => h('option', { value: v, selected: Math.abs(s.voice_speed - v) < .01 }, v + '×'))),
      h('label', {}, 'Style'), h('select', { onchange: e => saveSetting({ voice_mode: e.target.value }) }, [['coach', 'Coach: waits at each task until Blender confirms it'], ['book', 'Audiobook: reads straight through']].map(([v, t]) => h('option', { value: v, selected: s.voice_mode === v }, t))),
      h('label', {}, 'Cubby’s asides'), chk('voice_cubby_on'),
      h('label', {}, 'Read the “more” boxes'), chk('voice_extras'),
      h('label', {}, 'Point at things in Blender'), h('div', {}, chk('voice_cues'), h('span', { class: 'faint', style: { marginLeft: '8px', fontSize: '.8rem' } }, 'outlines the sidebar, Outliner, objects and so on while they are mentioned')),
      h('label', {}, 'Make all the audio now'), h('div', {},
        h('div', { class: 'row' },
          h('button', { class: 'sm', onclick: async () => { const r = await api('voice/prerender', { scope: 'all' }); toast(r.queued ? `${r.queued} segments queued. It runs quietly in the background.` : 'Everything is already made.', 'info', 4000); } }, 'All lessons'),
          h('button', { class: 'sm ghost', onclick: async () => { const r = await api('voice/cancel', {}); toast(`${r.cancelled} cancelled`, 'info', 2000); } }, 'Stop'),
          h('button', { class: 'sm ghost', onclick: async () => { if (!confirm('Delete all stored narration audio? It will be made again when needed.')) return; const r = await api('voice/clear', {}); toast(`${r.removed} files removed`, 'info', 2500); } }, 'Clear stored audio')),
        prog),
    ];
  const sel = (key, opts) => h('select', { onchange: e => saveSetting({ [key]: e.target.value }) }, opts.map(([v, t]) => h('option', { value: v, selected: String(s[key]) === String(v) }, t)));
  const txt = (key, w = '320px') => h('input', { type: 'text', value: s[key] || '', style: { width: w }, onchange: e => saveSetting({ [key]: e.target.value }).then(() => toast('Saved', 'good', 1200)) });
  root.append(h('div', { class: 'sheet' }, 'Setup'), h('h1', {}, 'Settings'), h('div', { class: 'form' },
    h('label', {}, 'Your name'), txt('name', '200px'),
    h('label', {}, 'Layout'), sel('layout', [['auto', 'Automatic (follows window width)'], ['dual', 'Dual: lesson and live panel side by side'], ['single', 'Single screen: the panel docks along the bottom']]),
    h('label', {}, 'Blender version notes'), sel('blender_major', [['auto', 'Auto (from the linked Blender)'], ['3', 'Blender 3.x'], ['4', 'Blender 4.x'], ['5', 'Blender 5.x']]),
    h('label', {}, 'Theme'), sel('theme', [['ember', 'Survey orange'], ['ocean', 'Teal'], ['grape', 'Violet'], ['moss', 'Olive']]),
    h('label', {}, 'Text size'), h('input', { type: 'range', min: '0.85', max: '1.5', step: '0.05', value: s.text_scale, onchange: e => saveSetting({ text_scale: e.target.value }) }),
    h('label', {}, 'Sounds'), h('input', { type: 'checkbox', checked: s.sound, onchange: e => saveSetting({ sound: e.target.checked }) }),
    h('h3', { style: { gridColumn: '1/-1', margin: '16px 0 0' } }, 'Narration (the lesson read aloud)'),
    ...voiceRows,
    h('h3', { style: { gridColumn: '1/-1', margin: '16px 0 0' } }, 'ComfyUI (texture generation)'),
    h('label', {}, 'ComfyUI address'), txt('comfy_url'),
    h('label', {}, 'Checkpoint'), comfy.ok ? sel('comfy_ckpt', comfy.checkpoints.map(c => [c, c])) : h('span', { class: 'bad' }, comfy.error),
    h('label', {}, 'Default size'), sel('comfy_side', [['384', '384 px (fastest)'], ['512', '512 px'], ['640', '640 px (slow on CPU)']]),
    h('h3', { style: { gridColumn: '1/-1', margin: '16px 0 0' } }, 'Godot / Kiln export'),
    h('label', {}, 'Folder'), h('div', {}, txt('godot_dir', '420px'),
      h('div', { class: 'faint', style: { fontSize: '.8rem', marginTop: '4px' } }, 'models/ and textures/ are created inside it. Point it at a Godot project or a Kiln game folder.'),
      h('div', { class: 'row', style: { marginTop: '6px' } }, kiln.kiln_games.map(g => h('button', { class: 'sm', onclick: async () => { await saveSetting({ godot_dir: g }); toast('Godot folder set', 'good'); location.reload(); } }, 'Kiln: ' + g.split('/').pop())))),
    h('h3', { style: { gridColumn: '1/-1', margin: '16px 0 0' } }, 'Progress'),
    h('label', {}, 'Start over'), h('button', { class: 'sm', onclick: async () => {
      if (!confirm('Wipe ALL XP, badges and lesson progress?')) return;
      await api('reset', { confirm: 'RESET' }); toast('Progress reset', 'info'); location.hash = '#/'; location.reload();
    } }, 'Reset all progress…')));
  return () => clearInterval(timer);
}
