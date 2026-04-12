#pragma once

#include "voxel_terrain.h"

#include <godot_cpp/classes/node.hpp>
#include <godot_cpp/variant/vector3.hpp>
#include <godot_cpp/variant/array.hpp>

#include <cstdint>
#include <vector>

// ---------------------------------------------------------------------------
// DEMParticle — one granular particle in the simulation
// ---------------------------------------------------------------------------
struct DEMParticle {
    godot::Vector3 pos;        // world-space position [m]
    godot::Vector3 vel;        // velocity [m/s]
    godot::Vector3 force;      // accumulated force this step [N]
    godot::Vector3 angular_vel;// angular velocity [rad/s]
    float          radius;     // [m]
    float          mass;       // [kg]
    uint8_t        material_id;
    bool           active;     // false = slot is free in pool
    bool           held;       // true = inside bucket, moves with it
    bool           settled;    // true = has come to rest, candidate for re-voxelisation
    float          rest_timer; // seconds since velocity dropped below threshold
};

// ---------------------------------------------------------------------------
// SolverConfig — tunable parameters exposed to GDScript
// ---------------------------------------------------------------------------
struct SolverConfig {
    int     substeps         = 8;       // integration substeps per game frame
    float   gravity          = 9.8f;    // [m/s²]
    float   restitution      = 0.3f;    // global fallback
    float   rest_threshold   = 0.02f;   // velocity [m/s] below which particle is "settled"
    float   rest_time_needed = 2.0f;    // seconds at rest before re-voxelisation
    int     max_particles    = 50000;
    float   damping          = 0.98f;   // linear damping factor per substep
};

// ---------------------------------------------------------------------------
// DEMSolver — lightweight CPU/OpenMP DEM solver (Phase 3 default).
// Replaced by ChronoBridge when DIGGER_USE_CHRONO is defined.
//
// Contact model:
//   Normal  : Hertz-Mindlin spring-dashpot
//   Tangent : Coulomb friction limit, δt = min(μN, kt·ut)
//   Rolling : torque = -μ_r * R * |N| * ω̂
//   Cohesion: JKR pull-off force  F_pull = 3π·γ·R*  (R* = harmonic mean radii)
// ---------------------------------------------------------------------------
class DEMSolver : public godot::Node {
    GDCLASS(DEMSolver, godot::Node)

public:
    DEMSolver();
    ~DEMSolver() override;

    void _ready() override;

    // -- GDScript API --
    void configure(const godot::Dictionary& cfg);
    void set_material_defs(const godot::Array& defs);
    void step(float game_delta);

    /// Spawn a particle at world_pos with initial velocity.
    int  spawn_particle(const godot::Vector3& world_pos,
                        const godot::Vector3& velocity,
                        uint8_t material_id);

    /// Mark particles inside the bucket volume as "held".
    void set_held(const godot::PackedInt32Array& indices, bool held);

    /// Returns positions of all active particles (for GPU instanced rendering).
    godot::PackedVector3Array get_positions() const;

    /// Returns material IDs of all active particles (parallel to get_positions).
    godot::PackedByteArray get_material_ids() const;

    /// Returns the total mass of all "held" particles [kg].
    float get_held_mass() const;

    /// Returns particles that have settled long enough for re-voxelisation.
    /// Marks them inactive after returning.
    std::vector<std::pair<godot::Vector3, uint8_t>> drain_settled();

    // -- C++ internal API --
    std::vector<DEMParticle>& particles() { return _particles; }

protected:
    static void _bind_methods();

private:
    SolverConfig              _config;
    std::vector<DEMParticle>  _particles;
    std::vector<MaterialDef>  _mat_defs;
    int                       _active_count = 0;

    // Broad-phase uniform grid for neighbour search.
    struct GridCell { std::vector<int> indices; };
    std::unordered_map<uint64_t, GridCell> _grid;
    float _grid_cell_size = 0.15f; // must be ≥ 2 * max_particle_radius

    void _broad_phase_rebuild();
    void _resolve_contacts(float dt);
    void _integrate(float dt);
    void _apply_gravity(float dt);

    // Initialise a particle slot with position, velocity, and material.
    void _init_particle(DEMParticle& p,
                        const godot::Vector3& pos,
                        const godot::Vector3& vel,
                        uint8_t mat_id);

    // Hertz-Mindlin contact force between two particles.
    void _contact_force(DEMParticle& a, DEMParticle& b,
                        const MaterialDef& ma, const MaterialDef& mb,
                        float dt);

    // Boundary: floor and level walls.
    void _boundary_contacts(DEMParticle& p, const MaterialDef& m, float dt);

    static uint64_t grid_key(int ix, int iy, int iz);
};
