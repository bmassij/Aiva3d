"use client";

import { useEffect, useRef } from "react";
import type { PrintModel } from "@/lib/bitmap-to-mesh";

type ThreeModule = typeof import("three");
type OrbitModule = typeof import("three/examples/jsm/controls/OrbitControls.js");

function hexToInt(hex: string): number {
  return Number.parseInt(hex.replace("#", ""), 16);
}

export function ModelViewer({ model }: { model: PrintModel }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;
    let cleanup = () => {};

    void Promise.all([
      import("three"),
      import("three/examples/jsm/controls/OrbitControls.js"),
    ]).then(([THREE, orbit]: [ThreeModule, OrbitModule]) => {
      if (cancelled || !hostRef.current) return;
      const root = hostRef.current;
      const width = root.clientWidth || 640;
      const height = root.clientHeight || 420;

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(width, height);
      renderer.setClearColor(0x0a0e14, 1);
      root.replaceChildren(renderer.domElement);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 400);
      camera.position.set(28, 22, 42);

      const controls = new orbit.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.target.set(0, 0.6, 0);

      scene.add(new THREE.AmbientLight(0xffffff, 0.55));
      const key = new THREE.DirectionalLight(0xffffff, 1.05);
      key.position.set(30, 40, 20);
      scene.add(key);
      const fill = new THREE.DirectionalLight(0x88aacc, 0.35);
      fill.position.set(-25, 10, -15);
      scene.add(fill);

      const group = new THREE.Group();
      const cx = model.widthMm / 2;
      const cy = model.heightMm / 2;
      for (const obj of model.objects) {
        const positions = new Float32Array(obj.triangles.length * 9);
        let i = 0;
        for (const [a, b, c] of obj.triangles) {
          const va = obj.vertices[a];
          const vb = obj.vertices[b];
          const vc = obj.vertices[c];
          positions.set([va[0] - cx, va[2], cy - va[1]], i);
          positions.set([vb[0] - cx, vb[2], cy - vb[1]], i + 3);
          positions.set([vc[0] - cx, vc[2], cy - vc[1]], i + 6);
          i += 9;
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        geometry.computeVertexNormals();
        const material = new THREE.MeshStandardMaterial({
          color: hexToInt(obj.color),
          roughness: 0.45,
          metalness: 0.05,
        });
        group.add(new THREE.Mesh(geometry, material));
      }
      scene.add(group);

      const grid = new THREE.GridHelper(60, 12, 0x2a3a4f, 0x1c2836);
      grid.position.y = -0.02;
      scene.add(grid);

      const onResize = () => {
        const w = root.clientWidth || width;
        const h = root.clientHeight || height;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      };
      const ro = new ResizeObserver(onResize);

      let frame = 0;
      const tick = () => {
        controls.update();
        renderer.render(scene, camera);
        frame = requestAnimationFrame(tick);
      };
      tick();
      ro.observe(root);

      cleanup = () => {
        cancelAnimationFrame(frame);
        ro.disconnect();
        controls.dispose();
        renderer.dispose();
        group.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.geometry.dispose();
            if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
            else child.material.dispose();
          }
        });
        renderer.domElement.remove();
      };
      if (cancelled) cleanup();
    });

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [model]);

  return <div ref={hostRef} className="viewer" aria-label="3D-model van de logo-hanger" />;
}
