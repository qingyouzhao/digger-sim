// Normalized actuator signals, each in [-1, 1].
// Index order matches MuJoCo actuator order in scene.xml.
export interface ControlSignal {
  turret: number  // +1 = rotate right
  boom:   number  // +1 = raise
  stick:  number  // +1 = extend
  bucket: number  // +1 = curl in
}

// Joint angles (radians) read back from the simulation each frame.
export interface DiggerState {
  turretAngle: number
  boomAngle:   number
  stickAngle:  number
  bucketAngle: number
  timestep:    number  // monotonic seconds since sim start
}

export interface SandParticle {
  id:       number
  position: [number, number, number]
  velocity: [number, number, number]
}

export interface SandState {
  particles: SandParticle[]
  timestep:  number
}
