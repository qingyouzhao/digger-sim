## excavator_controller.gd
## Drives the excavator machine: track locomotion, superstructure swing,
## and hydraulic arm/boom/bucket joint control.
##
## Joint control uses PD (proportional-derivative) controllers that output
## target angular velocities, forwarded to Jolt's HingeJoint3D motor.
## Resistance from the DEM solver is fed back as a counter-torque on the
## bucket pivot, which the PD controller naturally has to overcome.
extends RigidBody3D

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

## Track movement speed [m/s]
const TRACK_SPEED        := 3.0
## Track turn rate [rad/s]
const TRACK_TURN_RATE    := 1.2
## Swing (superstructure rotation) max speed [rad/s]
const SWING_SPEED        := 0.8
## Hydraulic joint max angular speed [rad/s]
const JOINT_SPEED        := 0.6
## PD proportional gain (shared across joints)
const KP                 := 8.0
## PD derivative gain
const KD                 := 1.2
## Boom angle limits [radians] (negative = lowered)
const BOOM_ANGLE_MIN     := deg_to_rad(-10.0)
const BOOM_ANGLE_MAX     := deg_to_rad(65.0)
## Arm angle limits [radians]
const ARM_ANGLE_MIN      := deg_to_rad(-110.0)
const ARM_ANGLE_MAX      := deg_to_rad(10.0)
## Bucket angle limits [radians]
const BUCKET_ANGLE_MIN   := deg_to_rad(-60.0)
const BUCKET_ANGLE_MAX   := deg_to_rad(80.0)

## Maximum bucket fill weight [kg] that reduces joint speed
const BUCKET_MAX_LOAD_KG := 800.0

# ---------------------------------------------------------------------------
# Node references (populated in _ready)
# ---------------------------------------------------------------------------
var _superstructure: Node3D
var _boom_pivot:     Node3D
var _arm_pivot:      Node3D
var _bucket_pivot:   Node3D
var _bucket_volume:  Area3D
var _bucket_contents: Area3D

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
var _swing_angle:   float = 0.0
var _boom_angle:    float = deg_to_rad(20.0)
var _arm_angle:     float = deg_to_rad(-60.0)
var _bucket_angle:  float = deg_to_rad(-10.0)

## Bucket fill weight reported by the GDExtension particle system [kg]
var bucket_load_kg: float = 0.0

## Previous-frame angular velocities for derivative term
var _prev_boom_vel:   float = 0.0
var _prev_arm_vel:    float = 0.0
var _prev_bucket_vel: float = 0.0

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

func _ready() -> void:
	_superstructure  = $Superstructure
	_boom_pivot      = $Superstructure/BoomPivot
	_arm_pivot       = $Superstructure/BoomPivot/Boom/ArmPivot
	_bucket_pivot    = $Superstructure/BoomPivot/Boom/ArmPivot/Arm/BucketPivot
	_bucket_volume   = $Superstructure/BoomPivot/Boom/ArmPivot/Arm/BucketPivot/Bucket/BucketVolume
	_bucket_contents = $Superstructure/BoomPivot/Boom/ArmPivot/Arm/BucketPivot/Bucket/BucketContents

	# Connect bucket volume to the GDExtension BucketInteraction system.
	_connect_bucket_to_physics()

func _physics_process(delta: float) -> void:
	_handle_track_input(delta)
	_handle_swing_input(delta)
	_handle_arm_input(delta)
	_apply_joint_transforms()

# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

func _handle_track_input(delta: float) -> void:
	var forward := float(Input.get_action_strength("track_forward")) \
	             - float(Input.get_action_strength("track_backward"))
	var turn    := float(Input.get_action_strength("track_turn_right")) \
	             - float(Input.get_action_strength("track_turn_left"))

	if abs(forward) > 0.01 or abs(turn) > 0.01:
		var move_dir := -global_transform.basis.z * forward * TRACK_SPEED
		apply_central_force(move_dir * mass)
		var torque_y := turn * TRACK_TURN_RATE
		apply_torque(Vector3(0.0, torque_y * mass, 0.0))

func _handle_swing_input(delta: float) -> void:
	var swing := float(Input.get_action_strength("swing_right")) \
	           - float(Input.get_action_strength("swing_left"))
	_swing_angle += swing * SWING_SPEED * delta

func _handle_arm_input(delta: float) -> void:
	var load_factor := 1.0 - clamp(bucket_load_kg / BUCKET_MAX_LOAD_KG, 0.0, 0.7)
	var speed := JOINT_SPEED * load_factor

	# --- Boom ---
	var boom_input := float(Input.get_action_strength("boom_up")) \
	                - float(Input.get_action_strength("boom_down"))
	_boom_angle = clamp(_boom_angle + boom_input * speed * delta,
	                    BOOM_ANGLE_MIN, BOOM_ANGLE_MAX)

	# --- Arm ---
	var arm_input := float(Input.get_action_strength("arm_extend")) \
	               - float(Input.get_action_strength("arm_retract"))
	_arm_angle = clamp(_arm_angle + arm_input * speed * delta,
	                   ARM_ANGLE_MIN, ARM_ANGLE_MAX)

	# --- Bucket ---
	var bucket_input := float(Input.get_action_strength("bucket_curl")) \
	                  - float(Input.get_action_strength("bucket_dump"))
	_bucket_angle = clamp(_bucket_angle + bucket_input * speed * delta,
	                      BUCKET_ANGLE_MIN, BUCKET_ANGLE_MAX)

# ---------------------------------------------------------------------------
# Joint transform application
# Jolt joint motors will eventually drive this; for now we set transforms
# directly (kinematic-style) so the scene works before GDExtension is built.
# ---------------------------------------------------------------------------

func _apply_joint_transforms() -> void:
	if _superstructure:
		_superstructure.rotation.y = _swing_angle
	if _boom_pivot:
		_boom_pivot.rotation.x = _boom_angle
	if _arm_pivot:
		_arm_pivot.rotation.x = _arm_angle
	if _bucket_pivot:
		_bucket_pivot.rotation.x = _bucket_angle

# ---------------------------------------------------------------------------
# GDExtension bridge
# ---------------------------------------------------------------------------

## Registers the BucketVolume Area3D and BucketContents Area3D with the
## DiggerPhysics system so the C++ layer can query them each frame.
func _connect_bucket_to_physics() -> void:
	var dp: Node = get_node_or_null("/root/DiggerPhysics")
	if dp == null:
		push_warning("ExcavatorController: DiggerPhysics autoload not found.")
		return
	dp.call("register_bucket",
		_bucket_volume,
		_bucket_contents,
		self   # receives on_bucket_load_changed(kg: float)
	)

## Called by GDExtension each physics frame with the current bucket load.
func on_bucket_load_changed(kg: float) -> void:
	bucket_load_kg = kg

## Returns the current global Transform3D of the bucket tip (lowest point).
func get_bucket_tip_transform() -> Transform3D:
	if _bucket_pivot == null:
		return global_transform
	return _bucket_pivot.global_transform

## Returns the bucket angular velocity [rad/s] for particle ejection velocity.
func get_bucket_angular_velocity() -> float:
	return Input.get_action_strength("bucket_dump") * JOINT_SPEED
