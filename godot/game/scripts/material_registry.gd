## material_registry.gd
## Singleton (autoload) — single source of truth for all soil/rock material
## definitions. The C++ GDExtension reads these values via DiggerPhysics.set_materials().
extends Node

## Material IDs must match the u8 stored in each voxel cell and the
## MaterialDef array index passed to the DEM solver.
enum MaterialID {
	AIR        = 0,
	DRY_SAND   = 1,
	WET_DIRT   = 2,
	GRAVEL     = 3,
	CLAY       = 4,
	SOFT_ROCK  = 5,
}

## Per-material physics and visual properties.
## cohesion         : JKR cohesion energy [J/m²] — 0 = free-flowing
## friction_coeff   : static friction coefficient (Coulomb)
## rolling_friction : rolling resistance coefficient
## restitution      : coefficient of restitution (0=perfectly plastic)
## density_kg_m3    : bulk density [kg/m³]
## angle_of_repose  : natural pile angle [degrees]
## particle_radius  : mean particle radius [m] (affects DEM timestep)
## dig_resistance   : extra resistive force multiplier for bucket (1 = baseline)
## color            : display color for toy aesthetic
## toy_scale        : visual particle scale multiplier (makes sand tiny, gravel chunky)
const MATERIALS: Array[Dictionary] = [
	# 0 — AIR (sentinel, no physics)
	{},

	# 1 — DRY SAND
	{
		"name":            "Dry Sand",
		"cohesion":        0.0,
		"friction_coeff":  0.60,
		"rolling_friction": 0.02,
		"restitution":     0.30,
		"density_kg_m3":   1600.0,
		"angle_of_repose": 34.0,
		"particle_radius": 0.01,
		"dig_resistance":  1.0,
		"color":           Color(0.96, 0.84, 0.55),
		"toy_scale":       0.5,
	},

	# 2 — WET DIRT
	{
		"name":            "Wet Dirt",
		"cohesion":        8.0,
		"friction_coeff":  0.70,
		"rolling_friction": 0.10,
		"restitution":     0.10,
		"density_kg_m3":   1900.0,
		"angle_of_repose": 45.0,
		"particle_radius": 0.025,
		"dig_resistance":  1.8,
		"color":           Color(0.45, 0.30, 0.18),
		"toy_scale":       0.8,
	},

	# 3 — GRAVEL
	{
		"name":            "Gravel",
		"cohesion":        0.0,
		"friction_coeff":  0.75,
		"rolling_friction": 0.05,
		"restitution":     0.40,
		"density_kg_m3":   1800.0,
		"angle_of_repose": 38.0,
		"particle_radius": 0.06,
		"dig_resistance":  1.4,
		"color":           Color(0.65, 0.63, 0.60),
		"toy_scale":       1.4,
	},

	# 4 — CLAY
	{
		"name":            "Clay",
		"cohesion":        25.0,
		"friction_coeff":  0.55,
		"rolling_friction": 0.15,
		"restitution":     0.05,
		"density_kg_m3":   2100.0,
		"angle_of_repose": 55.0,
		"particle_radius": 0.015,
		"dig_resistance":  2.5,
		"color":           Color(0.74, 0.45, 0.28),
		"toy_scale":       0.7,
	},

	# 5 — SOFT ROCK
	# Fractures into rigid-body chunks rather than flowing particles.
	{
		"name":            "Soft Rock",
		"cohesion":        0.0,          # handled by Jolt rigid bodies
		"friction_coeff":  0.80,
		"rolling_friction": 0.08,
		"restitution":     0.25,
		"density_kg_m3":   2400.0,
		"angle_of_repose": 90.0,         # doesn't flow
		"particle_radius": 0.12,
		"dig_resistance":  5.0,
		"color":           Color(0.55, 0.55, 0.52),
		"toy_scale":       2.0,
	},
]

## Returns the material dictionary for the given MaterialID, or an empty dict
## for AIR / out-of-range IDs.
func get_material(id: int) -> Dictionary:
	if id <= 0 or id >= MATERIALS.size():
		return {}
	return MATERIALS[id]

## Returns the display colour for a material ID.
func get_color(id: int) -> Color:
	var mat := get_material(id)
	return mat.get("color", Color.WHITE) as Color

## Returns the dig resistance multiplier.
func get_dig_resistance(id: int) -> float:
	var mat := get_material(id)
	return mat.get("dig_resistance", 1.0) as float

## Builds and returns the Array[Dictionary] that DiggerPhysics.set_materials()
## expects from the GDExtension.
func build_extension_config() -> Array:
	return MATERIALS.duplicate(true)
