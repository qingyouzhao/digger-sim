import * as THREE from 'three'
import { GEOM } from './mujoco-loader.js'

// Builds a Three.js mesh for a single MuJoCo geom.
export function geomMesh(type, size, rgba) {
  const color = new THREE.Color(rgba[0], rgba[1], rgba[2])
  const mat = new THREE.MeshLambertMaterial({
    color,
    transparent: rgba[3] < 0.99,
    opacity: rgba[3],
  })

  let geo
  switch (type) {
    case GEOM.SPHERE:
      geo = new THREE.SphereGeometry(size[0], 18, 14)
      break

    case GEOM.CAPSULE:
      // MuJoCo: size[0]=radius, size[1]=half-length of cylinder segment
      // CapsuleGeometry default axis is Y; MuJoCo capsule axis is Z → pre-rotate
      geo = new THREE.CapsuleGeometry(size[0], size[1] * 2, 8, 18)
      geo.applyMatrix4(new THREE.Matrix4().makeRotationX(Math.PI / 2))
      break

    case GEOM.CYLINDER:
      // MuJoCo: size[0]=radius, size[1]=half-height; axis is Z → pre-rotate
      geo = new THREE.CylinderGeometry(size[0], size[0], size[1] * 2, 18)
      geo.applyMatrix4(new THREE.Matrix4().makeRotationX(Math.PI / 2))
      break

    case GEOM.BOX:
      geo = new THREE.BoxGeometry(size[0] * 2, size[1] * 2, size[2] * 2)
      break

    case GEOM.PLANE:
      geo = new THREE.PlaneGeometry(30, 30)
      break

    default:
      geo = new THREE.SphereGeometry(0.04, 8, 6)
  }

  const mesh = new THREE.Mesh(geo, mat)
  mesh.castShadow = true
  mesh.receiveShadow = true
  return mesh
}

// Creates a Three.js mesh per visible MuJoCo geom and adds them to the scene.
// Returns an array of { mesh, i } used by syncGeoms each frame.
export function buildGeomObjects(model, scene) {
  const geomObjects = []
  for (let i = 0; i < model.ngeom; i++) {
    const type = model.geom_type[i]
    const size = Array.from(model.geom_size.subarray(i * 3, i * 3 + 3))
    const rgba = Array.from(model.geom_rgba.subarray(i * 4, i * 4 + 4))
    if (rgba[3] === 0) continue  // skip invisible (collision-only) geoms
    const mesh = geomMesh(type, size, rgba)
    scene.add(mesh)
    geomObjects.push({ mesh, i })
  }
  return geomObjects
}

const _rotMat = new THREE.Matrix4()

// Copies MuJoCo geom positions and orientations into Three.js meshes.
// xpos: Float64Array [x0,y0,z0, x1,y1,z1, ...]
// xmat: Float64Array, row-major 3×3 per geom
export function syncGeoms(geomObjects, xpos, xmat) {
  for (const { mesh, i } of geomObjects) {
    mesh.position.set(xpos[i * 3], xpos[i * 3 + 1], xpos[i * 3 + 2])

    // MuJoCo stores row-major R; Three.js Matrix4.set() is also row-major
    const m = xmat.subarray(i * 9, i * 9 + 9)
    _rotMat.set(
      m[0], m[1], m[2], 0,
      m[3], m[4], m[5], 0,
      m[6], m[7], m[8], 0,
      0,    0,    0,    1,
    )
    mesh.quaternion.setFromRotationMatrix(_rotMat)
  }
}
