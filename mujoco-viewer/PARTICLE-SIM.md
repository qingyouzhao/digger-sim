# 3D Particle Simulation Research & Proposal

This document evaluates approaches for implementing a performant 3D particle simulation for `digger-sim` to represent dirt, sand, and debris.

## 1. Approach Comparison

| Approach | Capacity (Particles) | CPU ms | GPU ms | Complexity | Browser Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. InstancedMesh (CPU)** | 1k – 10k | 1.0 – 2.5 | < 0.5 | Low | Universal |
| **B. GPGPU (Ping-pong)** | 50k – 200k | < 0.5 | 1.5 – 3.0 | High | WebGL2 |
| **C. WebGPU Compute** | 100k – 500k | < 0.1 | < 1.0 | Very High | Experimental |
| **D. Worker + SAB** | 5k – 15k | 0.5 (main) | < 0.5 | Medium | Cross-origin isolated |
| **E. MuJoCo Geoms** | 50 – 200 | 5.0 – 15.0 | < 0.5 | Medium | Universal |

## 2. Recommended Approach: Three.js InstancedMesh (CPU-driven)

### Rationale
For a kids' digger game, the particle count requirement is modest (50–200 particles per "burst"). Even with multiple bursts active, the total particle count is unlikely to exceed 5,000. 

**InstancedMesh (CPU)** is the optimal choice because:
1. **Reliability:** No reliance on experimental WebGPU or complex GPGPU state management.
2. **Performance:** Modern JS engines can easily update 5k matrices within the 2ms CPU budget.
3. **Ease of Integration:** Directly hooks into the existing Three.js scene without requiring renderer swaps.
4. **Collision:** Simple analytical ground collision (z=0) is sufficient for visual particles, avoiding the overhead of MuJoCo's solver.

## 3. Performance Budget (Target: 60fps / 16.7ms)

*   **Total Frame Budget:** 16.7ms
*   **MuJoCo Step:** ~4.0ms
*   **Particle Update (CPU):** 1.5ms (for ~5k particles)
*   **Particle Render (GPU):** 0.5ms
*   **Other Rendering:** 4.0ms
*   **Headroom:** ~6.7ms

## 4. V1 Implementation Sketch

```javascript
// Simple Particle Engine Hook
const MAX_PARTICLES = 5000;
const particleGeo = new THREE.BoxGeometry(0.05, 0.05, 0.05);
const particleMat = new THREE.MeshLambertMaterial({ color: 0x8B4513 });
const instancedMesh = new THREE.InstancedMesh(particleGeo, particleMat, MAX_PARTICLES);
instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
scene.add(instancedMesh);

const particles = {
  pos: new Float32Array(MAX_PARTICLES * 3),
  vel: new Float32Array(MAX_PARTICLES * 3),
  life: new Float32Array(MAX_PARTICLES), // 0 to 1
  count: 0,
  nextIdx: 0
};

const _dummy = new THREE.Object3D();

function spawnBurst(x, y, z, amount = 50) {
  for (let i = 0; i < amount; i++) {
    const idx = particles.nextIdx;
    particles.pos[idx * 3] = x;
    particles.pos[idx * 3 + 1] = y;
    particles.pos[idx * 3 + 2] = z;
    
    // Random velocity
    particles.vel[idx * 3] = (Math.random() - 0.5) * 2;
    particles.vel[idx * 3 + 1] = (Math.random() - 0.5) * 2;
    particles.vel[idx * 3 + 2] = Math.random() * 4;
    
    particles.life[idx] = 1.0;
    particles.nextIdx = (particles.nextIdx + 1) % MAX_PARTICLES;
  }
}

function updateParticles(dt) {
  for (let i = 0; i < MAX_PARTICLES; i++) {
    if (particles.life[i] <= 0) continue;
    
    // Gravity
    particles.vel[i * 3 + 2] -= 9.8 * dt;
    
    // Advect
    particles.pos[i * 3] += particles.vel[i * 3] * dt;
    particles.pos[i * 3 + 1] += particles.vel[i * 3 + 1] * dt;
    particles.pos[i * 3 + 2] += particles.vel[i * 3 + 2] * dt;
    
    // Ground Collision (z=0)
    if (particles.pos[i * 3 + 2] < 0) {
      particles.pos[i * 3 + 2] = 0;
      particles.vel[i * 3] *= 0.5; // Friction
      particles.vel[i * 3 + 1] *= 0.5;
      particles.vel[i * 3 + 2] *= -0.3; // Bounce
    }
    
    particles.life[i] -= dt / 3.0; // 3s lifespan
    
    _dummy.position.set(particles.pos[i * 3], particles.pos[i * 3 + 1], particles.pos[i * 3 + 2]);
    _dummy.scale.setScalar(particles.life[i]);
    _dummy.updateMatrix();
    instancedMesh.setMatrixAt(i, _dummy.matrix);
  }
  instancedMesh.instanceMatrix.needsUpdate = true;
}
```

## 5. Integration Notes (Three.js r164)

*   **InstancedMesh.count:** Use this to limit the number of particles rendered if needed.
*   **computeFrustumCulled:** Set to `false` if particles move far from the origin, or update the bounding box manually.
*   **Frustum Culling:** For high-performance, ensure `instancedMesh.frustumCulled = true` but be aware that the bounding sphere needs to encompass all active particles.
*   **Interleaving:** For better cache performance, consider using a single `Float32Array` for [x, y, z, vx, vy, vz, life].
