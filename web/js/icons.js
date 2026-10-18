// icons.js - one small set of line icons, drawn on a 24 grid with square caps, plus a glyph for each world.
// Use:  h('span', { class: 'ico', html: icon('cube') })   or   icon('cube', 18)
const P = {
  cube: '<path d="M12 2.5 21 7.5v9L12 21.5 3 16.5v-9z"/><path d="M3 7.5l9 5 9-5M12 12.5v9"/>',
  plug: '<path d="M9 2.5v5M15 2.5v5M6 7.5h12v4a6 6 0 0 1-12 0z"/><path d="M12 17.5v4"/>',
  keys: '<path d="M2.5 6.5h19v11h-19z"/><path d="M6 10h1M10 10h1M14 10h1M18 10h.5M7 14h10"/>',
  tex: '<path d="M3.5 3.5h17v17h-17z"/><path d="M3.5 12 12 3.5M3.5 20.5 20.5 3.5M12 20.5l8.5-8.5"/>',
  uv: '<path d="M9 2.5h6v6h6v6h-6v6H9v-6H3v-6h6z"/><path d="M9 8.5h6M9 14.5h6M9 8.5v6M15 8.5v6"/>',
  photo: '<path d="M3 4.5h18v15H3z"/><path d="m3 16 5-5 4 4 3-3 6 6"/><circle cx="16.5" cy="9" r="1.4"/>',
  star: '<path d="m12 2.8 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.6l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z"/>',
  gear: '<circle cx="12" cy="12" r="3.4"/><path d="M12 2.5v3.2M12 18.3v3.2M2.5 12h3.2M18.3 12h3.2M5.3 5.3l2.3 2.3M16.4 16.4l2.3 2.3M18.7 5.3l-2.3 2.3M7.6 16.4l-2.3 2.3"/>',
  flame: '<path d="M12 2.5c.8 4 5.5 6 5.5 11a5.5 5.5 0 0 1-11 0c0-2 .9-3.4 2.3-4.5.2 1.6 1 2.6 2 3 .4-3.4-.2-5.6 1.2-9.5z"/>',
  gem: '<path d="M6.5 3.5h11l4 5.5-9.5 12L2.5 9z"/><path d="M2.5 9h19M9 3.5 7.6 9l4.4 12 4.4-12L15 3.5"/>',
  check: '<path d="m4 12.5 5.2 5.2L20 6.5"/>',
  cross: '<path d="m5 5 14 14M19 5 5 19"/>',
  circle: '<circle cx="12" cy="12" r="7"/>',
  bulb: '<path d="M9 17.5h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9v2.1h7v-2.1A6 6 0 0 0 12 3z"/>',
  eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/>',
  play: '<path d="M7 4.5v15l12.5-7.5z"/>',
  skull: '<path d="M12 3a8 8 0 0 0-5 14.2V20.5h10v-3.3A8 8 0 0 0 12 3z"/><circle cx="9.3" cy="12" r="1.4"/><circle cx="14.7" cy="12" r="1.4"/><path d="M10 20.5v-2.2M14 20.5v-2.2"/>',
  down: '<path d="M12 3.5v12M6.5 10.5l5.5 5.5 5.5-5.5M4 20.5h16"/>',
  folder: '<path d="M2.5 5.5h7l2 2.5h10v11.5h-19z"/>',
  disk: '<path d="M3.5 3.5h14l3 3v14h-17z"/><path d="M7 3.5v6h8v-6M7 20.5v-6h10v6"/>',
  wand: '<path d="m4 20 11-11 2 2L6 22z"/><path d="M15 3.5v3M13.5 5h3M19.5 8v3M18 9.5h3"/>',
  dice: '<path d="M4 4h16v16H4z"/><circle cx="8.5" cy="8.5" r="1"/><circle cx="15.5" cy="15.5" r="1"/><circle cx="12" cy="12" r="1"/>',
  pencil: '<path d="m4 20 1-5L16.5 3.5l3.5 3.5L9 18.5z"/><path d="m14 6 4 4"/>',
  layers: '<path d="m12 3-10 5 10 5 10-5z"/><path d="m2 13 10 5 10-5M2 17.5l10 5 10-5"/>',
  target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><path d="M12 1.5v4M12 18.5v4M1.5 12h4M18.5 12h4"/>',
  window2: '<path d="M2 5h9v14H2zM13 5h9v14h-9z"/>',
  window1: '<path d="M3 5h18v14H3zM3 15h18"/>',
  popout: '<path d="M10 4.5H4v15h15v-6M13.5 3.5h7v7M20.5 3.5 11 13"/>',
  arrow: '<path d="M3.5 12h17M14.5 6l6 6-6 6"/>',
  back: '<path d="M20.5 12h-17M9.5 6l-6 6 6 6"/>',
  lock: '<path d="M5.5 10.5h13v10h-13zM8 10.5v-3a4 4 0 0 1 8 0v3"/>',
  // scene objects
  MESH: '<path d="M12 3.5 21 19H3z"/><path d="M12 3.5v15.5"/>',
  LIGHT: '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
  CAMERA: '<path d="M3 7.5h14v9H3zM17 11l4-2.5v7L17 13"/>',
  EMPTY: '<path d="M12 3v18M3 12h18"/>',
  CURVE: '<path d="M3 17c4 0 4-10 9-10s5 10 9 10"/>',
  ARMATURE: '<path d="M6 18l4-4M14 10l4-4"/><circle cx="5" cy="19" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="5" r="2"/>',
  FONT: '<path d="M5 5.5h14M12 5.5v13M9 18.5h6"/>',
  SURFACE: '<path d="M3 15c4-8 14-8 18 0z"/>',
  // world glyphs
  power: '<path d="M12 3v9M6.3 6.8a8 8 0 1 0 11.4 0"/>',
  verts: '<path d="M12 5 20 19H4z"/><rect x="10.5" y="3.5" width="3" height="3"/><rect x="2.5" y="17.5" width="3" height="3"/><rect x="18.5" y="17.5" width="3" height="3"/>',
  stack: '<path d="m12 3-9.5 4.5L12 12l9.5-4.5z"/><path d="m2.5 12 9.5 4.5 9.5-4.5M2.5 16.5 12 21l9.5-4.5"/>',
  cabin: '<path d="m2.5 12 9.5-8 9.5 8M5 10.5V20h14v-9.5M10 20v-5.5h4V20"/>',
  ball: '<circle cx="12" cy="12" r="9"/><path d="M6.5 8.2A6.2 6.2 0 0 1 12 5.2M21 12a9 9 0 0 1-9 9"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v3.2M12 18.8V22M2 12h3.2M18.8 12H22M4.9 4.9l2.3 2.3M16.8 16.8l2.3 2.3M19.1 4.9l-2.3 2.3M7.2 16.8l-2.3 2.3"/>',
  key: '<path d="m12 3.5 8 8.5-8 8.5-8-8.5z"/><path d="M1.5 12H4M20 12h2.5"/>',
  nodes: '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><path d="M7 6h10M6.2 7.8l4.8 8.4M17.8 7.8l-4.8 8.4"/>',
  crown: '<path d="M3 18.5h18l-1.8-10-5 5L12 5.5l-2.2 8-5-5z"/>',
};

export function icon(name, size = 18, cls = '') {
  const body = P[name] || P.circle;
  return `<svg class="ico ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true">${body}</svg>`;
}

const WORLD = { boot: 'power', mesh: 'verts', modifiers: 'stack', environment: 'cabin', materials: 'ball', uv: 'uv', light: 'sun',
  animation: 'key', nodes: 'nodes', guild: 'crown' };
export const worldGlyph = (id, size = 30) => icon(WORLD[id] || 'cube', size, 'wg');
export const objIcon = (type, size = 14) => icon(P[type] ? type : 'EMPTY', size);
