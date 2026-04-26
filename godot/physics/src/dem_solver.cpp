#include "dem_solver.h"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

#include <cmath>
#include <algorithm>
#include <numeric>

#ifdef DIGGER_OPENMP
#  include <omp.h>
#endif

using namespace godot;

// ---------------------------------------------------------------------------
// Godot bindings
// ---------------------------------------------------------------------------

void DEMSolver::_bind_methods() {
    ClassDB::bind_method(D_METHOD("configure", "cfg"),           &DEMSolver::configure);
    ClassDB::bind_method(D_METHOD("set_material_defs", "defs"),  &DEMSolver::set_material_defs);
    ClassDB::bind_method(D_METHOD("step", "delta"),              &DEMSolver::step);
    ClassDB::bind_method(D_METHOD("spawn_particle",
        "world_pos", "velocity", "material_id"),                  &DEMSolver::spawn_particle);
    ClassDB::bind_method(D_METHOD("get_positions"),              &DEMSolver::get_positions);
    ClassDB::bind_method(D_METHOD("get_material_ids"),           &DEMSolver::get_material_ids);
    ClassDB::bind_method(D_METHOD("get_held_mass"),              &DEMSolver::get_held_mass);
}

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

DEMSolver::DEMSolver() {
    _particles.reserve(static_cast<size_t>(_config.max_particles));
}

DEMSolver::~DEMSolver() {}

void DEMSolver::_ready() {}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

void DEMSolver::configure(const Dictionary& cfg) {
    if (cfg.has("substeps"))          _config.substeps       = int(cfg["substeps"]);
    if (cfg.has("gravity"))           _config.gravity        = float(cfg["gravity"]);
    if (cfg.has("max_particles"))     _config.max_particles  = int(cfg["max_particles"]);
    if (cfg.has("damping"))           _config.damping        = float(cfg["damping"]);
    if (cfg.has("rest_threshold"))    _config.rest_threshold = float(cfg["rest_threshold"]);
    if (cfg.has("rest_time_needed"))  _config.rest_time_needed = float(cfg["rest_time_needed"]);
    _particles.reserve(static_cast<size_t>(_config.max_particles));
}

void DEMSolver::set_material_defs(const Array& defs) {
    _mat_defs.resize(static_cast<size_t>(defs.size()));
    for (int i = 0; i < defs.size(); ++i) {
        if (defs[i].get_type() != Variant::DICTIONARY) continue;
        const Dictionary d = defs[i];
        MaterialDef& m = _mat_defs[i];
        m.id               = static_cast<uint8_t>(i);
        m.cohesion         = float(d.get("cohesion",         0.0));
        m.friction_coeff   = float(d.get("friction_coeff",   0.6));
        m.rolling_friction = float(d.get("rolling_friction", 0.05));
        m.restitution      = float(d.get("restitution",      0.3));
        m.density_kg_m3    = float(d.get("density_kg_m3",    1600.0));
        m.particle_radius  = float(d.get("particle_radius",  0.02));
    }
    // Choose broad-phase cell size = 2 × max particle radius + margin.
    float max_r = 0.0f;
    for (auto& m : _mat_defs) max_r = std::max(max_r, m.particle_radius);
    _grid_cell_size = 2.0f * max_r + 0.01f;
}

// ---------------------------------------------------------------------------
// Particle spawning
// ---------------------------------------------------------------------------

int DEMSolver::spawn_particle(const Vector3& world_pos,
                               const Vector3& velocity,
                               uint8_t material_id)
{
    if (static_cast<int>(_particles.size()) >= _config.max_particles) return -1;

    // Reuse an inactive slot if available.
    for (int i = 0; i < static_cast<int>(_particles.size()); ++i) {
        if (!_particles[i].active) {
            _init_particle(_particles[i], world_pos, velocity, material_id);
            ++_active_count;
            return i;
        }
    }

    // Append a new slot.
    DEMParticle p{};
    _init_particle(p, world_pos, velocity, material_id);
    _particles.push_back(p);
    ++_active_count;
    return static_cast<int>(_particles.size()) - 1;
}

void DEMSolver::_init_particle(DEMParticle& p,
                                const Vector3& pos,
                                const Vector3& vel,
                                uint8_t mat_id)
{
    p.pos         = pos;
    p.vel         = vel;
    p.force       = Vector3();
    p.angular_vel = Vector3();
    p.material_id = mat_id;
    p.active      = true;
    p.held        = false;
    p.settled     = false;
    p.rest_timer  = 0.0f;

    if (static_cast<size_t>(mat_id) < _mat_defs.size()) {
        const MaterialDef& m = _mat_defs[mat_id];
        p.radius = m.particle_radius;
        // Mass = density × volume of sphere.
        float r3 = p.radius * p.radius * p.radius;
        p.mass   = m.density_kg_m3 * (4.0f / 3.0f) * 3.14159265f * r3;
    } else {
        p.radius = 0.02f;
        p.mass   = 0.01f;
    }
}

