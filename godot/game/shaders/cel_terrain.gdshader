// cel_terrain.gdshader
// ---------------------------------------------------------------------------
// Toy-aesthetic terrain shader.
//
// Features:
//   - 2-step toon ramp based on NdotL (bright sun side vs. shadowed side)
//   - Material colour blending: four material colours blended per-vertex
//     using a weight texture written by VoxelTerrain during meshing
//   - Rim highlight at grazing angles (adds chunky plastic feel)
//   - Simple ambient occlusion darkening in crevices (via vertex colour A)
// ---------------------------------------------------------------------------
shader_type spatial;
render_mode diffuse_toon, specular_disabled, cull_back;

// Sun direction (set from WorldEnvironment or game_manager)
uniform vec3  sun_direction  : hint_default_black = vec3(0.577, 0.577, 0.577);
uniform vec3  sun_color      : source_color      = vec3(1.0, 0.95, 0.85);
uniform vec3  ambient_color  : source_color      = vec3(0.35, 0.45, 0.60);

// Toon ramp thresholds
uniform float ramp_threshold : hint_range(0.0, 1.0) = 0.4;
uniform float ramp_smoothing : hint_range(0.001, 0.2) = 0.05;

// Rim light
uniform float rim_strength   : hint_range(0.0, 1.0) = 0.25;
uniform vec3  rim_color      : source_color          = vec3(1.0, 0.85, 0.5);

// Four material colours, blended by vertex colour RGBA weights.
// The VoxelTerrain mesher packs material blend weights into vertex colour.
uniform vec3 mat_color_0 : source_color = vec3(0.96, 0.84, 0.55); // Dry Sand
uniform vec3 mat_color_1 : source_color = vec3(0.45, 0.30, 0.18); // Wet Dirt
uniform vec3 mat_color_2 : source_color = vec3(0.65, 0.63, 0.60); // Gravel
uniform vec3 mat_color_3 : source_color = vec3(0.74, 0.45, 0.28); // Clay

// AO strength (vertex colour A channel baked from voxel cavity depth)
uniform float ao_strength    : hint_range(0.0, 1.0) = 0.35;

varying vec3 v_normal_world;
varying vec3 v_view_dir;

void vertex() {
    v_normal_world = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
    v_view_dir     = normalize((INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz
                             - (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz);
}

void fragment() {
    // --- Material colour from vertex weights ---
    // Vertex colour channels store blend weights for 4 material types.
    vec4 w      = COLOR;
    vec3 base   = mat_color_0 * w.r
                + mat_color_1 * w.g
                + mat_color_2 * w.b
                + mat_color_3 * (1.0 - w.r - w.g - w.b);
    base        = clamp(base, 0.0, 1.0);

    // --- Toon ramp ---
    float ndotl  = dot(v_normal_world, normalize(sun_direction));
    float ramp   = smoothstep(ramp_threshold - ramp_smoothing,
                              ramp_threshold + ramp_smoothing,
                              ndotl);
    vec3 diffuse = mix(ambient_color, sun_color, ramp);

    // --- Rim highlight ---
    float rim    = 1.0 - clamp(dot(v_normal_world, v_view_dir), 0.0, 1.0);
    rim          = pow(rim, 3.0) * rim_strength;
    vec3 rim_contrib = rim_color * rim * ramp; // only on lit side

    // --- AO darkening (vertex colour A) ---
    float ao     = 1.0 - ao_strength * (1.0 - w.a);

    ALBEDO        = base * diffuse * ao + rim_contrib;
    ROUGHNESS     = 0.9;
    METALLIC      = 0.0;
}
