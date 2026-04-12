cmake_minimum_required(VERSION 3.22)
project(digger_physics VERSION 0.1.0 LANGUAGES CXX)

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
option(DIGGER_USE_CHRONO   "Link against Project Chrono DEM-Engine (requires CUDA)" OFF)
option(DIGGER_USE_OPENMP   "Enable OpenMP parallelism for the lightweight DEM solver" ON)
option(DIGGER_BUILD_TESTS  "Build unit tests" OFF)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---------------------------------------------------------------------------
# godot-cpp (header-only bindings shipped as submodule)
# ---------------------------------------------------------------------------
# Expected layout: physics/godot-cpp/ (git submodule of godotengine/godot-cpp)
set(GODOT_CPP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/godot-cpp")
if(NOT EXISTS "${GODOT_CPP_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "godot-cpp submodule not found at ${GODOT_CPP_DIR}.\n"
        "Run: git submodule update --init --recursive")
endif()
add_subdirectory(${GODOT_CPP_DIR} godot-cpp)

# ---------------------------------------------------------------------------
# Source files
# ---------------------------------------------------------------------------
set(DIGGER_SOURCES
    src/register_types.cpp
    src/digger_physics.cpp
    src/voxel_terrain.cpp
    src/dem_solver.cpp
    src/bucket_interaction.cpp
    src/particle_pool.cpp
    src/chrono_bridge.cpp     # no-op stub when DIGGER_USE_CHRONO=OFF
)

add_library(digger_physics SHARED ${DIGGER_SOURCES})

target_include_directories(digger_physics PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(digger_physics PRIVATE godot-cpp)

# ---------------------------------------------------------------------------
# Optional: OpenMP for lightweight DEM
# ---------------------------------------------------------------------------
if(DIGGER_USE_OPENMP)
    find_package(OpenMP REQUIRED)
    target_link_libraries(digger_physics PRIVATE OpenMP::OpenMP_CXX)
    target_compile_definitions(digger_physics PRIVATE DIGGER_OPENMP)
endif()

# ---------------------------------------------------------------------------
# Optional: Project Chrono DEM-Engine
# ---------------------------------------------------------------------------
if(DIGGER_USE_CHRONO)
    find_package(Chrono REQUIRED COMPONENTS GPU)
    target_link_libraries(digger_physics PRIVATE ChronoEngine ChronoEngine_gpu)
    target_compile_definitions(digger_physics PRIVATE DIGGER_CHRONO)
    message(STATUS "Chrono DEM backend ENABLED")
else()
    message(STATUS "Chrono DEM backend DISABLED — using lightweight CPU DEM")
endif()

# ---------------------------------------------------------------------------
# Output naming: Godot expects <name>.<platform>.<config>.<arch>.(so|dll|dylib)
# ---------------------------------------------------------------------------
set_target_properties(digger_physics PROPERTIES
    PREFIX          ""
    OUTPUT_NAME     "libdigger_physics"
)

# Put the built library into game/bin/ where the .gdextension file expects it
set(GAME_BIN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../game/bin")

add_custom_command(TARGET digger_physics POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${GAME_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:digger_physics>
        "${GAME_BIN_DIR}/$<TARGET_FILE_NAME:digger_physics>"
    COMMENT "Copying digger_physics library to game/bin/"
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
if(DIGGER_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
