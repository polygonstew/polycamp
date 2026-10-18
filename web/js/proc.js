// proc.js - pixel work for the Texture Lab: tileable procedural textures, seamless blending, PBR map derivation.
// Everything works on RGBA ImageData / Float32Array height fields and wraps at the edges so results tile.

const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const smooth = t => t * t * (3 - 2 * t);
const mix = (a, b, t) => a + (b - a) * t;
export const hex2rgb = h => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };

// ---------- deterministic hashing / periodic noise ----------
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
function hash2(x, y, seed) {
  let n = (x * 374761393 + y * 668265263 + seed * 2147483647) | 0;
  n = (n ^ (n >>> 13)) * 1274126177 | 0;
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}
// value noise that repeats every `px` x `py` lattice cells
function pnoise(x, y, px, py, seed) {
  const x0 = Math.floor(x), y0 = Math.floor(y), fx = smooth(x - x0), fy = smooth(y - y0);
  const w = (i, p) => ((i % p) + p) % p;
  const a = hash2(w(x0, px), w(y0, py), seed), b = hash2(w(x0 + 1, px), w(y0, py), seed);
  const c = hash2(w(x0, px), w(y0 + 1, py), seed), d = hash2(w(x0 + 1, px), w(y0 + 1, py), seed);
  return mix(mix(a, b, fx), mix(c, d, fx), fy);
}
function fbm(u, v, base, oct, seed, sx = 1, sy = 1) {      // u,v in 0..1 (tileable)
  let amp = .5, sum = 0, norm = 0, f = base;
  for (let o = 0; o < oct; o++) {
    sum += amp * pnoise(u * f * sx, v * f * sy, f * sx, f * sy, seed + o * 17);
    norm += amp; amp *= .5; f *= 2;
  }
  return sum / norm;
}

// ---------- procedural albedo + height generators ----------
// each: (u, v, o) -> [r,g,b, height]   with o = {A:[r,g,b], B:[r,g,b], scale, seed}
const col = (A, B, t) => [mix(A[0], B[0], t), mix(A[1], B[1], t), mix(A[2], B[2], t)];
const shade = (c, k) => c.map(x => clamp(x * k, 0, 255));

const GEN = {
  noise: (u, v, o) => { const n = fbm(u, v, 3 * o.scale, 5, o.seed); return [...col(o.A, o.B, n), n]; },
  planks: (u, v, o) => {
    const n = Math.max(2, Math.round(5 * o.scale)), pu = u * n, id = Math.floor(pu), f = pu - id;
    const tint = hash2(id, 0, o.seed), off = hash2(id, 1, o.seed);
    const grain = fbm(f * .6 + id * .17, ((v + off) % 1), 4 * o.scale, 4, o.seed + id, .35, 3);
    const rings = .5 + .5 * Math.sin((grain * 14 + f * 3) * Math.PI);
    const gap = Math.min(f, 1 - f) < .018 ? 0 : 1;
    const c = shade(col(o.A, o.B, clamp(.25 + tint * .5 + (rings - .5) * .35)), .85 + .3 * grain);
    return [...c.map(x => x * (gap ? 1 : .25)), gap ? .55 + rings * .12 : 0];
  },
  bricks: (u, v, o) => {
    const rows = Math.max(3, Math.round(8 * o.scale)), cols = Math.max(2, Math.round(4 * o.scale));
    const r = Math.floor(v * rows), pu = u * cols + (r % 2) * .5, c = Math.floor(pu);
    const fu = pu - c, fv = v * rows - r, edge = Math.min(fu, 1 - fu, fv, 1 - fv);
    const tint = hash2(((c % cols) + cols) % cols, r, o.seed), n = fbm(u, v, 24, 3, o.seed + 5);
    const mortar = edge < .07;
    const base = col(o.A, o.B, tint * .8 + n * .2);
    return mortar ? [...col([80, 78, 74], [120, 116, 108], n), 0] : [...shade(base, .9 + n * .25), .7 + n * .3];
  },
  cells: (u, v, o) => {
    const n = Math.max(3, Math.round(7 * o.scale));
    let d1 = 9, d2 = 9, id = 0;
    for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) {
      const cx = Math.floor(u * n) + i, cy = Math.floor(v * n) + j;
      const wx = ((cx % n) + n) % n, wy = ((cy % n) + n) % n;
      const px = cx + hash2(wx, wy, o.seed), py = cy + hash2(wx, wy, o.seed + 7);
      const d = Math.hypot(px - u * n, py - v * n);
      if (d < d1) { d2 = d1; d1 = d; id = hash2(wx, wy, o.seed + 3); } else if (d < d2) d2 = d;
    }
    const e = clamp((d2 - d1) * 3.2), n2 = fbm(u, v, 18, 3, o.seed + 2);
    return [...shade(col(o.A, o.B, id * .8 + n2 * .2), .35 + .65 * smooth(e)), smooth(e) * (.8 + .2 * n2)];
  },
  rust: (u, v, o) => {
    const n = fbm(u, v, 3 * o.scale, 6, o.seed), m = fbm(u, v, 9 * o.scale, 4, o.seed + 9);
    const scratches = pnoise(u * 120, v * 4, 120, 4, o.seed + 4) > .93 ? .5 : 0;
    const t = clamp((n - .35) * 2.4 + (m - .5) * .5);
    const c = col(o.A, o.B, t);
    return [...c.map(x => clamp(x + scratches * 90, 0, 255)), .45 + t * .45];
  },
  shingles: (u, v, o) => {
    const rows = Math.max(3, Math.round(8 * o.scale)), cols = Math.max(3, Math.round(6 * o.scale));
    const r = Math.floor(v * rows), fv = v * rows - r, pu = u * cols + (r % 2) * .5, c = Math.floor(pu), fu = pu - c;
    const round = fv > .62 ? Math.hypot((fu - .5) * 1.1, (fv - .62) * 1.8) > .55 : false;
    const tint = hash2(((c % cols) + cols) % cols, r, o.seed), n = fbm(u, v, 20, 3, o.seed + 1);
    const edge = Math.min(fu, 1 - fu) < .04 || fv < .03;
    const dark = round || edge ? .4 : 1;
    return [...shade(col(o.A, o.B, tint * .85), (.85 + n * .3) * dark), (round ? .2 : .3 + fv * .7) * (edge ? .7 : 1)];
  },
  grass: (u, v, o) => {
    const n = fbm(u, v, 4 * o.scale, 4, o.seed), blades = pnoise(u * 140, v * 26, 140, 26, o.seed + 1);
    const t = clamp(n * .8 + blades * .4);
    return [...shade(col(o.A, o.B, t), .75 + blades * .5), .4 + t * .6];
  },
};
export const GENERATORS = Object.keys(GEN);

