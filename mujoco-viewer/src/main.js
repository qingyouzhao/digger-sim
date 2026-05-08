import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import load_mujoco from 'mujoco-wasm'
import wasmUrl from 'mujoco-wasm/dist/mujoco_wasm.wasm?url'
import sceneXml from './scene.xml?raw'

// MuJoCo geom type constants (mjGeomType enum)
const GEOM = { PLANE: 0, SPHERE: 2, CAPSULE: 3, CYLINDER: 5, BOX: 6 }

// ── Renderer ─────────────────────────────────────────────────────────────────

const canvas = document.getElementById('canvas')
const renderer = new THREE.WebGLRenderer({ antialias: true, canvas })
renderer.setPixelRatio(devicePixelRatio)
renderer.setSize(innerWidth, innerHeight)
renderer.shadowMap.enabled = true
renderer.shadowMap.type = THREE.PCFSoftShadowMap

// ── Scene ─────────────────────────────────────────────────────────────────────

const scene = new THREE.Scene()
scene.background = new THREE.Color(0x87ceeb)
scene.fog = new THREE.FogExp2(0x87ceeb, 0.015)

// ── Camera (Z-up, matching MuJoCo's coordinate convention) ───────────────────

const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.01, 200)
camera.up.set(0, 0, 1)          // Z is up in MuJoCo world
camera.position.set(5, -4, 3.5)

const controls = new OrbitControls(camera, renderer.domElement)
controls.target.set(0.5, 0, 1.0)
controls.enableDamping = true
controls.dampingFactor = 0.08

// ── Lighting ──────────────────────────────────────────────────────────────────

scene.add(new THREE.AmbientLight(0xffffff, 0.55))

const sun = new THREE.DirectionalLight(0xffffff, 1.1)
sun.position.set(6, 6, 12)
sun.castShadow = true
sun.shadow.mapSize.set(2048, 2048)
const sc = sun.shadow.camera
sc.near = 0.5; sc.far = 60
sc.top = sc.right = 12; sc.bottom = sc.left = -12
scene.add(sun)

scene.add(new THREE.DirectionalLight(0x8080ff, 0.25).position.set(-5, -5, 5) && new THREE.DirectionalLight(0x8080ff, 0.25))

// ── MuJoCo init ───────────────────────────────────────────────────────────────

const statusEl = document.getElementById('status')

let mj, model, state, sim

try {
  mj = await load_mujoco({
    locateFile: (f) => (f.endsWith('.wasm') ? wasmUrl : f),
    print: () => {},
    printErr: (msg) => console.warn('[mujoco]', msg),
  })

  mj.FS.writeFile('/scene.xml', sceneXml)
  model = new mj.Model('/scene.xml')
  state = new mj.State(model)
  sim   = new mj.Simulation(model, state)
} catch (err) {
  statusEl.textContent = `Error: ${err.message}`
  throw err
}

// Run one step so all geom_xpos / geom_xmat values are populated
sim.step()

statusEl.textContent = `Ready — ${model.ngeom} geoms, ${model.nu} actuators`

// ── Build Three.js meshes from model geometry ─────────────────────────────────

function geomMesh(type, size, rgba) {
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

    case GEOM.CAPSULE: {
      // MuJoCo: size[0]=radius, size[1]=half-length of cylinder segment
      // Three.js CapsuleGeometry: (radius, length_of_cylinder, capSegs, radialSegs)
      // Default axis is Y; MuJoCo capsule axis is Z → pre-rotate geometry
      geo = new THREE.CapsuleGeometry(size[0], size[1] * 2, 8, 18)
      geo.applyMatrix4(new THREE.Matrix4().makeRotationX(Math.PI / 2))
      break
    }

    case GEOM.CYLINDER: {
      // MuJoCo: size[0]=radius, size[1]=half-height; axis is Z → pre-rotate
      geo = new THREE.CylinderGeometry(size[0], size[0], size[1] * 2, 18)
      geo.applyMatrix4(new THREE.Matrix4().makeRotationX(Math.PI / 2))
      break
    }

    case GEOM.BOX:
      // MuJoCo size = half-extents
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

// Collect renderable geoms
const geomObjects = []

for (let i = 0; i < model.ngeom; i++) {
  const type = model.geom_type[i]
  const size = Array.from(model.geom_size.subarray(i * 3, i * 3 + 3))
  const rgba = Array.from(model.geom_rgba.subarray(i * 4, i * 4 + 4))

  if (rgba[3] === 0) continue   // invisible (e.g. collision-only geoms)

  const mesh = geomMesh(type, size, rgba)
  scene.add(mesh)
  geomObjects.push({ mesh, i })
}

// ── Keyboard input ────────────────────────────────────────────────────────────

const keys = new Set()
window.addEventListener('keydown', (e) => keys.add(e.key.toLowerCase()))
window.addEventListener('keyup',   (e) => keys.delete(e.key.toLowerCase()))

// ctrl index: 0=turret, 1=boom, 2=stick, 3=bucket  (matches actuator order in XML)
const KEY_MAP = [
  ['q',  0,  1],  // Q → turret +
  ['e',  0, -1],  // E → turret −
  ['w',  1,  1],  // W → boom +
  ['s',  1, -1],  // S → boom −
  ['a',  2,  1],  // A → stick +
  ['d',  2, -1],  // D → stick −
  ['z',  3,  1],  // Z → bucket +
  ['x',  3, -1],  // X → bucket −
]

function applyControls() {
  const ctrl = sim.ctrl   // Float64Array view into mjData.ctrl
  for (let i = 0; i < model.nu; i++) ctrl[i] = 0
  for (const [key, idx, sign] of KEY_MAP) {
    if (keys.has(key)) ctrl[idx] = sign
  }
}

// ── Per-frame update ──────────────────────────────────────────────────────────

const _rotMat = new THREE.Matrix4()
let prevTime = performance.now()

function animate() {
  requestAnimationFrame(animate)

  const now = performance.now()
  const elapsed = Math.min((now - prevTime) / 1000, 0.05)  // cap at 50 ms
  prevTime = now

  applyControls()

  // Advance physics in fixed-timestep increments
  const steps = Math.round(elapsed / model.opt.timestep)
  for (let s = 0; s < steps; s++) sim.step()

  // Sync Three.js mesh transforms from MuJoCo geom data
  const xpos = sim.geom_xpos   // Float64Array, layout: [x0,y0,z0, x1,y1,z1, ...]
  const xmat = sim.geom_xmat   // Float64Array, layout: row-major 3×3 per geom

  for (const { mesh, i } of geomObjects) {
    mesh.position.set(xpos[i * 3], xpos[i * 3 + 1], xpos[i * 3 + 2])

    // Build rotation: MuJoCo stores row-major R, Three.js Matrix4.set() is also row-major
    const m = xmat.subarray(i * 9, i * 9 + 9)
    _rotMat.set(
      m[0], m[1], m[2], 0,
      m[3], m[4], m[5], 0,
      m[6], m[7], m[8], 0,
      0,    0,    0,    1,
    )
    mesh.quaternion.setFromRotationMatrix(_rotMat)
  }

  controls.update()
  renderer.render(scene, camera)
}

animate()

statusEl.style.opacity = '0'
setTimeout(() => statusEl.remove(), 1200)

// ── Resize ────────────────────────────────────────────────────────────────────

window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(innerWidth, innerHeight)
})
