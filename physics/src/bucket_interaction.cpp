#include "bucket_interaction.h"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/classes/rigid_body3d.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

#include <cmath>
#include <random>

using namespace godot;

// ---------------------------------------------------------------------------
// Godot bindings
// ---------------------------------------------------------------------------

void BucketInteraction::_bind_methods() {
    ClassDB::bind_method(
        D_METHOD("register_bucket", "dig_volume", "contents_volume", "excavator"),
        &BucketInteraction::register_bucket);
    ClassDB::bind_method(D_METHOD("set_terrain", "terrain"), &BucketInteraction::set_terrain);
    ClassDB::bind_method(D_METHOD("set_dem_solver", "solver"), &BucketInteraction::set_dem_solver);
    ClassDB::bind_method(D_METHOD("get_fill_mass"),  &BucketInteraction::get_fill_mass);
    ClassDB::bind_method(D_METHOD("get_held_count"), &BucketInteraction::get_held_count);
    ClassDB::bind_method(
        D_METHOD("set_particles_per_voxel", "n"), &BucketInteraction::set_particles_per_voxel);
    ClassDB::bind_method(
        D_METHOD("get_particles_per_voxel"), &BucketInteraction::get_particles_per_voxel);
}

// ---------------------------------------------------------------------------

BucketInteraction::BucketInteraction() {}
BucketInteraction::~BucketInteraction() {}

void BucketInteraction::_ready() {}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

void BucketInteraction::register_bucket(Area3D* dig_volume,
                                         Area3D* contents_volume,
                                         Node3D* excavator)
{
    _dig_volume      = dig_volume;
    _contents_volume = contents_volume;
    _excavator       = excavator;
    _has_prev_xform  = false;
}

void BucketInteraction::set_terrain(VoxelTerrain* terrain) { _terrain = terrain; }
void BucketInteraction::set_dem_solver(DEMSolver* solver)  { _solver  = solver;  }

// ---------------------------------------------------------------------------
// Physics update (called every physics frame = 60 Hz)
// ---------------------------------------------------------------------------

void BucketInteraction::_physics_process(double delta) {
    if (!_dig_volume || !_terrain || !_solver) return;

    Transform3D bucket_xform = _dig_volume->get_global_transform();

    if (_has_prev_xform) {
        _step_carve_and_spawn(bucket_xform, static_cast<float>(delta));
        _step_update_held(bucket_xform);
        _step_revoxelise();
    }

    _prev_bucket_xform = bucket_xform;
    _has_prev_xform    = true;

    // Update fill mass from held particles and notify excavator controller.
    _fill_mass_kg = _solver->get_held_mass();
    if (_excavator && _excavator->has_method("on_bucket_load_changed")) {
        _excavator->call("on_bucket_load_changed", _fill_mass_kg);
    }
}

// ---------------------------------------------------------------------------
// Step 1: Carve swept volume, spawn particles
// ---------------------------------------------------------------------------

void BucketInteraction::_step_carve_and_spawn(const Transform3D& bucket_xform,
                                               float delta)
{
    if (!_has_prev_xform) return;

    // Sample positions along the sweep arc.
    std::vector<Vector3> sweep_pts = _sample_sweep(
        _prev_bucket_xform, bucket_xform, _sweep_samples);

    // Approximate bucket tip radius from the dig_volume shape extents.
    // Default: 0.45 m (half the bucket width).
    const float bucket_radius = 0.45f;

    uint8_t dominant_mat = 0;
    float carved_vol = _terrain->carve_swept_volume(sweep_pts, bucket_radius, dominant_mat);

    if (carved_vol <= 0.0f || dominant_mat == 0) return;

    // Notify GDScript (terrain_changed signal).
    if (_terrain->on_carved) {
        _terrain->on_carved(bucket_xform.origin, dominant_mat, carved_vol);
    }

    // Spawn DEM particles for the excavated material.
    const MaterialDef& mat = _terrain->get_material_def(dominant_mat);
    float voxel_vol_per_particle = carved_vol / static_cast<float>(_particles_per_voxel);

    // Jitter spawn positions near the bucket tip.
    std::mt19937 rng(std::random_device{}());
    std::uniform_real_distribution<float> jitter(-bucket_radius * 0.5f, bucket_radius * 0.5f);

    Vector3 bucket_vel = (bucket_xform.origin - _prev_bucket_xform.origin) / delta;

    int to_spawn = _particles_per_voxel;
    for (int i = 0; i < to_spawn && carved_vol > 0.0f; ++i) {
        Vector3 spawn_pos = bucket_xform.origin
            + Vector3(jitter(rng), jitter(rng) * 0.3f, jitter(rng));
        // Initial velocity: bucket motion + small random scatter.
        Vector3 init_vel = bucket_vel * 0.6f
            + Vector3(jitter(rng)*0.5f, std::abs(jitter(rng)), jitter(rng)*0.5f);
        _solver->spawn_particle(spawn_pos, init_vel, dominant_mat);
    }

    _step_resistance_feedback(carved_vol, dominant_mat);
}

