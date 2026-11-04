shader_type canvas_item;
// The post-process on the low-res world image (nearest-filtered, so the warp stays pixel-sharp): the queasy wobble (a sine warp, a chroma split, desaturation, a vignette that
// breathes slowly), the mood dimming and ending fade (dim), the drop's strobe and bloom. All inputs are functions of song time (StoryLight.post_state).
uniform float queasy = 0.0;
uniform float time_s = 0.0;
uniform float dim = 0.0;
uniform vec3 dim_color = vec3(0.02, 0.02, 0.08);
uniform float strobe = 0.0;
uniform float flash = 0.0;
uniform vec3 flash_color = vec3(0.6, 0.7, 1.0);
uniform float vignette = 0.15;

void fragment() {
	vec2 uv = UV;
	float w = queasy;
	uv.x += (sin(UV.y * 9.0 + time_s * 1.3) * 0.012 + sin(UV.y * 23.0 - time_s * 0.9) * 0.004) * w;
	uv.y += sin(UV.x * 7.0 + time_s * 1.1) * 0.010 * w;
	float split = 0.006 * w;
	vec3 col;
	col.r = texture(TEXTURE, uv + vec2(split, 0.0)).r;
	col.g = texture(TEXTURE, uv).g;
	col.b = texture(TEXTURE, uv - vec2(split, 0.0)).b;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(col, vec3(l) * vec3(0.9, 1.0, 0.92), 0.55 * w);
	float breath = 0.5 + 0.5 * sin(time_s * 1.5);
	float v = smoothstep(0.35, 0.95, length((UV - 0.5) * vec2(1.0, 1.3)));
	col *= 1.0 - v * (vignette + w * 0.35 * breath);
	col = mix(col, dim_color, dim);
	col += flash_color * flash;
	col = mix(col, vec3(1.0), strobe);
	COLOR = vec4(col, 1.0);
}
