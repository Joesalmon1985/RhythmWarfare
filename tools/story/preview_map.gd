extends Control
## Fly a chapter's 2.5D map through the same low-res pipeline the game uses: what you see here is what ships.
##   godot --path . res://tools/story/preview_map.tscn [-- <chapter>]        (RW_MAP=<chapter> also works; default night_one)
## WASD move, Shift fast, mouse look (click to capture, Esc to release), Q/E turn, R/F eye up/down, 1-4 light palette (low/cool/warm/rave), Space pauses the light clock,
## `[` and `]` step through the waypoints, P prints the pose as a waypoint line (paste it into the map).
## RW_PREVIEW_POSE="x,z,yaw" starts there, RW_PREVIEW_T=<seconds> fixes the light clock (screenshots with tools/shoot.gd).

const SPEED := 3.0
const PALETTES := {
	"low": [Color(0.35, 0.3, 0.9), Color(0.6, 0.25, 0.8)],
	"cool": [Color(0.2, 0.85, 1.0), Color(0.55, 0.35, 1.0)],
	"warm": [Color(1.0, 0.7, 0.25), Color(1.0, 0.35, 0.65)],
	"rave": [Color(1.0, 0.25, 0.8), Color(0.2, 1.0, 0.9), Color(0.7, 0.4, 1.0), Color(1.0, 0.85, 0.3)],
}

var map: StoryMap
var world: StoryWorld
var lowres: StoryLowRes
var label: Label
var pos := Vector2.ZERO
var yaw := 0.0
var eye := 1.6
var t := 0.0
var paused := false
var palette := "rave"
var wp_index := -1
var captured := false
var _frames: PackedFloat32Array = PackedFloat32Array()


func _ready() -> void:
	var chapter := OS.get_environment("RW_MAP") if OS.has_environment("RW_MAP") else "night_one"
	var args := OS.get_cmdline_user_args()
	if args.size() > 0 and FileAccess.file_exists(StoryMap.PATH % args[0]):
		chapter = args[0]
	map = StoryMap.load_chapter(chapter)
	if not map.errors.is_empty():
		push_error("map %s: %s" % [chapter, "; ".join(PackedStringArray(map.errors))])
	var assets := StoryAssets.load_art(map.art)
	lowres = StoryLowRes.new()
	lowres.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(lowres)
	world = StoryWorld.new()
	world.build(map, assets)
	lowres.attach(world)
	label = Label.new()
	label.position = Vector2(10, 8)
	label.add_theme_color_override("font_color", Color(1, 1, 0.7))
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 4)
	add_child(label)
	var w := map.start_waypoint()
	pos = w.get("at", Vector2.ZERO)
	yaw = float(w.get("yaw", 0.0))
	if OS.has_environment("RW_PREVIEW_POSE"):
		var p := OS.get_environment("RW_PREVIEW_POSE").split(",")
		pos = Vector2(float(p[0]), float(p[1]))
		yaw = float(p[2])
	var sid := map.sector_at(pos)
	eye = map.eye_y(sid) if sid != "" else 1.6
	if OS.has_environment("RW_PREVIEW_T"):
		t = float(OS.get_environment("RW_PREVIEW_T"))
		paused = true


func _process(delta: float) -> void:
	if OS.has_environment("RW_PREVIEW_PROFILE"):  # RW_PREVIEW_PROFILE=<frames>: print the frame time of the world alone (run with --disable-vsync) and quit
		_frames.append(delta * 1000.0)
		t += 1.0 / 60.0
		yaw = 20.0 * sin(t * 0.5)
		if _frames.size() >= int(OS.get_environment("RW_PREVIEW_PROFILE")) + 30:
			var s := _frames.slice(30)
			s.sort()
			print("PROFILE world only: frames=%d mean=%.2f p95=%.2f max=%.2f" % [s.size(), Array(s).reduce(func(a: float, b: float) -> float: return a + b, 0.0) / s.size(), s[int(s.size() * 0.95)], s[s.size() - 1]])
			get_tree().quit()
	if not paused:
		t += delta
	var move := Vector2.ZERO
	if Input.is_key_pressed(KEY_W):
		move.y += 1.0
	if Input.is_key_pressed(KEY_S):
		move.y -= 1.0
	if Input.is_key_pressed(KEY_D):
		move.x += 1.0
	if Input.is_key_pressed(KEY_A):
		move.x -= 1.0
	if Input.is_key_pressed(KEY_Q):
		yaw += 90.0 * delta
	if Input.is_key_pressed(KEY_E):
		yaw -= 90.0 * delta
	if Input.is_key_pressed(KEY_R):
		eye += 1.5 * delta
	if Input.is_key_pressed(KEY_F):
		eye -= 1.5 * delta
	if move != Vector2.ZERO:
		var sp := SPEED * (3.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0) * delta
		var f := StoryProjector.forward(yaw)
		var r := StoryProjector.right(yaw)
		var np := pos + (f * move.y + r * move.x).normalized() * sp
		if map.sector_at(np) != "":  # stay inside the map
			pos = np
	var pose := {"cam": Vector3(pos.x, eye, pos.y), "yaw": yaw, "roll": 0.0}
	lowres.apply_pose(pose)
	var pieces := {}
	for pid in OS.get_environment("RW_PREVIEW_PIECES").split(",", false):  # screenshot aid: RW_PREVIEW_PIECES=a,b shows those set pieces
		pieces[pid] = {"visible": true, "alpha": 1.0, "pulse": 0.0}
	if OS.has_environment("RW_PREVIEW_KNOB"):  # screenshot aid: RW_PREVIEW_KNOB=0..3 poses the Space rave's bass knob thing on that frame
		world.thing_pose["bass_knob"] = {"tex": load("res://assets/story/mothership/textures/sr_knob_%d.png" % int(OS.get_environment("RW_PREVIEW_KNOB")))}
	world.update(t, {"bpm": 174.0, "palette": PALETTES[palette], "energy": 70.0, "flicker": false, "strobe": 0.0, "woofer_pump": true, "pieces": pieces})
	label.text = "%s  sector %s  pos (%.2f, %.2f) yaw %.0f  eye %.2f   internal %s  tris %d  fps %d" % [map.id, map.sector_at(pos), pos.x, pos.y, yaw, eye, lowres.sub.size, world.triangle_count, Engine.get_frames_per_second()]


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and not captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		captured = true
	elif event is InputEventMouseMotion and captured:
		yaw -= event.relative.x * 0.15
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_ESCAPE:
				if captured:
					Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
					captured = false
				else:
					get_tree().quit()
			KEY_SPACE:
				paused = not paused
			KEY_1, KEY_2, KEY_3, KEY_4:
				palette = ["low", "cool", "warm", "rave"][event.keycode - KEY_1]
			KEY_BRACKETRIGHT, KEY_BRACKETLEFT:
				var ids := map.waypoints.keys()
				wp_index = posmod(wp_index + (1 if event.keycode == KEY_BRACKETRIGHT else -1), ids.size())
				var w: Dictionary = map.waypoints[ids[wp_index]]
				pos = w["at"]
				yaw = float(w["yaw"])
				eye = map.eye_y(str(w["sector"]))
				print("waypoint ", ids[wp_index])
			KEY_P:
				print('{"id": "new", "at": [%.2f, %.2f], "yaw": %d, "sector": "%s"}' % [pos.x, pos.y, int(round(yaw)), map.sector_at(pos)])