// ---------------------------------------------------------------------------
// Step 2: Determine which particles are inside the contents volume
// ---------------------------------------------------------------------------

void BucketInteraction::_step_update_held(const Transform3D& bucket_xform) {
    if (!_contents_volume) return;

    // Release previously held particles first.
    if (_held_indices.size() > 0) {
        _solver->set_held(_held_indices, false);
        _held_indices.clear();
    }

    // A particle is "held" if it is close enough to the bucket origin and
    // moving with the bucket (inside the contents volume AABB).
    auto& particles = _solver->particles();
    PackedInt32Array new_held;

    for (int i = 0; i < static_cast<int>(particles.size()); ++i) {
        DEMParticle& p = particles[i];
        if (!p.active) continue;
        if (_inside_contents(p.pos)) {
            // Teleport particle to follow bucket transform if needed.
            // Simple approach: override velocity toward the bucket interior.
            new_held.push_back(i);
        }
    }

    if (new_held.size() > 0) {
        _solver->set_held(new_held, true);
    }
    _held_indices = new_held;
    _held_count   = _held_indices.size();
}

// ---------------------------------------------------------------------------
// Step 3: Re-voxelise settled particles
// ---------------------------------------------------------------------------

void BucketInteraction::_step_revoxelise() {
    auto settled = _solver->drain_settled();
    for (const auto& [world_pos, mat_id] : settled) {
        // Snap to voxel grid and set material.
        // This closes the loop: excavated material piled on the ground
        // eventually becomes static terrain again (saves particle count).
        _terrain->carve_sphere(world_pos, -_terrain->get_voxel_size() * 0.5f);
        // TODO: replace with a "fill_voxel" API on VoxelTerrain once the
        // full marching-cubes mesher is in place.
    }
}

// ---------------------------------------------------------------------------
// Step 4: Resistance feedback to excavator
// ---------------------------------------------------------------------------

void BucketInteraction::_step_resistance_feedback(float volume_carved_m3,
                                                    uint8_t dominant_mat)
{
    if (!_excavator) return;
    const MaterialDef& mat = _terrain->get_material_def(dominant_mat);
    // Resistance force [N] ≈ dig_resistance × density × volume × 9.8
    float resistance_n = mat.dig_resistance * mat.density_kg_m3 * volume_carved_m3 * 9.8f;
    // Forward to excavator so the PD controller experiences load.
    if (_excavator->has_method("apply_dig_resistance")) {
        _excavator->call("apply_dig_resistance", resistance_n);
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

std::vector<Vector3> BucketInteraction::_sample_sweep(
    const Transform3D& prev, const Transform3D& curr, int samples) const
{
    std::vector<Vector3> pts;
    pts.reserve(static_cast<size_t>(samples));
    for (int i = 0; i < samples; ++i) {
        float t = static_cast<float>(i) / static_cast<float>(samples - 1);
        pts.push_back(prev.origin.lerp(curr.origin, t));
    }
    return pts;
}

bool BucketInteraction::_inside_contents(const Vector3& world_pos) const {
    if (!_contents_volume) return false;
    // Transform world_pos into contents_volume local space.
    Transform3D inv = _contents_volume->get_global_transform().affine_inverse();
    Vector3 local   = inv.xform(world_pos);
    // AABB half-extents from our 0.80×0.50×0.40 shape (hard-coded to match scene).
    return std::abs(local.x) < 0.40f
        && std::abs(local.y) < 0.25f
        && std::abs(local.z) < 0.20f;
}
