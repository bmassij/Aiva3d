import type { MeshObject, PrintModel } from "./bitmap-to-mesh";

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[i] = c >>> 0;
  }
  return table;
})();

function crc32(data: Uint8Array): number {
  let c = 0xffffffff;
  for (const b of data) c = CRC_TABLE[(c ^ b) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function encodeUtf8(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function hexToDisplay(hex: string): string {
  const v = hex.replace("#", "");
  const full = v.length === 3 ? v.split("").map((c) => c + c).join("") : v;
  return `#${full.toUpperCase()}FF`;
}

function meshXml(mesh: MeshObject): string {
  const verts = mesh.vertices
    .map(([x, y, z]) => `<vertex x="${x.toFixed(3)}" y="${y.toFixed(3)}" z="${z.toFixed(3)}"/>`)
    .join("");
  const tris = mesh.triangles
    .map(([a, b, c]) => `<triangle v1="${a}" v2="${b}" v3="${c}"/>`)
    .join("");
  return `<mesh><vertices>${verts}</vertices><triangles>${tris}</triangles></mesh>`;
}

function modelXml(model: PrintModel): string {
  const materials = model.objects
    .map((obj) => `<base name="${obj.name}" displaycolor="${hexToDisplay(obj.color)}"/>`)
    .join("");
  const objects = model.objects
    .map(
      (obj, i) =>
        `<object id="${i + 2}" name="${obj.name}" type="model" pid="1" pindex="${i}">${meshXml(obj)}</object>`,
    )
    .join("");
  const items = model.objects.map((_, i) => `<item objectid="${i + 2}"/>`).join("");
  return [
    `<?xml version="1.0" encoding="UTF-8"?>`,
    `<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">`,
    `<metadata name="Application">Aiva3D</metadata>`,
    `<resources>`,
    `<basematerials id="1">${materials}</basematerials>`,
    objects,
    `</resources>`,
    `<build>${items}</build>`,
    `</model>`,
  ].join("");
}

function zipStore(files: Array<{ name: string; data: Uint8Array }>): Uint8Array {
  const parts: Uint8Array[] = [];
  const central: Uint8Array[] = [];
  let offset = 0;

  for (const file of files) {
    const name = encodeUtf8(file.name);
    const crc = crc32(file.data);
    const local = new Uint8Array(30 + name.length);
    const lv = new DataView(local.buffer);
    lv.setUint32(0, 0x04034b50, true);
    lv.setUint16(4, 20, true);
    lv.setUint16(8, 0, true);
    lv.setUint16(10, 0, true);
    lv.setUint16(12, 0, true);
    lv.setUint32(14, crc, true);
    lv.setUint32(18, file.data.length, true);
    lv.setUint32(22, file.data.length, true);
    lv.setUint16(26, name.length, true);
    local.set(name, 30);
    parts.push(local, file.data);

    const dir = new Uint8Array(46 + name.length);
    const dv = new DataView(dir.buffer);
    dv.setUint32(0, 0x02014b50, true);
    dv.setUint16(4, 20, true);
    dv.setUint16(6, 20, true);
    dv.setUint32(16, crc, true);
    dv.setUint32(20, file.data.length, true);
    dv.setUint32(24, file.data.length, true);
    dv.setUint16(28, name.length, true);
    dv.setUint32(42, offset, true);
    dir.set(name, 46);
    central.push(dir);
    offset += local.length + file.data.length;
  }

  const centralSize = central.reduce((n, c) => n + c.length, 0);
  const end = new Uint8Array(22);
  const ev = new DataView(end.buffer);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(8, files.length, true);
  ev.setUint16(10, files.length, true);
  ev.setUint32(12, centralSize, true);
  ev.setUint32(16, offset, true);

  const total = offset + centralSize + end.length;
  const out = new Uint8Array(total);
  let o = 0;
  for (const p of parts) {
    out.set(p, o);
    o += p.length;
  }
  for (const c of central) {
    out.set(c, o);
    o += c.length;
  }
  out.set(end, o);
  return out;
}

export function write3mf(model: PrintModel): Uint8Array {
  return zipStore([
    {
      name: "[Content_Types].xml",
      data: encodeUtf8(
        `<?xml version="1.0" encoding="UTF-8"?>` +
          `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
          `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
          `<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>` +
          `</Types>`,
      ),
    },
    {
      name: "_rels/.rels",
      data: encodeUtf8(
        `<?xml version="1.0" encoding="UTF-8"?>` +
          `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
          `<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>` +
          `</Relationships>`,
      ),
    },
    {
      name: "3D/3dmodel.model",
      data: encodeUtf8(modelXml(model)),
    },
  ]);
}
