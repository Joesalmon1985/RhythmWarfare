shader_type canvas_item;
// The post-process on the low-res world image (nearest-filtered, so the warp stays pixel-sharp): the queasy wobble (a sine warp, a chroma split, desaturation, a vignette that
// breathes slowly), the value range of the style guide (section 2: the toe and the shoulder below), the mood dimming and ending fade (dim), the drop's strobe and bloom. All inputs
// are functions of song time (StoryLight.post_state) and of the sector the camera is in (its fog).
uniform float queasy = 0.0;
uniform float time_s = 0.0;
uniform float dim = 0.0;
uniform vec3 dim_color = vec3(0.02, 0.02, 0.08);
uniform float strobe = 0.0;
uniform float flash = 0.0;
uniform vec3 flash_color = vec3(0.6, 0.7, 1.0);
uniform float vignette = 0.15;
// The value range (always on; StoryLowRes.floor_of): the toe lifts black to `floor_col`, the fog colour of the camera's sector brought to a luminance of 0.042 to 0.06, so
// shadows are a colour and never crushed (col = floor + col * (1 - floor)); the shoulder rolls everything above `knee` off towards `top`, so a lit surface never clips
// to white (1.0 comes out at 0.886). The strobe and the flash are lights and come after it.
uniform vec3 floor_col = vec3(0.045, 0.04, 0.07);
uniform float knee = 0.75;
uniform float top = 1.05;
// The pixel look (a setting, off with reduced effects): ordered 4x4 dithering in the low-res pixel grid onto a reduced set of levels per channel.
uniform float dither_on = 0.0;
uniform vec2 low_size = vec2(640.0, 360.0);
uniform float levels = 20.0;
const float BAYER[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

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
	col = floor_col + col * (1.0 - floor_col);
	vec3 over = max(col - knee, vec3(0.0));
	col = min(col, vec3(knee)) + over / (1.0 + over / (top - knee));
	col = mix(col, dim_color, dim);
	col += flash_color * flash;
	col = mix(col, vec3(1.0), strobe);
	if (dither_on > 0.5) {
		ivec2 p = ivec2(floor(UV * low_size));
		float b = (BAYER[(p.y % 4) * 4 + (p.x % 4)] + 0.5) / 16.0 - 0.5;
		col = max(floor(col * levels + 0.5 + b) / levels, floor_col * (1.0 - dim));
	}
	COLOR = vec4(col, 1.0);
}
