shader_type canvas_item;
// Red Alert player-colour remap. tools/extract_openra.py flags every pixel whose palette index lies in the remap
// range 80..95 with alpha 253/255; those pixels are replaced by this faction's ramp entry (matched against the
// sixteen source colours), exactly as OpenRA's player palette does. Everything else passes through unchanged.

uniform vec3 src_ramp[16];
uniform vec3 dst_ramp[16];

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec3 rgb = tex.rgb;
	float a = tex.a;
	if (abs(a - 253.0 / 255.0) < 0.003) {
		int best = 0;
		float best_d = 10.0;
		for (int i = 0; i < 16; i++) {
			float d = distance(rgb, src_ramp[i]);
			if (d < best_d) {
				best_d = d;
				best = i;
			}
		}
		rgb = dst_ramp[best];
		a = 1.0;
	}
	COLOR = vec4(rgb * COLOR.rgb / max(tex.rgb, vec3(0.0001)), a * COLOR.a / max(tex.a, 0.0001));
}
