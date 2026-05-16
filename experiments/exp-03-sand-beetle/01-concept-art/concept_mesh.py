"""Sand Beetle — Concept Silhouette Mesh / Blender 4.x / Concept Art Director Agent"""

import bpy
import bmesh
from mathutils import Vector

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
SHELL_RX = 0.55
SHELL_RY = 0.42
SHELL_RZ = 0.22

TRACK_RADIUS = 0.14
TRACK_LENGTH = 0.52
TRACK_OFFSET_X = 0.38

ARM_LENGTH = 0.65
BUCKET_WIDTH = 0.32
BUCKET_DEPTH = 0.14

# ---------------------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------------------
TONKA_YELLOW = (0.92, 0.62, 0.08, 1.0)   # roughness=0.75
BLACK_RUBBER  = (0.04, 0.04, 0.04, 1.0)  # roughness=0.95


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def ensure_collection(name: str) -> bpy.types.Collection:
    """Return existing collection by name or create it and link to scene."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    """Link object to collection, unlinking from all current collections first."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def new_mesh_obj(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Create a new mesh data-block from a bmesh and return a new object."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    return obj


def make_flat_material(name: str, color: tuple, roughness: float) -> bpy.types.Material:
    """Create a simple Principled BSDF material with flat shading intent."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


# ---------------------------------------------------------------------------
# BUILD FUNCTIONS
# ---------------------------------------------------------------------------

def build_shell(col: bpy.types.Collection) -> bpy.types.Object:
    """Oblate ellipsoid shell body.

    Construct a UV sphere via bmesh then scale each vertex to (SHELL_RX, SHELL_RY,
    SHELL_RZ). Add a Multiresolution modifier (2 levels, Catmull-Clark) for
    sculptor handoff.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=1.0)
    # Scale verts to ellipsoid proportions
    bmesh.ops.scale(bm, vec=Vector((SHELL_RX, SHELL_RY, SHELL_RZ)), verts=bm.verts)

    obj = new_mesh_obj("Shell", bm)
    link_to(obj, col)

    # Multiresolution for sculptor handoff
    mod = obj.modifiers.new("Multires", "MULTIRES")
    mod.subdivision_type = "CATMULL_CLARK"
    for _ in range(2):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.multires_subdivide(modifier="Multires", mode="CATMULL_CLARK")

    mat = make_flat_material("TonkaYellow", TONKA_YELLOW, 0.75)
    obj.data.materials.append(mat)
    return obj


def build_track(col: bpy.types.Collection, side: int) -> bpy.types.Object:
    """Barrel cylinder track pod for left (side=-1) or right (side=+1).

    Uses bmesh cone op with equal top and bottom radius to produce a cylinder,
    then caps are kept round by vertex-level sphere-project approximation on the
    end rings.
    """
    bm = bmesh.new()
    # create_cone with equal radii == cylinder; depth along local Z
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=TRACK_RADIUS,
        radius2=TRACK_RADIUS,
        depth=TRACK_LENGTH,
    )

    # Soften end caps: nudge outermost end-ring verts slightly inward to suggest rounding
    max_z = max(v.co.z for v in bm.verts)
    min_z = min(v.co.z for v in bm.verts)
    cap_thresh = TRACK_LENGTH * 0.42
    for v in bm.verts:
        if abs(v.co.z) > cap_thresh:
            shrink = 0.88
            v.co.x *= shrink
            v.co.y *= shrink

    # Rotate so the cylinder axis runs along Y (forward/back)
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=__import__("mathutils").Matrix.Rotation(1.5707963, 3, "X"),
        verts=bm.verts,
    )

    obj = new_mesh_obj(f"Track_{'R' if side > 0 else 'L'}", bm)
    obj.location = (side * TRACK_OFFSET_X, 0.0, -SHELL_RZ * 0.6)
    link_to(obj, col)

    mat = make_flat_material("BlackRubber", BLACK_RUBBER, 0.95)
    obj.data.materials.append(mat)
    return obj


