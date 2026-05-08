import RAPIER from '@dimforge/rapier3d-compat'

export function createPhysicsWorld(): RAPIER.World {
  return new RAPIER.World({ x: 0, y: -9.81, z: 0 })
}

export function stepPhysics(world: RAPIER.World): void {
  world.step()
}
