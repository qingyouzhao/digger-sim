## game_manager.gd
## Top-level game coordinator. Owns the scenario state machine, HUD data,
## and wires together the major subsystems at startup.
extends Node3D

## Current scenario phase.
enum Phase {
	SETUP,
	PLAYING,
	COMPLETE,
}

var current_phase: Phase = Phase.SETUP

## Reference to MaterialRegistry autoload.
@onready var _materials: Node = get_node("/root/MaterialRegistry")

## Reference to terrain.
@onready var _terrain: Node3D = $Terrain

## Reference to excavator.
@onready var _excavator: RigidBody3D = $Excavator

func _ready() -> void:
	_boot_physics_extension()
	current_phase = Phase.PLAYING

## Finds or creates the DiggerPhysics autoload from the GDExtension.
## If the extension is not compiled yet, a no-op stub is used so the
## rest of the game continues to run.
func _boot_physics_extension() -> void:
	if Engine.has_singleton("DiggerPhysics"):
		var dp: Object = Engine.get_singleton("DiggerPhysics")
		dp.call("initialize", {
			"max_particles":   50_000,
			"substeps":        8,
			"gravity":         Vector3(0.0, -9.8, 0.0),
			"use_gpu":         true,
		})
		dp.call("set_materials", _materials.build_extension_config())
		print("DiggerPhysics GDExtension initialised.")
	else:
		push_warning("GameManager: DiggerPhysics singleton not registered — physics running in placeholder mode.")

func _process(_delta: float) -> void:
	pass
