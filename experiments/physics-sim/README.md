# physics-sim

Browser-based physics sandbox using **Rapier3D** (Rust → WASM) and **Three.js**. Targets joint-based rigid body dynamics and granular material simulation (dirt, gravel, sand) deployable to GitHub Pages.

## Stack

| Layer | Library |
|---|---|
| Physics | `@dimforge/rapier3d-compat` (Rapier3D, WASM) |
| Rendering | Three.js |
| Build | Vite + TypeScript |
| Deploy | GitHub Pages (`gh-pages` branch) |

## Getting started

```bash
cd experiments/physics-sim
npm install
npm run dev        # → http://localhost:5173
```

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server with HMR |
| `npm run build` | Type-check + production build → `dist/` |
| `npm run preview` | Serve `dist/` locally |
| `npm run deploy` | Build and push to `gh-pages` branch |

## Source layout

```
src/
  main.ts      Entry point — init WASM, wire up scene + physics, run loop
  scene.ts     Three.js renderer, camera, shadow-casting lights, resize
  physics.ts   Rapier world creation and per-frame step
  objects.ts   Spawn helpers (ground, rigid boxes, granular pile) + syncMeshes
```

## Planned milestones

- [ ] Revolute + prismatic joints for a digger arm
- [ ] `InstancedMesh` rendering for 1 000+ grain counts
- [ ] Terrain heightmap with scoop-deformation
- [ ] WebGPU PBD layer for large-scale sand (100 k+ grains)
- [ ] GitHub Actions CI → automatic deploy on push to `main`
