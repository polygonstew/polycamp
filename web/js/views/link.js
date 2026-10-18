// link.js - install and troubleshooting guide for the Blender add-on, plus the two-monitor layout advice.
import { h } from '../ui.js';
import { S, on } from '../api.js';

export default async function (root) {
  const url = location.origin;
  const status = h('div');
  const paint = () => {
    const cl = (S.bridge.clients || []).filter(c => c.alive);
    status.replaceChildren(cl.length
      ? h('div', { class: 'note tip' }, h('b', { class: 't' }, 'Connected'), cl.map(c => h('div', {}, `Blender ${c.blender} on ${c.host || c.ip} (${c.platform})${c.file ? ' · ' + c.file : ''}`)))
      : h('div', { class: 'note warn' }, h('b', { class: 't' }, 'Waiting for Blender…'), 'This page turns green the moment the add-on connects.'));
  };
  paint();
  const off = on('live', paint);
  root.append(h('div', { style: { maxWidth: '980px' } },
    h('h1', {}, '🔌 Link Blender'), status,
    h('div', { class: 'card' }, h('h3', { style: { marginTop: 0 } }, '1. Get the add-on'),
      h('div', { class: 'row' }, h('a', { class: 'btn pri', href: '/addon/polycamp_link.zip' }, '⬇ polycamp_link.zip'), h('span', { class: 'dim' }, 'It already contains this server’s address: ' ), h('code', {}, url)),
      h('p', { class: 'dim' }, 'Blender on a different computer (say, Windows)? Open this page in that computer’s browser using the LAN address ', h('code', {}, S.lan || url), ' and download the zip there.')),
    h('div', { class: 'card', style: { marginTop: '14px' } }, h('h3', { style: { marginTop: 0 } }, '2. Install it'),
      h('ul', {}, h('li', {}, h('b', {}, 'Blender 3.3: '), 'Edit > Preferences > Add-ons > Install… > pick the zip > tick “System: Polycamp Link”.'),
        h('li', {}, h('b', {}, 'Blender 4.2 – 5.x: '), 'Edit > Preferences > Add-ons > ⌄ menu (top right) > Install from Disk… > pick the zip. If Blender warns about legacy add-ons, that’s fine.'),
        h('li', {}, h('b', {}, 'Same PC as this server, command line: '), h('code', {}, 'python3 tools/install_addon.py'), ' copies it into every Blender version it finds and switches it on.')),
      h('p', {}, 'Then in any 3D viewport press ', h('kbd', {}, 'N'), ' and open the ', h('b', {}, 'Polycamp'), ' tab.')),
    h('div', { class: 'card', style: { marginTop: '14px' } }, h('h3', { style: { marginTop: 0 } }, 'Two monitors, or one'),
      h('div', { class: 'row', style: { gap: '30px', alignItems: 'flex-start' } }, layoutDiagram('dual'), layoutDiagram('single')),
      h('ul', {}, h('li', {}, h('b', {}, 'Dual: '), 'Blender full-screen on monitor 1. This page on monitor 2, with the live quest panel on the right. Use ', h('b', {}, '⧉ HUD'), ' in the top bar for a slim tasks-only window.'),
        h('li', {}, h('b', {}, 'Single: '), 'switch the top-bar layout to Single, or enable “Show tasks in the 3D viewport” in the add-on preferences so the tasks float over Blender itself. The sidebar tab shows them too, no browser needed.'))),
    h('div', { class: 'card', style: { marginTop: '14px' } }, h('h3', { style: { marginTop: 0 } }, 'Not connecting?'),
      h('ul', {}, h('li', {}, 'In the add-on preferences, “Polycamp server” must match the address in your browser bar (', h('code', {}, url), ').'),
        h('li', {}, 'Firewall on the server PC: allow TCP port 8570. CachyOS with ufw: ', h('code', {}, 'sudo ufw allow 8570/tcp'), '. Windows: allow Python through the firewall when prompted.'),
        h('li', {}, 'Press ', h('b', {}, 'Reconnect'), ' in the add-on preferences after changing the address.'),
        h('li', {}, 'Blender’s System Console (Windows: Window > Toggle System Console) prints lines starting with ', h('code', {}, '[polycamp]'), '.')))));
  return off;
}

function layoutDiagram(kind) {
  const box = (w, hgt, label, extra = {}) => h('div', { style: Object.assign({ width: w, height: hgt, border: '2px solid var(--line2)', borderRadius: '6px', display: 'grid', placeItems: 'center', fontSize: '.7rem', color: 'var(--dim)', background: 'var(--bg2)' }, extra) }, label);
  if (kind === 'dual') return h('div', {}, h('div', { class: 'row' }, box('150px', '90px', 'Blender', { borderColor: 'var(--acc)' }), box('150px', '90px', 'Polycamp lesson | quests')), h('div', { class: 'faint', style: { fontSize: '.8rem', marginTop: '4px' } }, 'Dual monitor'));
  return h('div', {}, h('div', { style: { position: 'relative', width: '230px', height: '90px', border: '2px solid var(--line2)', borderRadius: '6px', background: 'var(--bg2)', display: 'grid', placeItems: 'center', fontSize: '.7rem', color: 'var(--dim)' } }, 'Blender',
    h('div', { style: { position: 'absolute', left: 0, right: 0, bottom: 0, height: '26px', background: 'color-mix(in srgb, var(--acc) 30%, var(--panel))', display: 'grid', placeItems: 'center' } }, 'quest dock / viewport overlay')), h('div', { class: 'faint', style: { fontSize: '.8rem', marginTop: '4px' } }, 'Single monitor'));
}
