// cubby.js - the mascot: an isometric cube with a face on its left side. Moods swap eyes and mouth.
const FACES = {
  happy: '<ellipse cx="12" cy="17" rx="3.2" ry="4" fill="#2a1604"/><ellipse cx="28" cy="17" rx="3.2" ry="4" fill="#2a1604"/><path d="M11 29q9 9 18 0" stroke="#2a1604" stroke-width="2.6" fill="none" stroke-linecap="round"/><circle cx="13" cy="15.5" r="1.1" fill="#fff"/><circle cx="29" cy="15.5" r="1.1" fill="#fff"/>',
  wink: '<path d="M8.5 17q3.5-4 7 0" stroke="#2a1604" stroke-width="2.6" fill="none" stroke-linecap="round"/><ellipse cx="28" cy="17" rx="3.2" ry="4" fill="#2a1604"/><path d="M11 29q9 9 18 0" stroke="#2a1604" stroke-width="2.6" fill="none" stroke-linecap="round"/>',
  smug: '<path d="M8 16h8M24 16h8" stroke="#2a1604" stroke-width="3" stroke-linecap="round"/><path d="M11 30q10 2 18-4" stroke="#2a1604" stroke-width="2.6" fill="none" stroke-linecap="round"/>',
  shock: '<circle cx="12" cy="16" r="4.4" fill="#fff" stroke="#2a1604" stroke-width="1.6"/><circle cx="28" cy="16" r="4.4" fill="#fff" stroke="#2a1604" stroke-width="1.6"/><circle cx="12" cy="16" r="1.7" fill="#2a1604"/><circle cx="28" cy="16" r="1.7" fill="#2a1604"/><ellipse cx="20" cy="31" rx="4" ry="5" fill="#2a1604"/>',
  think: '<ellipse cx="12" cy="17" rx="3" ry="3.6" fill="#2a1604"/><ellipse cx="28" cy="17" rx="3" ry="3.6" fill="#2a1604"/><path d="M13 30h14" stroke="#2a1604" stroke-width="2.6" stroke-linecap="round"/><path d="M5 9q4-3 9-1" stroke="#2a1604" stroke-width="2" fill="none" stroke-linecap="round"/>',
};
export function cubby(mood = 'happy', cls = '') {
  const face = FACES[mood] || FACES.happy;
  return `<svg class="${cls}" viewBox="0 0 100 106" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <ellipse cx="50" cy="100" rx="34" ry="5" fill="rgba(0,0,0,.35)"/>
  <polygon points="50,10 92,32 50,54 8,32" fill="#ffc48a"/>
  <polygon points="8,32 50,54 50,98 8,76" fill="#e8832a"/>
  <polygon points="92,32 50,54 50,98 92,76" fill="#b25a14"/>
  <g transform="translate(9 40) skewY(27.5) scale(1.0 1.0)">${face}</g>
  <polygon points="50,10 92,32 50,54 8,32" fill="none" stroke="#fff3" stroke-width="1"/></svg>`;
}
export const logoSvg = () => `<svg viewBox="0 0 64 64" width="28" height="28"><polygon points="32,6 56,19 32,32 8,19" fill="#ffb067"/><polygon points="8,19 32,32 32,59 8,46" fill="#e8832a"/><polygon points="56,19 32,32 32,59 56,46" fill="#b85a10"/></svg>`;
const QUIPS = {
  done: ['Nice. I felt that in my vertices.', 'Clean work. I would hug you but I have no arms.', 'Look at you, being competent.', 'Another one bites the dust.'],
  idle: ['Take your time. Polygons are patient.', 'Hydrate. Pixels need a healthy artist.', 'Ctrl+S. Do it now. I will wait.'],
};
export const quip = k => { const a = QUIPS[k]; return a[Math.floor(Math.random() * a.length)]; };
