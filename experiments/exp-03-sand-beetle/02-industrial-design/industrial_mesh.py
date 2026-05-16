"""Sand Beetle — Industrial Design Mesh / Blender 4.x / Industrial Designer Agent"""

import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
SHELL_RX       = 0.55
SHELL_RY       = 0.42
SHELL_RZ       = 0.22
SHELL_SEGS_U   = 32
SHELL_SEGS_V   = 24

TRACK_RADIUS   = 0.14
TRACK_LENGTH   = 0.52
TRACK_SEGS     = 24
TRACK_OFFSET_X = 0.38
TRACK_OFFSET_Y = 0.05

ARM_LENGTH     = 0.65
ARM_WIDTH      = 0.12
BOOM_TAPER     = 0.7

BUCKET_WIDTH   = 0.32
BUCKET_DEPTH   = 0.14
BUCKET_HEIGHT  = 0.10

JOINT_RING_R   = 0.065
JOINT_RING_W   = 0.018

# ---------------------------------------------------------------------------
# COLORS  (linear sRGB)
# ---------------------------------------------------------------------------
TONKA_YELLOW = (0.92, 0.62, 0.08, 1.0)   # roughness=0.75  metallic=0.0
BLACK_RUBBER  = (0.04, 0.04, 0.04, 1.0)  # roughness=0.92  metallic=0.0
CHROME        = (0.75, 0.75, 0.78, 1.0)  # roughness=0.08  metallic=1.0


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name: str) -> bpy.types.Collection:
    """Return existing collection by name or create it and link to the scene."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    """Link object to collection, removing from any current collections."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def new_mesh_obj(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Commit bmesh to a new mesh data-block and return a new object."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    return obj


