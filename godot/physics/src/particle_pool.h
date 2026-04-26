#pragma once

#include "dem_solver.h"
#include "voxel_terrain.h"

#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/classes/multi_mesh_instance3d.hpp>
#include <godot_cpp/classes/multi_mesh.hpp>
#include <godot_cpp/variant/packed_float32_array.hpp>

// ---------------------------------------------------------------------------
// ParticlePool
//
// GPU-instanced renderer for DEM particles. Each frame:
//   1. Queries DEMSolver for all active particle positions and material IDs.
//   2. Populates a MultiMeshInstance3D with per-instance transforms and
//      custom data (material colour + toy scale).
//   3. Applies a LOD strategy:
//      - < 20 m from camera: full individual spheres
//      - 20–60 m:            merged blobs (4 particles → 1 larger instance)
//      - > 60 m:             not rendered (too small to see)
//
// The mesh used is a single sphere (radius=1, scaled per instance via the
// MultiMesh transform). Material colour is packed into custom data channel 0.
// ---------------------------------------------------------------------------
class ParticlePool : public godot::Node3D {
    GDCLASS(ParticlePool, godot::Node3D)

public:
    ParticlePool();
    ~ParticlePool() override;

    void _ready()   override;
    void _process(double delta) override;

    // -- GDScript API --
    void set_solver(DEMSolver* solver);
    void set_terrain(VoxelTerrain* terrain);

    /// Set camera node path for LOD distance calculations.
    void set_camera_path(const godot::NodePath& path);

    /// Max simultaneous rendered instances (trim if over budget).
    void set_instance_budget(int budget) { _instance_budget = budget; }

protected:
    static void _bind_methods();

private:
    DEMSolver*                      _solver  = nullptr;
    VoxelTerrain*                   _terrain = nullptr;
    godot::MultiMeshInstance3D*     _mmi     = nullptr;
    godot::MultiMesh*               _mm      = nullptr;
    godot::Node3D*                  _camera  = nullptr;
    godot::NodePath                 _camera_path;
    int                             _instance_budget = 50000;

    void _update_multimesh(const godot::PackedVector3Array& positions,
                           const godot::PackedByteArray&    material_ids);

    // Builds a Transform3D for a particle at pos with given radius scaled by
    // the material's toy_scale.
    godot::Transform3D _particle_transform(const godot::Vector3& pos,
                                           float radius,
                                           float toy_scale) const;
};
