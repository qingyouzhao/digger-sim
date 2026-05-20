import RAPIER from '@dimforge/rapier3d-compat'
import { createScene } from './scene'
import { createPhysicsWorld } from './physics'
import { PhysicsObject, spawnGround, spawnRigidBox, spawnGranularPile, syncMeshes } from './objects'
import { SandSimulation } from './sand-sim'

async function main() {
  await RAPIER.init()

  const { renderer, scene, camera } = createScene()
  const world = createPhysicsWorld()
  const allObjects: PhysicsObject[] = []
  const particles: PhysicsObject[] = []

  spawnGround(world, scene)

  for (let i = 0; i < 8; i++) {
    spawnRigidBox(world, scene, {
      x: (Math.random() - 0.5) * 6,
      y: 3 + i * 1.5,
      z: (Math.random() - 0.5) * 6,
    }, allObjects)
  }

  spawnGranularPile(world, scene, 150, particles, 'gravel')

  const sandSim = new SandSimulation(world, particles)

  function animate() {
    requestAnimationFrame(animate)
    sandSim.step(1 / 60)
    syncMeshes([...allObjects, ...particles])
    renderer.render(scene, camera)
  }

  animate()
}

main()
