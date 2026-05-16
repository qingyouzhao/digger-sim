# Game Asset Specification — EXP-01: Classic Crawler
**Game Artist | Kids' Digger Simulator**

---

## Art Style and Platform Target

**Art style:** Stylised low-poly with PBR materials. Proportions from the concept brief (picture-book exaggeration). Surfaces retain hard industrial language with gentle bevel on all visible edges. No pixel-art or hand-painted look — clean PBR reads correctly at all lighting conditions.

**Platform target:** PC (primary), mobile (stretch). Budget is set at PC hero prop. Mobile LOD2 will serve as the highest LOD on lower-end mobile.

**Visual hierarchy:** Hero prop (player-controlled vehicle, held in frame at all times). Receives the full texture budget.

**Camera distance:** Closest approach ~2 m, typical play distance ~6–12 m, max LOD distance ~40 m.

---

## LOD Breakdown

| LOD | Tri Target | Usage | Distance Threshold |
|---|---|---|---|
| LOD0 | 4,200 tris | Close camera, cinematic shots | 0–8 m |
| LOD1 | 1,800 tris | Standard gameplay distance | 8–20 m |
| LOD2 | 600 tris | Far background, physics proxy | 20–40 m |
| Collision | 80 tris | Physics engine box set | always |

**Triangle budget breakdown (LOD0):**

| Component | Tris | Notes |
|---|---|---|
| Undercarriage (tracks × 2) | 640 | Rounded ends on track frames |
| Chassis | 120 | Simple box with chamfers |
| House | 180 | Tapered with top bevel |
| Counterweight | 160 | Rounded convex slab |
| Cab body | 220 | Trapezoid with bevel |
| Cab glass | 48 | Flat quad insets |
| Boom | 280 | 8-sided tapered section |
| Stick | 220 | 8-sided tapered section |
| Bucket body | 480 | Curved shell, key silhouette element |
| Bucket teeth × 4 | 320 (80 each) | Pyramidal teeth |
| Hydraulic cylinders × 3 | 360 (120 each) | 6-sided cylinders |
| Misc pins and detail | 172 | Pivot caps, exhaust stack |
| **TOTAL** | **3,200** | Within 4,200 budget |

---

## UV Layout Plan

### Material sheets: 2 total

**Sheet 1: Body_Diffuse (2K)**
Contains: Chassis, House, Counterweight, Cab body, Boom, Stick, Bucket body.
All yellow-body components share one sheet to allow atlas-level texture detail.

Layout strategy:
- Boom and Stick occupy the top-left quadrant (elongated UVs, high texel priority)
- Bucket occupies top-right quadrant (curved shell, needs curvature detail)
- Chassis + House in bottom-left (large flat surfaces, efficient packing)
- Cab in bottom-right
- Counterweight: small island, bottom row

**Sheet 2: Detail_Diffuse (1K)**
Contains: Tracks, Cab glazing, Hydraulic cylinders, Bucket teeth.
Tracks: very elongated UV island (the track tread pattern repeats). Use horizontal strip with repeat-friendly seam.

### Seam placement rules
- Boom/Stick: seam along underside (hidden from primary camera angle)
- Bucket: seam at rear spine and along side walls interior
- Cab: seam at rear corners and top-to-side transitions
- Tracks: seam at inner face (never visible in play camera)

### Texel density target
- Body_Diffuse: 512 px/m at LOD0
- Detail_Diffuse: 256 px/m

---

## PBR Channel Descriptions

### Material: Body_PBR (maps to Sheet 1)

**Base Color (sRGB, 2048×2048)**
- Primary fill: Gasco Construction Yellow (`#FFC107`)
- Colour variation: subtle warm/cool shift across boom and bucket faces to read depth without lighting bake
- Panel line darkening: 4 px dark edge at weld seams (painted, not geometry)
- Logo area: reserved 256×128 px island on House top face for Gasco logo decal

**Roughness (linear, 2048×2048)**
- Base roughness 0.45 (semi-gloss paint)
- Scuff variation: +0.15 roughness on lower surfaces (dirt/wear)
- Cab edge: −0.10 roughness (cleaner, newer surface)

**Metallic (linear, 2048×2048)**
- Body: 0.0 throughout (painted non-metal)
- Hydraulic rod areas: 1.0 (cylinder rods)

**Normal (OpenGL, 2048×2048)**
- Panel lines: 2 px recessed groove at seam locations
- Weld beads along boom/stick: subtle bead bump (+Y normal)
- Cab window rubber seal: shallow channel

### Material: Detail_PBR (maps to Sheet 2)

**Base Color (1024×1024)**
- Tracks: near-black with subtle tread pattern painted in (no geometry)
- Cab glass: aqua tint (`#7EC8D4`) at 60% opacity over environment
- Cylinder rods: chrome gradient (bright centre, darker at edges)
- Bucket teeth: steel grey with tip brightening (simulating wear polish)

**Roughness (1024×1024)**
- Tracks: 0.90 (worn rubber)
- Cylinder rods: 0.05–0.15 (polished chrome)
- Glass: 0.05
- Teeth: 0.35–0.70 (worn metal)

**Metallic (1024×1024)**
- Cylinder rods: 1.0
- Teeth: 0.7
- Tracks: 0.0
- Glass: 0.0

---

## Texture Budget

| Texture | Size | Format | VRAM (compressed) |
|---|---|---|---|
| Body BaseColor | 2048×2048 | BC1/DXT1 | 1.4 MB |
| Body Roughness | 2048×2048 | BC4 | 0.7 MB |
| Body Metallic | 2048×2048 | BC4 (pack R) | packed with roughness |
| Body Normal | 2048×2048 | BC5/ATI2 | 1.4 MB |
| Detail BaseColor | 1024×1024 | BC1/DXT1 | 0.35 MB |
| Detail RoughMetal | 1024×1024 | BC3/DXT5 | 0.7 MB |
| Detail Normal | 1024×1024 | BC5 | 0.35 MB |
| **TOTAL** | — | — | **~5.0 MB** |

Roughness and Metallic are packed into a single texture (R=Metallic, G=Roughness) to save a texture slot.

---

## Engine Integration Notes

**Axis convention:** +Y forward, +Z up (Blender default export). Engine import: use FBX or glTF with Y-forward correction if the target engine uses +Z forward (Unity: apply 90° rotation on import or use glTF importer).

**Pivot points:**
- Root object pivot: ground centre of undercarriage (0, 0, 0)
- Boom pivot: at boom base pin joint (for animation)
- Stick pivot: at boom tip pin joint
- Bucket pivot: at stick tip pin joint
- House pivot: at slew ring centre (for rotation animation)

**Material slots:**
- Slot 0: Body_PBR (yellow body components)
- Slot 1: Detail_PBR (tracks, glass, metal details)

**Collision mesh:** Generate from LOD2 with additional simplification. Single convex hull for gameplay physics; box collider sufficient for most interactions.

**Animation rig notes:** No skeletal rig needed. Use object-level transforms for:
- `House` rotate Z (slew)
- `Boom` rotate Y (raise/lower)
- `Stick` rotate Y (curl in/out)
- `Bucket` rotate Y (curl in/out)

**Collections:** Organise in three collections: `LOD0`, `LOD1`, `LOD2`. Engine prefab should reference LOD0 as primary, with auto LOD transitions.
