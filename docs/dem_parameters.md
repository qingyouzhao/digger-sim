# DEM Parameter Reference

Tuning guide for the Discrete Element Method solver (`DEMSolver`) and
the per-material definitions in `material_registry.gd`.

---

## Contact Model Overview

The lightweight CPU solver uses **Hertz-Mindlin** contact mechanics:

```
Normal force:   Fn = kn·δ^(3/2)  −  cn·(dδ/dt)
               kn ≈ (4/3) · E* · √(R*)
               cn = 2·√(5/6) · β · √(m* · kn)   (β from restitution e)

Tangential:     Ft = min(μ·|Fn|,  kt·ut)    (Coulomb limit)
Rolling torque: τ  = −μr · R* · |Fn| · ω̂

JKR cohesion:   F_pulloff = 3π · γ · R*
```

Where:
- `δ`  = overlap depth [m]
- `R*` = harmonic mean radius: `(Ra·Rb)/(Ra+Rb)`
- `m*` = reduced mass: `(ma·mb)/(ma+mb)`
- `β`  = damping ratio, from `e` via `β = −ln(e)/√(π²+ln²(e))`
- `γ`  = JKR surface energy density [J/m²]  (= `cohesion` field)

---

## Per-Material Parameters

### Dry Sand
| Parameter | Value | Notes |
|-----------|-------|-------|
| cohesion | 0.0 J/m² | free-flowing |
| friction_coeff | 0.60 | Coulomb static |
| rolling_friction | 0.02 | low rolling resistance |
| restitution | 0.30 | absorbs ~70% kinetic |
| density | 1600 kg/m³ | loose sand |
| particle_radius | 0.010 m | fine particles |
| angle_of_repose | 34° | literature: 30–36° |
| dig_resistance | 1.0× | baseline |

Literature reference: Cho et al. (2006), *Particle shape effect on strength
of soil*, Geotextiles and Geomembranes.

### Wet Dirt
| Parameter | Value | Notes |
|-----------|-------|-------|
| cohesion | 8.0 J/m² | mild adhesion |
| friction_coeff | 0.70 | clay-silt mix |
| rolling_friction | 0.10 | clumps roll less |
| restitution | 0.10 | near-plastic |
| density | 1900 kg/m³ | moist soil |
| particle_radius | 0.025 m | medium clumps |
| angle_of_repose | 45° | cohesion raises it |
| dig_resistance | 1.8× | noticeably heavier |

### Gravel
| Parameter | Value | Notes |
|-----------|-------|-------|
| cohesion | 0.0 J/m² | no cohesion |
| friction_coeff | 0.75 | rough angular faces |
| rolling_friction | 0.05 | some inter-locking |
| restitution | 0.40 | bouncy |
| density | 1800 kg/m³ | crushed granite |
| particle_radius | 0.060 m | coarse chunks |
| angle_of_repose | 38° | angular gravel |
| dig_resistance | 1.4× | slightly hard to scoop |

### Clay
| Parameter | Value | Notes |
|-----------|-------|-------|
| cohesion | 25.0 J/m² | high adhesion |
| friction_coeff | 0.55 | plasticity reduces friction |
| rolling_friction | 0.15 | sticky — rolls poorly |
| restitution | 0.05 | near-perfectly plastic |
| density | 2100 kg/m³ | compact clay |
| particle_radius | 0.015 m | fine |
| angle_of_repose | 55° | cohesion dominated |
| dig_resistance | 2.5× | hard excavation |

### Soft Rock
Handled primarily as Jolt rigid bodies (chunked geometry), not DEM particles.
DEM parameters apply only to secondary fines.

| Parameter | Value | Notes |
|-----------|-------|-------|
| dig_resistance | 5.0× | major machine load |
| density | 2400 kg/m³ | sandstone-like |
| restitution | 0.25 | cracks, doesn't bounce |

---

## Solver Tuning

### Timestep
- Game frame: 16.67 ms (60 Hz)
- `substeps`: 8 → physics dt = **2.08 ms**
- Hertz contact stiffness `kn ≈ 1e5` N/m requires dt < `√(m*/kn) × π`
  - Minimum particle (sand, r=0.01 m, ρ=1600): m* ≈ 1.4×10⁻⁵ kg
  - Stable dt limit ≈ 1.2 ms → substeps = 14 if sand is dominant
  - Practical: use 8 substeps for mixed scenes, increase when digging sand only

### Damping
- `damping = 0.98` per substep = 0.86 per game frame (~14% energy loss/frame)
- Reduces jitter and prevents oscillating particle piles
- Increase toward 0.999 for fluider-looking sand; decrease toward 0.90 for
  heavier gravel

### Rest detection
- `rest_threshold = 0.02 m/s` — particle speed below this counts as settled
- `rest_time_needed = 2.0 s` — must stay below threshold for this long
- Re-voxelised particles free up the particle budget; tune based on how
  quickly the scene fills up

---

## Chrono DEM-Engine Parameters (Phase 6)

When `DIGGER_USE_CHRONO=ON`, the solver switches to `chrono::gpu::ChGpuSolver`.
The equivalent Chrono API calls for each material parameter:

| DEM param | Chrono API |
|-----------|-----------|
| friction_coeff | `SetStaticFrictionCoeff_SPH2SPH(μ)` |
| rolling_friction | `SetRollingCoeff_SPH2SPH(μr)` |
| cohesion | `SetAdhesionRatio_SPH2SPH(ratio)` — ratio = γ / (Fn_max) |
| restitution | `SetCoefficientOfRestitution_SPH2SPH(e)` |
| particle_radius | `SetParticleRadius(r)` — monodisperse; polydisperse via `SetParticleRadii(array)` |

Chrono timestep recommendation: fixed dt = 5×10⁻⁴ s (2000 substeps/s).
Use `ChGpuSolver::SetFixedStepSize(5e-4)` and call solver at 60 Hz game rate
with `AdvanceSim(game_delta)`.
