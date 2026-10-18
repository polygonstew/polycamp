// settings.js - layout, theme, version notes, ComfyUI, Godot/Kiln folder, reset.
import { h, toast } from '../ui.js';
import { S, api, saveSetting } from '../api.js';

export default async function (root) {
  const s = S.settings;
  const kiln = await api('kiln/info');
  const comfy = await api('comfy/status');
  const sel = (key, opts) => h('select', { onchange: e => saveSetting({ [key]: e.target.value }) }, opts.map(([v, t]) => h('option', { value: v, selected: String(s[key]) === String(v) }, t)));
  const txt = (key, w = '320px') => h('input', { type: 'text', value: s[key] || '', style: { width: w }, onchange: e => saveSetting({ [key]: e.target.value }).then(() => toast('Saved', 'good', 1200)) });
  root.append(h('h1', {}, '⚙ Settings'), h('div', { class: 'form' },
    h('label', {}, 'Your name'), txt('name', '200px'),
    h('label', {}, 'Layout'), sel('layout', [['auto', 'Auto (dual when the window is wide)'], ['dual', 'Dual: lesson + live panel side by side'], ['single', 'Single screen: panel docks at the bottom']]),
    h('label', {}, 'Blender version notes'), sel('blender_major', [['auto', 'Auto (from the linked Blender)'], ['3', 'Blender 3.x'], ['4', 'Blender 4.x'], ['5', 'Blender 5.x']]),
    h('label', {}, 'Theme'), sel('theme', [['ember', 'Ember (orange)'], ['ocean', 'Ocean'], ['grape', 'Grape'], ['moss', 'Moss']]),
    h('label', {}, 'Text size'), h('input', { type: 'range', min: '0.85', max: '1.5', step: '0.05', value: s.text_scale, onchange: e => saveSetting({ text_scale: e.target.value }) }),
    h('label', {}, 'Sounds'), h('input', { type: 'checkbox', checked: s.sound, onchange: e => saveSetting({ sound: e.target.checked }) }),
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
}
