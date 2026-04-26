// cel_machine.gdshader
// ---------------------------------------------------------------------------
// Toy-aesthetic shader for machine bodies (excavator, dump truck, containers).
//
// Features:
//   - Inverted-hull outline pass (separate draw call via a second material
//     on the outline mesh child, configured in scene)
//   - 3-step toon ramp (highlight / mid / shadow) for chunkier look
//   - Specular dot (single Blinn-Phong highlight, cel-quantised)
//   - Scratches / dirt mask in texture A channel (darkens locally)
//   - Paint colour uniform — easy to swap per machine type
// ---------------------------------------------------------------------------
shader_type spatial;
render_mode diffuse_toon, specular_toon, cull_back;

// Machine paint colour (yellow for excavator, red for truck, etc.)
uniform vec4  paint_color    : source_color = vec4(0.97, 0.78, 0.10, 1.0);

// Toon ramp
uniform float ramp_hi_thresh : hint_range(0.0, 1.0) = 0.75;
uniform float ramp_lo_thresh : hint_range(0.0, 1.0) = 0.30;
uniform float ramp_smooth    : hint_range(0.001, 0.1) = 0.04;
uniform vec3  shadow_color   : source_color = vec3(0.15, 0.10, 0.05);
uniform vec3  sun_dir        : hint_default_black = vec3(0.577, 0.577, 0.577);

// Specular
uniform float spec_power     : hint_range(1.0, 128.0) = 32.0;
uniform float spec_threshold : hint_range(0.0, 1.0)   = 0.85;
uniform float spec_smooth    : hint_range(0.001, 0.1)  = 0.02;

// Dirt/scratch map (R=albedo detail, A=scratch mask)
uniform sampler2D dirt_map   : hint_default_white, repeat_enable;
uniform float     dirt_scale : hint_range(0.0, 1.0) = 0.15;
uniform vec2      dirt_uv_scale = vec2(4.0, 4.0);

// Outline width (for the outline pass — this shader handles the fill pass).
uniform float outline_width  : hint_range(0.0, 0.05) = 0.008;
uniform vec4  outline_color  : source_color = vec4(0.1, 0.05, 0.0, 1.0);

varying vec3 v_normal_world;
varying vec3 v_view_dir;
varying vec3 v_world_pos;

void vertex() {
    v_normal_world = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
    vec4 world_pos = MODEL_MATRIX * vec4(VERTEX, 1.0);
    v_world_pos    = world_pos.xyz;
    v_view_dir     = normalize((INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz
                             - world_pos.xyz);
}

void fragment() {
    vec3 N = normalize(v_normal_world);
    vec3 L = normalize(sun_dir);
    vec3 V = normalize(v_view_dir);

    // --- Toon ramp (3 steps) ---
    float ndotl  = dot(N, L);
    float hi     = smoothstep(ramp_hi_thresh - ramp_smooth, ramp_hi_thresh + ramp_smooth, ndotl);
    float mid    = smoothstep(ramp_lo_thresh - ramp_smooth, ramp_lo_thresh + ramp_smooth, ndotl);
    vec3 light   = mix(shadow_color, vec3(0.7), mid);
    light        = mix(light, vec3(1.0), hi);

    // --- Dirt / scratch ---
    vec4 dirt    = texture(dirt_map, UV * dirt_uv_scale);
    float scratch = dirt.a * dirt_scale;

    // --- Base paint ---
    vec3 base    = paint_color.rgb * (1.0 - scratch * 0.5);

    // --- Specular (quantised to on/off) ---
    vec3 H       = normalize(L + V);
    float spec_v = pow(max(dot(N, H), 0.0), spec_power);
    float spec   = smoothstep(spec_threshold - spec_smooth,
                              spec_threshold + spec_smooth, spec_v);

    ALBEDO        = base * light + vec3(spec * 0.8);
    ROUGHNESS     = 0.5;
    METALLIC      = 0.1;
    ALPHA         = paint_color.a;
}