export function generate(kind, W, o) {
  const g = GEN[kind] || GEN.noise;
  const img = new ImageData(W, W), hgt = new Float32Array(W * W);
  const opt = { A: hex2rgb(o.A), B: hex2rgb(o.B), scale: o.scale || 1, seed: o.seed || 1 };
  for (let y = 0; y < W; y++) for (let x = 0; x < W; x++) {
    const r = g((x + .5) / W, (y + .5) / W, opt), i = (y * W + x) * 4;
    img.data[i] = r[0]; img.data[i + 1] = r[1]; img.data[i + 2] = r[2]; img.data[i + 3] = 255;
    hgt[y * W + x] = r[3];
  }
  return { img, hgt };
}

// ---------- seamless ----------
// Blend the image with a copy shifted by half in both axes; the weight is 0 at the borders, so the borders
// come from the shifted copy (whose own borders are in the image middle) and wrap perfectly.
export function seamless(img, k = 2.2) {
  const W = img.width, H = img.height, out = new ImageData(W, H), s = img.data, d = out.data;
  for (let y = 0; y < H; y++) {
    const tv = 1 - Math.abs(2 * (y + .5) / H - 1), y2 = (y + (H >> 1)) % H;
    for (let x = 0; x < W; x++) {
      const tu = 1 - Math.abs(2 * (x + .5) / W - 1), m = smooth(clamp(Math.min(tu, tv) * k)), x2 = (x + (W >> 1)) % W;
      const i = (y * W + x) * 4, j = (y2 * W + x2) * 4;
      for (let c = 0; c < 3; c++) d[i + c] = s[i + c] * m + s[j + c] * (1 - m);
      d[i + 3] = 255;
    }
  }
  return out;
}

// ---------- PBR maps ----------
export function luminance(img) {
  const n = img.width * img.height, L = new Float32Array(n), s = img.data;
  for (let i = 0; i < n; i++) L[i] = (.2126 * s[i * 4] + .7152 * s[i * 4 + 1] + .0722 * s[i * 4 + 2]) / 255;
  return L;
}

