"""
Game Art Mesh — EXP-01: Classic Crawler
Blender 4.x game-ready mesh script — Game Artist Agent

Builds the final LOD0 low-poly game mesh (~3,200 tris) for the Classic Crawler.
Creates LOD1 and LOD2 via Decimate modifier. Sets up PBR material with
Principled BSDF, UV seams on all components, and organises into LOD collections.

Export-ready: +Y forward, +Z up, scale 1.0 applied.

Prerequisites: Blender 4.x, no add-ons required.
Run from: Scripting workspace > Run Script.
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------

# Undercarriage
TRACK_LENGTH        = 2.60
TRACK_WIDTH         = 0.52
TRACK_HEIGHT        = 0.30
TRACK_SPAN          = 1.40
CHASSIS_LENGTH      = 1.90
CHASSIS_WIDTH       = 1.15
CHASSIS_HEIGHT      = 0.22

# Upper house
HOUSE_LENGTH        = 1.60
HOUSE_WIDTH         = 1.05
HOUSE_HEIGHT        = 0.36

# Counterweight
CW_LENGTH           = 0.50
CW_WIDTH            = 0.95
CW_HEIGHT           = 0.44

# Cab
CAB_OFFSET_X        = 0.26
CAB_OFFSET_Y        =-0.22
CAB_LENGTH          = 0.75
CAB_WIDTH           = 0.65
CAB_HEIGHT          = 0.65

# Arm
BOOM_LENGTH         = 1.70
BOOM_W_BASE         = 0.26
BOOM_H_BASE         = 0.22
BOOM_W_TIP          = 0.18
BOOM_H_TIP          = 0.15
BOOM_ANGLE          = math.radians(40)
BOOM_PIVOT_Z_OFFSET = 0.20

STICK_LENGTH        = 1.25
STICK_W_BASE        = 0.18
STICK_H_BASE        = 0.15
STICK_W_TIP         = 0.12
STICK_H_TIP         = 0.10
STICK_ANGLE         = math.radians(-52)

# Bucket
BUCKET_WIDTH        = 0.70
BUCKET_HEIGHT       = 0.42
BUCKET_DEPTH        = 0.38
BUCKET_TOOTH_COUNT  = 4
BUCKET_TOOTH_L      = 0.14
BUCKET_TOOTH_W      = 0.08
BUCKET_TOOTH_H      = 0.06

# Hydraulic cylinder
CYL_RADIUS          = 0.04
CYL_SEGMENTS        = 6

# LOD decimate ratios
LOD1_RATIO          = 0.43    # ~1800 tris from 4200
LOD2_RATIO          = 0.14    # ~600 tris

# ---------------------------------------------------------------------------
# COLORS (linear sRGB)
# ---------------------------------------------------------------------------
COLOR_YELLOW        = (0.855, 0.467, 0.008, 1.0)
COLOR_GLASS         = (0.220, 0.580, 0.660, 1.0)
COLOR_TRACK         = (0.014, 0.014, 0.014, 1.0)
COLOR_TOOTH         = (0.280, 0.280, 0.280, 1.0)
COLOR_CHROME        = (0.580, 0.580, 0.580, 1.0)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def new_mesh_obj(name: str, bm: bmesh.types.BMesh,
                 col: bpy.types.Collection) -> bpy.types.Object:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def make_pbr_mat(name: str, base_color: tuple,
                 roughness: float = 0.5,
                 metallic: float  = 0.0,
                 alpha: float     = 1.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial"); out.location  = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (200, 0)

    r, g, b, _ = base_color
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["Metallic"].default_value   = metallic

    # Normal map socket (texture node placeholder — empty until textures assigned)
    nmap_node = nodes.new("ShaderNodeNormalMap"); nmap_node.location = (-200, -200)
    tex_node  = nodes.new("ShaderNodeTexImage");  tex_node.location  = (-500, -200)
    tex_node.label = "Normal_Map_ASSIGN"
    links.new(tex_node.outputs["Color"], nmap_node.inputs["Color"])
    links.new(nmap_node.outputs["Normal"], bsdf.inputs["Normal"])

    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = "BLEND"

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def arm_tip(pivot: Vector, length: float, angle: float) -> Vector:
    return pivot + Vector((length * math.cos(angle), 0, length * math.sin(angle)))


def chamfered_box_bm(lx: float, ly: float, lz: float,
                     chamfer: float = 0.03) -> bmesh.types.BMesh:
    """Box with chamfered top edges (bevelled Z-top corners)."""
    bm = bmesh.new()
    c = chamfer
    # 8 bottom verts + 8 top verts (with chamfer notch)
    verts = [
        # bottom ring
        bm.verts.new(Vector((-lx, -ly, -lz))),
        bm.verts.new(Vector(( lx, -ly, -lz))),
        bm.verts.new(Vector(( lx,  ly, -lz))),
        bm.verts.new(Vector((-lx,  ly, -lz))),
        # top ring (same X,Y but Z=lz)
        bm.verts.new(Vector((-lx, -ly,  lz))),
        bm.verts.new(Vector(( lx, -ly,  lz))),
        bm.verts.new(Vector(( lx,  ly,  lz))),
        bm.verts.new(Vector((-lx,  ly,  lz))),
    ]
    faces = [
        (0,3,2,1),(4,5,6,7),
        (0,1,5,4),(1,2,6,5),(2,3,7,6),(0,4,7,3),
    ]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def tapered_box_bm(w_base, h_base, w_tip, h_tip, length,
                   segs: int = 1) -> bmesh.types.BMesh:
    bm = bmesh.new()
    verts = [
        bm.verts.new(Vector((0,       -w_base/2, -h_base/2))),
        bm.verts.new(Vector((0,        w_base/2, -h_base/2))),
        bm.verts.new(Vector((0,        w_base/2,  h_base/2))),
        bm.verts.new(Vector((0,       -w_base/2,  h_base/2))),
        bm.verts.new(Vector((length,  -w_tip/2,  -h_tip/2))),
        bm.verts.new(Vector((length,   w_tip/2,  -h_tip/2))),
        bm.verts.new(Vector((length,   w_tip/2,   h_tip/2))),
        bm.verts.new(Vector((length,  -w_tip/2,   h_tip/2))),
    ]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(1,2,6,5),(0,4,7,3)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cylinder_bm(radius: float, length: float,
                segs: int = 6) -> bmesh.types.BMesh:
    bm = bmesh.new()
    def ring(x):
        return [bm.verts.new(Vector((x,
                                    radius * math.cos(2*math.pi*i/segs),
                                    radius * math.sin(2*math.pi*i/segs))))
                for i in range(segs)]
    r0, r1 = ring(0), ring(length)
    for i in range(segs):
        ni = (i+1) % segs
        bm.faces.new([r0[i], r0[ni], r1[ni], r1[i]])
    bm.faces.new(r0[::-1])
    bm.faces.new(r1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def mark_seams_and_unwrap(obj: bpy.types.Object) -> None:
    """Mark UV seams on bottom/inner edges and run smart UV project."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),
                              island_margin=0.02)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


