# MuJoCo Integration Guide: Custom Digger Models

This document outlines the workflow for exporting custom 3D models from Blender and integrating them into the MuJoCo WASM viewer.

## 1. Supported Mesh Formats

The MuJoCo WASM build supports the following mesh formats:
- **STL** (Binary or ASCII)
- **OBJ** (Wavefront)

> **Note:** For WASM, mesh files must be explicitly written to the Emscripten virtual filesystem (`FS`) at runtime before the model is initialized.

## 2. Workflow to Load a Custom Mesh

### A. Asset Placement
Place your `.obj` or `.stl` files in the `mujoco-viewer/public/` directory.

### B. Pre-loading in JavaScript
Before calling `new mj.Model('/scene.xml')`, you must fetch the mesh data and write it to the MuJoCo `FS`.

```javascript
// Example in main.js
async function loadAssets(mj) {
  const assets = ['digger_bucket.obj', 'digger_arm.obj'];
  for (const file of assets) {
    const response = await fetch(`./${file}`);
    const data = await response.arrayBuffer();
    mj.FS.writeFile(`/${file}`, new Uint8Array(data));
  }
}
```

### C. Referencing in `scene.xml`
Define the mesh in the `<asset>` section and reference it in a `<geom>`.

```xml
<mujoco>
  <asset>
    <mesh name="digger_bucket" file="digger_bucket.obj" scale="1 1 1"/>
  </asset>

  <worldbody>
    <body>
      <geom type="mesh" mesh="digger_bucket" material="steel"/>
    </body>
  </worldbody>
</mujoco>
```

## 3. Articulated Digger Arm XML Structure

A minimal 3-DOF digger arm (Boom, Stick, Bucket) should follow this hierarchical body structure to ensure correct parent-child coordinate propagation.

```xml
<!-- Minimal 3-DOF Digger Arm -->
<body name="boom" pos="0.2 0 0.5">
  <joint name="boom_joint" type="hinge" axis="0 1 0" range="-10 60"/>
  <geom type="mesh" mesh="boom_mesh"/>

  <body name="stick" pos="1.5 0 0">
    <joint name="stick_joint" type="hinge" axis="0 1 0" range="-90 10"/>
    <geom type="mesh" mesh="stick_mesh"/>

    <body name="bucket" pos="1.2 0 0">
      <joint name="bucket_joint" type="hinge" axis="0 1 0" range="-100 100"/>
      <geom type="mesh" mesh="bucket_mesh"/>
    </body>
  </body>
</body>
```

## 4. Blender to MuJoCo Pipeline

To ensure your models align correctly in MuJoCo:

1.  **Coordinate System:**
    *   MuJoCo: +Z Up, +X Forward.
    *   Blender: +Z Up, -Y Forward (standard).
    *   When exporting to OBJ from Blender, use **Forward: X Forward** and **Up: Z Up**.

2.  **Scale:**
    *   Ensure "Scale" is applied in Blender (`Ctrl+A` > `Scale`) so that dimensions are 1.0.
    *   MuJoCo uses meters as the default unit.

3.  **Origin/Pivot:**
    *   Set the origin of each part (Boom, Stick, Bucket) to its **rotation pivot point** in Blender.
    *   In MuJoCo, the `<body pos="...">` should then represent the location of this pivot relative to the parent.
    *   The mesh itself will be rendered relative to the body's origin.

4.  **Geometry:**
    *   Keep poly count reasonable for WASM (LOD0 ~3k-5k tris).
    *   Triangulate faces if the OBJ exporter doesn't do it automatically, as MuJoCo prefers triangles.

## 5. Rendering Meshes in Three.js (Future Work)

The current `main.js` only renders MuJoCo primitives. To support custom meshes, `geomMesh()` needs to be extended to handle `type 7` (GEOM.MESH).

```javascript
// Planned extension for main.js
case 7: // GEOM.MESH
  // Option A: Extract geometry from model.mesh_vert / model.mesh_face
  // Option B: Load external OBJ/STL directly into Three.js
  break;
```

> **Prerequisite:** The `FS` export error investigated in `ds-w4q` must be resolved for this workflow to function.
