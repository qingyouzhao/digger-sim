"""
Concept Silhouette Mesh — EXP-02: Compact Spider
Blender 4.x base mesh script — Concept Art Director Agent

Design intent: Evoke a 4-legged walking excavator — compact hexagonal body
suspended on four articulating leg-pairs, single central arm, exposed hydraulic
actuators at each joint. The silhouette reads as "mechanical spider holding
a digger arm." Each leg has hip and knee segments; feet are wide pad discs.
Rough geometry for sculptor handoff via Multiresolution modifier.

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

# Central body (hexagonal prism approximated as chamfered box)
BODY_RADIUS         = 0.55    # circumscribed radius of hex
BODY_HEIGHT         = 0.32
BODY_SIDES          = 6       # hexagonal

# Leg geometry
LEG_HIP_RADIUS      = 0.065   # tubular leg radius
LEG_HIP_LENGTH      = 0.55    # femur length
LEG_KNEE_LENGTH     = 0.60    # tibia length
LEG_KNEE_BEND       = math.radians(-42)   # tibia bends down from femur
LEG_HIP_ANGLE_OUT   = math.radians(38)    # femur droops outward from horizontal
LEG_POSITIONS       = [
    math.radians(45),    # front-right
    math.radians(135),   # front-left
    math.radians(-135),  # rear-left
    math.radians(-45),   # rear-right
]
LEG_SEGMENTS        = 8

# Foot pads
FOOT_RADIUS         = 0.14
FOOT_HEIGHT         = 0.04
FOOT_SEGMENTS       = 10

# Arm (central boom/stick/bucket — same as crawler but thinner)
BOOM_LENGTH         = 1.30
BOOM_RADIUS         = 0.06
BOOM_ANGLE          = math.radians(50)

STICK_LENGTH        = 1.00
STICK_RADIUS        = 0.045
STICK_ANGLE_REL     = math.radians(-55)

BUCKET_WIDTH        = 0.52
BUCKET_HEIGHT       = 0.34
BUCKET_DEPTH        = 0.30

# Sensor dome on body top
SENSOR_RADIUS       = 0.12

# Colors (linear sRGB)
ORANGE_LINEAR       = (0.929, 0.216, 0.071, 1.0)   # Robot orange
DARK_GREY_LINEAR    = (0.030, 0.030, 0.030, 1.0)   # Anthracite grey

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


def make_flat_material(name: str, color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out  = nodes.new("ShaderNodeOutputMaterial"); out.location  = (300, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.55
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign_mat(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def add_multires(obj: bpy.types.Object, levels: int = 2) -> None:
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Multiresolution", "MULTIRES")
    for _ in range(levels):
        bpy.ops.object.multires_subdivide(modifier="Multiresolution",
                                          mode='LINEAR')


def hex_prism_bm(radius: float, height: float,
                 sides: int = 6) -> bmesh.types.BMesh:
    """Hexagonal prism centred at origin."""
    bm = bmesh.new()
    bottom = []
    top    = []
    for i in range(sides):
        a = 2 * math.pi * i / sides + math.pi / sides
        x = radius * math.cos(a)
        y = radius * math.sin(a)
        bottom.append(bm.verts.new(Vector((x, y, -height/2))))
        top.append(bm.verts.new(Vector((x, y,  height/2))))
    # Side faces
    for i in range(sides):
        ni = (i+1) % sides
        bm.faces.new([bottom[i], bottom[ni], top[ni], top[i]])
    # Caps
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def tube_bm(radius: float, length: float, segs: int = 8) -> bmesh.types.BMesh:
    """Open-ended cylinder along +X."""
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


def disc_bm(radius: float, height: float, segs: int = 10) -> bmesh.types.BMesh:
    """Flat disc (short cylinder)."""
    return tube_bm(radius, height, segs)


def sphere_bm(radius: float, segs: int = 8) -> bmesh.types.BMesh:
    """UV sphere approximation using stacked rings."""
    bm = bmesh.new()
    rings = segs // 2
    all_verts = []
    for r in range(rings + 1):
        lat = math.pi * r / rings - math.pi / 2
        ring_r = radius * math.cos(lat)
        z      = radius * math.sin(lat)
        ring = [bm.verts.new(Vector((ring_r * math.cos(2*math.pi*i/segs),
                                     ring_r * math.sin(2*math.pi*i/segs),
                                     z)))
                for i in range(segs)]
        all_verts.append(ring)
    for r in range(rings):
        for i in range(segs):
            ni = (i+1) % segs
            if r == 0:
                bm.faces.new([all_verts[r][0], all_verts[r+1][ni],
                               all_verts[r+1][i]])
            elif r == rings - 1:
                bm.faces.new([all_verts[r][i], all_verts[r][ni],
                               all_verts[r+1][0]])
            else:
                bm.faces.new([all_verts[r][i], all_verts[r][ni],
                               all_verts[r+1][ni], all_verts[r+1][i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

BODY_Z = 0.60    # height of body centre above ground

def build_body(col, mat_orange) -> bpy.types.Object:
    bm = hex_prism_bm(BODY_RADIUS, BODY_HEIGHT, sides=BODY_SIDES)
    obj = new_mesh_obj("Body", bm, col)
    obj.location = (0.0, 0.0, BODY_Z)
    assign_mat(obj, mat_orange)
    return obj


def build_sensor_dome(col, mat_orange) -> bpy.types.Object:
    """Small dome on body top — sensor cluster placeholder."""
    bm = sphere_bm(SENSOR_RADIUS, segs=8)
    obj = new_mesh_obj("SensorDome", bm, col)
    obj.location = (0.0, 0.0, BODY_Z + BODY_HEIGHT/2 + SENSOR_RADIUS * 0.7)
    assign_mat(obj, mat_orange)
    return obj


def build_leg(col, mat_dark, leg_idx: int) -> list:
    """Build hip tube + knee tube + foot disc for one leg."""
    angle = LEG_POSITIONS[leg_idx]
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    # Hip attach point on body perimeter
    hip_x = BODY_RADIUS * cos_a
    hip_y = BODY_RADIUS * sin_a
    hip_origin = Vector((hip_x, hip_y, BODY_Z))

    # Femur: extends outward and slightly downward
    # Femur local direction: along body radial direction, drooping by LEG_HIP_ANGLE_OUT
    femur_dir_x = cos_a * math.cos(LEG_HIP_ANGLE_OUT)
    femur_dir_y = sin_a * math.cos(LEG_HIP_ANGLE_OUT)
    femur_dir_z = -math.sin(LEG_HIP_ANGLE_OUT)
    femur_tip = hip_origin + Vector((femur_dir_x, femur_dir_y, femur_dir_z)) * LEG_HIP_LENGTH

    # Tibia: continues from femur tip, bending further down
    knee_droop = LEG_HIP_ANGLE_OUT - LEG_KNEE_BEND
    tibia_dir_x = cos_a * math.cos(knee_droop)
    tibia_dir_y = sin_a * math.cos(knee_droop)
    tibia_dir_z = -math.sin(knee_droop)
    tibia_tip = femur_tip + Vector((tibia_dir_x, tibia_dir_y, tibia_dir_z)) * LEG_KNEE_LENGTH

    objs = []

    # Femur tube
    bm_f = tube_bm(LEG_HIP_RADIUS, LEG_HIP_LENGTH, segs=LEG_SEGMENTS)
    femur_obj = new_mesh_obj(f"Leg{leg_idx:02d}_Femur", bm_f, col)
    femur_obj.location = hip_origin
    femur_dir_v = Vector((femur_dir_x, femur_dir_y, femur_dir_z))
    femur_obj.rotation_euler = femur_dir_v.to_track_quat('X', 'Z').to_euler()
    assign_mat(femur_obj, mat_dark)
    objs.append(femur_obj)

    # Tibia tube
    bm_t = tube_bm(LEG_HIP_RADIUS * 0.85, LEG_KNEE_LENGTH, segs=LEG_SEGMENTS)
    tibia_obj = new_mesh_obj(f"Leg{leg_idx:02d}_Tibia", bm_t, col)
    tibia_obj.location = femur_tip
    tibia_dir_v = Vector((tibia_dir_x, tibia_dir_y, tibia_dir_z))
    tibia_obj.rotation_euler = tibia_dir_v.to_track_quat('X', 'Z').to_euler()
    assign_mat(tibia_obj, mat_dark)
    objs.append(tibia_obj)

    # Foot pad disc at tibia tip (flat on ground)
    bm_fp = disc_bm(FOOT_RADIUS, FOOT_HEIGHT, segs=FOOT_SEGMENTS)
    foot_obj = new_mesh_obj(f"Leg{leg_idx:02d}_Foot", bm_fp, col)
    foot_obj.location = Vector((tibia_tip.x, tibia_tip.y, FOOT_HEIGHT/2))
    assign_mat(foot_obj, mat_dark)
    objs.append(foot_obj)

    return objs


def get_arm_pivot() -> Vector:
    return Vector((0.0, 0.0, BODY_Z + BODY_HEIGHT/2 + 0.04))


def build_arm_boom(col, mat_dark) -> tuple:
    """Tubular boom arm emerging from body top centre."""
    pivot = get_arm_pivot()
    bm = tube_bm(BOOM_RADIUS, BOOM_LENGTH, segs=8)
    obj = new_mesh_obj("ArmBoom", bm, col)
    obj.location = pivot
    obj.rotation_euler = (0.0, -BOOM_ANGLE, 0.0)
    assign_mat(obj, mat_dark)
    tip = pivot + Vector((
        BOOM_LENGTH * math.cos(BOOM_ANGLE),
        0,
        BOOM_LENGTH * math.sin(BOOM_ANGLE)
    ))
    return obj, tip


def build_arm_stick(col, mat_dark, boom_tip: Vector) -> tuple:
    bm = tube_bm(STICK_RADIUS, STICK_LENGTH, segs=8)
    obj = new_mesh_obj("ArmStick", bm, col)
    obj.location = boom_tip
    total = BOOM_ANGLE + STICK_ANGLE_REL
    obj.rotation_euler = (0.0, -total, 0.0)
    assign_mat(obj, mat_dark)
    tip = boom_tip + Vector((
        STICK_LENGTH * math.cos(total),
        0,
        STICK_LENGTH * math.sin(total)
    ))
    return obj, tip


def build_arm_bucket(col, mat_dark, stick_tip: Vector) -> bpy.types.Object:
    bm = bmesh.new()
    hw = BUCKET_WIDTH / 2
    profile = [
        Vector((0.0,              0, 0.0)),
        Vector((-BUCKET_DEPTH*0.4, 0, -BUCKET_HEIGHT*0.1)),
        Vector((-BUCKET_DEPTH*0.9, 0,  BUCKET_HEIGHT*0.25)),
        Vector((-BUCKET_DEPTH,     0,  BUCKET_HEIGHT*0.60)),
        Vector((-BUCKET_DEPTH*0.9, 0,  BUCKET_HEIGHT*1.0)),
        Vector((-BUCKET_DEPTH*0.4, 0,  BUCKET_HEIGHT*1.1)),
        Vector((0.0,               0,  BUCKET_HEIGHT*0.85)),
    ]
    front = [bm.verts.new(Vector((p.x, -hw, p.z))) for p in profile]
    back  = [bm.verts.new(Vector((p.x,  hw, p.z))) for p in profile]
    n = len(profile)
    for i in range(n-1):
        bm.faces.new([front[i], front[i+1], back[i+1], back[i]])
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("ArmBucket", bm, col)
    total = BOOM_ANGLE + STICK_ANGLE_REL - math.radians(15)
    obj.location = stick_tip
    obj.rotation_euler = (0.0, total, 0.0)
    assign_mat(obj, mat_dark)
    return obj


def setup_camera_and_lights() -> None:
    for name in ("SpiderConceptCam", "SpiderKeyLight", "SpiderFillLight", "SpiderRimLight"):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    cam_d = bpy.data.cameras.new("SpiderConceptCam")
    cam_d.lens = 50.0
    cam = bpy.data.objects.new("SpiderConceptCam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (4.0, -3.5, 2.5)
    cam.rotation_euler = (math.radians(65), 0, math.radians(49))
    bpy.context.scene.camera = cam

    key_d = bpy.data.lights.new("SpiderKeyLight", "SUN")
    key_d.energy = 5.0
    key_d.color  = (1.0, 0.92, 0.82)
    key = bpy.data.objects.new("SpiderKeyLight", key_d)
    bpy.context.scene.collection.objects.link(key)
    key.rotation_euler = (math.radians(50), 0, math.radians(-55))

    fill_d = bpy.data.lights.new("SpiderFillLight", "AREA")
    fill_d.energy = 2.0
    fill_d.size   = 5.0
    fill_d.color  = (0.65, 0.80, 1.0)
    fill = bpy.data.objects.new("SpiderFillLight", fill_d)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (-3.5, 2.5, 4.5)
    fill.rotation_euler = (math.radians(-25), 0, math.radians(-115))

    rim_d = bpy.data.lights.new("SpiderRimLight", "SPOT")
    rim_d.energy    = 100.0
    rim_d.spot_size = math.radians(35)
    rim_d.color     = (1.0, 0.85, 0.65)
    rim = bpy.data.objects.new("SpiderRimLight", rim_d)
    bpy.context.scene.collection.objects.link(rim)
    rim.location = (-2.5, -2.5, 5.0)
    rim.rotation_euler = (math.radians(135), 0, math.radians(-135))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    col  = ensure_collection("CompactSpider_Concept")
    mat_orange = make_flat_material("ConceptOrange", ORANGE_LINEAR)
    mat_dark   = make_flat_material("ConceptDark",   DARK_GREY_LINEAR)

    body   = build_body(col, mat_orange)
    sensor = build_sensor_dome(col, mat_orange)

    leg_objs = []
    for i in range(4):
        leg_objs.extend(build_leg(col, mat_dark, i))

    boom, boom_tip     = build_arm_boom(col, mat_dark)
    stick, stick_tip   = build_arm_stick(col, mat_dark, boom_tip)
    bucket             = build_arm_bucket(col, mat_dark, stick_tip)

    all_mesh = [body, sensor, boom, stick, bucket] + leg_objs
    for obj in all_mesh:
        add_multires(obj, levels=2)

    setup_camera_and_lights()

    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    print(f"Compact Spider concept mesh built. {len(all_mesh)} mesh objects.")


if __name__ == "__main__":
    main()
