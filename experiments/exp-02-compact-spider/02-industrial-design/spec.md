# Industrial Design Specification — EXP-02: Compact Spider
**Industrial Designer | Kids' Digger Simulator**

---

## Function Analysis

### Primary Function
The Compact Spider must communicate *walking excavation* — a machine that moves by stepping, not rolling. The single most important job of the design is making the four legs read immediately as a locomotion system, not decoration.

### Secondary Functions
1. Communicate terrain adaptability — each leg must look independently controllable (no rigid frame connecting them all).
2. Communicate compactness — despite four legs the overall footprint must not feel sprawling. The legs fold in; the machine is nimble.
3. Support gameplay novelty — the Spider is the "interesting" machine in the fleet. Its mechanical transparency makes it visually richer than the crawler.
4. Communicate Vex Robotics brand: precise, modern, unafraid of showing how it works.

### Failure Modes
- **Leg confusion:** If the four legs look like a track system or a static support structure, the locomotion concept is lost. Each leg must have a clearly visible hip joint and knee joint.
- **Complexity overload:** Too many exposed mechanisms compete for attention. Priority hierarchy: legs > arm > body. Sensor dome is background detail.
- **Unreadable at distance:** With complex geometry, the silhouette must still read cleanly at 10 m. The hexagonal body + four legs + central arm must be the only readable elements at LOD1 distances.
- **Too threatening:** Exposed mechanisms can read as hostile or insect-like in a negative way. The orange colour, rounded leg terminations (foot pads), and friendly dome sensor prevent this.

---

## Form Language Rationale

### Central Body (Hexagonal Prism)
**Decision:** Regular hexagonal prism in plan, flat top and bottom, chamfered horizontal edges.
**Rationale:** Hexagon reads as engineered-precision (honeycomb geometry, the shape of efficient structure) rather than arbitrary. It also gives the machine a unique silhouette compared to the rectangular crawler. The flat faces provide clear attachment points for the four leg pivots — two pairs of opposing hex faces, each pair equidistant from the centre. This makes the symmetry of the leg arrangement immediately obvious.

### Legs — Femur Segments
**Decision:** Circular-section tube, 62 mm outer diameter. Extends outward and 30° downward from body perimeter.
**Rationale:** Circular tube section is the most efficient structural form and reads as mechanical arm/bone geometry. The 30° initial downward droop gives the machine a "ready stance" — slightly crouched, not standing rigidly. Rigid-standing spider legs read as a display stand; drooped legs read as a creature ready to move.

### Legs — Tibia Segments
**Decision:** Slightly thinner circular tube (52 mm OD) continuing from knee joint, bending further downward to reach the ground.
**Rationale:** Tibia/femur differentiation by diameter is visually clear and structurally logical (tibia carries less bending moment). The single knee joint per leg is a deliberate simplification from real spiders' multiple joints — additional joints would be visually illegible at game scale and add unnecessary complexity.

### Knee Joint Actuator
**Decision:** Visible hydraulic cylinder (chrome-silver) bridging from mid-femur to mid-tibia, outside the leg axis.
**Rationale:** Visible actuators are the core visual honesty of this design philosophy. The cylinder is the mechanism that bends the knee — showing it tells the story of how the machine works. Positioned on the "outside" (away from body) of each leg so it's visible from all game camera angles.

### Foot Pads
**Decision:** Wide flat disc (140 mm radius, 40 mm tall), significantly wider than the tibia tube.
**Rationale:** The foot pad's width communicates stability — it distributes load over a large surface area. The disc form references surveying equipment tripod feet and Boston Dynamics Spot's foot pads. The visual contrast between the narrow tube and wide pad emphasises the "planting" action.

### Central Arm (Boom/Stick/Bucket)
**Decision:** Circular-section arm emerging from exact body top centre. Same swept bucket as Classic Crawler but narrower, more precise.
**Rationale:** Circular tube section maintains visual consistency with the leg language. Emerging from exact centre maintains the radial symmetry of the overall design — the arm is a fifth "limb" in the same language as the four legs.

### Sensor Dome
**Decision:** Small hemispherical dome on body top, slightly offset forward from arm base.
**Rationale:** Adds the suggestion of machine intelligence / autonomous operation — key to the "robotic" narrative. Small enough not to compete with the arm but present enough to be noticed on close inspection.

---

## CMF Specification

### Component: Central Body
- **Color:** Vex Robot Orange
  - Hex: `#FF6B2B`
  - Linear sRGB: (0.929, 0.216, 0.071)
  - Description: Deep warm orange, clearly distinct from construction yellow. Safety-signal colour associated with specialist/rescue equipment.
