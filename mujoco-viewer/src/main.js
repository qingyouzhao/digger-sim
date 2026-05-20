import sceneXml from './scene.xml?raw'
import { loadMujoco } from './mujoco-loader.js'
import { createRenderer } from './threejs-renderer.js'
import { buildGeomObjects, syncGeoms } from './geom-builder.js'
import { DiggerSimulation } from './digger-sim.js'
import { keyboardToSignal } from '@shared/control'

const statusEl = document.getElementById('status')

let mj, model, state, sim

try {
  mj = await loadMujoco({
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

// One warm-up step populates geom_xpos / geom_xmat before we build meshes
sim.step()
statusEl.textContent = `Ready — ${model.ngeom} geoms, ${model.nu} actuators`

const { renderer, scene, camera, controls } = createRenderer()
const geomObjects = buildGeomObjects(model, scene)
const diggerSim = new DiggerSimulation(model, sim)

const keys = new Set()
window.addEventListener('keydown', (e) => keys.add(e.key.toLowerCase()))
window.addEventListener('keyup',   (e) => keys.delete(e.key.toLowerCase()))

let prevTime = performance.now()

function animate() {
  requestAnimationFrame(animate)

  const now = performance.now()
  const dt = Math.min((now - prevTime) / 1000, 0.05)  // cap at 50 ms
  prevTime = now

  diggerSim.step(dt, keyboardToSignal(keys))

  const { xpos, xmat } = diggerSim.getGeomData()
  syncGeoms(geomObjects, xpos, xmat)

  controls.update()
  renderer.render(scene, camera)
}

animate()

statusEl.style.opacity = '0'
setTimeout(() => statusEl.remove(), 1200)
