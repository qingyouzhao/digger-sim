import RAPIER from '@dimforge/rapier3d-compat'
import type { SandState } from '@shared/types'
import { stepPhysics } from './physics'
import type { PhysicsObject } from './objects'

// Wraps the Rapier world and the granular particle bodies.
// step() advances physics; getState() returns plain serializable data.
// Three.js sync (syncMeshes) stays in main.ts since it's renderer-specific.
export class SandSimulation {
  private world: RAPIER.World
  private particles: PhysicsObject[]
  private elapsed = 0

  constructor(world: RAPIER.World, particles: PhysicsObject[]) {
    this.world = world
    this.particles = particles
  }

  step(dt: number): void {
    stepPhysics(this.world)
    this.elapsed += dt
  }

  getState(): SandState {
    return {
      timestep: this.elapsed,
      particles: this.particles.map((p, id) => {
        const t = p.body.translation()
        const v = p.body.linvel()
        return { id, position: [t.x, t.y, t.z], velocity: [v.x, v.y, v.z] }
      }),
    }
  }
}