- **Material:** Aerospace-grade aluminium alloy (real) / ABS injection moulded (toy)
- **Finish:** Anodised satin. Slight texture visible close-up; reads as smooth medium-gloss at distance. (60° gloss ≈ 35).

### Component: Leg Tubes (Femur + Tibia)
- **Color:** Anthracite Dark
  - Hex: `#2D2D2D`
  - Linear sRGB: (0.027, 0.027, 0.027)
  - Description: Near-black with very slight warm tint. Reads as structural steel or carbon fibre composite.
- **Material:** CFRP (real) / ABS with matte finish (toy)
- **Finish:** Matte (60° gloss ≈ 8). Carbon fibre has almost no specularity.

### Component: Knee Actuators + Arm Cylinders
- **Color:** Polished chrome
  - Hex: `#D4D4D4`
  - Linear sRGB: (0.660, 0.660, 0.660)
  - Description: Bright metallic. Creates specular sparkle that communicates "working precision mechanism."
- **Material:** Chrome-plated steel
- **Finish:** Mirror/high-gloss (60° gloss ≈ 95). Maximum metallic contrast with dark legs.

### Component: Foot Pads
- **Color:** Safety orange tint
  - Hex: `#CC4A12`
  - Linear sRGB: (0.640, 0.102, 0.020)
  - Description: Darker, earthier version of body orange. Communicates "contact surface" — the part that touches terrain.
- **Material:** Hardened rubber (real) / TPU (toy)
- **Finish:** Matte-satin (simulates rubber grip material, 60° gloss ≈ 15).

### Component: Sensor Dome
- **Color:** Tinted black / dark blue-grey
  - Hex: `#1A2030`
  - Linear sRGB: (0.010, 0.016, 0.032)
  - Description: Very dark with slight blue-grey tint — reads as a camera/lens element.
- **Material:** Polycarbonate dome (real) / clear PC with tinted coating (toy)
- **Finish:** Gloss (like a lens, 60° gloss ≈ 80).

---

## Manufacturing Notes

### Toy Version
- **Body:** Single injection moulded hexagonal shell, 3.5 mm wall. Internal rib structure for rigidity.
- **Leg tubes:** ABS tubes, standard diameter. Rounded ends at foot to prevent sharp edges.
- **Leg assembly:** Each leg assembled as two-part system — femur and tibia snap-connected at knee joint. Joint allows approximately 60° of movement range for play value.
- **Knee actuator:** Cosmetic chrome-stickered ABS slug — not functional, represents the actuator cylinder.
- **Foot pads:** Separate TPU discs press-fit onto tibia ends. Wide base means stable freestanding.
- **Arm:** Three-part injection moulded (boom + stick + bucket). Boom pivots from body top via centre pin.
- **Safety:** All exterior radii ≥ 3 mm. Leg/knee joints have rotation stops to prevent pinch.

---

## Component Breakdown

| Component | Object Name | Parent | Notes |
|---|---|---|---|
| Hexagonal Body | `Body` | root | Central pivot for all sub-assemblies |
| Sensor Dome | `SensorDome` | `Body` | — |
| Leg FR Femur | `Leg00_Femur` | `Body` | Front-right |
| Leg FR Tibia | `Leg00_Tibia` | `Leg00_Femur` | — |
| Leg FR Foot | `Leg00_Foot` | `Leg00_Tibia` | — |
| Leg FL Femur | `Leg01_Femur` | `Body` | Front-left |
| Leg FL Tibia | `Leg01_Tibia` | `Leg01_Femur` | — |
| Leg FL Foot | `Leg01_Foot` | `Leg01_Tibia` | — |
| Leg RL Femur | `Leg02_Femur` | `Body` | Rear-left |
| Leg RL Tibia | `Leg02_Tibia` | `Leg02_Femur` | — |
| Leg RL Foot | `Leg02_Foot` | `Leg02_Tibia` | — |
| Leg RR Femur | `Leg03_Femur` | `Body` | Rear-right |
| Leg RR Tibia | `Leg03_Tibia` | `Leg03_Femur` | — |
| Leg RR Foot | `Leg03_Foot` | `Leg03_Tibia` | — |
| Knee Actuator × 4 | `KneeActuator_0x` | `Leg0x_Femur` | Chrome cylinder |
| Boom | `ArmBoom` | `Body` | Central arm |
| Stick | `ArmStick` | `ArmBoom` | — |
| Bucket | `ArmBucket` | `ArmStick` | — |
| Boom Actuator | `CylBoom` | `Body`/`ArmBoom` | Chrome cylinder |
