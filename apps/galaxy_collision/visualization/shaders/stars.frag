#version 330

in vec3 v_color;
in float v_depth;

out vec4 f_color;

void main() {
    // Kreisförmige Punkte
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist_sq = dot(coord, coord);
    
    if (dist_sq > 0.25) {
        discard;
    }
    
    // Weicher Rand
    float alpha = 1.0 - smoothstep(0.1, 0.25, dist_sq);
    
    // Leichtes Glow im Zentrum
    float glow = exp(-dist_sq * 10.0);
    vec3 final_color = v_color + vec3(glow * 0.3);
    
    // Tiefenbasiertes Dimming (entfernte Sterne dunkler)
    float depth_factor = clamp(100.0 / v_depth, 0.3, 1.0);
    
    f_color = vec4(final_color * depth_factor, alpha);
}
