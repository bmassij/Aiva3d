export type Vec3 = [number, number, number];
export type Vec2 = [number, number];

export type MeshObject = {
  name: string;
  color: string;
  vertices: Vec3[];
  triangles: [number, number, number][];
};

export type PrintModel = {
  widthMm: number;
  heightMm: number;
  objects: MeshObject[];
  logoCells: number;
};

export type BuildOptions = {
  sizeMm?: number;
  baseMm?: number;
  reliefMm?: number;
  holeMm?: number;
  baseColor?: string;
  logoColor?: string;
};

const DEFAULT_SIZE = 40;
const DEFAULT_BASE = 2;
const DEFAULT_RELIEF = 1.2;
const DEFAULT_HOLE = 4.2;
const PAD_MM = 2.4;
const CORNER_R = 2.4;

function signedArea(poly: Vec2[]): number {
  let a = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x1, y1] = poly[i];
    const [x2, y2] = poly[(i + 1) % poly.length];
    a += x1 * y2 - x2 * y1;
  }
  return a / 2;
}

function ensureCCW(poly: Vec2[]): Vec2[] {
  return signedArea(poly) < 0 ? [...poly].reverse() : poly;
}

function ensureCW(poly: Vec2[]): Vec2[] {
  return signedArea(poly) > 0 ? [...poly].reverse() : poly;
}

function pointInPoly(x: number, y: number, poly: Vec2[]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    const hit = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi || 1e-9) + xi;
    if (hit) inside = !inside;
  }
  return inside;
}

function rdp(points: Vec2[], epsilon: number): Vec2[] {
  if (points.length < 3) return points;
  const first = points[0];
  const last = points[points.length - 1];
  let maxD = 0;
  let idx = 0;
  for (let i = 1; i < points.length - 1; i++) {
    const d = perpDist(points[i], first, last);
    if (d > maxD) {
      maxD = d;
      idx = i;
    }
  }
  if (maxD > epsilon) {
    const left = rdp(points.slice(0, idx + 1), epsilon);
    const right = rdp(points.slice(idx), epsilon);
    return [...left.slice(0, -1), ...right];
  }
  return [first, last];
}

function perpDist(p: Vec2, a: Vec2, b: Vec2): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy) || 1;
  return Math.abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / len;
}

function chaikin(points: Vec2[], closed = true): Vec2[] {
  const out: Vec2[] = [];
  const n = points.length;
  for (let i = 0; i < n; i++) {
    const a = points[i];
    const b = points[(i + 1) % n];
    if (!closed && i === n - 1) break;
    out.push([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]]);
    out.push([0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]);
  }
  return out;
}

function smoothLoop(points: Vec2[]): Vec2[] {
  let loop = points;
  if (loop.length > 4) loop = rdp(loop, 0.85);
  if (loop.length > 6) loop = chaikin(loop, true);
  if (loop.length > 8) loop = rdp(loop, 0.35);
  if (loop.length < 3) return points;
  return loop;
}

function at(
  cells: Uint8Array,
  width: number,
  height: number,
  x: number,
  y: number,
): number {
  if (x < 0 || y < 0 || x >= width || y >= height) return 0;
  return cells[y * width + x];
}

/** Moore-neighbor outer/inner contours in pixel space (x right, y down). */
function extractLoops(cells: Uint8Array, width: number, height: number): Vec2[][] {
  const seen = new Uint8Array(width * height);
  const loops: Vec2[][] = [];
  const dirs: Vec2[] = [
    [1, 0],
    [1, 1],
    [0, 1],
    [-1, 1],
    [-1, 0],
    [-1, -1],
    [0, -1],
    [1, -1],
  ];

  const isBorder = (x: number, y: number) => {
    if (!at(cells, width, height, x, y)) return false;
    return (
      !at(cells, width, height, x - 1, y) ||
      !at(cells, width, height, x + 1, y) ||
      !at(cells, width, height, x, y - 1) ||
      !at(cells, width, height, x, y + 1)
    );
  };

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!isBorder(x, y) || seen[y * width + x]) continue;
      const start: Vec2 = [x, y];
      const path: Vec2[] = [];
      let cx = x;
      let cy = y;
      let dir = 4;
      let guard = 0;
      do {
        seen[cy * width + cx] = 1;
        path.push([cx + 0.5, cy + 0.5]);
        let found = false;
        for (let k = 0; k < 8; k++) {
          const nd = (dir + 6 + k) % 8;
          const nx = cx + dirs[nd][0];
          const ny = cy + dirs[nd][1];
          if (isBorder(nx, ny)) {
            cx = nx;
            cy = ny;
            dir = nd;
            found = true;
            break;
          }
        }
        if (!found) break;
        guard += 1;
      } while ((cx !== start[0] || cy !== start[1]) && guard < width * height);

      if (path.length >= 8) loops.push(path);
    }
  }
  return loops;
}

