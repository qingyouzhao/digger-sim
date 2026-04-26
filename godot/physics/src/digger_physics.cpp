#include "digger_physics.h"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

using namespace godot;

// ---------------------------------------------------------------------------
// Godot bindings
// ---------------------------------------------------------------------------

void DiggerPhysics::_bind_methods() {
    ClassDB::bind_method(D_METHOD("initialize", "cfg"),           &DiggerPhysics::initialize);
    ClassDB::bind_method(D_METHOD("set_materials", "defs"),       &DiggerPhysics::set_materials);
    ClassDB::bind_method(D_METHOD("register_bucket",
        "dig_volume", "contents_volume", "excavator"),            &DiggerPhysics::register_bucket);
    ClassDB::bind_method(D_METHOD("set_terrain_node", "terrain"), &DiggerPhysics::set_terrain_node);
    ClassDB::bind_method(D_METHOD("set_particle_pool_node","pool"),&DiggerPhysics::set_particle_pool_node);
    ClassDB::bind_method(D_METHOD("get_active_particle_count"),   &DiggerPhysics::get_active_particle_count);
    ClassDB::bind_method(D_METHOD("get_bucket_fill_mass"),        &DiggerPhysics::get_bucket_fill_mass);
    ClassDB::bind_method(D_METHOD("get_held_particle_count"),     &DiggerPhysics::get_held_particle_count);
}

// ---------------------------------------------------------------------------
// Construction / destruction
// ---------------------------------------------------------------------------

DiggerPhysics::DiggerPhysics() {
    // Child objects are created lazily in initialize() so they don't
    // allocate memory before Godot's scene tree is ready.
}

DiggerPhysics::~DiggerPhysics() {
    // memdelete is used for Godot-managed objects.
    if (_bucket)  { memdelete(_bucket);  _bucket  = nullptr; }
    if (_solver)  { memdelete(_solver);  _solver  = nullptr; }
    // _pool and _terrain are scene-tree nodes owned by the scene; don't delete them.
}

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

void DiggerPhysics::initialize(const Dictionary& cfg) {
    if (_initialised) return;

    // Create the DEM solver.
    _solver = memnew(DEMSolver);
    _solver->configure(cfg);

    // Create the bucket interaction coordinator.
    _bucket = memnew(BucketInteraction);
    _bucket->set_dem_solver(_solver);

    _initialised = true;
    UtilityFunctions::print("DiggerPhysics: initialised. max_particles=",
        int(cfg.get("max_particles", 50000)));
}

void DiggerPhysics::set_materials(const Array& defs) {
    if (_solver)  _solver->set_material_defs(defs);
}

// ---------------------------------------------------------------------------
// Node registration
// ---------------------------------------------------------------------------

void DiggerPhysics::register_bucket(Area3D* dig_volume,
                                     Area3D* contents_volume,
                                     Node3D* excavator)
{
    if (!_bucket) {
        UtilityFunctions::push_warning("DiggerPhysics::register_bucket called before initialize()");
        return;
    }
    _bucket->register_bucket(dig_volume, contents_volume, excavator);
}

void DiggerPhysics::set_terrain_node(VoxelTerrain* terrain) {
    _terrain = terrain;
    if (_bucket) _bucket->set_terrain(terrain);
}

void DiggerPhysics::set_particle_pool_node(ParticlePool* pool) {
    _pool = pool;
    if (_pool && _solver)  _pool->set_solver(_solver);
    if (_pool && _terrain) _pool->set_terrain(_terrain);
}

// ---------------------------------------------------------------------------
// Per-frame queries
// ---------------------------------------------------------------------------

int DiggerPhysics::get_active_particle_count() const {
    if (!_solver) return 0;
    return static_cast<int>(_solver->particles().size());
}

float DiggerPhysics::get_bucket_fill_mass() const {
    if (!_bucket) return 0.0f;
    return _bucket->get_fill_mass();
}

int DiggerPhysics::get_held_particle_count() const {
    if (!_bucket) return 0;
    return _bucket->get_held_count();
}
