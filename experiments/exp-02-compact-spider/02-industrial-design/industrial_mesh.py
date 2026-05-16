"""Compact Spider — Industrial Design Mesh / Blender 4.x / Industrial Designer Agent"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
BODY_RADIUS    = 0.45
BODY_HEIGHT    = 0.12
LEG_LENGTH     = 0.6
LEG_RADIUS     = 0.04
LEG_SEGMENTS   = 3
ARM_REACH      = 1.2
BOOM_RADIUS    = 0.05
STICK_LENGTH   = 0.5
BUCKET_WIDTH   = 0.28
BUCKET_DEPTH   = 0.18
COCKPIT_RADIUS = 0.22

# ---------------------------------------------------------------------------
# COLORS  (linear sRGB)
# ---------------------------------------------------------------------------
DARK_GREY      = (0.08, 0.09, 0.10, 1.0)
ORANGE_ACCENT  = (0.85, 0.35, 0.05, 1.0)
COCKPIT_GLASS  = (0.10, 0.20, 0.40, 0.15)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name: str) -> bpy.types.Collection:
    """Return existing collection by name, or create and link it to the scene."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    """Link obj to col; unlink from scene root if present."""
    if obj.name not in col.objects:
        col.objects.link(obj)
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)


def new_mesh_obj(
    name: str,
    mesh: bpy.types.Mesh,
    col: bpy.types.Collection,
) -> bpy.types.Object:
    """Create a new Object wrapping *mesh*, link to *col*, return it."""
    obj = bpy.data.objects.new(name, mesh)
    link_to(obj, col)
    return obj


def make_pbr_material(
    name: str,
    color: tuple,
    roughness: float,
    metallic: float,
    transmission: float = 0.0,
) -> bpy.types.Material:
    """Create (or reuse) a Principled BSDF material with given PBR values."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["Metallic"].default_value   = metallic

    if transmission > 0.0:
        # Blender 4.x uses "Transmission Weight" on Principled BSDF
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
        mat.blend_method = "BLEND"
        mat.use_backface_culling = False

    return mat


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_body(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Flat disc body using bmesh subdivided cylinder.
    Returns the body object positioned at world origin.
    """
    mat_grey = make_pbr_material("CS_DarkGrey", DARK_GREY, 0.55, 0.35)

    bm = bmesh.new()
    # Create a cylinder (disc shape) — bmesh primitive
    bmesh.ops.create_cylinder(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=32,
        radius1=BODY_RADIUS,
        radius2=BODY_RADIUS,
        depth=BODY_HEIGHT,
    )
    # Bevel top/bottom edges for subtle chamfer
    bevel_edges = [e for e in bm.edges if abs(abs(v.co.z for v in e.verts).__next__() - BODY_HEIGHT / 2) < 0.001]
    # Subdivide to add edge loops for smoothness
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)

    mesh = bpy.data.meshes.new("CS_BodyMesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.calc_normals_split()

    obj = new_mesh_obj("CS_Body", mesh, col)
    obj.location = (0.0, 0.0, 0.0)
    obj.data.materials.append(mat_grey)
    return obj


def build_leg(
    col: bpy.types.Collection,
    angle_deg: float,
) -> bpy.types.Object:
    """
    3-segment articulating leg at *angle_deg* around Z axis.
    Each segment is a tapered cylinder; joint spheres mark each knee.
    Returns a parent Empty that owns all leg pieces.
    """
    mat_grey   = make_pbr_material("CS_DarkGrey",   DARK_GREY,     0.55, 0.35)
    mat_orange = make_pbr_material("CS_OrangeAccent", ORANGE_ACCENT, 0.40, 0.50)

    angle_rad   = math.radians(angle_deg)
    seg_length  = LEG_LENGTH / LEG_SEGMENTS
    hip_offset  = BODY_RADIUS * 0.85

    # Parent empty for the whole leg
    leg_root = bpy.data.objects.new(f"CS_Leg_{int(angle_deg):03d}", None)
    leg_root.location = (
        math.cos(angle_rad) * hip_offset,
        math.sin(angle_rad) * hip_offset,
        0.0,
    )
    link_to(leg_root, col)

    pieces = []

    for seg_idx in range(LEG_SEGMENTS):
        # Taper: upper segment wider, lower narrower
        r1 = LEG_RADIUS * (1.0 - seg_idx * 0.20)
        r2 = LEG_RADIUS * (1.0 - (seg_idx + 1) * 0.20)
        r1 = max(r1, LEG_RADIUS * 0.45)
        r2 = max(r2, LEG_RADIUS * 0.35)

        bm = bmesh.new()
        bmesh.ops.create_cylinder(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=12,
            radius1=r1,
            radius2=r2,
            depth=seg_length,
        )
        mesh = bpy.data.meshes.new(f"CS_LegSeg_{int(angle_deg):03d}_{seg_idx}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        seg_obj = new_mesh_obj(f"CS_LegSeg_{int(angle_deg):03d}_{seg_idx}", mesh, col)
        seg_obj.data.materials.append(mat_grey)

        # Cascade each segment from the previous tip
        # First segment hangs from hip; subsequent from tip of prior segment
        # Spread downward and outward for planted stance
        spread_angle = math.radians(35)  # outward lean
        sag_angle    = math.radians(20 + seg_idx * 15)  # downward droop

        local_x = math.cos(angle_rad) * math.sin(spread_angle)
        local_y = math.sin(angle_rad) * math.sin(spread_angle)
        local_z = -math.cos(spread_angle)

        seg_obj.location = (
            local_x * seg_length * seg_idx,
            local_y * seg_length * seg_idx,
            local_z * seg_length * seg_idx,
        )
        seg_obj.rotation_euler = (
            math.radians(-15 * (seg_idx + 1)),
            0.0,
            angle_rad,
        )
        seg_obj.parent = leg_root
        pieces.append(seg_obj)

        # Joint sphere at knee (between segments)
        if seg_idx < LEG_SEGMENTS - 1:
            bm_sphere = bmesh.new()
            bmesh.ops.create_uvsphere(bm_sphere, u_segments=8, v_segments=6, radius=r1 * 1.4)
            mesh_s = bpy.data.meshes.new(f"CS_Knee_{int(angle_deg):03d}_{seg_idx}_Mesh")
            bm_sphere.to_mesh(mesh_s)
            bm_sphere.free()

            knee_obj = new_mesh_obj(f"CS_Knee_{int(angle_deg):03d}_{seg_idx}", mesh_s, col)
            knee_obj.data.materials.append(mat_orange)
            knee_obj.location = seg_obj.location.copy()
            knee_obj.parent = leg_root

    return leg_root


def build_arm(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Digging arm: boom (tapered box) + stick (smaller tapered box) + open-U bucket.
    Returns a parent Empty anchored at the body front.
    """
    mat_grey   = make_pbr_material("CS_DarkGrey",   DARK_GREY,     0.55, 0.35)
    mat_orange = make_pbr_material("CS_OrangeAccent", ORANGE_ACCENT, 0.40, 0.50)

    arm_root = bpy.data.objects.new("CS_Arm", None)
    arm_root.location = (BODY_RADIUS * 0.9, 0.0, BODY_HEIGHT * 0.3)
    link_to(arm_root, col)

    # --- Boom ---
    boom_w1, boom_w2 = BOOM_RADIUS * 2.2, BOOM_RADIUS * 1.4
    boom_h1, boom_h2 = BOOM_RADIUS * 1.8, BOOM_RADIUS * 1.0
    boom_len = ARM_REACH * 0.55

    bm = bmesh.new()
    # Tapered box via manual verts
    verts = [
        # Base (wider)
        (-boom_w1 / 2, 0.0,          -boom_h1 / 2),
        ( boom_w1 / 2, 0.0,          -boom_h1 / 2),
        ( boom_w1 / 2, 0.0,           boom_h1 / 2),
        (-boom_w1 / 2, 0.0,           boom_h1 / 2),
        # Tip (narrower), offset along +Y
        (-boom_w2 / 2, boom_len,     -boom_h2 / 2),
        ( boom_w2 / 2, boom_len,     -boom_h2 / 2),
        ( boom_w2 / 2, boom_len,      boom_h2 / 2),
        (-boom_w2 / 2, boom_len,      boom_h2 / 2),
    ]
    bm_verts = [bm.verts.new(v) for v in verts]
    faces = [
        [0, 1, 2, 3],   # base cap
        [4, 5, 6, 7],   # tip cap
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
    ]
    for f in faces:
        bm.faces.new([bm_verts[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_boom = bpy.data.meshes.new("CS_BoomMesh")
    bm.to_mesh(mesh_boom)
    bm.free()

    boom_obj = new_mesh_obj("CS_Boom", mesh_boom, col)
    boom_obj.data.materials.append(mat_grey)
    boom_obj.location = (0.0, 0.0, 0.0)
    boom_obj.rotation_euler = (math.radians(-35), 0.0, 0.0)
    boom_obj.parent = arm_root

    # Pivot joint sphere at boom base
    bm_piv = bmesh.new()
    bmesh.ops.create_uvsphere(bm_piv, u_segments=8, v_segments=6, radius=BOOM_RADIUS * 1.6)
    mesh_piv = bpy.data.meshes.new("CS_BoomPivotMesh")
    bm_piv.to_mesh(mesh_piv)
    bm_piv.free()
    piv_obj = new_mesh_obj("CS_BoomPivot", mesh_piv, col)
    piv_obj.data.materials.append(mat_orange)
    piv_obj.location = (0.0, 0.0, 0.0)
    piv_obj.parent = arm_root

    # --- Stick ---
    st_w1, st_w2 = BOOM_RADIUS * 1.4, BOOM_RADIUS * 1.0
    st_h1, st_h2 = BOOM_RADIUS * 1.2, BOOM_RADIUS * 0.8

    bm = bmesh.new()
    verts = [
        (-st_w1 / 2, 0.0,           -st_h1 / 2),
        ( st_w1 / 2, 0.0,           -st_h1 / 2),
        ( st_w1 / 2, 0.0,            st_h1 / 2),
        (-st_w1 / 2, 0.0,            st_h1 / 2),
        (-st_w2 / 2, STICK_LENGTH,  -st_h2 / 2),
        ( st_w2 / 2, STICK_LENGTH,  -st_h2 / 2),
        ( st_w2 / 2, STICK_LENGTH,   st_h2 / 2),
        (-st_w2 / 2, STICK_LENGTH,   st_h2 / 2),
    ]
    bm_verts = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([bm_verts[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_stick = bpy.data.meshes.new("CS_StickMesh")
    bm.to_mesh(mesh_stick)
    bm.free()

    stick_obj = new_mesh_obj("CS_Stick", mesh_stick, col)
    stick_obj.data.materials.append(mat_grey)
    # Position stick at tip of boom (approximate)
    stick_obj.location = (0.0, boom_len * math.sin(math.radians(35)),
                          -boom_len * math.cos(math.radians(35)) * 0.5)
    stick_obj.rotation_euler = (math.radians(-10), 0.0, 0.0)
    stick_obj.parent = arm_root

    # Stick pivot joint
    bm_sp = bmesh.new()
    bmesh.ops.create_uvsphere(bm_sp, u_segments=8, v_segments=6, radius=BOOM_RADIUS * 1.3)
    mesh_sp = bpy.data.meshes.new("CS_StickPivotMesh")
    bm_sp.to_mesh(mesh_sp)
    bm_sp.free()
    sp_obj = new_mesh_obj("CS_StickPivot", mesh_sp, col)
    sp_obj.data.materials.append(mat_orange)
    sp_obj.location = stick_obj.location.copy()
    sp_obj.parent = arm_root

    # --- Bucket (open U-shape) ---
    bw = BUCKET_WIDTH / 2
    bd = BUCKET_DEPTH
    bt = BOOM_RADIUS * 0.7   # wall thickness

    bm = bmesh.new()
    # Left wall
    v = [bm.verts.new(p) for p in [
        (-bw,       0.0,  0.0),
        (-bw + bt,  0.0,  0.0),
        (-bw + bt,  bd,   0.0),
        (-bw,       bd,   0.0),
        (-bw,       0.0,  bt * 2),
        (-bw + bt,  0.0,  bt * 2),
        (-bw + bt,  bd,   bt * 2),
        (-bw,       bd,   bt * 2),
    ]]
    for fi in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]:
        bm.faces.new([v[i] for i in fi])

    # Right wall (mirror)
    v2 = [bm.verts.new(p) for p in [
        (bw - bt,  0.0,  0.0),
        (bw,       0.0,  0.0),
        (bw,       bd,   0.0),
        (bw - bt,  bd,   0.0),
        (bw - bt,  0.0,  bt * 2),
        (bw,       0.0,  bt * 2),
        (bw,       bd,   bt * 2),
        (bw - bt,  bd,   bt * 2),
    ]]
    for fi in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]:
        bm.faces.new([v2[i] for i in fi])

    # Back wall (bottom of U)
    v3 = [bm.verts.new(p) for p in [
        (-bw,      0.0,  0.0),
        ( bw,      0.0,  0.0),
        ( bw,      bt,   0.0),
        (-bw,      bt,   0.0),
        (-bw,      0.0,  bt * 2),
        ( bw,      0.0,  bt * 2),
        ( bw,      bt,   bt * 2),
        (-bw,      bt,   bt * 2),
    ]]
    for fi in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]:
        bm.faces.new([v3[i] for i in fi])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    mesh_bucket = bpy.data.meshes.new("CS_BucketMesh")
    bm.to_mesh(mesh_bucket)
    bm.free()

    bucket_obj = new_mesh_obj("CS_Bucket", mesh_bucket, col)
    bucket_obj.data.materials.append(mat_grey)
    bucket_obj.location = (
        -bw,
        stick_obj.location.y + STICK_LENGTH * 0.85,
        stick_obj.location.z - 0.05,
    )
    bucket_obj.parent = arm_root

    # Bucket tilt joint
    bm_bj = bmesh.new()
    bmesh.ops.create_uvsphere(bm_bj, u_segments=8, v_segments=6, radius=BOOM_RADIUS * 1.1)
    mesh_bj = bpy.data.meshes.new("CS_BucketJointMesh")
    bm_bj.to_mesh(mesh_bj)
    bm_bj.free()
    bj_obj = new_mesh_obj("CS_BucketJoint", mesh_bj, col)
    bj_obj.data.materials.append(mat_orange)
    bj_obj.location = bucket_obj.location.copy()
    bj_obj.parent = arm_root

    return arm_root


def build_cockpit(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Compact enclosed cockpit dome: subdivided UV sphere, flattened on Z,
    with glass material.  Returns the cockpit object.
    """
    mat_glass = make_pbr_material(
        "CS_CockpitGlass",
        COCKPIT_GLASS,
        roughness=0.05,
        metallic=0.0,
        transmission=0.9,
    )
    mat_grey = make_pbr_material("CS_DarkGrey", DARK_GREY, 0.55, 0.35)

    # Rim ring (dark grey)
    bm_rim = bmesh.new()
    bmesh.ops.create_cylinder(
        bm_rim,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=COCKPIT_RADIUS * 1.05,
        radius2=COCKPIT_RADIUS * 1.05,
        depth=0.025,
    )
    mesh_rim = bpy.data.meshes.new("CS_CockpitRimMesh")
    bm_rim.to_mesh(mesh_rim)
    bm_rim.free()
    rim_obj = new_mesh_obj("CS_CockpitRim", mesh_rim, col)
    rim_obj.data.materials.append(mat_grey)
    rim_obj.location = (0.0, 0.0, BODY_HEIGHT / 2 + 0.012)

    # Dome glass sphere (upper hemisphere flattened)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=COCKPIT_RADIUS)
    # Remove lower-hemisphere verts (z < 0)
    del_verts = [v for v in bm.verts if v.co.z < -0.005]
    bmesh.ops.delete(bm, geom=del_verts, context="VERTS")
    # Flatten slightly on Z
    for v in bm.verts:
        v.co.z *= 0.65
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh_dome = bpy.data.meshes.new("CS_CockpitDomeMesh")
    bm.to_mesh(mesh_dome)
    bm.free()

    dome_obj = new_mesh_obj("CS_CockpitDome", mesh_dome, col)
    dome_obj.data.materials.append(mat_glass)
    dome_obj.location = (0.0, 0.0, BODY_HEIGHT / 2 + 0.012)
    dome_obj.parent = rim_obj

    return rim_obj


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    # Clear default objects if present
    for obj in list(bpy.data.objects):
        if obj.name in ("Cube", "Light", "Camera"):
            bpy.data.objects.remove(obj, do_unlink=True)

    col = ensure_collection("CompactSpider")

    # Body
    body = build_body(col)

    # 4 legs at 45°, 135°, 225°, 315° (diagonal corners)
    leg_angles = [45.0, 135.0, 225.0, 315.0]
    legs = [build_leg(col, a) for a in leg_angles]
    for leg in legs:
        leg.parent = body

    # Arm extending from front (+Y axis = 0°)
    arm = build_arm(col)
    arm.parent = body

    # Cockpit on top
    cockpit = build_cockpit(col)
    cockpit.parent = body
    cockpit.location = (0.0, 0.0, BODY_HEIGHT / 2)

    # Deselect all
    for obj in bpy.data.objects:
        obj.select_set(False)

    print("[CompactSpider] Industrial mesh built successfully.")
    print(f"  Body radius:    {BODY_RADIUS}m")
    print(f"  Leg length:     {LEG_LENGTH}m  ({LEG_SEGMENTS} segments each)")
    print(f"  Arm reach:      {ARM_REACH}m")
    print(f"  Cockpit radius: {COCKPIT_RADIUS}m")


if __name__ == "__main__":
    main()
