## terrain_manager.gd
## Owns the voxel terrain and acts as the GDScript-side bridge to the
## DiggerPhysics GDExtension's VoxelTerrain class.
##
## Responsibilities:
##   - Initialise voxel grid with procedural or heightmap-derived data
##   - Forward carve/query calls from other game systems
##   - Re-voxelise settled particles (particles → static voxels)
extends Node3D

const MaterialID := preload("res://scripts/material_registry.gd").MaterialID

## Grid dimensions in voxels. Each voxel = 0.25 m.
## 256 × 64 × 256 = 64 m × 16 m × 64 m play area.
const GRID_W := 256
const GRID_H := 64
const GRID_D := 256
const VOXEL_SIZE := 0.25  # metres per voxel side

## Chunk size (must match GDExtension compile constant).
const CHUNK_SIZE := 16

## Reference to the GDExtension VoxelTerrain node (added as child at runtime
## once the extension is compiled). Falls back to placeholder behaviour.
var _voxel_terrain: Node = null

## Emitted when a voxel region changes so other systems (dust VFX, audio)
## can react.
signal terrain_changed(aabb: AABB)

func _ready() -> void:
	_try_attach_extension()
	_generate_default_terrain()

## Attempts to find a VoxelTerrain child registered by the GDExtension.
func _try_attach_extension() -> void:
	for child in get_children():
		if child.get_class() == "VoxelTerrain":
			_voxel_terrain = child
			_configure_extension()
			return
	push_warning("TerrainManager: VoxelTerrain GDExtension not found — running in placeholder mode.")

func _configure_extension() -> void:
	if _voxel_terrain == null:
		return
	var registry: Node = get_node("/root/MaterialRegistry")
	_voxel_terrain.call("set_materials", registry.build_extension_config())
	_voxel_terrain.call("set_voxel_size", VOXEL_SIZE)
	_voxel_terrain.call("set_grid_size", Vector3i(GRID_W, GRID_H, GRID_D))
	_voxel_terrain.call("set_chunk_size", CHUNK_SIZE)

## Fills the grid with a simple layered default landscape:
##   0–2 voxels deep : Dry Sand top layer
##   2–8 voxels deep : Wet Dirt
##   8–20 voxels deep: Clay
##   20+             : Soft Rock bedrock
func _generate_default_terrain() -> void:
	if _voxel_terrain != null:
		_voxel_terrain.call("generate_layered", [
			{"depth": 2,  "material": MaterialID.DRY_SAND},
			{"depth": 6,  "material": MaterialID.WET_DIRT},
			{"depth": 12, "material": MaterialID.CLAY},
			{"depth": 9999, "material": MaterialID.SOFT_ROCK},
		])
	# In placeholder mode, the StaticBody3D ground in terrain.tscn is enough.

## Called by BucketInteraction (via the GDExtension callback) to notify
## GDScript-side systems of a carve event.
func on_voxels_carved(world_aabb: AABB, material_id: int, volume_m3: float) -> void:
	terrain_changed.emit(world_aabb)

## Converts a world-space position to voxel grid coordinates.
func world_to_voxel(world_pos: Vector3) -> Vector3i:
	var local_pos: Vector3 = to_local(world_pos)
	return Vector3i(
		int(local_pos.x / VOXEL_SIZE),
		int(local_pos.y / VOXEL_SIZE),
		int(local_pos.z / VOXEL_SIZE)
	)

## Returns the MaterialID at a world-space position (-1 if out of bounds).
func get_material_at(world_pos: Vector3) -> int:
	if _voxel_terrain == null:
		return MaterialID.WET_DIRT  # placeholder fallback
	var vp: Vector3i = world_to_voxel(world_pos)
	return int(_voxel_terrain.call("get_material", vp))

## Manually carves a sphere (used by debug tools and tests).
func carve_sphere(world_center: Vector3, radius_m: float) -> void:
	if _voxel_terrain == null:
		return
	_voxel_terrain.call("carve_sphere", world_center, radius_m)
	terrain_changed.emit(AABB(world_center - Vector3.ONE * radius_m, Vector3.ONE * radius_m * 2.0))