export function blur(f, W, H, r) {                       // wrapping box blur, separable
  if (r < 1) return f;
  const tmp = new Float32Array(f.length), out = new Float32Array(f.length), n = 2 * r + 1;
  for (let y = 0; y < H; y++) {
    let sum = 0;
    for (let k = -r; k <= r; k++) sum += f[y * W + ((k + W) % W)];
    for (let x = 0; x < W; x++) {
      tmp[y * W + x] = sum / n;
      sum += f[y * W + ((x + r + 1) % W)] - f[y * W + (((x - r) % W + W) % W)];
    }
  }
  for (let x = 0; x < W; x++) {
    let sum = 0;
    for (let k = -r; k <= r; k++) sum += tmp[((k + H) % H) * W + x];
    for (let y = 0; y < H; y++) {
      out[y * W + x] = sum / n;
      sum += tmp[((y + r + 1) % H) * W + x] - tmp[(((y - r) % H + H) % H) * W + x];
    }
  }
  return out;
}

export function heightMap(L, W, H, { contrast = 1.4, smoothing = 1, invert = false }) {
  let f = blur(L, W, H, smoothing | 0);
  let lo = 1, hi = 0;
  for (const v of f) { if (v < lo) lo = v; if (v > hi) hi = v; }
  const span = Math.max(hi - lo, 1e-4), out = new Float32Array(f.length);
  for (let i = 0; i < f.length; i++) { let v = (f[i] - lo) / span; v = clamp((v - .5) * contrast + .5); out[i] = invert ? 1 - v : v; }
  return out;
}

export function normalMap(hgt, W, H, strength = 3) {          // OpenGL convention (green = up), tileable
  const out = new ImageData(W, H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const xl = (x - 1 + W) % W, xr = (x + 1) % W, yu = (y - 1 + H) % H, yd = (y + 1) % H;
    const dx = (hgt[y * W + xr] - hgt[y * W + xl]) * strength, dy = (hgt[yd * W + x] - hgt[yu * W + x]) * strength;
    let nx = -dx, ny = dy, nz = 1;
    const l = Math.hypot(nx, ny, nz); nx /= l; ny /= l; nz /= l;
    const i = (y * W + x) * 4;
    out.data[i] = (nx * .5 + .5) * 255; out.data[i + 1] = (ny * .5 + .5) * 255; out.data[i + 2] = (nz * .5 + .5) * 255; out.data[i + 3] = 255;
  }
  return out;
}

export function roughnessMap(L, W, H, { base = .65, contrast = .8, invert = false }) {
  const out = new ImageData(W, H);
  for (let i = 0; i < L.length; i++) {
    let v = clamp(base + ((invert ? 1 - L[i] : L[i]) - .5) * contrast);
    out.data[i * 4] = out.data[i * 4 + 1] = out.data[i * 4 + 2] = v * 255; out.data[i * 4 + 3] = 255;
  }
  return out;
}

export function aoMap(hgt, W, H, { radius = 6, strength = 2.5 }) {
  const b = blur(hgt, W, H, radius | 0), out = new ImageData(W, H);
  for (let i = 0; i < hgt.length; i++) {
    const v = clamp(1 - Math.max(0, b[i] - hgt[i]) * strength);
    out.data[i * 4] = out.data[i * 4 + 1] = out.data[i * 4 + 2] = v * 255; out.data[i * 4 + 3] = 255;
  }
  return out;
}

export function grayImage(f, W, H) {
  const out = new ImageData(W, H);
  for (let i = 0; i < f.length; i++) { const v = clamp(f[i]) * 255; out.data[i * 4] = out.data[i * 4 + 1] = out.data[i * 4 + 2] = v; out.data[i * 4 + 3] = 255; }
  return out;
}

// ---------- relief preview: light the albedo with the normal map ----------
export function relief(albedo, normal, lx, ly, ambient = .25) {
  const W = albedo.width, H = albedo.height, out = new ImageData(W, H);
  const L = [lx, ly, .65], ll = Math.hypot(...L); L[0] /= ll; L[1] /= ll; L[2] /= ll;
  for (let i = 0; i < W * H; i++) {
    const nx = normal.data[i * 4] / 127.5 - 1, ny = normal.data[i * 4 + 1] / 127.5 - 1, nz = normal.data[i * 4 + 2] / 127.5 - 1;
    const d = clamp(nx * L[0] + ny * L[1] + nz * L[2]), k = ambient + (1 - ambient) * d * 1.15;
    for (let c = 0; c < 3; c++) out.data[i * 4 + c] = clamp(albedo.data[i * 4 + c] * k, 0, 255);
    out.data[i * 4 + 3] = 255;
  }
  return out;
}

export function toCanvas(img) {
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  c.getContext('2d').putImageData(img, 0, 0);
  return c;
}
export function imageDataOf(src) {
  const c = document.createElement('canvas'); c.width = src.width || src.naturalWidth; c.height = src.height || src.naturalHeight;
  const g = c.getContext('2d'); g.drawImage(src, 0, 0, c.width, c.height);
  return g.getImageData(0, 0, c.width, c.height);
}
