# Industrial Design Specification — EXP-01: Classic Crawler
**Industrial Designer | Kids' Digger Simulator**

---

## Function Analysis

### Primary Function
The Classic Crawler must read, at a glance, as "the digger" — not "a digger." It occupies the archetype slot in the child's mental model. Its single most important job is **immediate recognisability**.

### Secondary Functions
1. Communicate digging action potential — the arm must look capable of reaching ground level.
2. Communicate mobility — tracks must look like they grip terrain.
3. Communicate safety to parents — no sharp projections, no threatening geometry.
4. Support gameplay legibility — key interactive parts (bucket, cab) must be visually distinct at a 5-metre play distance.

### Failure Modes
- **Too generic:** Becomes a "yellow box" rather than an excavator. Avoid featureless surfaces.
- **Too realistic:** Loses the toy warmth; children find it less approachable. Avoid hyper-detailed surface clutter.
- **Silhouette confusion:** Counterweight and boom must read distinctly from any camera angle in-game. Ensure the rear weight and front arm are never visually equivalent.
- **Scale error:** At cartoon proportions, the cab must remain the human-readable focal point. Never let the bucket dominate the composition.

---

## Form Language Rationale

### Chassis / Undercarriage
**Decision:** Wide, low rectangular form with pronounced track overhang beyond chassis width.
**Rationale:** Width communicates stability — the visual centre of gravity is low and wide. In real excavators the track extends beyond the house to prevent tipping. Here the overhang is exaggerated 15% to make this read clearly at toy scale. Chamfered bottom edges (4 mm radius) prevent visual harshness without softening the industrial character.

### House (Upper Body / Engine Compartment)
**Decision:** Trapezoidal in plan — wider at front, narrowing toward rear where counterweight begins.
**Rationale:** Directs the eye from the wide, stable base toward the working arm. The taper is functional on real machines (counterweight clearance) and here serves visual hierarchy: the arm and cab are the "point of the arrow" formed by the tapering house.

### Cab
**Decision:** Glassy greenhouse box, slightly trapezoidal in elevation (wider base), offset to the left of the arm pivot.
**Rationale:** The cab is where the child imagines themselves. It must be window-dominant — glazing should occupy 60% of the cab elevation elevation area. Offset position (as on real excavators) creates visual asymmetry that makes the machine feel dynamic rather than statically symmetrical.

### Boom (Main Arm)
**Decision:** Tapered box section, wider at pivot (25 cm) narrowing to 16 cm at stick pin. Slight upward curve achieved by two-section angular break at midpoint.
**Rationale:** Tapering communicates load-path logic — more material where stress is highest (pivot). The slight curve softens the industrial austerity and echoes the curved forms found on Tonka toys and LEGO Technic. A perfectly straight boom reads as too mechanical for a children's product.

### Stick (Forearm)
**Decision:** Thinner tapered section than boom, rigid-looking.
**Rationale:** The visual hierarchy of boom (big) → stick (smaller) → bucket (hero) guides the eye to the business end. Keep the stick relatively thin to let the bucket dominate.

### Bucket
**Decision:** Swept-back curvature on rear face, flat cutting spine, four prominent teeth.
**Rationale:** The bucket is the most recognisable element of any excavator. It must be immediately readable. Four teeth (not six or eight) is the minimum to communicate "digging teeth" while remaining legible at distance. Teeth at 12 cm length each — long enough to read clearly.

### Counterweight
**Decision:** Smoothly rounded horizontal slab — no sharp corners, distinct from all other surfaces by its convex rounding.
**Rationale:** The counterweight is a passive form (it does nothing interactive) so it must be visually quieter than the active arm. Rounded surfaces reduce its visual weight while maintaining the correct rear-balance read.

---

## CMF Specification

### Component: Body (Chassis, House, Boom, Stick)
- **Color:** Gasco Construction Yellow
  - Hex: `#FFC107`
  - Linear sRGB: (0.855, 0.467, 0.008)
  - Description: Warm amber-yellow, high visibility. Matches Caterpillar Safety Yellow in hue, shifted 5° warmer for child-friendliness.
