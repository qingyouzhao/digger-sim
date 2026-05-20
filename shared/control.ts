import type { ControlSignal } from './types'

export type KeyState = Set<string>

// Matches the key layout in mujoco-viewer — extracted here so any frontend can share it.
const KEY_BINDINGS: Array<[key: string, axis: keyof ControlSignal, sign: number]> = [
  ['q', 'turret',  1],
  ['e', 'turret', -1],
  ['w', 'boom',    1],
  ['s', 'boom',   -1],
  ['a', 'stick',   1],
  ['d', 'stick',  -1],
  ['z', 'bucket',  1],
  ['x', 'bucket', -1],
]

export function zeroSignal(): ControlSignal {
  return { turret: 0, boom: 0, stick: 0, bucket: 0 }
}

// Pure function: current key set → control signal. No DOM side-effects.
export function keyboardToSignal(keys: KeyState): ControlSignal {
  const sig = zeroSignal()
  for (const [key, axis, sign] of KEY_BINDINGS) {
    if (keys.has(key)) sig[axis] += sign
  }
  // Clamp in case two opposing keys are held at once
  for (const axis of Object.keys(sig) as Array<keyof ControlSignal>) {
    sig[axis] = Math.max(-1, Math.min(1, sig[axis]))
  }
  return sig
}
