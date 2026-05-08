import RAPIER from '@dimforge/rapier3d-compat'
import { createScene } from './scene'
import { createPhysicsWorld, stepPhysics } from './physics'
import { PhysicsObject, spawnGround, spawnRigidBox, spawnGranularPile, syncMeshes } from './objects'

async function main() {
  await RAPIER.init()

  const { renderer, scene, camera } = createScene()
  const world = createPhysicsWorld()
  const objects: PhysicsObject[] = []

  spawnGround(world, scene)

  for (let i = 0; i < 8; i++) {
    spawnRigidBox(world, scene, {
      x: (Math.random() - 0.5) * 6,
      y: 3 + i * 1.5,
      z: (Math.random() - 0.5) * 6,
    }, objects)
  }

  spawnGranularPile(world, scene, 150, objects, 'gravel')

  function animate() {
    requestAnimationFrame(animate)
    stepPhysics(world)
    syncMeshes(objects)
    renderer.render(scene, camera)
  }

  animate()
}

main()
