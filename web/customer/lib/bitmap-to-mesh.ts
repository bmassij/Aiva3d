export type Vec3 = [number, number, number];

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
const PAD_MM = 2.2;

function addBox(
  mesh: MeshObject,
  x0: number,
  y0: number,
  z0: number,
  x1: number,
  y1: number,
  z1: number,
) {
  const s = mesh.vertices.length;
  mesh.vertices.push(
    [x0, y0, z0],
    [x1, y0, z0],
    [x1, y1, z0],
    [x0, y1, z0],
    [x0, y0, z1],
    [x1, y0, z1],
    [x1, y1, z1],
    [x0, y1, z1],
  );
  const faces: Array<[number, number, number, number]> = [
    [0, 2, 1, 3],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [1, 2, 6, 5],
    [2, 3, 7, 6],
    [3, 0, 4, 7],
  ];
  for (const [a, b, c, d] of faces) {
    mesh.triangles.push([s + a, s + b, s + c], [s + a, s + c, s + d]);
  }
}

function inHole(x: number, y: number, width: number, height: number, holeR: number): boolean {
  if (holeR <= 0) return false;
  const cx = width / 2;
  const cy = height - holeR - 1.6;
  const dx = x - cx;
  const dy = y - cy;
  return dx * dx + dy * dy <= holeR * holeR;
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
  const innerH = sizeMm - PAD_MM * 2 - holeMm * 0.35;
  let logoW = innerW;
  let logoH = innerW / aspect;
  if (logoH > innerH) {
    logoH = innerH;
    logoW = innerH * aspect;
  }

  const plateW = sizeMm;
  const plateH = sizeMm;
  const ox = (plateW - logoW) / 2;
  const oy = (plateH - logoH) / 2 - holeMm * 0.15;
  const cellW = logoW / bitmap.width;
  const cellH = logoH / bitmap.height;
  const holeR = holeMm / 2;

  const base: MeshObject = {
    name: "base",
    color: options.baseColor ?? "#7ed957",
    vertices: [],
    triangles: [],
  };
  const logo: MeshObject = {
    name: "logo",
    color: options.logoColor ?? "#4a90d9",
    vertices: [],
    triangles: [],
  };

  const step = 0.8;
  for (let y = 0; y < plateH; y += step) {
    let x = 0;
    while (x < plateW) {
      while (x < plateW && inHole(x + step / 2, y + step / 2, plateW, plateH, holeR)) x += step;
      if (x >= plateW) break;
      const start = x;
      while (x < plateW && !inHole(x + step / 2, y + step / 2, plateW, plateH, holeR)) x += step;
      addBox(base, start, y, 0, Math.min(plateW, x), Math.min(plateH, y + step), baseMm);
    }
  }

  let logoCells = 0;
  for (let row = 0; row < bitmap.height; row++) {
    let col = 0;
    while (col < bitmap.width) {
      while (col < bitmap.width && bitmap.cells[row * bitmap.width + col] === 0) col += 1;
      if (col >= bitmap.width) break;
      const start = col;
      while (col < bitmap.width && bitmap.cells[row * bitmap.width + col] === 1) col += 1;
      const x0 = ox + start * cellW;
      const x1 = ox + col * cellW;
      const y0 = oy + (bitmap.height - 1 - row) * cellH;
      const y1 = y0 + cellH;
      const cx = (x0 + x1) / 2;
      const cy = (y0 + y1) / 2;
      if (inHole(cx, cy, plateW, plateH, holeR + 0.6)) continue;
      addBox(logo, x0, y0, baseMm, x1, y1, baseMm + reliefMm);
      logoCells += col - start;
    }
  }

  if (logoCells === 0) {
    throw new Error("Geen logo-pixels gevonden. Zet ‘Kleuren omdraaien’ aan of kies een duidelijker foto.");
  }

  return { widthMm: plateW, heightMm: plateH, objects: [base, logo], logoCells };
}
