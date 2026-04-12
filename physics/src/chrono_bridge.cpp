// chrono_bridge.cpp
// ---------------------------------------------------------------------------
// No-op stub when compiled without DIGGER_USE_CHRONO.
// When DIGGER_USE_CHRONO is defined (and Chrono::GPU is found by CMake),
// this file is replaced with the full bridge that wraps ChGpuSolver and
// converts between ChVector3<double> and godot::Vector3.
//
// Phase 6 implementation notes:
//   - ChGpuSolver handles the DEM integration; results are read back via
//     ChGpuApiSMC::GetParticlePositions() / GetParticleVelocities() into
//     host vectors each frame and copied into the ParticlePool multimesh.
//   - The Jolt rigid-body world (machines, rocks) runs independently in
//     Godot; at each physics frame the bucket transform is sent to Chrono
//     as a boundary body, and Chrono returns the net contact force on it,
//     which is applied to the Jolt excavator body.
//   - Material parameters are passed via ChGpuApiSMC::SetKn_SPH2SPH,
//     SetGn_SPH2SPH, SetFrictionMode, SetAdhesionRatio_SPH2WALL etc.
//
// To enable:
//   cmake -DDIGGER_USE_CHRONO=ON -DChronoEngine_DIR=<path/to/chrono/lib/cmake> ..
// ---------------------------------------------------------------------------

#ifdef DIGGER_CHRONO

#include "chrono_bridge.h"
// Full implementation — Phase 6.
// Placeholder to prevent linker errors during Phase 3.

#else
// Nothing — lightweight DEMSolver in dem_solver.cpp is active.
#endif
