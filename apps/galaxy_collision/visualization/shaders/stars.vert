#version 330

in vec3 in_position;
in vec3 in_color;

out vec3 v_color;
out float v_depth;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_point_size;

void main() {
    vec4 view_pos = u_view * u_model * vec4(in_position, 1.0);
    gl_Position = u_projection * view_pos;
    
    // Punktgröße basierend auf Tiefe
    float dist = length(view_pos.xyz);
    gl_PointSize = u_point_size * (50.0 / dist);
    gl_PointSize = clamp(gl_PointSize, 1.0, 10.0);
    
    v_color = in_color;
    v_depth = dist;
}
