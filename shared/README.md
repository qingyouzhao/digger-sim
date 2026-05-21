# shared/

Engine-agnostic types and pure logic shared across all frontends in this repo.
No `package.json`, no dependencies — just TypeScript source imported via the
`@shared` Vite alias configured in each app's `vite.config`.

## What lives here

### `types.ts` — wire types

Plain, serializable objects that cross the boundary between simulation and renderer.

| Type | Description |
|---|---|
| `ControlSignal` | Four normalized actuator values `[-1, 1]`: turret, boom, stick, bucket |
| `DiggerState` | Joint angles (radians) read back from the sim each frame + elapsed time |
| `SandParticle` | Per-particle position and velocity as plain number tuples |
| `SandState` | Full particle array + elapsed time |

### `control.ts` — input → signal

Pure functions that map raw input to a `ControlSignal`. No DOM side-effects,
no physics dependencies — pass in whatever key/gamepad state you have.

| Export | Description |
|---|---|
| `keyboardToSignal(keys)` | `Set<string>` of held keys → `ControlSignal` |
| `zeroSignal()` | Returns `{ turret:0, boom:0, stick:0, bucket:0 }` |
| `KeyState` | Type alias for `Set<string>` |

## How the abstraction works

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  keyboard / gamepad / programmatic                           │
│        │                                                     │
│        ▼                                                     │
│  keyboardToSignal(keys)  ──────────────────────────────────► ControlSignal
│                                                     │        │
│                                                     ▼        │
│                                           DiggerSimulation   │
│                                           .step(dt, signal)  │
│                                                     │        │
│                                                     ▼        │
│                                           DiggerState / geom data
│                                                     │        │
│                                                     ▼        │
│                                           Renderer sync      │
│                                      (Three.js / Godot / …) │
└─────────────────────────────────────────────────────────────┘
```

The key insight is that **`ControlSignal` is the handshake** between input and
simulation. Any input source (keyboard, gamepad, AI agent, network) produces
one; any simulation backend (`DiggerSimulation` over MuJoCo, Rapier joints,
Godot physics) consumes one.

`DiggerState` is the other seam: the simulation writes it, the renderer reads
it. Because it's plain JSON-serializable data it can also be sent over a
WebSocket to a remote frontend (e.g. Godot) without any adapter layer.

## Adding a new frontend

1. Import `keyboardToSignal` (or write your own input → `ControlSignal` mapper).
2. On each frame, call `diggerSim.step(dt, signal)` — your simulation class just
   needs to accept those two arguments.
3. Read `diggerSim.getState()` → `DiggerState` and drive your renderer from it.
4. Renderer-specific sync (Three.js mesh transforms, Godot node positions) stays
   inside the frontend — it never bleeds into `shared/`.

## Alias setup

Each Vite app resolves `@shared` to this directory:

```js
// vite.config.js / vite.config.ts
resolve: {
  alias: { '@shared': path.resolve(__dirname, '../shared') }
}
```

TypeScript projects also need the matching `tsconfig.json` entry:

```json
"paths": { "@shared/*": ["../../shared/*"] },
"include": ["src", "../../shared"]
```
