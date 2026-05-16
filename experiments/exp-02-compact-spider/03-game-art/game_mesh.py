"""Compact Spider — Game Art Mesh / Blender 4.x / Game Artist Agent / LOD0 target: 4,500 tris"""

import bpy
import bmesh
import math

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
BODY_RADIUS    = 0.45
BODY_SEGS      = 12
LEG_LENGTH     = 0.6
LEG_SEGS       = 6
ARM_REACH      = 1.2
BOOM_SEGS      = 4
BUCKET_WIDTH   = 0.28
COCKPIT_RADIUS = 0.22
COCKPIT_SEGS   = 8
LOD1_RATIO     = 0.44
LOD2_RATIO     = 0.18

# ---------------------------------------------------------------------------
# COLORS  (linear sRGB)
# ---------------------------------------------------------------------------
DARK_GREY     = (0.08, 0.09, 0.10, 1.0)
ORANGE_ACCENT = (0.85, 0.35, 0.05, 1.0)
COCKPIT_GLASS = (0.10, 0.20, 0.40, 0.15)

BODY_HEIGHT   = 0.12
LEG_RADIUS    = 0.04
BOOM_RADIUS   = 0.05
STICK_LENGTH  = 0.5
BUCKET_DEPTH  = 0.18


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
) -> bpy.types.Material:
    """Create (or reuse) a Principled BSDF material."""
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
    return mat


