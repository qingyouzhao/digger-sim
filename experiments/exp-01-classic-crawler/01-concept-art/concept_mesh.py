"""
Concept Silhouette Mesh — EXP-01: Classic Crawler
Blender 4.x base mesh script — Concept Art Director Agent

Design intent: Evoke the iconic tracked excavator silhouette that every child
recognises from picture books and toy boxes. Proportions lean toward a Tonka/
picture-book exaggeration — squat undercarriage, heroic boom arm, oversized
bucket, friendly cab with big windshield. Not photorealistic — archetypal.

This rough mesh is intentionally low-resolution for sculptor handoff via
Multiresolution modifier. The geometry captures the major masses only; surface
detail is left to the sculptor.

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
# Undercarriage / track frame
TRACK_LENGTH     = 2.4   # total track footprint length
TRACK_WIDTH      = 0.55  # width of one track assembly
TRACK_HEIGHT     = 0.28  # height of track assembly (ground to top)
TRACK_SPAN       = 1.30  # centre-to-centre distance between tracks
CHASSIS_LENGTH   = 1.80
CHASSIS_WIDTH    = 1.10
CHASSIS_HEIGHT   = 0.28

# Upper body (house / slew ring area)
HOUSE_LENGTH     = 1.40
HOUSE_WIDTH      = 1.00
HOUSE_HEIGHT     = 0.32

# Cab
CAB_LENGTH       = 0.70
CAB_WIDTH        = 0.68
CAB_HEIGHT       = 0.60
CAB_OFFSET_X     = 0.25   # forward of house centre
CAB_OFFSET_Z     = 0.32   # raised above house

# Counterweight
CW_LENGTH        = 0.40
CW_WIDTH         = 0.90
CW_HEIGHT        = 0.38

# Boom (main arm section)
BOOM_LENGTH      = 1.60
BOOM_THICKNESS   = 0.20
BOOM_WIDTH       = 0.24
BOOM_ANGLE       = math.radians(38)   # angle from horizontal

# Stick (forearm)
STICK_LENGTH     = 1.20
STICK_THICKNESS  = 0.15
STICK_WIDTH      = 0.18
STICK_ANGLE      = math.radians(-50)  # relative to boom tip, angled down

# Bucket
BUCKET_WIDTH     = 0.64
BUCKET_HEIGHT    = 0.38
BUCKET_DEPTH     = 0.36

# Flat construction yellow (linear sRGB approximation)
YELLOW_LINEAR    = (0.855, 0.467, 0.008, 1.0)

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
                 collection: bpy.types.Collection) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def box_bm(lx: float, ly: float, lz: float) -> bmesh.types.BMesh:
    """Return a bmesh box centred at origin with half-extents lx, ly, lz."""
    bm = bmesh.new()
    verts = [
        bm.verts.new(Vector((sx * lx, sy * ly, sz * lz)))
        for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
    ]
    # Indices into verts list: (sx,sy,sz) -> index = sx_i*4 + sy_i*2 + sz_i
    faces = [
        (0, 2, 3, 1),   # -X
        (4, 5, 7, 6),   # +X
        (0, 1, 5, 4),   # -Y
        (2, 6, 7, 3),   # +Y
        (0, 4, 6, 2),   # -Z
        (1, 3, 7, 5),   # +Z
    ]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def trapezoid_bm(lx_bot: float, lx_top: float, ly: float, lz: float) -> bmesh.types.BMesh:
    """A box tapered in X: wider at bottom (-Z), narrower at top (+Z)."""
    bm = bmesh.new()
    verts = [
        bm.verts.new(Vector((-lx_bot, -ly, -lz))),
        bm.verts.new(Vector(( lx_bot, -ly, -lz))),
        bm.verts.new(Vector(( lx_bot,  ly, -lz))),
        bm.verts.new(Vector((-lx_bot,  ly, -lz))),
        bm.verts.new(Vector((-lx_top, -ly,  lz))),
        bm.verts.new(Vector(( lx_top, -ly,  lz))),
        bm.verts.new(Vector(( lx_top,  ly,  lz))),
        bm.verts.new(Vector((-lx_top,  ly,  lz))),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 4, 7, 3),
    ]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def make_flat_material(name: str, color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Metallic"].default_value = 0.0
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    output.location = (300, 0)
    bsdf.location = (0, 0)
    return mat


def apply_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def add_multires(obj: bpy.types.Object, levels: int = 2) -> None:
    mod = obj.modifiers.new("Multiresolution", "MULTIRES")
    for _ in range(levels):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.multires_subdivide(modifier="Multiresolution", mode='LINEAR')


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_tracks(col: bpy.types.Collection, mat: bpy.types.Material) -> list:
    """Two track assemblies — long rectangular pads, low and wide."""
    objects = []
    for side, offset_y in (("L", TRACK_SPAN * 0.5), ("R", -TRACK_SPAN * 0.5)):
        bm = box_bm(TRACK_LENGTH * 0.5, TRACK_WIDTH * 0.5, TRACK_HEIGHT * 0.5)
        obj = new_mesh_obj(f"Track_{side}", bm, col)
        obj.location = (0.0, offset_y, TRACK_HEIGHT * 0.5)
        apply_material(obj, mat)
        objects.append(obj)
    return objects


def build_chassis(col: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    """Lower chassis plate sitting on top of tracks."""
    bm = box_bm(CHASSIS_LENGTH * 0.5, CHASSIS_WIDTH * 0.5, CHASSIS_HEIGHT * 0.5)
    obj = new_mesh_obj("Chassis", bm, col)
    obj.location = (0.0, 0.0, TRACK_HEIGHT + CHASSIS_HEIGHT * 0.5)
    apply_material(obj, mat)
    return obj


def build_house(col: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    """Upper rotating house / engine compartment."""
    bm = trapezoid_bm(
        HOUSE_LENGTH * 0.5, HOUSE_LENGTH * 0.45,
        HOUSE_WIDTH * 0.5,
        HOUSE_HEIGHT * 0.5
    )
    obj = new_mesh_obj("House", bm, col)
    house_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT * 0.5
    obj.location = (0.0, 0.0, house_z)
    apply_material(obj, mat)
    return obj


def build_counterweight(col: bpy.types.Collection,
                        mat: bpy.types.Material) -> bpy.types.Object:
    """Rounded slab at rear balancing the boom weight."""
    bm = bmesh.new()
    # Slightly rounded block — chamfer not done here (left for multires sculptor)
    verts = [
        bm.verts.new(Vector((sx * CW_LENGTH * 0.5, sy * CW_WIDTH * 0.5, sz * CW_HEIGHT * 0.5)))
        for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Counterweight", bm, col)
    cw_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT * 0.5
    obj.location = (-(HOUSE_LENGTH * 0.5 + CW_LENGTH * 0.5 - 0.05),
                    0.0, cw_z)
    apply_material(obj, mat)
    return obj


def build_cab(col: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    """Cab greenhouse — trapezoid wider at base, raked front glass."""
    bm = trapezoid_bm(
        CAB_LENGTH * 0.5, CAB_LENGTH * 0.38,
        CAB_WIDTH  * 0.5,
        CAB_HEIGHT * 0.5
    )
    obj = new_mesh_obj("Cab", bm, col)
    cab_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT + CAB_OFFSET_Z + CAB_HEIGHT * 0.5
    obj.location = (CAB_OFFSET_X, 0.0, cab_z)
    apply_material(obj, mat)
    return obj


def build_boom(col: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    """Main boom arm — tapered box rotated to BOOM_ANGLE."""
    # Build tapered box (wide at pivot, narrow at tip) along local X
    bm = bmesh.new()
    hw_base = BOOM_THICKNESS * 0.5
    hw_tip  = BOOM_THICKNESS * 0.30
    hd      = BOOM_WIDTH * 0.5
    verts = [
        bm.verts.new(Vector((0,            -hd, -hw_base))),
        bm.verts.new(Vector((BOOM_LENGTH,  -hd, -hw_tip))),
        bm.verts.new(Vector((BOOM_LENGTH,   hd, -hw_tip))),
        bm.verts.new(Vector((0,             hd, -hw_base))),
        bm.verts.new(Vector((0,            -hd,  hw_base))),
        bm.verts.new(Vector((BOOM_LENGTH,  -hd,  hw_tip))),
        bm.verts.new(Vector((BOOM_LENGTH,   hd,  hw_tip))),
        bm.verts.new(Vector((0,             hd,  hw_base))),
    ]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(1,2,6,5),(0,4,7,3)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Boom", bm, col)
    # Position at front of house, pivot near base
    pivot_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT * 0.5
    obj.location = (HOUSE_LENGTH * 0.5 - 0.05, 0.0, pivot_z + 0.05)
    obj.rotation_euler = (0.0, -BOOM_ANGLE, 0.0)
    apply_material(obj, mat)
    return obj


def boom_tip_world(boom_obj: bpy.types.Object) -> Vector:
    """Approximate world position of boom tip after rotation."""
    local_tip = Vector((BOOM_LENGTH, 0, 0))
    pivot = Vector(boom_obj.location)
    rot_y = -BOOM_ANGLE
    # Rotate local_tip around Y
    rx = local_tip.x * math.cos(rot_y) - local_tip.z * math.sin(rot_y)
    rz = local_tip.x * math.sin(rot_y) + local_tip.z * math.cos(rot_y)
    return pivot + Vector((rx, 0, rz))


def build_stick(col: bpy.types.Collection, mat: bpy.types.Material,
                boom_obj: bpy.types.Object) -> bpy.types.Object:
    """Stick (forearm) hanging from boom tip."""
    bm = bmesh.new()
    hw_base = STICK_THICKNESS * 0.5
    hw_tip  = STICK_THICKNESS * 0.30
    hd      = STICK_WIDTH * 0.5
    verts = [
        bm.verts.new(Vector((0,            -hd, -hw_base))),
        bm.verts.new(Vector((STICK_LENGTH, -hd, -hw_tip))),
        bm.verts.new(Vector((STICK_LENGTH,  hd, -hw_tip))),
        bm.verts.new(Vector((0,             hd, -hw_base))),
        bm.verts.new(Vector((0,            -hd,  hw_base))),
        bm.verts.new(Vector((STICK_LENGTH, -hd,  hw_tip))),
        bm.verts.new(Vector((STICK_LENGTH,  hd,  hw_tip))),
        bm.verts.new(Vector((0,             hd,  hw_base))),
    ]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(1,2,6,5),(0,4,7,3)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Stick", bm, col)
    tip = boom_tip_world(boom_obj)
    obj.location = tip
    # Stick angle: boom angle minus stick relative angle
    obj.rotation_euler = (0.0, -(BOOM_ANGLE + STICK_ANGLE), 0.0)
    apply_material(obj, mat)
    return obj


def stick_tip_world(stick_obj: bpy.types.Object) -> Vector:
    pivot = Vector(stick_obj.location)
    angle = stick_obj.rotation_euler.y
    rx = STICK_LENGTH * math.cos(-angle)
    rz = STICK_LENGTH * math.sin(-angle)
    return pivot + Vector((rx, 0, rz))


def build_bucket(col: bpy.types.Collection, mat: bpy.types.Material,
                 stick_obj: bpy.types.Object) -> bpy.types.Object:
    """Curved excavator bucket — the most iconic element."""
    bm = bmesh.new()
    hw = BUCKET_WIDTH * 0.5
    # 6-vertex profile rotated: back plate, sides, curved bottom, cutting edge
    profile = [
        Vector((0.0,           0.0,              0.0)),
        Vector((-BUCKET_DEPTH * 0.6, 0.0,  BUCKET_HEIGHT * 0.3)),
        Vector((-BUCKET_DEPTH,       0.0,  BUCKET_HEIGHT * 0.6)),
        Vector((-BUCKET_DEPTH * 1.0, 0.0,  BUCKET_HEIGHT * 1.0)),
        Vector((-BUCKET_DEPTH * 0.4, 0.0,  BUCKET_HEIGHT * 1.1)),
        Vector(( 0.0,                0.0,  BUCKET_HEIGHT * 0.9)),
    ]
    # Extrude profile in Y to create bucket shell
    front_verts = [bm.verts.new(Vector((p.x, -hw, p.z))) for p in profile]
    back_verts  = [bm.verts.new(Vector((p.x,  hw, p.z))) for p in profile]
    n = len(profile)
    # Side walls
    for i in range(n - 1):
        bm.faces.new([front_verts[i], front_verts[i+1],
                      back_verts[i+1], back_verts[i]])
    # Front and back caps
    bm.faces.new(front_verts[::-1])
    bm.faces.new(back_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Bucket", bm, col)
    tip = stick_tip_world(stick_obj)
    obj.location = tip
    # Bucket rotated to point teeth forward-downward
    total_angle = BOOM_ANGLE + STICK_ANGLE + math.radians(-20)
    obj.rotation_euler = (0.0, total_angle, 0.0)
    apply_material(obj, mat)
    return obj


def setup_camera_and_lights() -> None:
    """3-point lighting + concept presentation camera."""
    # --- Camera ---
    cam_data = bpy.data.cameras.new("ConceptCam")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new("ConceptCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = Vector((4.5, -4.0, 2.8))
    cam_obj.rotation_euler = (math.radians(68), 0.0, math.radians(48))
    bpy.context.scene.camera = cam_obj

    # --- Key light (warm sun from upper left) ---
    key_data = bpy.data.lights.new("KeyLight", "SUN")
    key_data.energy = 4.0
    key_data.color = (1.0, 0.95, 0.85)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    bpy.context.scene.collection.objects.link(key_obj)
    key_obj.rotation_euler = (math.radians(55), 0.0, math.radians(-45))

    # --- Fill light (cool sky from right) ---
    fill_data = bpy.data.lights.new("FillLight", "AREA")
    fill_data.energy = 1.5
    fill_data.size = 6.0
    fill_data.color = (0.7, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = Vector((-4.0, 3.0, 4.0))
    fill_obj.rotation_euler = (math.radians(-30), 0.0, math.radians(-120))

    # --- Rim light (back highlight) ---
    rim_data = bpy.data.lights.new("RimLight", "SPOT")
    rim_data.energy = 80.0
    rim_data.spot_size = math.radians(40)
    rim_data.color = (1.0, 0.9, 0.7)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.location = Vector((-3.0, -3.0, 5.0))
    rim_obj.rotation_euler = (math.radians(140), 0.0, math.radians(-140))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Setup — deselect all, remove pre-existing concept objects
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    existing_names = {
        "Track_L", "Track_R", "Chassis", "House", "Counterweight",
        "Cab", "Boom", "Stick", "Bucket",
        "ConceptCam", "KeyLight", "FillLight", "RimLight",
    }
    for name in existing_names:
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            bpy.data.objects.remove(obj, do_unlink=True)

    # 2. Collection and material
    col = ensure_collection("ClassicCrawler_Concept")
    mat = make_flat_material("ConceptYellow", YELLOW_LINEAR)

    # 3. Build geometry in construction order (bottom up)
    tracks    = build_tracks(col, mat)
    chassis   = build_chassis(col, mat)
    house     = build_house(col, mat)
    cw        = build_counterweight(col, mat)
    cab       = build_cab(col, mat)
    boom      = build_boom(col, mat)
    stick     = build_stick(col, mat, boom)
    bucket    = build_bucket(col, mat, stick)

    # 4. Multiresolution on all mesh objects for sculptor handoff
    all_mesh_objs = tracks + [chassis, house, cw, cab, boom, stick, bucket]
    for obj in all_mesh_objs:
        add_multires(obj, levels=2)

    # 5. Camera + lighting
    setup_camera_and_lights()

    # 6. Cleanup — deselect everything
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    print("Classic Crawler concept mesh built. Collection: ClassicCrawler_Concept")
    print(f"Objects created: {len(all_mesh_objs)} mesh objects + camera + 3 lights")


if __name__ == "__main__":
    main()
