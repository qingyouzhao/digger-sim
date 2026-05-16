# 3D Particle Simulation Investigation for Digger-Sim

This document evaluates approaches for implementing a performant 3D particle simulation within the existing Three.js + MuJoCo WASM stack.

## 1. Approach Comparison

| Approach | Max Particles | CPU ms (Budget ≤2ms) | GPU ms (Budget ≤4ms) | Complexity | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. InstancedMesh (CPU)** | 5k – 15k | 1.0 – 2.0ms | 0.5ms | Low | **Best for V1** |
| **B. GPGPU (WebGL2)** | 100k – 500k | 0.2ms | 2.0 – 3.5ms | High | **Target for V2** |
| **C. WebGPU Compute** | 500k+ | <0.1ms | 1.0 – 2.5ms | Very High | Experimental |
| **D. Worker + SAB** | 20k – 40k | 0.5ms (main) | 0.5ms | Medium | Overkill |
| **E. MuJoCo Native** | 100 – 300 | 5.0 – 15.0ms | 0.2ms | Low | Too slow |

### Analysis

*   **Approach A (CPU InstancedMesh):** The most straightforward to integrate with the current `main.js`. Modern JS engines can easily handle the math for ~10k particles within 2ms. The main bottleneck is the upload of the `instanceMatrix` buffer to the GPU, but at 10k particles (~640KB), this is negligible.
*   **Approach B (GPGPU):** Ideal for "sand-like" behavior where hundreds of thousands of particles are needed. Requires custom GLSL for simulation logic (gravity, floor collision). Integration is more complex as it involves ping-pong FBOs.
*   **Approach E (MuJoCo Native):** While tempting for perfect collisions, MuJoCo is a high-precision rigid body solver. Adding hundreds of small dynamic geoms will cause the physics timestep to explode, breaking the 60fps requirement.

---

## 2. Performance Budget Definition

Target: **60 FPS** (16.7ms frame time)

| Component | Target Allocation | Notes |
| :--- | :--- | :--- |
| **MuJoCo Physics** | 6.0ms | Includes `sim.step()` (multiple per frame) |
| **Three.js Scene Sync** | 2.0ms | Updating mesh transforms from MuJoCo |
| **Particle Simulation** | **2.0ms (CPU)** | Euler integration + bucket collision |
| **Rendering (GPU)** | **4.0ms** | Particle draw calls + main scene |
| **Overhead/Misc** | 2.7ms | Input, UI, browser jitter |

**Max Memory:** 32MB. An `InstancedMesh` with 10k particles uses:
*   `instanceMatrix`: 10,000 * 16 * 4 bytes = 640 KB
*   `instanceColor` (optional): 10,000 * 3 * 4 bytes = 120 KB
*   Total: **< 1 MB** (well within the 32MB limit).

---

## 3. Visual Design for Digging

### Behaviors
1.  **Dig Event:** Triggered when the bucket enters a "dirt zone" with high velocity or force. Spawns a burst of 50–200 particles.
2.  **Scoop:** Particles inside the bucket volume are constrained to its transform or given a "velocity bias" to stay inside.
3.  **Dump:** When the bucket tilt exceeds a threshold, particles are released from the constraint and given initial downward velocity.
4.  **Settle:** Particles stop moving upon hitting the ground plane. Despawn after ~3s to keep the pool fresh.

### Appearance
*   **Geometry:** Low-poly `TetrahedronGeometry` or `BoxGeometry` (3–4 faces).
*   **Material:** `MeshLambertMaterial` with `instanceColor` to provide variation (brown, grey, tan).
*   **Scale:** Randomize scale between 0.05 and 0.15 to prevent a "grid" look.

---

## 4. Integration with Existing Renderer

### Hook Points
The particle system should update **after** the MuJoCo step but **before** the final render.

```javascript
// main.js loop
function animate() {
  applyControls();
  for (let s = 0; s < steps; s++) sim.step(); // MuJoCo Step

  const bucketContact = checkBucketContact(sim); // Custom logic
  if (bucketContact) {
    particleSystem.spawn(bucketPos, bucketVel);
  }

  particleSystem.update(elapsed); // Particle logic
  syncMeshes();
  renderer.render(scene, camera);
}
```

### Dig Detection
Detecting a "dig" can be done by:
1.  **MuJoCo Contact Forces:** Checking `sim.data.contact` for collisions involving the bucket geoms.
2.  **Kinematic Threshold:** If the bucket is below `Z=0.2` and moving with `velocity.z < -0.5`.

---

## 5. Recommended Implementation Plan (V1)

**Approach:** CPU-driven `InstancedMesh`.

### Data Structure
```javascript
const particles = {
  pos: new Float32Array(MAX_COUNT * 3),
  vel: new Float32Array(MAX_COUNT * 3),
  life: new Float32Array(MAX_COUNT), // 0 to 1
  count: 0
};
```

### V1 Sketch (Pseudocode)
```javascript
class ParticleSystem {
  constructor(maxCount, scene) {
    this.mesh = new THREE.InstancedMesh(
      new THREE.TetrahedronGeometry(0.1),
      new THREE.MeshLambertMaterial(),
      maxCount
    );
    scene.add(this.mesh);
    // ... init buffers
  }

  update(dt) {
    for (let i = 0; i < this.count; i++) {
      // Gravity
      this.vel[i*3 + 2] -= 9.8 * dt;
      // Advection
      this.pos[i*3] += this.vel[i*3] * dt;
      this.pos[i*3+1] += this.vel[i*3+1] * dt;
      this.pos[i*3+2] += this.vel[i*3+2] * dt;

      // Ground collision
      if (this.pos[i*3+2] < 0) {
        this.pos[i*3+2] = 0;
        this.vel[i*3] *= 0.5; // Friction
        this.vel[i*3+1] *= 0.5;
        this.vel[i*3+2] = 0;
      }

      // Update matrix
      _dummy.position.set(this.pos[i*3], this.pos[i*3+1], this.pos[i*3+2]);
      _dummy.updateMatrix();
      this.mesh.setMatrixAt(i, _dummy.matrix);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
```

### Three.js r164 Specific Notes
*   **InstancedMesh:** Ensure `count` property is used to limit draw calls to only active particles.
*   **Coloring:** Use `instanceColor` attribute for variety without multiple materials.
*   **Matrix updates:** For high-performance, consider using a custom shader that reads positions from a `DataTexture` even with CPU-driven logic to avoid full matrix reconstruction in JS.
