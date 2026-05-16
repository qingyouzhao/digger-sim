"""
Sand Beetle — Game Art Mesh
Blender 4.x — Game Artist Agent
LOD0 target: 3,000 tris | 1K texture atlas | 3 material slots

Run from: Scripting workspace > Run Script
Prerequisites: Blender 4.x, no add-ons required.
"""

import bpy
import bmesh
from mathutils import Vector
import math

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
SHELL_RX     = 0.55   # shell X semi-axis
SHELL_RY     = 0.42   # shell Y semi-axis
SHELL_RZ     = 0.22   # shell Z semi-axis
SHELL_SEGS_U = 16     # low-poly: 16 longitude segs
SHELL_SEGS_V = 10     # low-poly: 10 latitude segs

TRACK_RADIUS = 0.14
TRACK_LENGTH = 0.52
TRACK_SEGS   = 10     # low-poly cylinder
TRACK_OFFSET_X = 0.38

ARM_LENGTH   = 0.65
ARM_WIDTH    = 0.11
BOOM_TAPER   = 0.70   # tip width as fraction of base width

BUCKET_WIDTH = 0.32
BUCKET_DEPTH = 0.14
BUCKET_HEIGHT = 0.10

JOINT_RING_R  = 0.065
JOINT_RING_SEGS = 10

LOD1_RATIO   = 0.40
LOD2_RATIO   = 0.13