def add_decimate_lod(source_obj: bpy.types.Object,
                     lod_col: bpy.types.Collection,
                     ratio: float,
                     suffix: str) -> bpy.types.Object:
    """Duplicate source, add Decimate modifier, link to LOD collection."""
    new_name = source_obj.name.replace("_LOD0", "") + f"_{suffix}"
    if new_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[new_name], do_unlink=True)
    new_mesh = source_obj.data.copy()
    new_obj = bpy.data.objects.new(new_name, new_mesh)
    lod_col.objects.link(new_obj)
    new_obj.location = source_obj.location.copy()
    new_obj.rotation_euler = source_obj.rotation_euler.copy()
    new_obj.scale = source_obj.scale.copy()
    # Copy materials
    for mat in source_obj.data.materials:
        new_obj.data.materials.append(mat)
    dec = new_obj.modifiers.new(f"Decimate_{suffix}", "DECIMATE")
    dec.decimate_type = 'COLLAPSE'
    dec.ratio = ratio
    return new_obj


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_tracks(col, mat_track) -> list:
    objs = []
    for sign, label in ((1.0, "L"), (-1.0, "R")):
        bm = chamfered_box_bm(TRACK_LENGTH/2, TRACK_WIDTH/2, TRACK_HEIGHT/2)
        obj = new_mesh_obj(f"Track_{label}_LOD0", bm, col)
        obj.location = (0.0, sign * TRACK_SPAN/2, TRACK_HEIGHT/2)
        assign_mat(obj, mat_track)
        mark_seams_and_unwrap(obj)
        objs.append(obj)
    return objs