def build_arm(col: bpy.types.Collection) -> bpy.types.Object:
    """Chunky arm assembly: tapered boom box + wide shallow bucket (open U)."""
    import mathutils

    # --- Boom ---
    bm_boom = bmesh.new()
    hw = 0.07   # half-width at base
    hd = 0.06   # half-depth
    # 8 verts: base quad (wider) + tip quad (narrower)
    tip_scale = 0.65
    verts = [
        bm_boom.verts.new((-hw,          0.0,        -hd)),
        bm_boom.verts.new(( hw,          0.0,        -hd)),
        bm_boom.verts.new(( hw,          0.0,         hd)),
        bm_boom.verts.new((-hw,          0.0,         hd)),
        bm_boom.verts.new((-hw*tip_scale, ARM_LENGTH, -hd*tip_scale)),
        bm_boom.verts.new(( hw*tip_scale, ARM_LENGTH, -hd*tip_scale)),
        bm_boom.verts.new(( hw*tip_scale, ARM_LENGTH,  hd*tip_scale)),
        bm_boom.verts.new((-hw*tip_scale, ARM_LENGTH,  hd*tip_scale)),
    ]
    faces = [
        [verts[0], verts[1], verts[2], verts[3]],  # base
        [verts[4], verts[5], verts[6], verts[7]],  # tip
        [verts[0], verts[1], verts[5], verts[4]],  # front
        [verts[2], verts[3], verts[7], verts[6]],  # back
        [verts[1], verts[2], verts[6], verts[5]],  # right
        [verts[3], verts[0], verts[4], verts[7]],  # left
    ]
    for f in faces:
        bm_boom.faces.new(f)
    bm_boom.normal_update()

    boom_obj = new_mesh_obj("Boom", bm_boom)
    boom_obj.location = (0.0, SHELL_RY * 0.85, -SHELL_RZ * 0.1)
    link_to(boom_obj, col)

    # --- Bucket (open U: back + left side + right side) ---
    bm_bkt = bmesh.new()
    bw = BUCKET_WIDTH * 0.5
    bd = BUCKET_DEPTH
    bh = 0.10

    # 8 unique verts for U-shape
    bverts = [
        # back face bottom/top
        bm_bkt.verts.new((-bw, 0.0,  0.0)),
        bm_bkt.verts.new(( bw, 0.0,  0.0)),
        bm_bkt.verts.new(( bw, 0.0,  bh )),
        bm_bkt.verts.new((-bw, 0.0,  bh )),
        # front edge
        bm_bkt.verts.new((-bw, bd,   0.0)),
        bm_bkt.verts.new(( bw, bd,   0.0)),
        bm_bkt.verts.new(( bw, bd,   bh )),
        bm_bkt.verts.new((-bw, bd,   bh )),
    ]
    bfaces = [
        [bverts[0], bverts[1], bverts[2], bverts[3]],  # back wall
        [bverts[0], bverts[4], bverts[5], bverts[1]],  # bottom
        [bverts[3], bverts[2], bverts[6], bverts[7]],  # top lip (open top — omit if desired)
        [bverts[0], bverts[3], bverts[7], bverts[4]],  # left side
        [bverts[1], bverts[5], bverts[6], bverts[2]],  # right side
    ]
    for f in bfaces:
        bm_bkt.faces.new(f)
    bm_bkt.normal_update()

    bucket_obj = new_mesh_obj("Bucket", bm_bkt)
    bucket_obj.location = (
        -BUCKET_WIDTH * 0.5,
        SHELL_RY * 0.85 + ARM_LENGTH,
        -SHELL_RZ * 0.1 - 0.05,
    )
    link_to(bucket_obj, col)

    mat = make_flat_material("TonkaYellow", TONKA_YELLOW, 0.75)
    boom_obj.data.materials.append(mat)
    bucket_obj.data.materials.append(mat)

    return boom_obj


# ---------------------------------------------------------------------------
# CAMERA & LIGHTING
# ---------------------------------------------------------------------------

def setup_camera() -> None:
    """Place a perspective camera at (2.5, -2.0, 1.5) looking at the origin."""
    import mathutils

    cam_data = bpy.data.cameras.new("ConceptCam")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new("ConceptCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = Vector((2.5, -2.0, 1.5))

    # Point camera at origin
    direction = Vector((0, 0, 0)) - cam_obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.camera = cam_obj


def setup_lighting() -> None:
    """3-point lighting: key sun, fill area, rim spot."""
    # Key light — sun
    key_data = bpy.data.lights.new("KeyLight", "SUN")
    key_data.energy = 3.0
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((3.0, 2.0, 4.0))
    bpy.context.scene.collection.objects.link(key_obj)

    # Fill light — area
    fill_data = bpy.data.lights.new("FillLight", "AREA")
    fill_data.energy = 1.0
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((-2.0, 1.0, 2.0))
    bpy.context.scene.collection.objects.link(fill_obj)

    # Rim light — spot
    rim_data = bpy.data.lights.new("RimLight", "SPOT")
    rim_data.energy = 2.0
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -3.0, 2.0))
    # Point rim at origin
    direction = Vector((0, 0, 0)) - rim_obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    rim_obj.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.collection.objects.link(rim_obj)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    """Assemble the Sand Beetle concept silhouette scene."""
    # Clear existing mesh objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    col = ensure_collection("SandBeetle_Concept")

    # Shell
    build_shell(col)

    # Tracks — symmetric left/right
    build_track(col, side= 1)
    build_track(col, side=-1)

    # Arm (boom + bucket) at front-center
    build_arm(col)

    # Camera & lighting
    setup_camera()
    setup_lighting()

    # Final deselect
    bpy.ops.object.select_all(action="DESELECT")

    print("Sand Beetle concept mesh built successfully.")


if __name__ == "__main__":
    main()
