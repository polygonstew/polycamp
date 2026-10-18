// api.js - fetch helper, shared state S, a tiny event bus, and the live Server-Sent Events stream.
export const S = {
  profile: null, settings: {}, bridge: { connected: false, clients: [] }, live: { hud: null, scene: null },
  overview: null, lan: '', active: null, version: '',
};
const listeners = {};
export const on = (ev, fn) => { (listeners[ev] ||= new Set()).add(fn); return () => listeners[ev].delete(fn); };
export const emit = (ev, d) => (listeners[ev] ? [...listeners[ev]] : []).forEach(fn => { try { fn(d); } catch (e) { console.error(ev, e); } });

export async function api(path, body) {
  const opt = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  const r = await fetch('/api/' + path, opt);
  const j = await r.json().catch(() => ({ error: 'bad response' }));
  if (!r.ok && !j.error) j.error = 'HTTP ' + r.status;
  return j;
}

export async function loadState() {
  const s = await api('state');
  S.profile = s.profile; S.settings = s.settings; S.bridge = s.bridge; S.lan = s.lan; S.active = s.active; S.version = s.version;
  if (s.live) S.live = s.live;
  applySettings();
  emit('profile'); emit('live');
  return s;
}

export function applySettings() {
  const st = S.settings;
  document.documentElement.dataset.theme = st.theme || 'ember';
  document.documentElement.style.setProperty('--scale', st.text_scale || 1);
  const single = layoutMode() === 'single';
  document.body.classList.toggle('single', single);
}

export function layoutMode() {
  const l = S.settings.layout || 'auto';
  return l === 'auto' ? (innerWidth >= 1250 ? 'dual' : 'single') : l;
}

export async function saveSetting(patch) {
  S.settings = await api('settings', patch);
  applySettings();
  emit('settings');
}

// which Blender generation the lesson text should show (3 / 4 / 5)
export function blenderMajor() {
  const s = S.settings.blender_major;
  if (s && s !== 'auto') return +s;
  const c = (S.bridge.clients || []).find(x => x.alive);
  return c && c.bver ? c.bver[0] : 4;
}

export function connectEvents() {
  const es = new EventSource('/api/events');
  es.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.type === 'live') { S.live = { hud: m.hud, scene: m.scene }; S.bridge = m.bridge; }
    if (m.type === 'profile') S.profile = m.profile;
    emit(m.type, m);
    if (m.type === 'live') emit('live', m);
  };
  es.onerror = () => { S.bridge = { connected: false, clients: [] }; emit('live'); };
  return es;
}