def smart_uv_project(obj: bpy.types.Object, angle_limit: float = 66.0) -> None:
    """
    Apply Smart UV Project to *obj*.
    bpy.ops requires the object to be active and in Edit mode.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_limit))
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS  (game-ready low-poly, bmesh)
# ---------------------------------------------------------------------------

def build_game_body(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Low-poly disc body with BODY_SEGS cylinder segments.
    Contributes ~(BODY_SEGS * 4) tris to budget.
    """
    mat_grey = make_pbr_material("GA_DarkGrey", DARK_GREY, 0.55, 0.35)

    bm = bmesh.new()
    bmesh.ops.create_cylinder(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=BODY_SEGS,
        radius1=BODY_RADIUS,
        radius2=BODY_RADIUS,
        depth=BODY_HEIGHT,
    )
    mesh = bpy.data.meshes.new("GA_BodyMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = new_mesh_obj("GA_Body", mesh, col)
    obj.location = (0.0, 0.0, 0.0)
    obj.data.materials.append(mat_grey)

    smart_uv_project(obj)
    return obj


def build_game_leg(
    col: bpy.types.Collection,
    angle_deg: float,
) -> bpy.types.Object:
    """
    Simplified 2-segment leg (game art simplification from 3-segment industrial).
    Each segment is a straight cylinder with LEG_SEGS sides.
    Returns a parent Empty for the leg assembly.
    """
    mat_grey   = make_pbr_material("GA_DarkGrey",    DARK_GREY,     0.55, 0.35)
    mat_orange = make_pbr_material("GA_OrangeAccent", ORANGE_ACCENT, 0.40, 0.50)

    angle_rad  = math.radians(angle_deg)
    hip_offset = BODY_RADIUS * 0.85
    seg_len    = LEG_LENGTH / 2  # 2 segments

    leg_root = bpy.data.objects.new(f"GA_Leg_{int(angle_deg):03d}", None)
    leg_root.location = (
        math.cos(angle_rad) * hip_offset,
        math.sin(angle_rad) * hip_offset,
        0.0,
    )
    link_to(leg_root, col)

    for seg_idx in range(2):
        r = LEG_RADIUS * (1.0 - seg_idx * 0.25)
        r = max(r, LEG_RADIUS * 0.55)

        bm = bmesh.new()
        bmesh.ops.create_cylinder(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=LEG_SEGS,
            radius1=r,
            radius2=r * 0.8,
            depth=seg_len,
        )
        mesh = bpy.data.meshes.new(f"GA_LegSeg_{int(angle_deg):03d}_{seg_idx}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        seg_obj = new_mesh_obj(f"GA_LegSeg_{int(angle_deg):03d}_{seg_idx}", mesh, col)
        seg_obj.data.materials.append(mat_grey)

        spread = math.radians(35)
        local_x = math.cos(angle_rad) * math.sin(spread)
        local_y = math.sin(angle_rad) * math.sin(spread)
        local_z = -math.cos(spread)

        seg_obj.location = (
            local_x * seg_len * seg_idx,
            local_y * seg_len * seg_idx,
            local_z * seg_len * seg_idx,
        )
        seg_obj.rotation_euler = (math.radians(-20 * (seg_idx + 1)), 0.0, angle_rad)
        seg_obj.parent = leg_root

        smart_uv_project(seg_obj)

        # Knee accent joint between segments
        if seg_idx == 0:
            bm_k = bmesh.new()
            bmesh.ops.create_uvsphere(bm_k, u_segments=6, v_segments=4, radius=r * 1.35)
            mesh_k = bpy.data.meshes.new(f"GA_Knee_{int(angle_deg):03d}_Mesh")
            bm_k.to_mesh(mesh_k)
            bm_k.free()
            knee_obj = new_mesh_obj(f"GA_Knee_{int(angle_deg):03d}", mesh_k, col)
            knee_obj.data.materials.append(mat_orange)
            knee_obj.location = seg_obj.location.copy()
            knee_obj.parent = leg_root
            smart_uv_project(knee_obj)

    return leg_root


def build_game_arm(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Simplified arm: single tapered boom (BOOM_SEGS cross-sections) + low-poly bucket.
    """
    mat_grey   = make_pbr_material("GA_DarkGrey",    DARK_GREY,     0.55, 0.35)
    mat_orange = make_pbr_material("GA_OrangeAccent", ORANGE_ACCENT, 0.40, 0.50)

    arm_root = bpy.data.objects.new("GA_Arm", None)
    arm_root.location = (BODY_RADIUS * 0.9, 0.0, BODY_HEIGHT * 0.3)
    link_to(arm_root, col)

    # --- Boom (tapered box, BOOM_SEGS loop cuts) ---
    bw1, bw2 = BOOM_RADIUS * 2.2, BOOM_RADIUS * 1.2
    bh1, bh2 = BOOM_RADIUS * 1.8, BOOM_RADIUS * 0.9
    boom_len  = ARM_REACH * 0.55

    bm = bmesh.new()
    seg_step = boom_len / BOOM_SEGS
    all_quads = []
    prev_ring = None

    for s in range(BOOM_SEGS + 1):
        t = s / BOOM_SEGS
        w = bw1 + (bw2 - bw1) * t
        h = bh1 + (bh2 - bh1) * t
        y = seg_step * s
        ring = [
            bm.verts.new((-w / 2, y, -h / 2)),
            bm.verts.new(( w / 2, y, -h / 2)),
            bm.verts.new(( w / 2, y,  h / 2)),
            bm.verts.new((-w / 2, y,  h / 2)),
        ]
        if prev_ring is not None:
            for i in range(4):
                bm.faces.new([prev_ring[i], ring[i], ring[(i+1)%4], prev_ring[(i+1)%4]])
        if s == 0:
            bm.faces.new(ring[::-1])  # base cap (face inward)
        if s == BOOM_SEGS:
            bm.faces.new(ring)        # tip cap
        prev_ring = ring

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_boom = bpy.data.meshes.new("GA_BoomMesh")
    bm.to_mesh(mesh_boom)
    bm.free()

    boom_obj = new_mesh_obj("GA_Boom", mesh_boom, col)
    boom_obj.data.materials.append(mat_grey)
    boom_obj.location = (0.0, 0.0, 0.0)
    boom_obj.rotation_euler = (math.radians(-35), 0.0, 0.0)
    boom_obj.parent = arm_root
    smart_uv_project(boom_obj)

    # Pivot accent
    bm_piv = bmesh.new()
    bmesh.ops.create_uvsphere(bm_piv, u_segments=6, v_segments=4, radius=BOOM_RADIUS * 1.5)
    mesh_piv = bpy.data.meshes.new("GA_BoomPivotMesh")
    bm_piv.to_mesh(mesh_piv)
    bm_piv.free()
    piv_obj = new_mesh_obj("GA_BoomPivot", mesh_piv, col)
    piv_obj.data.materials.append(mat_orange)
    piv_obj.location = (0.0, 0.0, 0.0)
    piv_obj.parent = arm_root
    smart_uv_project(piv_obj)

    # --- Bucket (simple low-poly U-shape: 3-face open box) ---
    bw  = BUCKET_WIDTH / 2
    bd  = BUCKET_DEPTH
    bt  = BOOM_RADIUS * 0.7

    bm = bmesh.new()

    def add_wall(bm, corners):
        verts = [bm.verts.new(c) for c in corners]
        bm.faces.new(verts)
        bm.faces.new(verts[::-1])
        return verts

    # Left wall
    add_wall(bm, [
        (-bw,      0.0, 0.0),
        (-bw + bt, 0.0, 0.0),
        (-bw + bt, bd,  0.0),
        (-bw,      bd,  0.0),
    ])
    # Right wall
    add_wall(bm, [
        (bw - bt, 0.0, 0.0),
        (bw,      0.0, 0.0),
        (bw,      bd,  0.0),
        (bw - bt, bd,  0.0),
    ])
    # Back (curl) wall
    add_wall(bm, [
        (-bw, 0.0,  0.0),
        ( bw, 0.0,  0.0),
        ( bw, bt,   0.0),
        (-bw, bt,   0.0),
    ])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    mesh_bucket = bpy.data.meshes.new("GA_BucketMesh")
    bm.to_mesh(mesh_bucket)
    bm.free()

    bucket_obj = new_mesh_obj("GA_Bucket", mesh_bucket, col)
    bucket_obj.data.materials.append(mat_grey)
    bucket_obj.location = (
        -bw,
        boom_len * 0.85,
        -(boom_len * math.cos(math.radians(35))) * 0.4,
    )
    bucket_obj.parent = arm_root
    smart_uv_project(bucket_obj)

    # Bucket accent joint
    bm_bj = bmesh.new()
    bmesh.ops.create_uvsphere(bm_bj, u_segments=6, v_segments=4, radius=BOOM_RADIUS * 1.0)
    mesh_bj = bpy.data.meshes.new("GA_BucketJointMesh")
    bm_bj.to_mesh(mesh_bj)
    bm_bj.free()
    bj_obj = new_mesh_obj("GA_BucketJoint", mesh_bj, col)
    bj_obj.data.materials.append(mat_orange)
    bj_obj.location = bucket_obj.location.copy()
    bj_obj.parent = arm_root
    smart_uv_project(bj_obj)

    return arm_root


def build_game_cockpit(col: bpy.types.Collection) -> bpy.types.Object:
    """
    Low-poly cockpit dome: UV sphere upper hemisphere with COCKPIT_SEGS segments.
    """
    mat_glass = make_pbr_material("GA_CockpitGlass", COCKPIT_GLASS, 0.05, 0.0)
    mat_grey  = make_pbr_material("GA_DarkGrey",     DARK_GREY,     0.55, 0.35)

    # Rim
    bm_rim = bmesh.new()
    bmesh.ops.create_cylinder(
        bm_rim,
        cap_ends=True,
        cap_tris=False,
        segments=COCKPIT_SEGS,
        radius1=COCKPIT_RADIUS * 1.05,
        radius2=COCKPIT_RADIUS * 1.05,
        depth=0.025,
    )
    mesh_rim = bpy.data.meshes.new("GA_CockpitRimMesh")
    bm_rim.to_mesh(mesh_rim)
    bm_rim.free()
    rim_obj = new_mesh_obj("GA_CockpitRim", mesh_rim, col)
    rim_obj.data.materials.append(mat_grey)
    rim_obj.location = (0.0, 0.0, BODY_HEIGHT / 2 + 0.012)
    smart_uv_project(rim_obj)

    # Dome (upper hemisphere only)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=COCKPIT_SEGS, v_segments=COCKPIT_SEGS // 2, radius=COCKPIT_RADIUS)
    del_verts = [v for v in bm.verts if v.co.z < -0.005]
    bmesh.ops.delete(bm, geom=del_verts, context="VERTS")
    for v in bm.verts:
        v.co.z *= 0.65
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_dome = bpy.data.meshes.new("GA_CockpitDomeMesh")
    bm.to_mesh(mesh_dome)
    bm.free()

    dome_obj = new_mesh_obj("GA_CockpitDome", mesh_dome, col)
    dome_obj.data.materials.append(mat_glass)
    dome_obj.location = (0.0, 0.0, BODY_HEIGHT / 2 + 0.012)
    dome_obj.parent = rim_obj
    smart_uv_project(dome_obj)

    return rim_obj


# ---------------------------------------------------------------------------
# LOD GENERATION
# ---------------------------------------------------------------------------

def generate_lods(
    lod0_col: bpy.types.Collection,
    lod1_col: bpy.types.Collection,
    lod2_col: bpy.types.Collection,
) -> None:
    """
    Duplicate all mesh objects from LOD0 into LOD1 and LOD2 collections,
    then apply Decimate modifiers with the configured ratios.
    """
    for src_obj in list(lod0_col.objects):
        if src_obj.type != "MESH":
            continue

        for target_col, ratio, suffix in [
            (lod1_col, LOD1_RATIO, "LOD1"),
            (lod2_col, LOD2_RATIO, "LOD2"),
        ]:
            new_mesh = src_obj.data.copy()
            new_obj  = bpy.data.objects.new(
                src_obj.name.replace("GA_", f"{suffix}_"),
                new_mesh,
            )
            # Copy materials
            for mat in src_obj.data.materials:
                new_obj.data.materials.append(mat)
            new_obj.location = src_obj.location.copy()
            new_obj.rotation_euler = src_obj.rotation_euler.copy()
            new_obj.scale = src_obj.scale.copy()
            link_to(new_obj, target_col)

            # Decimate modifier
            mod = new_obj.modifiers.new(name="Decimate", type="DECIMATE")
            mod.ratio = ratio


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    # Remove default scene objects
    for obj in list(bpy.data.objects):
        if obj.name in ("Cube", "Light", "Camera"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Collections
    lod0_col = ensure_collection("LOD0")
    lod1_col = ensure_collection("LOD1")
    lod2_col = ensure_collection("LOD2")

    # Build LOD0 geometry
    body    = build_game_body(lod0_col)
    cockpit = build_game_cockpit(lod0_col)
    cockpit.parent = body
    cockpit.location = (0.0, 0.0, BODY_HEIGHT / 2)

    leg_angles = [45.0, 135.0, 225.0, 315.0]
    legs = [build_game_leg(lod0_col, a) for a in leg_angles]
    for leg in legs:
        leg.parent = body

    arm = build_game_arm(lod0_col)
    arm.parent = body

    # Generate LOD1 and LOD2 via Decimate
    generate_lods(lod0_col, lod1_col, lod2_col)

    # Deselect all
    for obj in bpy.data.objects:
        obj.select_set(False)

    print("[CompactSpider-GameArt] LOD0/LOD1/LOD2 meshes built.")
    print(f"  LOD0 (full):  target ~4,500 tris")
    print(f"  LOD1 ratio:   {LOD1_RATIO}  → target ~2,000 tris")
    print(f"  LOD2 ratio:   {LOD2_RATIO}  → target ~800 tris")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Export: File > Export > FBX, +Y Forward, +Z Up, Apply Transform
# ---------------------------------------------------------------------------
# Settings:
#   Path Mode: Copy, embed textures if needed
#   Object Types: Mesh
#   Scale: 1.0
#   Apply Scalings: FBX Units Scale
#   Forward: +Y Forward
#   Up: +Z Up
#   Apply Transform: ON
#   Mesh: Smoothing = Face, Triangulate Faces = ON
#   Export each LOD collection as a separate FBX:
#     compact_spider_LOD0.fbx
#     compact_spider_LOD1.fbx
#     compact_spider_LOD2.fbx
# ---------------------------------------------------------------------------