function cross(a: Vec2, b: Vec2, c: Vec2): number {
  return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

function pointInTri(p: Vec2, a: Vec2, b: Vec2, c: Vec2): boolean {
  const c1 = cross(a, b, p);
  const c2 = cross(b, c, p);
  const c3 = cross(c, a, p);
  return (c1 >= 0 && c2 >= 0 && c3 >= 0) || (c1 <= 0 && c2 <= 0 && c3 <= 0);
}

function earClip(poly: Vec2[]): Array<[number, number, number]> {
  const n0 = poly.length;
  if (n0 < 3) return [];
  const verts = poly.map((p, i) => i);
  const tris: Array<[number, number, number]> = [];
  let guard = 0;
  while (verts.length > 3 && guard < n0 * n0) {
    guard += 1;
    let clipped = false;
    for (let i = 0; i < verts.length; i++) {
      const i0 = verts[(i + verts.length - 1) % verts.length];
      const i1 = verts[i];
      const i2 = verts[(i + 1) % verts.length];
      const a = poly[i0];
      const b = poly[i1];
      const c = poly[i2];
      if (cross(a, b, c) <= 0) continue;
      let empty = true;
      for (const iv of verts) {
        if (iv === i0 || iv === i1 || iv === i2) continue;
        if (pointInTri(poly[iv], a, b, c)) {
          empty = false;
          break;
        }
      }
      if (!empty) continue;
      tris.push([i0, i1, i2]);
      verts.splice(i, 1);
      clipped = true;
      break;
    }
    if (!clipped) break;
  }
  if (verts.length === 3) tris.push([verts[0], verts[1], verts[2]]);
  return tris;
}

function insertHole(outer: Vec2[], hole: Vec2[]): Vec2[] {
  let oi = 0;
  let hi = 0;
  let best = Infinity;
  for (let i = 0; i < outer.length; i++) {
    for (let j = 0; j < hole.length; j++) {
      const dx = outer[i][0] - hole[j][0];
      const dy = outer[i][1] - hole[j][1];
      const d = dx * dx + dy * dy;
      if (d < best) {
        best = d;
        oi = i;
        hi = j;
      }
    }
  }
  const rotated = [...hole.slice(hi), ...hole.slice(0, hi), hole[hi]];
  return [...outer.slice(0, oi + 1), ...rotated, outer[oi], ...outer.slice(oi + 1)];
}

function addVertex(mesh: MeshObject, v: Vec3): number {
  mesh.vertices.push(v);
  return mesh.vertices.length - 1;
}

function extrudeLoops(mesh: MeshObject, outers: Vec2[][], holesFor: Vec2[][][], z0: number, z1: number) {
  for (let i = 0; i < outers.length; i++) {
    const outer = ensureCCW(outers[i]);
    const holes = (holesFor[i] || []).map(ensureCW);
    let flat = outer;
    for (const hole of holes) flat = insertHole(flat, hole);
    const caps = earClip(flat);
    if (caps.length === 0) continue;

    const bottom = flat.map((p) => addVertex(mesh, [p[0], p[1], z0]));
    const top = flat.map((p) => addVertex(mesh, [p[0], p[1], z1]));
    for (const [a, b, c] of caps) {
      mesh.triangles.push([bottom[a], bottom[c], bottom[b]]);
      mesh.triangles.push([top[a], top[b], top[c]]);
    }

    const rings = [outer, ...holes];
    for (const ring of rings) {
      for (let k = 0; k < ring.length; k++) {
        const a = ring[k];
        const b = ring[(k + 1) % ring.length];
        const a0 = addVertex(mesh, [a[0], a[1], z0]);
        const b0 = addVertex(mesh, [b[0], b[1], z0]);
        const b1 = addVertex(mesh, [b[0], b[1], z1]);
        const a1 = addVertex(mesh, [a[0], a[1], z1]);
        mesh.triangles.push([a0, b0, b1], [a0, b1, a1]);
      }
    }
  }
}

function roundedRect(w: number, h: number, r: number): Vec2[] {
  const rad = Math.min(r, w / 2 - 0.2, h / 2 - 0.2);
  const steps = 10;
  const pts: Vec2[] = [];
  const corners: Array<[number, number, number, number]> = [
    [w - rad, rad, -Math.PI / 2, 0],
    [w - rad, h - rad, 0, Math.PI / 2],
    [rad, h - rad, Math.PI / 2, Math.PI],
    [rad, rad, Math.PI, (3 * Math.PI) / 2],
  ];
  for (const [cx, cy, a0, a1] of corners) {
    for (let i = 0; i <= steps; i++) {
      const t = a0 + ((a1 - a0) * i) / steps;
      pts.push([cx + rad * Math.cos(t), cy + rad * Math.sin(t)]);
    }
  }
  return pts;
}

function circle(cx: number, cy: number, r: number, segs = 48): Vec2[] {
  const pts: Vec2[] = [];
  for (let i = 0; i < segs; i++) {
    const t = (i / segs) * Math.PI * 2;
    pts.push([cx + r * Math.cos(t), cy + r * Math.sin(t)]);
  }
  return pts;
}

function mapLoop(
  loop: Vec2[],
  bitmapW: number,
  bitmapH: number,
  ox: number,
  oy: number,
  cellW: number,
  cellH: number,
): Vec2[] {
  return loop.map(([x, y]) => [ox + x * cellW, oy + (bitmapH - y) * cellH]);
}

function groupOutersAndHoles(loops: Vec2[][]): { outers: Vec2[][]; holes: Vec2[][][] } {
  const areas = loops.map((loop, i) => ({ i, area: Math.abs(signedArea(loop)), loop }));
  areas.sort((a, b) => b.area - a.area);
  const outers: Vec2[][] = [];
  const holes: Vec2[][][] = [];
  const parent: number[] = [];

  for (const item of areas) {
    let p = -1;
    const [x, y] = item.loop[0];
    for (let oi = 0; oi < outers.length; oi++) {
      if (pointInPoly(x, y, outers[oi])) p = oi;
    }
    if (p === -1) {
      parent.push(outers.length);
      holes.push([]);
      outers.push(item.loop);
    } else {
      holes[p].push(item.loop);
    }
  }
  return { outers, holes };
}

export function buildPrintModel(
  bitmap: { width: number; height: number; cells: Uint8Array },
  options: BuildOptions = {},
): PrintModel {
  const sizeMm = Math.min(40, Math.max(20, options.sizeMm ?? DEFAULT_SIZE));
  const baseMm = options.baseMm ?? DEFAULT_BASE;
  const reliefMm = options.reliefMm ?? DEFAULT_RELIEF;
  const holeMm = options.holeMm ?? DEFAULT_HOLE;
  const aspect = bitmap.width / bitmap.height;
  const innerW = sizeMm - PAD_MM * 2;
  const innerH = sizeMm - PAD_MM * 2 - holeMm * 0.45;
  let logoW = innerW;
  let logoH = innerW / aspect;
  if (logoH > innerH) {
    logoH = innerH;
    logoW = innerH * aspect;
  }

  const plateW = sizeMm;
  const plateH = sizeMm;
  const ox = (plateW - logoW) / 2;
  const oy = (plateH - logoH) / 2 - holeMm * 0.2;
  const cellW = logoW / bitmap.width;
  const cellH = logoH / bitmap.height;
  const holeR = holeMm / 2;
  const holeCx = plateW / 2;
  const holeCy = plateH - holeR - 1.5;

  const logoCells = bitmap.cells.reduce((n, v) => n + v, 0);
  if (logoCells === 0) {
    throw new Error("Geen logo-pixels gevonden. Zet ‘Kleuren omdraaien’ aan of kies een duidelijker foto.");
  }

  const rawLoops = extractLoops(bitmap.cells, bitmap.width, bitmap.height)
    .map(smoothLoop)
    .filter((loop) => loop.length >= 3)
    .map((loop) => mapLoop(loop, bitmap.width, bitmap.height, ox, oy, cellW, cellH))
    .filter((loop) => !pointInPoly(loop[0][0], loop[0][1], circle(holeCx, holeCy, holeR + 0.8)));

  const grouped = groupOutersAndHoles(rawLoops);

  const base: MeshObject = {
    name: "base",
    color: options.baseColor ?? "#f3f1eb",
    vertices: [],
    triangles: [],
  };
  const logo: MeshObject = {
    name: "logo",
    color: options.logoColor ?? "#0e3d3a",
    vertices: [],
    triangles: [],
  };

  extrudeLoops(base, [roundedRect(plateW, plateH, CORNER_R)], [[circle(holeCx, holeCy, holeR)]], 0, baseMm);

  if (grouped.outers.length === 0) {
    throw new Error("Logo-contour kon niet worden getrokken. Gebruik een scherper logo.");
  }
  extrudeLoops(logo, grouped.outers, grouped.holes, baseMm, baseMm + reliefMm);

  return { widthMm: plateW, heightMm: plateH, objects: [base, logo], logoCells };
}
