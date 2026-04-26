#pragma once

#include <godot_cpp/core/class_db.hpp>

// Called by the GDExtension entry point to register all custom classes
// and the DiggerPhysics singleton with Godot's ClassDB.
void initialize_digger_physics_module(godot::ModuleInitializationLevel p_level);
void uninitialize_digger_physics_module(godot::ModuleInitializationLevel p_level);
