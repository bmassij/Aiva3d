export type LogoBitmap = {
  width: number;
  height: number;
  /** 1 = logo relief, 0 = empty */
  cells: Uint8Array;
  threshold: number;
};

const MAX_GRID = 96;

function otsuThreshold(hist: Uint32Array, total: number): number {
  let sum = 0;
  for (let i = 0; i < 256; i++) sum += i * hist[i];
  let sumB = 0;
  let wB = 0;
  let max = 0;
  let threshold = 128;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (wB === 0) continue;
    const wF = total - wB;
    if (wF === 0) break;
    sumB += t * hist[t];
    const mB = sumB / wB;
    const mF = (sum - sumB) / wF;
    const between = wB * wF * (mB - mF) * (mB - mF);
    if (between > max) {
      max = between;
      threshold = t;
    }
  }
  return threshold;
}

export async function fileToImageData(source: File | string): Promise<ImageData> {
  const url = typeof source === "string" ? source : URL.createObjectURL(source);
  try {
    const img = await loadImage(url);
    const side = Math.max(img.naturalWidth || img.width, img.naturalHeight || img.height);
    const scale = Math.min(1, 512 / side);
    const width = Math.max(1, Math.round((img.naturalWidth || img.width) * scale));
    const height = Math.max(1, Math.round((img.naturalHeight || img.height) * scale));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) throw new Error("Canvas niet beschikbaar.");
    ctx.drawImage(img, 0, 0, width, height);
    return ctx.getImageData(0, 0, width, height);
  } finally {
    if (typeof source !== "string") URL.revokeObjectURL(url);
  }
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Afbeelding kon niet worden gelezen."));
    img.src = url;
  });
}

export function imageDataToBitmap(
  image: ImageData,
  options: { invert?: boolean; threshold?: number } = {},
): LogoBitmap {
  const scale = MAX_GRID / Math.max(image.width, image.height);
  const width = Math.max(8, Math.round(image.width * scale));
  const height = Math.max(8, Math.round(image.height * scale));
  const lum = new Uint8Array(width * height);
  const hist = new Uint32Array(256);
  let opaque = 0;

  for (let y = 0; y < height; y++) {
    const sy = Math.min(image.height - 1, Math.floor((y + 0.5) * (image.height / height)));
    for (let x = 0; x < width; x++) {
      const sx = Math.min(image.width - 1, Math.floor((x + 0.5) * (image.width / width)));
      const i = (sy * image.width + sx) * 4;
      const a = image.data[i + 3];
      const l = Math.round(
        0.2126 * image.data[i] + 0.7152 * image.data[i + 1] + 0.0722 * image.data[i + 2],
      );
      const value = a < 16 ? 255 : l;
      lum[y * width + x] = value;
      if (a >= 16) {
        hist[value] += 1;
        opaque += 1;
      }
    }
  }

  const cut = options.threshold ?? otsuThreshold(hist, Math.max(1, opaque));
  const invert = options.invert ?? false;
  const cells = new Uint8Array(width * height);
  for (let i = 0; i < lum.length; i++) {
    const dark = lum[i] < cut;
    cells[i] = (invert ? !dark : dark) ? 1 : 0;
  }

  return { width, height, cells, threshold: cut };
}

export function bitmapToPreviewUrl(bitmap: LogoBitmap, logoHex: string, baseHex: string): string {
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  const img = ctx.createImageData(bitmap.width, bitmap.height);
  const logo = hexToRgb(logoHex);
  const base = hexToRgb(baseHex);
  for (let i = 0; i < bitmap.cells.length; i++) {
    const on = bitmap.cells[i] === 1;
    const o = i * 4;
    const c = on ? logo : base;
    img.data[o] = c.r;
    img.data[o + 1] = c.g;
    img.data[o + 2] = c.b;
    img.data[o + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL("image/png");
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const v = hex.replace("#", "");
  const n = Number.parseInt(v.length === 3 ? v.split("").map((c) => c + c).join("") : v, 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}