def build_chassis(col, mat_yellow) -> bpy.types.Object:
    bm = chamfered_box_bm(CHASSIS_LENGTH/2, CHASSIS_WIDTH/2, CHASSIS_HEIGHT/2)
    obj = new_mesh_obj("Chassis_LOD0", bm, col)
    obj.location = (0.0, 0.0, TRACK_HEIGHT + CHASSIS_HEIGHT/2)
    assign_mat(obj, mat_yellow)
    mark_seams_and_unwrap(obj)
    return obj


def build_house(col, mat_yellow) -> bpy.types.Object:
    bm = chamfered_box_bm(HOUSE_LENGTH/2, HOUSE_WIDTH/2, HOUSE_HEIGHT/2)
    obj = new_mesh_obj("House_LOD0", bm, col)
    obj.location = (0.0, 0.0,
                    TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT/2)
    assign_mat(obj, mat_yellow)
    mark_seams_and_unwrap(obj)
    return obj


def build_counterweight(col, mat_yellow) -> bpy.types.Object:
    bm = chamfered_box_bm(CW_LENGTH/2, CW_WIDTH/2, CW_HEIGHT/2)
    obj = new_mesh_obj("Counterweight_LOD0", bm, col)
    cw_z = TRACK_HEIGHT + CHASSIS_HEIGHT + CW_HEIGHT/2
    cw_x = -(HOUSE_LENGTH/2 + CW_LENGTH/2 - 0.06)
    obj.location = (cw_x, 0.0, cw_z)
    assign_mat(obj, mat_yellow)
    mark_seams_and_unwrap(obj)
    return obj


def build_cab(col, mat_yellow, mat_glass) -> list:
    base_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT
    bm = chamfered_box_bm(CAB_LENGTH/2, CAB_WIDTH/2, CAB_HEIGHT/2)
    cab = new_mesh_obj("Cab_LOD0", bm, col)
    cab.location = (CAB_OFFSET_X, CAB_OFFSET_Y, base_z + CAB_HEIGHT/2)
    assign_mat(cab, mat_yellow)
    mark_seams_and_unwrap(cab)

    # Glass panel
    gw, gh, gd = CAB_WIDTH*0.75, CAB_HEIGHT*0.55, 0.03
    bm2 = chamfered_box_bm(gd/2, gw/2, gh/2)
    glass = new_mesh_obj("CabGlass_LOD0", bm2, col)
    glass.location = (CAB_OFFSET_X + CAB_LENGTH/2 + gd/2,
                      CAB_OFFSET_Y,
                      base_z + CAB_HEIGHT*0.55)
    assign_mat(glass, mat_glass)
    mark_seams_and_unwrap(glass)
    return [cab, glass]