- **Material:** High-density polyethylene (HDPE) for toy version / injection-moulded ABS
- **Finish:** Semi-gloss (60° gloss unit ≈ 45). Not mirror-polish (looks cheap), not matte (looks flat). The semi-gloss reads as "painted metal" which is the intended association.

### Component: Cab Glazing
- **Color:** Tinted blue-green
  - Hex: `#7EC8D4`
  - Linear sRGB: (0.22, 0.58, 0.66)
  - Description: Cool aqua tint — communicates glass/transparency without full transparency (which doesn't work in stylised art).
- **Material:** PC (polycarbonate) — scratch resistant, toy-safe
- **Finish:** Gloss (60° gloss ≈ 80) with specular highlight to read as glass.

### Component: Tracks / Rubber Pads
- **Color:** Charcoal black
  - Hex: `#1A1A1A`
  - Linear sRGB: (0.014, 0.014, 0.014)
  - Description: Near-black — maximum contrast with yellow body, grounds the machine to earth, reads as rubber.
- **Material:** TPU (toy version) / rubber compound
- **Finish:** Matte-satin. Rubber is never shiny; any specularity reads as wrong material.

### Component: Bucket Teeth
- **Color:** Steel grey
  - Hex: `#8C8C8C`
  - Linear sRGB: (0.28, 0.28, 0.28)
  - Description: Worn steel — slightly desaturated from chrome, communicates hardness and use.
- **Material:** Cast iron (real) / ABS with metallic paint (toy)
- **Finish:** Semi-matt (60° gloss ≈ 25). Scratched metal is matte, not shiny.

### Component: Hydraulic Cylinders
- **Color:** Polished chrome
  - Hex: `#C8C8C8`
  - Linear sRGB: (0.58, 0.58, 0.58)
  - Description: Bright metallic — creates visual sparkle and communicates "working mechanism."
- **Material:** Chrome-plated steel (real) / ABS + chrome film (toy)
- **Finish:** High gloss metallic (60° gloss ≈ 90+).

---

## Manufacturing Notes

### Toy Version (Primary)
- **Process:** Injection moulding (ABS) for all structural parts
- **Draft angle:** Minimum 2° on all vertical faces for clean ejection
- **Wall thickness:** 3.0 mm nominal, 2.5 mm minimum, 4.0 mm maximum (warp control)
- **Split line placement:** Split lines on boom and stick run along the centreline (Y=0 plane) — hidden in shadow
- **Bucket:** Two-piece (left + right half) with internal snap-fit ribs. Teeth as separate injection moulded parts, push-in during assembly.
- **Track assembly:** Each track frame as single moulded part. Track links not represented (solid form).
- **Cab glazing:** Clear PC part with tinted coating, separate from main cab body.
- **Fasteners:** No exposed screws. All joints snap-fit or ultrasonic welded.
- **Safety:** All exterior radii ≥ 3 mm. No pinch points at arm joints (covered by joint fairings).

### Game Asset Version
- No manufacturing constraints apply. All geometry can be built to visual specification.
- However: maintain design intent of injection moulding language — visible split lines as subtle normal map detail, flat parting surfaces, consistent wall thickness appearance.

---

## Component Breakdown

| Component | Object Name | Parent | Notes |
|---|---|---|---|
| Left Track | `Track_L` | `Undercarriage` | Mirror of right |
| Right Track | `Track_R` | `Undercarriage` | — |
| Chassis Plate | `Chassis` | `Undercarriage` | Sits atop tracks |
| Upper House | `House` | `Slew_Ring` | Rotates on slew ring |
| Counterweight | `Counterweight` | `House` | Rear of house |
| Cab | `Cab` | `House` | Left side of house |
| Boom | `Boom` | `House` | Front, pivots at foot |
| Stick | `Stick` | `Boom` | Pivots at boom tip |
| Bucket | `Bucket` | `Stick` | Pivots at stick tip |
| Boom Cylinder | `CylBoom` | `House`/`Boom` | Actuates boom raise |
| Stick Cylinder | `CylStick` | `Boom`/`Stick` | Actuates stick curl |
| Bucket Cylinder | `CylBucket` | `Stick`/`Bucket` | Actuates bucket curl |
