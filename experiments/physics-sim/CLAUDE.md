# CLAUDE.md — physics-sim

Self-contained Vite + TypeScript experiment inside `experiments/physics-sim/`.
Part of the `digger-sim` monorepo; other experiments live at the same level.

## Commands

```bash
npm install          # install deps (node_modules stays local)
npm run dev          # dev server → http://localhost:5173
npm run build        # tsc type-check + vite build → dist/
npm run preview      # serve dist/ to verify production build
npm run deploy       # build + gh-pages push (needs gh-pages package)
```

## Architecture

| File | Responsibility |
|---|---|
| `src/main.ts` | `await RAPIER.init()`, create world + scene, push objects, run `requestAnimationFrame` loop |
| `src/scene.ts` | `WebGLRenderer`, `PerspectiveCamera`, shadow-casting lights, window resize handler |
| `src/physics.ts` | `RAPIER.World` construction and `world.step()` wrapper |
| `src/objects.ts` | `PhysicsObject` type, spawn helpers, `syncMeshes()` |

## Key invariants

- **RAPIER.init() must resolve before any Rapier API call.** The `-compat` package handles WASM loading internally.
- **`syncMeshes(objects)`** runs every frame after `world.step()` to copy Rapier translation + quaternion into Three.js meshes.
- **`vite.config.ts` sets `base: './'`** so the built assets resolve correctly whether served from a repo subdirectory or root on GitHub Pages.
- **`optimizeDeps.exclude`** for rapier prevents Vite from pre-bundling the WASM module, which would break it.

## Patterns

### Add a new physics body type

```typescript
// 1. Describe + create body
const body = world.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(x, y, z))

// 2. Attach collider
world.createCollider(RAPIER.ColliderDesc.ball(r).setFriction(0.7), body)

// 3. Visual mesh
const mesh = new THREE.Mesh(geo, mat)
scene.add(mesh)

// 4. Register for sync
objects.push({ mesh, body })
```

### Add a joint (example: revolute hinge)

```typescript
const axis   = { x: 0, y: 0, z: 1 }
const anchor1 = { x: 0, y: -0.5, z: 0 }  // local to bodyA
const anchor2 = { x: 0, y:  0.5, z: 0 }  // local to bodyB
const joint = RAPIER.JointData.revolute(anchor1, anchor2, axis)
world.createImpulseJoint(joint, bodyA, bodyB, true)
```

### Scale up granular particles

Replace per-mesh spheres in `spawnGranularPile` with `THREE.InstancedMesh`:
```typescript
const im = new THREE.InstancedMesh(geo, mat, count)
scene.add(im)
// in syncMeshes: im.setMatrixAt(i, matrix); im.instanceMatrix.needsUpdate = true
```

## Deploy to GitHub Pages

Option A — manual:
```bash
npm run deploy      # uses gh-pages npm package
```

Option B — GitHub Actions: add `.github/workflows/deploy.yml` targeting
`experiments/physics-sim` with `actions/upload-pages-artifact`.
