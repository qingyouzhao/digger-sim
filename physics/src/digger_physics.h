#pragma once

#include "dem_solver.h"
#include "voxel_terrain.h"
#include "bucket_interaction.h"
#include "particle_pool.h"

#include <godot_cpp/classes/object.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/array.hpp>

// ---------------------------------------------------------------------------
// DiggerPhysics — Engine singleton
//
// Registered with Engine::register_singleton() so GDScript can access it as:
//   Engine.get_singleton("DiggerPhysics")
//
// Responsibilities:
//   - Own and coordinate DEMSolver, BucketInteraction, and ParticlePool
//   - Provide the initialise() / set_materials() entry points called from
//     game_manager.gd at startup
//   - Expose per-frame query methods used by UI (fill mass, particle count)
// ---------------------------------------------------------------------------
class DiggerPhysics : public godot::Object {
    GDCLASS(DiggerPhysics, godot::Object)

public:
    DiggerPhysics();
    ~DiggerPhysics() override;

    // -- GDScript API --

    /// Called once at startup with global solver configuration.
    /// cfg keys: max_particles (int), substeps (int), gravity (float), use_gpu (bool)
    void initialize(const godot::Dictionary& cfg);

    /// Set per-material physics definitions (forwarded to DEMSolver and VoxelTerrain).
    void set_materials(const godot::Array& material_defs);

    /// Register a bucket Area3D pair and the owning excavator Node3D.
    /// Wraps BucketInteraction::register_bucket().
    void register_bucket(godot::Area3D* dig_volume,
                         godot::Area3D* contents_volume,
                         godot::Node3D* excavator);

    /// Link the active VoxelTerrain node (called from TerrainManager after _ready).
    void set_terrain_node(VoxelTerrain* terrain);

    /// Link the ParticlePool renderer node.
    void set_particle_pool_node(ParticlePool* pool);

    // -- Per-frame queries (called from HUD / game_manager) --
    int   get_active_particle_count() const;
    float get_bucket_fill_mass() const;
    int   get_held_particle_count() const;

    // -- Accessors for child systems --
    DEMSolver*        get_solver()            { return _solver; }
    BucketInteraction* get_bucket_interaction(){ return _bucket; }

protected:
    static void _bind_methods();

private:
    DEMSolver*         _solver  = nullptr;
    BucketInteraction* _bucket  = nullptr;
    ParticlePool*      _pool    = nullptr;
    VoxelTerrain*      _terrain = nullptr;
    bool               _initialised = false;
};
