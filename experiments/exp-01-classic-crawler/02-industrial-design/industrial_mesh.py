"""
Industrial Design Mesh — EXP-01: Classic Crawler
Blender 4.x parametric mesh script — Industrial Designer Agent

Builds a precise parametric excavator from the CMF spec. Each component is
a separate named object with PBR material. Hierarchy mirrors the component
breakdown table in spec.md. All dimensions are in metres; designed for a
5-metre-long real-world machine scaled proportionally.

Prerequisites: Blender 4.x, no add-ons required.
Run from: Scripting workspace > Run Script.
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# ---------------------------------------------------------------------------
# PARAMETERS (metres, matching spec.md component breakdown)
# ---------------------------------------------------------------------------

# Undercarriage
TRACK_LENGTH        = 2.60
TRACK_WIDTH         = 0.52
TRACK_HEIGHT        = 0.30
TRACK_SPAN          = 1.40    # centre-to-centre Y
CHASSIS_LENGTH      = 1.90
CHASSIS_WIDTH       = 1.15
CHASSIS_HEIGHT      = 0.22
CHASSIS_CHAMFER     = 0.04

# Upper house
HOUSE_LENGTH        = 1.60
HOUSE_WIDTH         = 1.05
HOUSE_HEIGHT        = 0.36
HOUSE_FRONT_TAPER   = 0.12   # narrowing of front vs rear in X

# Counterweight
CW_LENGTH           = 0.50
CW_WIDTH            = 0.95
CW_HEIGHT           = 0.44
CW_RADIUS           = 0.10   # corner rounding (approximated by chamfer)

# Cab
CAB_OFFSET_X        = 0.26   # forward from house centre
CAB_OFFSET_Y        =-0.22   # left side (negative Y = left)
CAB_LENGTH          = 0.75
CAB_WIDTH           = 0.65
CAB_HEIGHT          = 0.65
CAB_BASE_BEVEL      = 0.06   # base bevel for industrial quality feel

# Boom arm
BOOM_LENGTH         = 1.70
BOOM_W_BASE         = 0.26   # width at pivot
BOOM_H_BASE         = 0.22   # thickness at pivot
BOOM_W_TIP          = 0.18
BOOM_H_TIP          = 0.15
BOOM_PIVOT_X        = 0.55   # X offset from house front for pivot
BOOM_PIVOT_Z        = 0.20   # Z offset above house top
BOOM_ANGLE          = math.radians(40)

# Stick arm
STICK_LENGTH        = 1.25
STICK_W_BASE        = 0.18
STICK_H_BASE        = 0.15
STICK_W_TIP         = 0.12
STICK_H_TIP         = 0.10
STICK_ANGLE         = math.radians(-52)  # relative to boom, angled down

# Bucket
BUCKET_WIDTH        = 0.70
BUCKET_HEIGHT       = 0.42
BUCKET_DEPTH        = 0.38
BUCKET_TOOTH_COUNT  = 4
BUCKET_TOOTH_LENGTH = 0.14
BUCKET_TOOTH_WIDTH  = 0.08
BUCKET_TOOTH_HEIGHT = 0.06
BUCKET_ANGLE_OFFSET = math.radians(-18)

# Hydraulic cylinders
CYL_BOOM_RADIUS     = 0.05
CYL_STICK_RADIUS    = 0.04
CYL_BUCKET_RADIUS   = 0.035

# ---------------------------------------------------------------------------
# COLORS — linear sRGB (from CMF spec)
# ---------------------------------------------------------------------------
COLOR_YELLOW        = (0.855, 0.467, 0.008, 1.0)   # Gasco Construction Yellow
COLOR_GLASS         = (0.220, 0.580, 0.660, 1.0)   # Cab glazing (blue-green tint)
COLOR_TRACK         = (0.014, 0.014, 0.014, 1.0)   # Charcoal black
COLOR_TOOTH         = (0.280, 0.280, 0.280, 1.0)   # Steel grey
COLOR_CHROME        = (0.580, 0.580, 0.580, 1.0)   # Hydraulic rods

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    if obj.name not in col.objects:
        col.objects.link(obj)


def new_mesh_obj(name: str, bm: bmesh.types.BMesh,
                 col: bpy.types.Collection) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    # Remove existing object with same name
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def make_pbr_material(name: str,
                      base_color: tuple,
                      roughness: float = 0.5,
                      metallic: float  = 0.0,
                      alpha: float     = 1.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat:
        mat.node_tree.nodes.clear()
    else:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    r, g, b, a = base_color
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = "BLEND"
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def tapered_box_bm(w_base: float, h_base: float,
                   w_tip:  float, h_tip:  float,
                   length: float) -> bmesh.types.BMesh:
    """Box along +X, tapered from (w_base,h_base) at X=0 to (w_tip,h_tip) at X=length."""
    bm = bmesh.new()
    verts = [
        bm.verts.new(Vector((0,      -w_base/2, -h_base/2))),
        bm.verts.new(Vector((0,       w_base/2, -h_base/2))),
        bm.verts.new(Vector((0,       w_base/2,  h_base/2))),
        bm.verts.new(Vector((0,      -w_base/2,  h_base/2))),
        bm.verts.new(Vector((length, -w_tip/2,  -h_tip/2))),
        bm.verts.new(Vector((length,  w_tip/2,  -h_tip/2))),
        bm.verts.new(Vector((length,  w_tip/2,   h_tip/2))),
        bm.verts.new(Vector((length, -w_tip/2,   h_tip/2))),
    ]
    faces = [
        (0, 3, 2, 1),   # -X base
        (4, 5, 6, 7),   # +X tip
        (0, 1, 5, 4),   # -Y
        (2, 3, 7, 6),   # +Y
        (1, 2, 6, 5),   # +Z
        (0, 4, 7, 3),   # -Z
    ]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cylinder_bm(radius: float, length: float, segments: int = 12) -> bmesh.types.BMesh:
    """Cylinder along X axis."""
    bm = bmesh.new()
    def ring(x):
        return [bm.verts.new(Vector((x,
                                    radius * math.cos(2*math.pi*i/segments),
                                    radius * math.sin(2*math.pi*i/segments))))
                for i in range(segments)]
    r0 = ring(0)
    r1 = ring(length)
    for i in range(segments):
        ni = (i + 1) % segments
        bm.faces.new([r0[i], r0[ni], r1[ni], r1[i]])
    bm.faces.new(r0[::-1])
    bm.faces.new(r1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_track(col, mat_track, side_sign: float, name: str) -> bpy.types.Object:
    bm = bmesh.new()
    hw = TRACK_HEIGHT / 2
    hl = TRACK_LENGTH / 2
    hd = TRACK_WIDTH  / 2
    verts = [
        bm.verts.new(Vector((sx*hl, sy*hd, sz*hw)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj(name, bm, col)
    obj.location = (0.0, side_sign * TRACK_SPAN / 2, TRACK_HEIGHT / 2)
    assign_mat(obj, mat_track)
    return obj


def build_chassis(col, mat_yellow) -> bpy.types.Object:
    bm = bmesh.new()
    hl = CHASSIS_LENGTH / 2
    hw = CHASSIS_WIDTH  / 2
    hh = CHASSIS_HEIGHT / 2
    verts = [
        bm.verts.new(Vector((sx*hl, sy*hw, sz*hh)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Chassis", bm, col)
    obj.location = (0.0, 0.0, TRACK_HEIGHT + CHASSIS_HEIGHT / 2)
    assign_mat(obj, mat_yellow)
    return obj


def build_house(col, mat_yellow) -> bpy.types.Object:
    """Trapezoidal house — wider front, narrowing toward rear."""
    bm = bmesh.new()
    hl   = HOUSE_LENGTH / 2
    hw   = HOUSE_WIDTH  / 2
    hh   = HOUSE_HEIGHT / 2
    taper = HOUSE_FRONT_TAPER / 2  # half-taper per side
    # Front face wider, rear face same width (taper in X only)
    verts = [
        bm.verts.new(Vector((-hl,         -hw, -hh))),
        bm.verts.new(Vector((-hl,          hw, -hh))),
        bm.verts.new(Vector(( hl + taper, -hw, -hh))),
        bm.verts.new(Vector(( hl + taper,  hw, -hh))),
        bm.verts.new(Vector((-hl,         -hw,  hh))),
        bm.verts.new(Vector((-hl,          hw,  hh))),
        bm.verts.new(Vector(( hl + taper, -hw,  hh))),
        bm.verts.new(Vector(( hl + taper,  hw,  hh))),
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("House", bm, col)
    house_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT / 2
    obj.location = (0.0, 0.0, house_z)
    assign_mat(obj, mat_yellow)
    return obj


def build_counterweight(col, mat_yellow) -> bpy.types.Object:
    bm = bmesh.new()
    hl = CW_LENGTH / 2
    hw = CW_WIDTH  / 2
    hh = CW_HEIGHT / 2
    verts = [
        bm.verts.new(Vector((sx*hl, sy*hw, sz*hh)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_mesh_obj("Counterweight", bm, col)
    cw_z = TRACK_HEIGHT + CHASSIS_HEIGHT + CW_HEIGHT / 2
    cw_x = -(HOUSE_LENGTH / 2 + CW_LENGTH / 2 - 0.06)
    obj.location = (cw_x, 0.0, cw_z)
    assign_mat(obj, mat_yellow)
    return obj


def build_cab(col, mat_yellow, mat_glass) -> list:
    """Cab body + glazing as separate objects."""
    base_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT

    # Cab body
    bm = tapered_box_bm(CAB_WIDTH, CAB_HEIGHT * 0.12,
                        CAB_WIDTH * 0.85, CAB_HEIGHT,
                        CAB_LENGTH)
    bm_body = bmesh.new()
    hw = CAB_WIDTH  / 2
    hl = CAB_LENGTH / 2
    hh = CAB_HEIGHT / 2
    bv = 0.06  # bevel stub
    verts = [
        bm_body.verts.new(Vector((sx*hl, sy*hw, sz*hh)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]
    for fi in faces:
        bm_body.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm_body, faces=bm_body.faces)
    bm_body.free()

    bm2 = bmesh.new()
    verts = [
        bm2.verts.new(Vector((sx*hl, sy*hw, sz*hh)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    for fi in faces:
        bm2.faces.new([verts[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)

    cab_obj = new_mesh_obj("Cab", bm2, col)
    cab_obj.location = (CAB_OFFSET_X, CAB_OFFSET_Y, base_z + CAB_HEIGHT / 2)
    assign_mat(cab_obj, mat_yellow)

    # Glazing (front window inset)
    gw = CAB_WIDTH  * 0.75
    gh = CAB_HEIGHT * 0.55
    gd = 0.025
    bm3 = bmesh.new()
    verts_g = [
        bm3.verts.new(Vector((sx*gd/2, sy*gw/2, sz*gh/2)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    for fi in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(1,3,7,5),(0,4,6,2)]:
        bm3.faces.new([verts_g[i] for i in fi])
    bmesh.ops.recalc_face_normals(bm3, faces=bm3.faces)
    glass_obj = new_mesh_obj("CabGlass", bm3, col)
    glass_obj.location = (CAB_OFFSET_X + CAB_LENGTH / 2 + gd / 2,
                          CAB_OFFSET_Y,
                          base_z + CAB_HEIGHT * 0.55)
    assign_mat(glass_obj, mat_glass)

    return [cab_obj, glass_obj]


def get_arm_tip(pivot: Vector, length: float, angle_y: float) -> Vector:
    """World position of arm tip given pivot, arm length, and Y rotation angle."""
    rx = length * math.cos(-angle_y)
    rz = length * math.sin(-angle_y)
    return pivot + Vector((rx, 0, rz))


def build_boom(col, mat_yellow) -> tuple:
    """Returns (boom_obj, tip_position)."""
    bm = tapered_box_bm(BOOM_W_BASE, BOOM_H_BASE,
                        BOOM_W_TIP,  BOOM_H_TIP,
                        BOOM_LENGTH)
    obj = new_mesh_obj("Boom", bm, col)
    house_top_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT
    pivot = Vector((HOUSE_LENGTH / 2 - BOOM_PIVOT_X + 0.1,
                    0.0,
                    house_top_z + BOOM_PIVOT_Z))
    obj.location = pivot
    obj.rotation_euler = (0.0, -BOOM_ANGLE, 0.0)
    assign_mat(obj, mat_yellow)
    tip = get_arm_tip(pivot, BOOM_LENGTH, BOOM_ANGLE)
    return obj, tip


def build_stick(col, mat_yellow, boom_tip: Vector) -> tuple:
    """Returns (stick_obj, tip_position)."""
    bm = tapered_box_bm(STICK_W_BASE, STICK_H_BASE,
                        STICK_W_TIP,  STICK_H_TIP,
                        STICK_LENGTH)
    obj = new_mesh_obj("Stick", bm, col)
    obj.location = boom_tip
    total_angle = BOOM_ANGLE + STICK_ANGLE
    obj.rotation_euler = (0.0, -total_angle, 0.0)
    assign_mat(obj, mat_yellow)
    tip = get_arm_tip(boom_tip, STICK_LENGTH, total_angle)
    return obj, tip


def build_bucket(col, mat_yellow, mat_tooth, stick_tip: Vector) -> list:
    """Bucket body + teeth."""
    bm = bmesh.new()
    hw = BUCKET_WIDTH / 2
    # 7-point profile for swept bucket shape
    profile = [
        Vector((0.0,                              0.0,  0.0)),
        Vector((-BUCKET_DEPTH * 0.40,            0.0, -BUCKET_HEIGHT * 0.10)),
        Vector((-BUCKET_DEPTH * 0.85,            0.0,  BUCKET_HEIGHT * 0.20)),
        Vector((-BUCKET_DEPTH * 1.00,            0.0,  BUCKET_HEIGHT * 0.55)),
        Vector((-BUCKET_DEPTH * 0.95,            0.0,  BUCKET_HEIGHT * 1.00)),
        Vector((-BUCKET_DEPTH * 0.45,            0.0,  BUCKET_HEIGHT * 1.10)),
        Vector(( 0.0,                            0.0,  BUCKET_HEIGHT * 0.90)),
    ]
    front = [bm.verts.new(Vector((p.x, -hw, p.z))) for p in profile]
    back  = [bm.verts.new(Vector((p.x,  hw, p.z))) for p in profile]
    n = len(profile)
    for i in range(n - 1):
        bm.faces.new([front[i], front[i+1], back[i+1], back[i]])
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bucket_obj = new_mesh_obj("Bucket", bm, col)
    total_angle = BOOM_ANGLE + STICK_ANGLE + BUCKET_ANGLE_OFFSET
    bucket_obj.location = stick_tip
    bucket_obj.rotation_euler = (0.0, total_angle, 0.0)
    assign_mat(bucket_obj, mat_yellow)

    # Teeth
    tooth_objs = []
    for i in range(BUCKET_TOOTH_COUNT):
        t_offset_y = -hw + BUCKET_WIDTH / (BUCKET_TOOTH_COUNT + 1) * (i + 1)
        bm_t = tapered_box_bm(BUCKET_TOOTH_WIDTH, BUCKET_TOOTH_HEIGHT,
                               BUCKET_TOOTH_WIDTH * 0.3, BUCKET_TOOTH_HEIGHT * 0.2,
                               BUCKET_TOOTH_LENGTH)
        t_obj = new_mesh_obj(f"BucketTooth_{i:02d}", bm_t, col)
        # Position relative to bucket, at cutting edge (profile[1])
        cx = profile[1].x
        cz = profile[1].z
        t_obj.location = stick_tip + Vector((cx, t_offset_y, cz))
        t_obj.rotation_euler = (0.0, total_angle + math.radians(20), 0.0)
        assign_mat(t_obj, mat_tooth)
        tooth_objs.append(t_obj)

    return [bucket_obj] + tooth_objs


def build_cylinder(col, mat_chrome, name: str,
                   start: Vector, end: Vector, radius: float) -> bpy.types.Object:
    """A hydraulic cylinder rod between two world positions."""
    direction = end - start
    length = direction.length
    bm = cylinder_bm(radius, length, segments=8)
    obj = new_mesh_obj(name, bm, col)
    obj.location = start
    if length > 0.001:
        z_axis = Vector((1, 0, 0))
        d_norm = direction.normalized()
        axis = z_axis.cross(d_norm)
        if axis.length > 0.001:
            angle = z_axis.angle(d_norm)
            obj.rotation_euler = axis.to_track_quat('X', 'Z').to_euler()
        obj.rotation_euler = direction.to_track_quat('X', 'Z').to_euler()
    assign_mat(obj, mat_chrome)
    return obj


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Setup
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    col = ensure_collection("ClassicCrawler_Industrial")

    # 2. Materials
    mat_yellow = make_pbr_material("IDYellow",  COLOR_YELLOW, roughness=0.45, metallic=0.0)
    mat_glass  = make_pbr_material("IDGlass",   COLOR_GLASS,  roughness=0.05, metallic=0.0, alpha=0.75)
    mat_track  = make_pbr_material("IDTrack",   COLOR_TRACK,  roughness=0.85, metallic=0.0)
    mat_tooth  = make_pbr_material("IDTooth",   COLOR_TOOTH,  roughness=0.70, metallic=0.6)
    mat_chrome = make_pbr_material("IDChrome",  COLOR_CHROME, roughness=0.10, metallic=1.0)

    # 3. Build — bottom up
    track_l  = build_track(col, mat_track,  1.0, "Track_L")
    track_r  = build_track(col, mat_track, -1.0, "Track_R")
    chassis  = build_chassis(col, mat_yellow)
    house    = build_house(col, mat_yellow)
    cw       = build_counterweight(col, mat_yellow)
    cab_objs = build_cab(col, mat_yellow, mat_glass)

    boom, boom_tip      = build_boom(col, mat_yellow)
    stick, stick_tip    = build_stick(col, mat_yellow, boom_tip)
    bucket_objs         = build_bucket(col, mat_yellow, mat_tooth, stick_tip)

    # Hydraulic cylinders (approximate positions)
    house_top_z = TRACK_HEIGHT + CHASSIS_HEIGHT + HOUSE_HEIGHT
    cyl_boom_start  = Vector((HOUSE_LENGTH * 0.3, 0.08, house_top_z + 0.18))
    cyl_boom_end    = boom.location + Vector((BOOM_LENGTH * 0.40, 0.08, -0.05))
    build_cylinder(col, mat_chrome, "CylBoom",
                   cyl_boom_start, cyl_boom_end, CYL_BOOM_RADIUS)

    cyl_stick_start = boom.location + Vector((BOOM_LENGTH * 0.70, 0.08, 0.08))
    cyl_stick_end   = stick.location + Vector((STICK_LENGTH * 0.25, 0.08, 0.0))
    build_cylinder(col, mat_chrome, "CylStick",
                   cyl_stick_start, cyl_stick_end, CYL_STICK_RADIUS)

    # 4. Parent hierarchy (house as root of upper assembly)
    objs_to_parent_to_house = [house, cw] + cab_objs + [boom, stick] + bucket_objs
    for obj in [cw] + cab_objs:
        obj.parent = house

    # 5. Cleanup
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    all_objs = ([track_l, track_r, chassis, house, cw, boom, stick]
                + cab_objs + bucket_objs)
    print(f"Classic Crawler industrial mesh built. {len(all_objs)} objects.")


if __name__ == "__main__":
    main()
