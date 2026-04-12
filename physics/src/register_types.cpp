#include "register_types.h"
#include "digger_physics.h"
#include "voxel_terrain.h"
#include "dem_solver.h"
#include "bucket_interaction.h"
#include "particle_pool.h"

#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>
#include <godot_cpp/classes/engine.hpp>

using namespace godot;

// ---------------------------------------------------------------------------
// Singleton instance (owned by the extension, lifetime == Godot process)
// ---------------------------------------------------------------------------
static DiggerPhysics *_digger_singleton = nullptr;

// ---------------------------------------------------------------------------
// Module init / deinit
// ---------------------------------------------------------------------------

void initialize_digger_physics_module(ModuleInitializationLevel p_level) {
    if (p_level == MODULE_INITIALIZATION_LEVEL_SCENE) {
        // Register node types so they appear in the editor Add-Node dialog.
        GDREGISTER_CLASS(VoxelTerrain);
        GDREGISTER_CLASS(ParticlePool);
        GDREGISTER_CLASS(BucketInteraction);

        // Register and install the DiggerPhysics singleton.
        GDREGISTER_CLASS(DiggerPhysics);
        _digger_singleton = memnew(DiggerPhysics);
        Engine::get_singleton()->register_singleton("DiggerPhysics", _digger_singleton);
    }
}

void uninitialize_digger_physics_module(ModuleInitializationLevel p_level) {
    if (p_level == MODULE_INITIALIZATION_LEVEL_SCENE) {
        Engine::get_singleton()->unregister_singleton("DiggerPhysics");
        memdelete(_digger_singleton);
        _digger_singleton = nullptr;
    }
}

// ---------------------------------------------------------------------------
// GDExtension entry point (symbol matched in .gdextension file)
// ---------------------------------------------------------------------------

extern "C" {
GDExtensionBool GDE_EXPORT digger_physics_library_init(
    GDExtensionInterfaceGetProcAddress  p_get_proc_address,
    const GDExtensionClassLibraryPtr    p_library,
    GDExtensionInitialization          *r_initialization)
{
    godot::GDExtensionBinding::InitObject init_obj(p_get_proc_address, p_library, r_initialization);
    init_obj.register_initializer(initialize_digger_physics_module);
    init_obj.register_terminator(uninitialize_digger_physics_module);
    init_obj.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_SCENE);
    return init_obj.init();
}
}
