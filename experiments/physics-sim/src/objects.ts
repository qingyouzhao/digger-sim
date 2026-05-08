import * as THREE from 'three'
import RAPIER from '@dimforge/rapier3d-compat'

export interface PhysicsObject {
  mesh: THREE.Object3D
  body: RAPIER.RigidBody
}

const MATERIAL_COLORS = {
  dirt:   0x8b5e3c,
  gravel: 0x7a7a7a,
  sand:   0xc2a96e,
}

const MATERIAL_RADIUS = {
  dirt:   0.10,
  gravel: 0.12,
  sand:   0.07,
}

const MATERIAL_FRICTION = {
  dirt:   0.9,
  gravel: 0.7,
  sand:   0.5,
}

export function spawnGround(world: RAPIER.World, scene: THREE.Scene): void {
  const body = world.createRigidBody(RAPIER.RigidBodyDesc.fixed())
  world.createCollider(RAPIER.ColliderDesc.cuboid(12, 0.15, 12), body)

  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(24, 0.3, 24),
    new THREE.MeshLambertMaterial({ color: 0x3d6b35 })
  )
  mesh.receiveShadow = true
  scene.add(mesh)
}

export function spawnRigidBox(
  world: RAPIER.World,
  scene: THREE.Scene,
  position: { x: number; y: number; z: number },
  objects: PhysicsObject[]
): void {
  const size = 0.5 + Math.random() * 0.5
  const half = size / 2

  const body = world.createRigidBody(
    RAPIER.RigidBodyDesc.dynamic().setTranslation(position.x, position.y, position.z)
  )
  world.createCollider(RAPIER.ColliderDesc.cuboid(half, half, half).setRestitution(0.2).setFriction(0.6), body)

  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(size, size, size),
    new THREE.MeshLambertMaterial({ color: 0x4a9eff })
  )
  mesh.castShadow = true
  scene.add(mesh)

  objects.push({ mesh, body })
}

export function spawnGranularPile(
  world: RAPIER.World,
  scene: THREE.Scene,
  count: number,
  objects: PhysicsObject[],
  material: keyof typeof MATERIAL_COLORS = 'gravel'
): void {
  const radius = MATERIAL_RADIUS[material]
  const friction = MATERIAL_FRICTION[material]

  // Shared geometry + material — one draw call per mesh but GPU buffers are shared
  const geo = new THREE.SphereGeometry(radius, 6, 5)
  const mat = new THREE.MeshLambertMaterial({ color: MATERIAL_COLORS[material] })

  for (let i = 0; i < count; i++) {
    const x = (Math.random() - 0.5) * 4
    const y = 1 + Math.random() * 6
    const z = (Math.random() - 0.5) * 4

    const body = world.createRigidBody(
      RAPIER.RigidBodyDesc.dynamic().setTranslation(x, y, z)
    )
    world.createCollider(
      RAPIER.ColliderDesc.ball(radius).setRestitution(0.05).setFriction(friction),
      body
    )

    const mesh = new THREE.Mesh(geo, mat)
    mesh.castShadow = true
    scene.add(mesh)

    objects.push({ mesh, body })
  }
}

// Called every frame — copies Rapier state into Three.js transforms
export function syncMeshes(objects: PhysicsObject[]): void {
  for (const { mesh, body } of objects) {
    const t = body.translation()
    const r = body.rotation()
    mesh.position.set(t.x, t.y, t.z)
    mesh.quaternion.set(r.x, r.y, r.z, r.w)
  }
}
