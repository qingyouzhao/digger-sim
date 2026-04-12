#pragma once

#include "voxel_terrain.h"
#include "dem_solver.h"

#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/classes/area3d.hpp>
#include <godot_cpp/variant/transform3d.hpp>
#include <godot_cpp/variant/vector3.hpp>
#include <godot_cpp/variant/packed_int32_array.hpp>

#include <vector>

// ---------------------------------------------------------------------------
// BucketInteraction
//
// Runs each physics frame to:
//   1. Compute the swept volume between last frame's and current bucket transform.
//   2. Forward the sweep to VoxelTerrain::carve_swept_volume().
//   3. Spawn particles from the carved volume via DEMSolver::spawn_particle().
//   4. Determine which existing particles are inside the bucket contents volume.
//   5. Mark held particles; release them on dump.
//   6. Compute resistance force and apply it back to the excavator node.
//   7. Re-voxelise settled particles (DEMSolver::drain_settled → VoxelTerrain).
// ---------------------------------------------------------------------------
class BucketInteraction : public godot::Node3D {
    GDCLASS(BucketInteraction, godot::Node3D)

public:
    BucketInteraction();
    ~BucketInteraction() override;

    void _ready()  override;
    void _physics_process(double delta) override;

    // -- GDScript API --

    /// Called once by ExcavatorController to register the bucket Area3D nodes
    /// and the excavator RigidBody3D that receives resistance torque feedback.
    void register_bucket(godot::Area3D* dig_volume,
                         godot::Area3D* contents_volume,
                         godot::Node3D* excavator);

    /// Link to the VoxelTerrain and DEMSolver nodes.
    void set_terrain(VoxelTerrain* terrain);
    void set_dem_solver(DEMSolver* solver);

    /// Returns the current bucket fill mass [kg] (forwarded to excavator HUD).
    float get_fill_mass() const { return _fill_mass_kg; }

    /// Returns the number of particles currently held in the bucket.
    int get_held_count() const { return _held_count; }

    // -- Configuration --
    void set_particles_per_voxel(int n) { _particles_per_voxel = n; }
    int  get_particles_per_voxel() const { return _particles_per_voxel; }

    void set_sweep_sample_count(int n) { _sweep_samples = n; }

protected:
    static void _bind_methods();

private:
    VoxelTerrain*    _terrain        = nullptr;
    DEMSolver*       _solver         = nullptr;
    godot::Area3D*   _dig_volume     = nullptr;
    godot::Area3D*   _contents_volume= nullptr;
    godot::Node3D*   _excavator      = nullptr;

    godot::Transform3D _prev_bucket_xform;
    bool               _has_prev_xform = false;

    float _fill_mass_kg       = 0.0f;
    int   _held_count         = 0;
    int   _particles_per_voxel = 4;  // DEM particles to spawn per carved voxel
    int   _sweep_samples      = 6;   // interpolation samples along the sweep arc

    // Indices of particles currently inside the contents volume.
    godot::PackedInt32Array _held_indices;

    // -- Internal steps --
    void _step_carve_and_spawn(const godot::Transform3D& bucket_xform, float delta);
    void _step_update_held(const godot::Transform3D& bucket_xform);
    void _step_revoxelise();
    void _step_resistance_feedback(float volume_carved_m3, uint8_t dominant_mat);

    // Samples N world-space positions along the bucket tip arc between
    // prev_xform and curr_xform.
    std::vector<godot::Vector3> _sample_sweep(
        const godot::Transform3D& prev,
        const godot::Transform3D& curr,
        int samples) const;

    // Returns true if world_pos is inside the contents_volume AABB.
    bool _inside_contents(const godot::Vector3& world_pos) const;
};
