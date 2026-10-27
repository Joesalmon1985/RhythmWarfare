shader_type canvas_item;
// Red Alert player-colour remap: the sixteen temperat.pal ramp colours (indices 80..95) baked into the sprites are
// replaced by this faction's ramp. Everything else passes through. Modulate alpha still applies.

uniform vec3 src_ramp[16];
uniform vec3 dst_ramp[16];

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec3 rgb = tex.rgb;
	for (int i = 0; i < 16; i++) {
		if (distance(rgb, src_ramp[i]) < 0.02) {
			rgb = dst_ramp[i];
			break;
		}
	}
	COLOR = vec4(rgb * COLOR.rgb / max(tex.rgb, vec3(0.0001)), tex.a * COLOR.a / max(tex.a, 0.0001));
}
