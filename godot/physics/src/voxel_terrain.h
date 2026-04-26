#pragma once

#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/variant/vector3i.hpp>
#include <godot_cpp/variant/vector3.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/dictionary.hpp>

#include <cstdint>
#include <vector>
#include <unordered_map>
#include <functional>

namespace godot { class ArrayMesh; }

// ---------------------------------------------------------------------------
// MaterialDef — mirrors the GDScript dictionary from material_registry.gd
// ---------------------------------------------------------------------------
struct MaterialDef {
    uint8_t  id               = 0;
    float    cohesion         = 0.0f;    // JKR energy [J/m²]
    float    friction_coeff   = 0.6f;
    float    rolling_friction = 0.05f;
    float    restitution      = 0.3f;
    float    density_kg_m3    = 1600.0f;
    float    angle_of_repose  = 34.0f;   // degrees
    float    particle_radius  = 0.02f;   // metres
    float    dig_resistance   = 1.0f;
    uint32_t color_rgba       = 0xFFFFFFFF;
    float    toy_scale        = 1.0f;
};

// ---------------------------------------------------------------------------
// Voxel cell — packed into 4 bytes to keep the grid cache-friendly
// ---------------------------------------------------------------------------
#pragma pack(push, 1)
struct VoxelCell {
    uint8_t material_id = 0;  // 0 = AIR
    uint8_t density     = 255; // 0 = empty, 255 = full (used by marching cubes)
    uint8_t _pad[2]     = {};
};
#pragma pack(pop)
static_assert(sizeof(VoxelCell) == 4, "VoxelCell must be 4 bytes");

// ---------------------------------------------------------------------------
// Chunk — a fixed-size block of voxels with its own dirty flag and mesh
// ---------------------------------------------------------------------------
struct Chunk {
    static constexpr int SIZE = 16; // voxels per side (must match GDScript constant)
    static constexpr int TOTAL = SIZE * SIZE * SIZE;

    std::vector<VoxelCell> cells;
    bool dirty = true;

    Chunk() : cells(TOTAL) {}

    inline VoxelCell& at(int x, int y, int z) {
        return cells[x + SIZE * (y + SIZE * z)];
    }
    inline const VoxelCell& at(int x, int y, int z) const {
        return cells[x + SIZE * (y + SIZE * z)];
    }
};

// ---------------------------------------------------------------------------
// VoxelTerrain — Godot Node3D that owns the voxel grid, manages mesh
// generation via marching cubes, and exposes carve/query API to GDScript
// and to the C++ BucketInteraction system.
// ---------------------------------------------------------------------------
class VoxelTerrain : public godot::Node3D {
    GDCLASS(VoxelTerrain, godot::Node3D)

public:
    VoxelTerrain();
    ~VoxelTerrain() override;

    // -- Godot lifecycle --
    void _ready() override;
    void _process(double delta) override;

    // -- GDScript API (bound via _bind_methods) --
    void set_voxel_size(float size);
    float get_voxel_size() const;

    void set_grid_size(const godot::Vector3i& size);
    godot::Vector3i get_grid_size() const;

    void set_chunk_size(int size);

    /// Populate the grid with layered materials.
    /// layers: Array of Dictionaries { "depth": int, "material": int }
    void generate_layered(const godot::Array& layers);

    /// Set material definitions from GDScript MaterialRegistry.
    void set_materials(const godot::Array& material_defs);

    /// Returns the material ID at voxel coords, or 0 (AIR) if out of bounds.
    int get_material(const godot::Vector3i& voxel_pos) const;

    /// Carve a sphere (debug / test use).
    void carve_sphere(const godot::Vector3& world_center, float radius);

    // -- C++ internal API (used by BucketInteraction) --
    /// Carve the voxels swept by the bucket last frame. Returns the
    /// total volume [m³] and material ID of the dominant carved material.
    float carve_swept_volume(
        const std::vector<godot::Vector3>& swept_positions,
        float bucket_radius,
        uint8_t& out_dominant_material
    );

    /// Callback invoked after carving; set by BucketInteraction.
    std::function<void(const godot::Vector3&, uint8_t, float)> on_carved;

    const MaterialDef& get_material_def(uint8_t id) const;

protected:
    static void _bind_methods();

private:
    // Grid dimensions (in chunks)
    godot::Vector3i _grid_size_voxels  = {256, 64, 256};
    godot::Vector3i _grid_size_chunks  = {16, 4, 16};
    float           _voxel_size        = 0.25f;
    int             _chunk_size        = 16;

    std::unordered_map<uint64_t, Chunk> _chunks;
    std::vector<MaterialDef>            _material_defs;

    // -- Chunk helpers --
    static uint64_t chunk_key(int cx, int cy, int cz);
    Chunk& get_or_create_chunk(int cx, int cy, int cz);
    VoxelCell* cell_at(int gx, int gy, int gz);
    const VoxelCell* cell_at_c(int gx, int gy, int gz) const;

    // -- Marching cubes meshing --
    void _remesh_dirty_chunks();
    void _mesh_chunk(int cx, int cy, int cz, Chunk& chunk);

    // Mesh instance nodes keyed by chunk coordinate
    std::unordered_map<uint64_t, godot::Node3D*> _chunk_nodes;

    // Marching cubes lookup tables (populated in constructor)
    static int _mc_edge_table[256];
    static int _mc_tri_table[256][16];
    void _mc_init();
};
