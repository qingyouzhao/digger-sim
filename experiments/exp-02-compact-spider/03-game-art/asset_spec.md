# Compact Spider — Game Asset Specification
## Art Style & Platform
Stylized sci-fi. Target: PC/web browser. Visual register: mid-fi, readable at 5–15m game camera.

## LOD Breakdown
| LOD | Tri Budget | Distance Threshold |
|-----|-----------|-------------------|
| LOD0 | 4,500 | 0–8m |
| LOD1 | 2,000 | 8–20m |
| LOD2 | 800 | 20m+ |

## UV Layout
- Single 2K atlas (2048×2048)
- Seam placement: joint creases (knee bends, arm pivots, cockpit rim)
- Texel density: 8px/cm for LOD0 hero

## PBR Channels
| Channel | Description |
|---------|-------------|
| Base Color | Dark grey chassis (#181A1C), orange joints (#D95A0D) |
| Roughness | 0.55 chassis, 0.40 joints |
| Metallic | 0.35 chassis, 0.50 joints |
| Normal | Micro-panel seams baked from high-poly |

## Texture Budget
- 1× 2K BaseColor+Alpha
- 1× 2K Roughness+Metallic (packed RG channels)
- 1× 2K Normal

## Rig / Animation Notes
- 4 leg bones (hip + knee per leg = 8 bones total)
- 3 arm bones: boom_pivot, stick_pivot, bucket_tilt
- Body rotation bone: turret_yaw
- All FK, no IK needed for game controller input

## Engine Integration
- Single mesh per LOD, all parts merged (except animated bones)
- Collision: convex hull of body disc + 4 capsule legs
- Material slots: 2 (chassis, accent)
