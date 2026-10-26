import type { MeshObject, PrintModel, Vec3 } from "./bitmap-to-mesh";

function normal(a: Vec3, b: Vec3, c: Vec3): Vec3 {
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];
  const nx = uy * vz - uz * vy;
  const ny = uz * vx - ux * vz;
  const nz = ux * vy - uy * vx;
  const len = Math.hypot(nx, ny, nz) || 1;
  return [nx / len, ny / len, nz / len];
}

function writeMesh(view: DataView, offset: number, mesh: MeshObject): number {
  let o = offset;
  for (const [ia, ib, ic] of mesh.triangles) {
    const a = mesh.vertices[ia];
    const b = mesh.vertices[ib];
    const c = mesh.vertices[ic];
    const n = normal(a, b, c);
    for (const v of [n, a, b, c]) {
      view.setFloat32(o, v[0], true);
      view.setFloat32(o + 4, v[1], true);
      view.setFloat32(o + 8, v[2], true);
      o += 12;
    }
    view.setUint16(o, 0, true);
    o += 2;
  }
  return o;
}

export function writeBinaryStl(model: PrintModel): Uint8Array {
  const triangles = model.objects.reduce((n, obj) => n + obj.triangles.length, 0);
  const bytes = 84 + triangles * 50;
  const buffer = new ArrayBuffer(bytes);
  const view = new DataView(buffer);
  const header = "Aiva3D company logo hanger";
  for (let i = 0; i < 80; i++) view.setUint8(i, i < header.length ? header.charCodeAt(i) : 0);
  view.setUint32(80, triangles, true);
  let offset = 84;
  for (const mesh of model.objects) offset = writeMesh(view, offset, mesh);
  return new Uint8Array(buffer);
}