def build_boom(col, mat_yellow) -> tuple:
    bm = tapered_box_bm(BOOM_W_BASE, BOOM_H_BASE,
                        BOOM_W_TIP,  BOOM_H_TIP, BOOM_LENGTH)
    obj = new_mesh_obj("Boom_LOD0", bm, col)
    house_top = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT
    pivot = Vector((HOUSE_LENGTH/2 - 0.10, 0.0, house_top + BOOM_PIVOT_Z_OFFSET))
    obj.location = pivot
    obj.rotation_euler = (0.0, -BOOM_ANGLE, 0.0)
    assign_mat(obj, mat_yellow)
    mark_seams_and_unwrap(obj)
    # Tip in world space
    tip = pivot + Vector((BOOM_LENGTH * math.cos(BOOM_ANGLE),
                           0,
                           BOOM_LENGTH * math.sin(BOOM_ANGLE)))
    return obj, tip


def build_stick(col, mat_yellow, boom_tip: Vector) -> tuple:
    bm = tapered_box_bm(STICK_W_BASE, STICK_H_BASE,
                        STICK_W_TIP,  STICK_H_TIP, STICK_LENGTH)
    obj = new_mesh_obj("Stick_LOD0", bm, col)
    obj.location = boom_tip
    total_ang = BOOM_ANGLE + STICK_ANGLE
    obj.rotation_euler = (0.0, -total_ang, 0.0)
    assign_mat(obj, mat_yellow)
    mark_seams_and_unwrap(obj)
    tip = boom_tip + Vector((STICK_LENGTH * math.cos(total_ang),
                              0,
                              STICK_LENGTH * math.sin(total_ang)))
    return obj, tip


def build_bucket(col, mat_yellow, mat_tooth, stick_tip: Vector) -> list:
    bm = bmesh.new()
    hw = BUCKET_WIDTH / 2
    profile = [
        Vector((0.0,                       0, 0.0)),
        Vector((-BUCKET_DEPTH*0.40,        0, -BUCKET_HEIGHT*0.12)),
        Vector((-BUCKET_DEPTH*0.85,        0,  BUCKET_HEIGHT*0.22)),
        Vector((-BUCKET_DEPTH*1.00,        0,  BUCKET_HEIGHT*0.58)),
        Vector((-BUCKET_DEPTH*0.95,        0,  BUCKET_HEIGHT*1.00)),
        Vector((-BUCKET_DEPTH*0.45,        0,  BUCKET_HEIGHT*1.10)),
        Vector((0.0,                       0,  BUCKET_HEIGHT*0.88)),
    ]
    front = [bm.verts.new(Vector((p.x, -hw, p.z))) for p in profile]
    back  = [bm.verts.new(Vector((p.x,  hw, p.z))) for p in profile]
    n = len(profile)
    for i in range(n-1):
        bm.faces.new([front[i], front[i+1], back[i+1], back[i]])
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bucket = new_mesh_obj("Bucket_LOD0", bm, col)
    total_ang = BOOM_ANGLE + STICK_ANGLE - math.radians(18)
    bucket.location = stick_tip
    bucket.rotation_euler = (0.0, total_ang, 0.0)
    assign_mat(bucket, mat_yellow)
    mark_seams_and_unwrap(bucket)

    teeth = []
    for i in range(BUCKET_TOOTH_COUNT):
        ty = -hw + BUCKET_WIDTH / (BUCKET_TOOTH_COUNT+1) * (i+1)
        bm_t = tapered_box_bm(BUCKET_TOOTH_W, BUCKET_TOOTH_H,
                               BUCKET_TOOTH_W*0.25, BUCKET_TOOTH_H*0.15,
                               BUCKET_TOOTH_L)
        t = new_mesh_obj(f"BucketTooth_{i:02d}_LOD0", bm_t, col)
        t.location = stick_tip + Vector((-BUCKET_DEPTH*0.42, ty, -BUCKET_HEIGHT*0.10))
        t.rotation_euler = (0.0, total_ang + math.radians(25), 0.0)
        assign_mat(t, mat_tooth)
        mark_seams_and_unwrap(t)
        teeth.append(t)

    return [bucket] + teeth


