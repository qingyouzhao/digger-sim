extends Node3D

const ORBIT_SPEED := 0.4
const ORBIT_RADIUS := 10.0
const ORBIT_HEIGHT := 5.0

var _angle := 0.0

@onready var _camera: Camera3D = $Camera3D

func _process(delta: float) -> void:
	_angle += delta * ORBIT_SPEED
	_camera.position = Vector3(
		sin(_angle) * ORBIT_RADIUS,
		ORBIT_HEIGHT,
		cos(_angle) * ORBIT_RADIUS
	)
	_camera.look_at(Vector3.ZERO)
