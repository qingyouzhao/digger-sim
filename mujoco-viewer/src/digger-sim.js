// Wraps the MuJoCo simulation objects behind a stable interface.
// Accepts a ControlSignal each step; exposes DiggerState for external consumers.
export class DiggerSimulation {
  constructor(model, sim) {
    this.model = model
    this.sim = sim
    this.elapsed = 0
  }

  // dt: seconds since last frame (caller should cap, e.g. at 0.05)
  // signal: ControlSignal { turret, boom, stick, bucket }, each in [-1, 1]
  step(dt, signal) {
    const ctrl = this.sim.ctrl
    ctrl[0] = signal.turret
    ctrl[1] = signal.boom
    ctrl[2] = signal.stick
    ctrl[3] = signal.bucket

    const steps = Math.round(dt / this.model.opt.timestep)
    for (let s = 0; s < steps; s++) this.sim.step()
    this.elapsed += dt
  }

  // Returns joint angles in radians; qpos order matches joint declaration in scene.xml
  getState() {
    const qpos = this.sim.qpos
    return {
      turretAngle: qpos[0],
      boomAngle:   qpos[1],
      stickAngle:  qpos[2],
      bucketAngle: qpos[3],
      timestep:    this.elapsed,
    }
  }

  // Raw geom arrays for Three.js sync — MuJoCo-specific, not part of DiggerState
  getGeomData() {
    return { xpos: this.sim.geom_xpos, xmat: this.sim.geom_xmat }
  }
}
