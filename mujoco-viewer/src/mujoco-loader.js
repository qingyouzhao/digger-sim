// MuJoCo geom type constants (mjGeomType enum)
export const GEOM = { PLANE: 0, SPHERE: 2, CAPSULE: 3, CYLINDER: 5, BOX: 6 }

// Injects mujoco_wasm.js via a script tag and resolves with the Module object.
// Uses the global Module pattern that the Emscripten build expects.
export function loadMujoco(opts = {}) {
  return new Promise((resolve, reject) => {
    const base = new URL('.', document.baseURI).href
    window.Module = {
      ...opts,
      locateFile: (f) => new URL(f, base).href,
      onRuntimeInitialized() {
        if (opts.onRuntimeInitialized) opts.onRuntimeInitialized()
        resolve(window.Module)
      },
    }
    const s = document.createElement('script')
    s.onerror = reject
    s.src = new URL('mujoco_wasm.js', base).href
    document.head.appendChild(s)
  })
}
