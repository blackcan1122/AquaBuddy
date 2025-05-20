#version 330 core
uniform float u_time;
uniform vec2 u_resolution;
out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float wave = 0.02 * sin(uv.x * 30.0 + u_time * 2.0);
    vec3 color = vec3(0.0, 0.3 + wave, 0.7 + wave*0.5);
    fragColor = vec4(color, 1.0);
}