// ---------------------------------------------------------------------------
// Main step
// ---------------------------------------------------------------------------

void DEMSolver::step(float game_delta) {
    const float dt = game_delta / static_cast<float>(_config.substeps);
    for (int sub = 0; sub < _config.substeps; ++sub) {
        _broad_phase_rebuild();
        _apply_gravity(dt);
        _resolve_contacts(dt);
        _integrate(dt);
    }
}

void DEMSolver::_apply_gravity(float dt) {
    const Vector3 g(0.0f, -_config.gravity, 0.0f);
#ifdef DIGGER_OPENMP
    #pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < static_cast<int>(_particles.size()); ++i) {
        DEMParticle& p = _particles[i];
        if (!p.active || p.held) continue;
        p.force += g * p.mass;
    }
}

void DEMSolver::_resolve_contacts(float dt) {
    // Particle-particle contacts via broad-phase grid.
    for (auto& [key, cell] : _grid) {
        const auto& ids = cell.indices;
        for (size_t a = 0; a < ids.size(); ++a) {
            DEMParticle& pa = _particles[ids[a]];
            if (!pa.active) continue;
            const MaterialDef& ma = ids[a] < static_cast<int>(_mat_defs.size())
                ? _mat_defs[pa.material_id] : MaterialDef{};

            // Check 27-neighbour grid cells.
            int ax = static_cast<int>(std::floor(pa.pos.x / _grid_cell_size));
            int ay = static_cast<int>(std::floor(pa.pos.y / _grid_cell_size));
            int az = static_cast<int>(std::floor(pa.pos.z / _grid_cell_size));
            for (int dz = -1; dz <= 1; ++dz) {
                for (int dy = -1; dy <= 1; ++dy) {
                    for (int dx = -1; dx <= 1; ++dx) {
                        auto it = _grid.find(grid_key(ax+dx, ay+dy, az+dz));
                        if (it == _grid.end()) continue;
                        for (int bIdx : it->second.indices) {
                            if (bIdx <= ids[a]) continue; // avoid double counting
                            DEMParticle& pb = _particles[bIdx];
                            if (!pb.active) continue;
                            const MaterialDef& mb = bIdx < static_cast<int>(_mat_defs.size())
                                ? _mat_defs[pb.material_id] : MaterialDef{};
                            _contact_force(pa, pb, ma, mb, dt);
                        }
                    }
                }
            }
            // Boundary check per particle.
            _boundary_contacts(pa, ma, dt);
        }
    }
}

void DEMSolver::_contact_force(DEMParticle& a, DEMParticle& b,
                                const MaterialDef& ma, const MaterialDef& mb,
                                float dt)
{
    Vector3 delta = b.pos - a.pos;
    float dist    = delta.length();
    float overlap = a.radius + b.radius - dist;
    if (overlap <= 0.0f) return;

    Vector3 n = (dist > 1e-7f) ? (delta / dist) : Vector3(0.0f, 1.0f, 0.0f);

    // Effective moduli (Hertz: 1/E* = (1-v²a)/Ea + (1-v²b)/Eb — approximate).
    // We use a simplified stiffness kn proportional to radius.
    float R_eff = (a.radius * b.radius) / (a.radius + b.radius);
    float kn    = 1.0e5f * std::sqrt(R_eff * overlap);  // Hertz stiffness
    float cn    = 50.0f * std::sqrt(a.mass * b.mass / (a.mass + b.mass)); // damping

    // Relative velocity at contact.
    Vector3 rel_vel = b.vel - a.vel;
    float   vn      = rel_vel.dot(n);

    // Normal impulse (compressive only).
    float fn = kn * overlap - cn * vn;
    fn = std::max(fn, 0.0f);

    // JKR cohesion pull-off force.
    if (ma.cohesion > 0.0f || mb.cohesion > 0.0f) {
        float gamma = 0.5f * (ma.cohesion + mb.cohesion);
        float f_pulloff = 3.0f * 3.14159265f * gamma * R_eff;
        fn -= f_pulloff;  // adhesive: can be negative (tension)
    }

    Vector3 fn_vec = n * fn;

    // Tangential (friction) impulse.
    Vector3 rel_vel_t = rel_vel - n * vn;
    float   rel_speed_t = rel_vel_t.length();
    float   mu = 0.5f * (ma.friction_coeff + mb.friction_coeff);
    float   ft = std::min(mu * std::abs(fn), 5000.0f * rel_speed_t);
    Vector3 ft_vec = (rel_speed_t > 1e-7f)
        ? (-rel_vel_t / rel_speed_t * ft)
        : Vector3();

    // Apply to both particles (Newton's third law).
    Vector3 total = fn_vec + ft_vec;
    a.force -= total;
    b.force += total;
}