# ---------------------------------------------------------------------------
# COLORS — linear sRGB
# ---------------------------------------------------------------------------
TONKA_YELLOW = (0.92, 0.62, 0.08, 1.0)
BLACK_RUBBER = (0.04, 0.04, 0.04, 1.0)
CHROME       = (0.75, 0.75, 0.78, 1.0)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name):
    """Get or create a collection by name and link it to the scene."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj, col):
    """Link obj to col, unlinking from the scene root collection if present."""
    if obj.name not in col.objects:
        col.objects.link(obj)
    scene_col = bpy.context.scene.collection
    if obj.name in scene_col.objects:
        scene_col.objects.unlink(obj)


def new_mesh_obj(name, mesh, col):
    """Create a new object with the given mesh, link it to col, return the object."""
    obj = bpy.data.objects.new(name, mesh)
    link_to(obj, col)
    return obj


def make_pbr_material(name, base_color, roughness, metallic):
    """Create a Principled BSDF material and return it."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def _apply_smart_uv(obj):
    """Select obj and run Smart UV Project in edit mode."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66.0)
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_shell(col):
    """
    Oblate-spheroid shell: UV sphere scaled by (SHELL_RX, SHELL_RY, SHELL_RZ).
    Assigned Tonka yellow material, Smart UV projected.
    """
    mesh = bpy.data.meshes.new("SandBeetle_Shell_LOD0_Mesh")
    obj = new_mesh_obj("SandBeetle_Shell_LOD0", mesh, col)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=SHELL_SEGS_U,
        v_segments=SHELL_SEGS_V,
        radius=1.0,
    )
    bmesh.ops.scale(
        bm,
        vec=Vector((SHELL_RX, SHELL_RY, SHELL_RZ)),
        verts=bm.verts,
    )
    bm.to_mesh(mesh)
    bm.free()

    mat = make_pbr_material("shell_yellow", TONKA_YELLOW, 0.75, 0.0)
    mesh.materials.append(mat)

    _apply_smart_uv(obj)
    return obj


def build_track(col, side):
    """
    Track pod: low-poly cylinder rotated so its length runs along Y.
    side = -1 (left) or +1 (right), offset on X by TRACK_OFFSET_X.
    Black rubber material, Smart UV projected.
    """
    name = "SandBeetle_TrackL_LOD0" if side < 0 else "SandBeetle_TrackR_LOD0"
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = new_mesh_obj(name, mesh, col)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=TRACK_SEGS,
        radius1=TRACK_RADIUS,
        radius2=TRACK_RADIUS,
        depth=TRACK_LENGTH,
    )
    # Rotate 90 degrees around X so the cylinder length runs along Y
    angle = math.radians(90.0)
    bmesh.ops.rotate(
        bm,
        verts=bm.verts,
        cent=Vector((0.0, 0.0, 0.0)),
        matrix=__import__('mathutils').Matrix.Rotation(angle, 3, 'X'),
    )
    # Translate to the correct side
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector((side * TRACK_OFFSET_X, 0.0, 0.0)),
    )
    bm.to_mesh(mesh)
    bm.free()

    mat = make_pbr_material("track_black", BLACK_RUBBER, 0.92, 0.0)
    mesh.materials.append(mat)

    _apply_smart_uv(obj)
    return obj


def build_boom(col):
    """
    Tapered boom arm: 8-vert box, base width ARM_WIDTH, tip width ARM_WIDTH*BOOM_TAPER.
    Aligned along Y from 0 to ARM_LENGTH. Tonka yellow, Smart UV projected.
    """
    mesh = bpy.data.meshes.new("SandBeetle_Boom_LOD0_Mesh")
    obj = new_mesh_obj("SandBeetle_Boom_LOD0", mesh, col)

    bm = bmesh.new()

    hw_base = ARM_WIDTH * 0.5
    hw_tip  = ARM_WIDTH * BOOM_TAPER * 0.5
    hh      = ARM_WIDTH * 0.5   # uniform height equals base width for chunky look

    # 8 verts: base (y=0) then tip (y=ARM_LENGTH)
    # base face (y=0) — CCW when viewed from -Y
    v0 = bm.verts.new((-hw_base, 0.0,   -hh))
    v1 = bm.verts.new(( hw_base, 0.0,   -hh))
    v2 = bm.verts.new(( hw_base, 0.0,    hh))
    v3 = bm.verts.new((-hw_base, 0.0,    hh))
    # tip face (y=ARM_LENGTH)
    v4 = bm.verts.new((-hw_tip,  ARM_LENGTH, -hh))
    v5 = bm.verts.new(( hw_tip,  ARM_LENGTH, -hh))
    v6 = bm.verts.new(( hw_tip,  ARM_LENGTH,  hh))
    v7 = bm.verts.new((-hw_tip,  ARM_LENGTH,  hh))

    bm.verts.ensure_lookup_table()

    # 6 faces: bottom, top, left, right, base cap, tip cap
    bm.faces.new([v0, v1, v5, v4])  # bottom
    bm.faces.new([v3, v7, v6, v2])  # top
    bm.faces.new([v0, v4, v7, v3])  # left
    bm.faces.new([v1, v2, v6, v5])  # right
    bm.faces.new([v0, v3, v2, v1])  # base cap
    bm.faces.new([v4, v5, v6, v7])  # tip cap

    bm.to_mesh(mesh)
    bm.free()

    mat = make_pbr_material("shell_yellow", TONKA_YELLOW, 0.75, 0.0)
    mesh.materials.append(mat)

    _apply_smart_uv(obj)
    return obj


def build_bucket(col):
    """
    Open U-shaped bucket: back panel + left side panel + right side panel.
    3 quads built from 8 unique verts. Tonka yellow.
    """
    mesh = bpy.data.meshes.new("SandBeetle_Bucket_LOD0_Mesh")
    obj = new_mesh_obj("SandBeetle_Bucket_LOD0", mesh, col)

    bm = bmesh.new()

    hw = BUCKET_WIDTH  * 0.5
    d  = BUCKET_DEPTH
    h  = BUCKET_HEIGHT

    # Back panel (at y=0) — vertical face spanning full width
    b0 = bm.verts.new((-hw, 0.0,  0.0))
    b1 = bm.verts.new(( hw, 0.0,  0.0))
    b2 = bm.verts.new(( hw, 0.0,  h  ))
    b3 = bm.verts.new((-hw, 0.0,  h  ))

    # Left side panel (x = -hw) — reaches forward by BUCKET_DEPTH
    ls0 = bm.verts.new((-hw, 0.0, 0.0))
    ls1 = bm.verts.new((-hw, d,   0.0))
    ls2 = bm.verts.new((-hw, d,   h  ))
    ls3 = bm.verts.new((-hw, 0.0, h  ))

    # Right side panel (x = +hw) — mirrors left
    rs0 = bm.verts.new(( hw, 0.0, 0.0))
    rs1 = bm.verts.new(( hw, d,   0.0))
    rs2 = bm.verts.new(( hw, d,   h  ))
    rs3 = bm.verts.new(( hw, 0.0, h  ))

    bm.verts.ensure_lookup_table()

    bm.faces.new([b0, b1, b2, b3])          # back panel
    bm.faces.new([ls0, ls1, ls2, ls3])      # left side
    bm.faces.new([rs0, rs3, rs2, rs1])      # right side (flipped normal outward)

    bm.to_mesh(mesh)
    bm.free()

    mat = make_pbr_material("shell_yellow", TONKA_YELLOW, 0.75, 0.0)
    mesh.materials.append(mat)

    return obj


def build_joint_ring(col, location):
    """
    Chrome joint ring: low-poly cylinder with JOINT_RING_SEGS segments.
    Placed at 'location'. Chrome material.
    """
    mesh = bpy.data.meshes.new("SandBeetle_JointRing_LOD0_Mesh")
    obj = new_mesh_obj("SandBeetle_JointRing_LOD0", mesh, col)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=JOINT_RING_SEGS,
        radius1=JOINT_RING_R,
        radius2=JOINT_RING_R,
        depth=0.018,
    )
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector(location),
    )
    bm.to_mesh(mesh)
    bm.free()

    mat = make_pbr_material("joint_chrome", CHROME, 0.08, 1.0)
    mesh.materials.append(mat)

    return obj


# ---------------------------------------------------------------------------
# LOD GENERATION
# ---------------------------------------------------------------------------

def generate_lods(col_lod0):
    """Duplicate LOD0 into LOD1 and LOD2 with Decimate modifiers."""
    for lod_name, ratio in [("LOD1", LOD1_RATIO), ("LOD2", LOD2_RATIO)]:
        col = ensure_collection(lod_name)
        for src_obj in col_lod0.objects:
            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.name = src_obj.name.replace("LOD0", lod_name)
            link_to(new_obj, col)
            mod = new_obj.modifiers.new("Decimate", "DECIMATE")
            mod.ratio = ratio


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    col_lod0 = ensure_collection("LOD0")

    shell = build_shell(col_lod0)
    shell.name = "SandBeetle_Shell_LOD0"

    track_l = build_track(col_lod0, -1)
    track_l.name = "SandBeetle_TrackL_LOD0"
    track_r = build_track(col_lod0, +1)
    track_r.name = "SandBeetle_TrackR_LOD0"

    boom = build_boom(col_lod0)
    boom.name = "SandBeetle_Boom_LOD0"
    boom.location = (0, SHELL_RY * 0.85, SHELL_RZ * 0.3)

    bucket = build_bucket(col_lod0)
    bucket.name = "SandBeetle_Bucket_LOD0"
    bucket.location = (0, SHELL_RY * 0.85 + ARM_LENGTH, SHELL_RZ * 0.3 - 0.05)
    bucket.parent = boom

    ring1 = build_joint_ring(col_lod0, (0, SHELL_RY * 0.85, SHELL_RZ * 0.3))
    ring1.name = "SandBeetle_JointRing1_LOD0"
    ring2 = build_joint_ring(col_lod0, (0, SHELL_RY * 0.85 + ARM_LENGTH, SHELL_RZ * 0.3 - 0.05))
    ring2.name = "SandBeetle_JointRing2_LOD0"

    generate_lods(col_lod0)

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    print("Sand Beetle game mesh complete.")
    print("LOD0 collection ready. LOD1/LOD2 have Decimate modifiers.")
    print("Export: File > Export > FBX, +Y Forward, +Z Up, Apply Transform checked.")


if __name__ == "__main__":
    main()