def make_pbr_material(
    name: str,
    color: tuple,
    roughness: float,
    metallic: float,
) -> bpy.types.Material:
    """Create a Principled BSDF PBR material; reuse if already created."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_shell(col: bpy.types.Collection) -> bpy.types.Object:
    """Precise UV sphere scaled to an oblate spheroid (SHELL_RX, SHELL_RY, SHELL_RZ).

    Uses bmesh.ops.create_uvsphere then bmesh.ops.scale for parametric control.
    """
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
    bm.normal_update()

    obj = new_mesh_obj("Shell", bm)
    link_to(obj, col)

    mat = make_pbr_material("TonkaYellow", TONKA_YELLOW, 0.75, 0.0)
    obj.data.materials.append(mat)
    return obj


def build_track(col: bpy.types.Collection, side: int) -> bpy.types.Object:
    """Precision cylinder track pod for left (side=-1) or right (side=+1).

    Uses bmesh.ops.create_cone with equal radii (cylinder). Applies black rubber
    PBR material and positions the pod symmetrically on the X axis.
    """
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
    # Rotate so the long axis runs along Y (fore/aft of vehicle)
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=Matrix.Rotation(math.pi / 2, 3, "X"),
        verts=bm.verts,
    )
    bm.normal_update()

    label = "Track_R" if side > 0 else "Track_L"
    obj = new_mesh_obj(label, bm)
    obj.location = Vector((side * TRACK_OFFSET_X, TRACK_OFFSET_Y, -SHELL_RZ * 0.65))
    link_to(obj, col)

    mat = make_pbr_material("BlackRubber", BLACK_RUBBER, 0.92, 0.0)
    obj.data.materials.append(mat)
    return obj


def build_boom(col: bpy.types.Collection) -> bpy.types.Object:
    """Tapered rectangular boom arm.

    Bottom (base) cross-section is full ARM_WIDTH; top (tip) cross-section is
    ARM_WIDTH * BOOM_TAPER. Manual bmesh construction — bmesh.ops has no taper-box
    primitive.
    """
    bm = bmesh.new()
    hw_base = ARM_WIDTH * 0.5
    hw_tip  = hw_base * BOOM_TAPER
    hd      = ARM_WIDTH * 0.45   # depth half-extent (slightly less than width)

    # 8 verts: 4 at base (Y=0), 4 at tip (Y=ARM_LENGTH)
    v = [
        bm.verts.new((-hw_base,  0.0,        -hd)),
        bm.verts.new(( hw_base,  0.0,        -hd)),
        bm.verts.new(( hw_base,  0.0,         hd)),
        bm.verts.new((-hw_base,  0.0,         hd)),
        bm.verts.new((-hw_tip,   ARM_LENGTH, -hd * BOOM_TAPER)),
        bm.verts.new(( hw_tip,   ARM_LENGTH, -hd * BOOM_TAPER)),
        bm.verts.new(( hw_tip,   ARM_LENGTH,  hd * BOOM_TAPER)),
        bm.verts.new((-hw_tip,   ARM_LENGTH,  hd * BOOM_TAPER)),
    ]
    face_indices = [
        (0, 1, 2, 3),  # base cap
        (4, 5, 6, 7),  # tip cap
        (0, 1, 5, 4),  # bottom face
        (2, 3, 7, 6),  # top face
        (1, 2, 6, 5),  # right face
        (3, 0, 4, 7),  # left face
    ]
    for fi in face_indices:
        bm.faces.new([v[i] for i in fi])
    bm.normal_update()

    obj = new_mesh_obj("Boom", bm)
    obj.location = Vector((0.0, SHELL_RY * 0.88, -SHELL_RZ * 0.08))
    link_to(obj, col)

    mat = make_pbr_material("TonkaYellow", TONKA_YELLOW, 0.75, 0.0)
    obj.data.materials.append(mat)
    return obj


def build_bucket(col: bpy.types.Collection) -> bpy.types.Object:
    """Wide shallow open-U bucket.

    3 quad faces: back wall + left side + right side. No front face, no top.
    bmesh manual construction (no bmesh.ops primitive for open U-shape).
    """
    bm = bmesh.new()
    bw = BUCKET_WIDTH * 0.5
    bd = BUCKET_DEPTH
    bh = BUCKET_HEIGHT

    # 8 verts defining the U envelope
    v = [
        # rear edge  (Y=0)
        bm.verts.new((-bw, 0.0, 0.0)),   # 0  rear-left-bottom
        bm.verts.new(( bw, 0.0, 0.0)),   # 1  rear-right-bottom
        bm.verts.new(( bw, 0.0, bh )),   # 2  rear-right-top
        bm.verts.new((-bw, 0.0, bh )),   # 3  rear-left-top
        # front edge (Y=bd)
        bm.verts.new((-bw, bd,  0.0)),   # 4  front-left-bottom
        bm.verts.new(( bw, bd,  0.0)),   # 5  front-right-bottom
        bm.verts.new(( bw, bd,  bh )),   # 6  front-right-top
        bm.verts.new((-bw, bd,  bh )),   # 7  front-left-top
    ]
    # Back wall, bottom floor, left side, right side
    face_indices = [
        (0, 1, 2, 3),  # back wall
        (0, 4, 5, 1),  # bottom floor
        (0, 3, 7, 4),  # left side
        (1, 5, 6, 2),  # right side
    ]
    for fi in face_indices:
        bm.faces.new([v[i] for i in fi])
    bm.normal_update()

    obj = new_mesh_obj("Bucket", bm)
    obj.location = Vector((
        -BUCKET_WIDTH * 0.5,
        SHELL_RY * 0.88 + ARM_LENGTH,
        -SHELL_RZ * 0.08 - BUCKET_HEIGHT * 0.5,
    ))
    link_to(obj, col)

    mat = make_pbr_material("TonkaYellow", TONKA_YELLOW, 0.75, 0.0)
    obj.data.materials.append(mat)
    return obj


def build_joint_ring(
    col: bpy.types.Collection,
    location: Vector,
) -> bpy.types.Object:
    """Thin decorative chrome ring at a boom joint.

    Approximated as a short cylinder (JOINT_RING_W depth, JOINT_RING_R radius)
    using bmesh.ops.create_cone with equal radii. Oriented so the ring plane
    faces along Y (the boom axis).
    """
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=32,
        radius1=JOINT_RING_R,
        radius2=JOINT_RING_R,
        depth=JOINT_RING_W,
    )
    # Rotate so ring face is perpendicular to boom (Y axis)
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=Matrix.Rotation(math.pi / 2, 3, "X"),
        verts=bm.verts,
    )
    bm.normal_update()

    name = f"JointRing_{id(location)}"
    obj = new_mesh_obj(name, bm)
    obj.location = location
    link_to(obj, col)

    mat = make_pbr_material("Chrome", CHROME, 0.08, 1.0)
    obj.data.materials.append(mat)
    return obj


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    """Build the complete Sand Beetle industrial design mesh."""
    # Clear scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    col = ensure_collection("SandBeetle")

    # Shell body (centred at origin)
    shell = build_shell(col)

    # Track pods — symmetric on X, slightly forward on Y
    track_r = build_track(col, side= 1)
    track_l = build_track(col, side=-1)

    # Arm: boom at shell front, bucket at boom tip
    boom   = build_boom(col)
    bucket = build_bucket(col)

    # Chrome joint rings: one at boom base, one at boom tip (bucket pivot)
    ring_base = build_joint_ring(
        col,
        location=Vector((0.0, SHELL_RY * 0.88, -SHELL_RZ * 0.08)),
    )
    ring_tip = build_joint_ring(
        col,
        location=Vector((0.0, SHELL_RY * 0.88 + ARM_LENGTH, -SHELL_RZ * 0.08)),
    )

    # Parent arm assembly to shell so body rotation carries them
    boom.parent   = shell
    bucket.parent = shell
    ring_base.parent = shell
    ring_tip.parent  = shell

    # Final deselect
    bpy.ops.object.select_all(action="DESELECT")

    print("Sand Beetle industrial mesh built successfully.")


if __name__ == "__main__":
    main()
