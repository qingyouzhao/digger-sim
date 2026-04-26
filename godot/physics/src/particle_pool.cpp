#include "particle_pool.h"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/classes/sphere_mesh.hpp>
#include <godot_cpp/classes/standard_material3d.hpp>
#include <godot_cpp/classes/engine.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

#include <algorithm>
#include <cmath>

using namespace godot;

// ---------------------------------------------------------------------------
// Godot bindings
// ---------------------------------------------------------------------------

void ParticlePool::_bind_methods() {
    ClassDB::bind_method(D_METHOD("set_solver",  "solver"),  &ParticlePool::set_solver);
    ClassDB::bind_method(D_METHOD("set_terrain", "terrain"), &ParticlePool::set_terrain);
    ClassDB::bind_method(D_METHOD("set_camera_path", "path"), &ParticlePool::set_camera_path);
    ClassDB::bind_method(
        D_METHOD("set_instance_budget", "budget"), &ParticlePool::set_instance_budget);
}

// ---------------------------------------------------------------------------

ParticlePool::ParticlePool() {}
ParticlePool::~ParticlePool() {}

void ParticlePool::_ready() {
    if (Engine::get_singleton()->is_editor_hint()) return;

    // Create a MultiMeshInstance3D as a child node.
    _mmi = memnew(MultiMeshInstance3D);
    add_child(_mmi);

    _mm = memnew(MultiMesh);
    _mm->set_transform_format(MultiMesh::TRANSFORM_3D);
    _mm->set_use_custom_data(true);   // channel 0 = RGBA colour
    _mm->set_instance_count(0);

    // Unit sphere mesh — scaled per-instance via transform.
    Ref<SphereMesh> sphere;
    sphere.instantiate();
    sphere->set_radius(1.0f);
    sphere->set_height(2.0f);
    sphere->set_radial_segments(6);   // low-poly for performance
    sphere->set_rings(4);
    _mm->set_mesh(sphere);

    // Material: unshaded per-instance colour driven by custom data.
    // The cel_particle.gdshader will be set from GDScript after the
    // extension is loaded, replacing this default.
    Ref<StandardMaterial3D> mat;
    mat.instantiate();
    mat->set_shading_mode(BaseMaterial3D::SHADING_MODE_UNSHADED);
    mat->set_flag(BaseMaterial3D::FLAG_SRGB_VERTEX_COLOR, true);
    _mm->set_surface_override_material(0, mat);

    _mmi->set_multimesh(_mm);
}

void ParticlePool::_process(double /*delta*/) {
    if (!_solver || !_mm) return;
    if (Engine::get_singleton()->is_editor_hint()) return;

    PackedVector3Array positions   = _solver->get_positions();
    PackedByteArray    material_ids = _solver->get_material_ids();

    _update_multimesh(positions, material_ids);
}

// ---------------------------------------------------------------------------
// Solver / terrain links
// ---------------------------------------------------------------------------

void ParticlePool::set_solver(DEMSolver* solver)    { _solver  = solver; }
void ParticlePool::set_terrain(VoxelTerrain* terrain){ _terrain = terrain; }

void ParticlePool::set_camera_path(const NodePath& path) {
    _camera_path = path;
    _camera = get_node_or_null<Node3D>(path);
}

// ---------------------------------------------------------------------------
// MultiMesh update
// ---------------------------------------------------------------------------

void ParticlePool::_update_multimesh(const PackedVector3Array& positions,
                                      const PackedByteArray&    material_ids)
{
    int count = std::min(static_cast<int>(positions.size()), _instance_budget);
    if (_mm->get_instance_count() != count) {
        _mm->set_instance_count(count);
    }

    Vector3 cam_pos = _camera ? _camera->get_global_position() : Vector3();

    for (int i = 0; i < count; ++i) {
        const Vector3& pos = positions[i];
        uint8_t mat_id = material_ids[i];

        // LOD: skip distant particles entirely.
        float dist2 = cam_pos.distance_squared_to(pos);
        if (dist2 > 60.0f * 60.0f) {
            // Move off-screen rather than resizing the multimesh every frame.
            _mm->set_instance_transform(i, Transform3D(Basis(), Vector3(0.0f, -1000.0f, 0.0f)));
            continue;
        }

        // Fetch material definition for radius + colour.
        float radius    = 0.02f;
        float toy_scale = 1.0f;
        Color color     = Color(0.8f, 0.7f, 0.5f);

        if (_terrain) {
            const MaterialDef& m = _terrain->get_material_def(mat_id);
            radius    = m.particle_radius;
            toy_scale = m.toy_scale;
            uint32_t rgba = m.color_rgba;
            color = Color(
                float((rgba >> 24) & 0xFF) / 255.0f,
                float((rgba >> 16) & 0xFF) / 255.0f,
                float((rgba >>  8) & 0xFF) / 255.0f,
                1.0f
            );
        }

        // LOD merge: > 20 m → double visual radius (fewer draw calls in practice
        // since we still use the same multimesh; real merging would reduce count).
        if (dist2 > 20.0f * 20.0f) toy_scale *= 2.0f;

        _mm->set_instance_transform(i, _particle_transform(pos, radius, toy_scale));
        _mm->set_instance_custom_data(i, color);
    }
}

Transform3D ParticlePool::_particle_transform(const Vector3& pos,
                                               float radius,
                                               float toy_scale) const
{
    float s = radius * toy_scale;
    Basis b = Basis().scaled(Vector3(s, s, s));
    return Transform3D(b, pos);
}
