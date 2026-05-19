extends Node2D

func _ready() -> void:
	print("Godot Digger loaded")

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