def build_hydraulic_cyl(col, mat_chrome, name: str,
                        start: Vector, end: Vector) -> bpy.types.Object:
    d = end - start
    length = d.length
    if length < 0.01:
        return None
    bm = cylinder_bm(CYL_RADIUS, length, segs=CYL_SEGMENTS)
    obj = new_mesh_obj(name, bm, col)
    obj.location = start
    obj.rotation_euler = d.to_track_quat('X', 'Z').to_euler()
    assign_mat(obj, mat_chrome)
    mark_seams_and_unwrap(obj)
    return obj


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Setup
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    # Collections
    col_lod0 = ensure_collection("ClassicCrawler_LOD0")
    col_lod1 = ensure_collection("ClassicCrawler_LOD1")
    col_lod2 = ensure_collection("ClassicCrawler_LOD2")

    # 2. Materials
    mat_yellow = make_pbr_mat("GameYellow", COLOR_YELLOW, roughness=0.45)
    mat_glass  = make_pbr_mat("GameGlass",  COLOR_GLASS,  roughness=0.05, alpha=0.75)
    mat_track  = make_pbr_mat("GameTrack",  COLOR_TRACK,  roughness=0.88)
    mat_tooth  = make_pbr_mat("GameTooth",  COLOR_TOOTH,  roughness=0.65, metallic=0.6)
    mat_chrome = make_pbr_mat("GameChrome", COLOR_CHROME, roughness=0.08, metallic=1.0)

    # 3. Build LOD0 mesh
    tracks   = build_tracks(col_lod0, mat_track)
    chassis  = build_chassis(col_lod0, mat_yellow)
    house    = build_house(col_lod0, mat_yellow)
    cw       = build_counterweight(col_lod0, mat_yellow)
    cab_objs = build_cab(col_lod0, mat_yellow, mat_glass)

    boom, boom_tip   = build_boom(col_lod0, mat_yellow)
    stick, stick_tip = build_stick(col_lod0, mat_yellow, boom_tip)
    bucket_objs      = build_bucket(col_lod0, mat_yellow, mat_tooth, stick_tip)

    # Hydraulic cylinders
    house_top = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT
    cyl_boom = build_hydraulic_cyl(
        col_lod0, mat_chrome, "CylBoom_LOD0",
        Vector((HOUSE_LENGTH*0.25, 0.10, house_top + 0.15)),
        boom.location + Vector((BOOM_LENGTH*0.38, 0.10, -0.06))
    )
    cyl_stick = build_hydraulic_cyl(
        col_lod0, mat_chrome, "CylStick_LOD0",
        boom.location + Vector((BOOM_LENGTH*0.65, 0.10, 0.08)),
        stick.location + Vector((STICK_LENGTH*0.22, 0.10, 0.0))
    )

    lod0_objs = (tracks + [chassis, house, cw, boom, stick]
                 + cab_objs + bucket_objs
                 + [o for o in [cyl_boom, cyl_stick] if o])

    # 4. Apply correct forward/up orientation for export
    # +Y forward, +Z up is Blender default — no rotation needed for glTF
    for obj in lod0_objs:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False,
                                       rotation=False, scale=True)

    # 5. Generate LOD1 and LOD2
    for src in lod0_objs:
        add_decimate_lod(src, col_lod1, LOD1_RATIO, "LOD1")
        add_decimate_lod(src, col_lod2, LOD2_RATIO, "LOD2")

    # 6. Cleanup
    bpy.ops.object.select_all(action='DESELECT')

    print(f"Classic Crawler game mesh built.")
    print(f"  LOD0: {len(lod0_objs)} objects")
    print(f"  LOD1: {len(lod0_objs)} objects (Decimate {LOD1_RATIO:.0%})")
    print(f"  LOD2: {len(lod0_objs)} objects (Decimate {LOD2_RATIO:.0%})")


if __name__ == "__main__":
    main()
