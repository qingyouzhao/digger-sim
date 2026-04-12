// particle_material.gdshader
// ---------------------------------------------------------------------------
// Shader for GPU-instanced DEM particles rendered via MultiMeshInstance3D.
//
// Each particle instance carries:
//   INSTANCE_CUSTOM.rgb — material colour (set by ParticlePool from MaterialDef)
//   INSTANCE_CUSTOM.a   — reserved (could encode wetness / shininess)
//
// The sphere mesh is a unit sphere (radius=1). The per-instance Transform3D
// scales it to the correct physical radius × toy_scale.
//
// Visual goals:
//   - Tiny sand: warm yellow, slight gloss, almost round
//   - Dirt clumps: dark brown, matte, slightly rough silhouette
//   - Gravel: grey, faceted feel from low-poly sphere + sharp normals
//   - Clay: terracotta, slightly plastic sheen
//
// The shader uses a simple toon-ish lighting model without a ramp —
// just N·L with a minimum ambient term — so particles read as solid
// coloured volumes rather than realistic spheres.
// ---------------------------------------------------------------------------
shader_type spatial;
render_mode diffuse_lambert, specular_disabled, cull_back, depth_draw_opaque;

uniform vec3 sun_direction  : hint_default_black = vec3(0.577, 0.577, 0.577);
uniform vec3 sun_color      : source_color       = vec3(1.0, 0.95, 0.85);
uniform vec3 ambient_color  : source_color       = vec3(0.3, 0.4, 0.55);

// Slightly quantise shading to match terrain/machine toon aesthetic.
uniform float shade_steps   : hint_range(1.0, 8.0) = 3.0;

void vertex() {
    // No custom vertex logic needed — MultiMesh applies per-instance transform.
}

void fragment() {
    // Per-instance colour packed into INSTANCE_CUSTOM by ParticlePool.
    vec3 base_color = INSTANCE_CUSTOM.rgb;

    // N·L shading, quantised.
    float ndotl     = max(dot(NORMAL, normalize(sun_direction)), 0.0);
    float shade     = floor(ndotl * shade_steps) / shade_steps;
    vec3 diffuse    = mix(ambient_color, sun_color, shade);

    ALBEDO          = base_color * diffuse;
    ROUGHNESS       = 0.85;
    METALLIC        = 0.0;
}
