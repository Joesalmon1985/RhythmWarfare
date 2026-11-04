shader_type canvas_item;
// The baked people (StoryPeople, tools/story/art/people.py): an 8-bit sheet pixel is (material << 2 | shade step), +128 on the silhouette's rim, 0 transparent.
// COLOR carries the actor (self_modulate): r = palette row, g = depth fog 0..1, b = brightness / 2 (a followspot lifts it), a = alpha.
// The colour is the actor's palette entry lit by the light where they stand (light_tex, one texel per row, stored halved); far figures fade towards the fog
// colour and keep a rim of the light, so the back rows read as dark silhouettes edged with the room's light.
uniform sampler2D palette : filter_nearest, repeat_disable;
uniform sampler2D light_tex : filter_nearest, repeat_disable;
uniform vec3 fog_color = vec3(0.04, 0.03, 0.1);
varying vec4 actor;  // the self_modulate as the vertex stage sees it (the fragment's COLOR is already multiplied by the texture)
uniform float min_light = 0.55;
uniform float gain = 1.3;  // the figures' palette is darker than the world's albedo: the room light is scaled up for them

void vertex() {
	actor = COLOR;
}

void fragment() {
	int idx = int(texture(TEXTURE, UV).r * 255.0 + 0.5);
	if (idx == 0) {
		discard;
	}
	int rim = idx >= 128 ? 1 : 0;
	int pi = idx - rim * 128;
	int row = int(actor.r * 256.0);
	vec4 pc = texelFetch(palette, ivec2(pi, row), 0);
	vec3 light = texelFetch(light_tex, ivec2(row, 0), 0).rgb * 2.0 * gain;
	float fog = actor.g;
	float bright = actor.b * 2.0;
	vec3 lit = pc.a < 0.999 ? pc.rgb : pc.rgb * clamp(light, vec3(min_light), vec3(1.12)) * bright;
	vec3 c = mix(lit, fog_color, fog * 0.82);
	if (rim == 1) {
		vec3 rl = light / max(max(light.r, max(light.g, light.b)), 0.2);
		c += rl * (0.0 + 0.38 * fog) * vec3(1.0, 0.92, 1.0);
	}
	COLOR = vec4(c, actor.a);
}