void DEMSolver::_boundary_contacts(DEMParticle& p, const MaterialDef& m, float /*dt*/) {
    // Floor at y = 0.
    float floor_overlap = p.radius - p.pos.y;
    if (floor_overlap > 0.0f) {
        float kn = 1.0e5f;
        float fn = kn * floor_overlap - 50.0f * p.vel.y;
        fn = std::max(fn, 0.0f);
        p.force.y += fn;
        // Friction on floor.
        float ft = m.friction_coeff * fn;
        float hspeed = std::sqrt(p.vel.x*p.vel.x + p.vel.z*p.vel.z);
        if (hspeed > 1e-4f) {
            p.force.x -= ft * p.vel.x / hspeed;
            p.force.z -= ft * p.vel.z / hspeed;
        }
    }
}

void DEMSolver::_integrate(float dt) {
#ifdef DIGGER_OPENMP
    #pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < static_cast<int>(_particles.size()); ++i) {
        DEMParticle& p = _particles[i];
        if (!p.active || p.held) continue;

        // Semi-implicit Euler.
        p.vel += (p.force / p.mass) * dt;
        p.vel *= _config.damping;
        p.pos += p.vel * dt;

        // Reset accumulated force.
        p.force = Vector3();

        // Settle detection.
        float speed = p.vel.length();
        if (speed < _config.rest_threshold) {
            p.rest_timer += dt;
            if (p.rest_timer >= _config.rest_time_needed) p.settled = true;
        } else {
            p.rest_timer = 0.0f;
            p.settled    = false;
        }
    }
}

// ---------------------------------------------------------------------------
// Broad-phase uniform grid
// ---------------------------------------------------------------------------

void DEMSolver::_broad_phase_rebuild() {
    _grid.clear();
    for (int i = 0; i < static_cast<int>(_particles.size()); ++i) {
        const DEMParticle& p = _particles[i];
        if (!p.active) continue;
        int ix = static_cast<int>(std::floor(p.pos.x / _grid_cell_size));
        int iy = static_cast<int>(std::floor(p.pos.y / _grid_cell_size));
        int iz = static_cast<int>(std::floor(p.pos.z / _grid_cell_size));
        _grid[grid_key(ix, iy, iz)].indices.push_back(i);
    }
}

uint64_t DEMSolver::grid_key(int ix, int iy, int iz) {
    // Pack three 21-bit signed integers. Offset by 2^20 to handle negatives.
    constexpr int OFF = 1 << 20;
    return (static_cast<uint64_t>((ix + OFF) & 0x1FFFFF)      )
         | (static_cast<uint64_t>((iy + OFF) & 0x1FFFFF) << 21)
         | (static_cast<uint64_t>((iz + OFF) & 0x1FFFFF) << 42);
}

// ---------------------------------------------------------------------------
// Query helpers
// ---------------------------------------------------------------------------

PackedVector3Array DEMSolver::get_positions() const {
    PackedVector3Array out;
    out.resize(_active_count);
    int idx = 0;
    for (const DEMParticle& p : _particles) {
        if (p.active) out[idx++] = p.pos;
    }
    return out;
}

PackedByteArray DEMSolver::get_material_ids() const {
    PackedByteArray out;
    out.resize(_active_count);
    int idx = 0;
    for (const DEMParticle& p : _particles) {
        if (p.active) out[idx++] = p.material_id;
    }
    return out;
}

float DEMSolver::get_held_mass() const {
    float total = 0.0f;
    for (const DEMParticle& p : _particles) {
        if (p.active && p.held) total += p.mass;
    }
    return total;
}

void DEMSolver::set_held(const PackedInt32Array& indices, bool held) {
    for (int i = 0; i < indices.size(); ++i) {
        int idx = indices[i];
        if (idx >= 0 && idx < static_cast<int>(_particles.size())) {
            _particles[idx].held = held;
        }
    }
}

std::vector<std::pair<Vector3, uint8_t>> DEMSolver::drain_settled() {
    std::vector<std::pair<Vector3, uint8_t>> out;
    for (DEMParticle& p : _particles) {
        if (p.active && p.settled) {
            out.emplace_back(p.pos, p.material_id);
            p.active  = false;
            p.settled = false;
            --_active_count;
        }
    }
    return out;
}

