# Sand Beetle — Game Asset Specification

## Art Style & Platform
Stylized toy aesthetic. Target: PC/web browser + mobile. Visual register: low-fi stylized,
reads clearly at 2–10m game camera (kids game, close camera typical).

## LOD Breakdown
| LOD | Tri Budget | Distance Threshold | Notes |
|-----|-----------|-------------------|-------|
| LOD0 | 3,000 | 0–6m | Hero close-up, main gameplay |
| LOD1 | 1,200 | 6–15m | Mid-distance |
| LOD2 | 400 | 15m+ | Far distance / shadow caster |

## UV Layout
- Single 1K atlas (1024×1024) — toy prop tier budget
- Seam placement: shell equator split, track pod back face, arm underside, bucket inside
- Texel density: 6px/cm (appropriate for kids game at play distance)
- No overlapping UVs — shell top and bottom in separate UV islands

## PBR Channels
| Channel | Shell / Arm | Tracks | Joint Rings |
|---------|-------------|--------|-------------|
| Base Color | Tonka Yellow #F5A623 | Gloss Black #0A0A0A | Chrome #C8C8D0 |
| Roughness | 0.75 (matte ABS) | 0.92 (rubber) | 0.08 (mirror chrome) |
| Metallic | 0.0 | 0.0 | 1.0 |
| Normal | Panel seam bake | Tread pattern bake | Edge highlight |

## Texture Budget
- 1× 1K BaseColor (RGB)
- 1× 1K ORM (Occlusion R, Roughness G, Metallic B — packed)
- 1× 1K Normal (DirectX or OpenGL — document which for engine)
Total: 3× 1K = 3MB uncompressed, ~768KB with BC compression

## Rig / Animation Notes
- 3 animation bones: boom_pivot (shell attachment), bucket_tilt (boom end), body_yaw (shell rotation)
- All FK — simple enough for game controller mapping:
  - Left stick: drive tracks
  - Right stick Y: boom up/down
  - Right stick X: bucket curl/dump
  - R button: yaw body left/right

## Engine Integration
- 3 material slots: shell_yellow, track_black, joint_chrome
- Collision mesh: convex hull of shell + 2 track capsules (author separately)
- Shell and arm are separate meshes (joined at export for draw call budget)
- Anchor point: center of track contact patch (world Y=0 at ground)
