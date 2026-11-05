extends Control
## The blackjack table without the whole game: the REAL BlackjackActivity (real RunWallet) on its own clock at 174 BPM, with the BlackjackView inside a 640 x 230 SubViewport shown nearest-neighbour
## scaled (320 x 115 with RW_GALLERY_LOW=1) over a dark stand-in for the Ward's day room (or a picture of the real room: RW_DEMO_BACKDROP). Every frame advances the song time by RW_DEMO_STEP seconds (default 0.05), so a screenshot at frame N is a known time.
## Env:
##   RW_MINIGAME_SEED=<n>        the deck's seed (default 7)
##   RW_DEMO_TAPS="bet@6,deck@14,hand@18,exit@60"   target@beats after sitting; goes through view.hit like a finger (falls back to a direct tap)
##   RW_DEMO_WOBBLE="1@20,0@36"  wobble level@beat
##   RW_DEMO_FALL=<beat>         interrupt("fall") at that beat
##   RW_DEMO_WALLET=<pence>      the starting balance (default 2000)
##   RW_DEMO_T0=<seconds>        the first frame shows this song time (everything before it is simulated at once)
##   RW_DEMO_STEP=<seconds>      song seconds per rendered frame
##   RW_DEMO_DECK=<ranks>        a stacked deck "npc_a,player,npc_b,dealer,npc_a,..." ranks 1..13 (deal order, then draws), suits cycle
##   RW_DEMO_REDUCED=1, RW_DEMO_HC=1   reduced motion, high contrast
##   RW_DEMO_BACKDROP=<image path>     draw this picture (a capture of the day room from the seat, any size: it is cropped to the stage) behind the table
##   RW_DEMO_EXITS=<run node id>  the table sits in that scene: its ways out (RunMinigameHost.room_exits, from the run data and the map) become the doors; taps may name
##                               "exit:<route>" (e.g. RW_DEMO_TAPS=bet@5,exit:ward.dorm@20). RW_DEMO_EXITS=<n>x gives n made-up doors (1 to 4) to try the layout.

const BEAT := 60.0 / 174.0
const WALL := Color("1d2522")
const WALL_DARK := Color("161c1a")
const FLOOR_A := Color("1a1b20")
const FLOOR_B := Color("15161a")


class Layer:
	extends Control
	var fn: Callable

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)


var _size := Vector2(640, 230)
var _sub: SubViewport
var _back: Layer
var _view: BlackjackView
var _activity: BlackjackActivity
var _wallet: RunWallet
var _t := 0.0
var _step := 0.05
var _taps: Array = []
var _wobbles: Array = []
var _fall := -1.0
var _screen := Vector2(1280, 460)
var _backdrop: Texture2D


func _ready() -> void:
	var low := OS.get_environment("RW_GALLERY_LOW") == "1"
	_size = Vector2(320, 115) if low else Vector2(640, 230)
	if OS.has_environment("RW_DEMO_STEP"):
		_step = float(OS.get_environment("RW_DEMO_STEP"))
	_wallet = RunWallet.new()
	if OS.has_environment("RW_DEMO_WALLET"):
		var want := int(OS.get_environment("RW_DEMO_WALLET"))
		_wallet.spend(_wallet.balance_pence())
		_wallet.add(want)
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/blackjack.json"))
	var ctx := {"wallet": _wallet, "seed": int(OS.get_environment("RW_MINIGAME_SEED")) if OS.has_environment("RW_MINIGAME_SEED") else 7, "beat_s": BEAT, "config": cfg}
	if OS.get_environment("RW_DEMO_EXITS") != "":
		ctx["exits"] = _demo_exits(OS.get_environment("RW_DEMO_EXITS"))
	if OS.has_environment("RW_DEMO_DECK"):
		var cards: Array = []
		var i := 0
		for r in OS.get_environment("RW_DEMO_DECK").split(",", false):
			cards.append({"rank": int(r), "suit": i % 4})
			i += 1
		ctx["deck"] = BlackjackDeck.stacked(cards, 99)
	_activity = BlackjackActivity.new()
	_activity.setup(ctx)
	_activity.begin(0.0)
	_parse("RW_DEMO_TAPS", _taps)
	_parse("RW_DEMO_WOBBLE", _wobbles)
	if OS.has_environment("RW_DEMO_FALL"):
		_fall = float(OS.get_environment("RW_DEMO_FALL")) * BEAT
	_sub = SubViewport.new()
	_sub.size = Vector2i(_size)
	_sub.transparent_bg = false
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_sub)
	var rect := TextureRect.new()
	rect.texture = _sub.get_texture()
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(rect)
	if OS.has_environment("RW_DEMO_BACKDROP"):
		var img := Image.load_from_file(OS.get_environment("RW_DEMO_BACKDROP"))
		if img != null:
			_backdrop = ImageTexture.create_from_image(img)
	_back = Layer.new()
	_back.size = _size
	_back.fn = _room
	_sub.add_child(_back)
	_view = _activity.make_view() as BlackjackView
	_view.now_fn = func() -> float: return _t
	_view.state_fn = func() -> Dictionary: return _activity.state()
	_view.beat_s = BEAT
	_view.reduced = OS.get_environment("RW_DEMO_REDUCED") == "1"
	_view.high_contrast = OS.get_environment("RW_DEMO_HC") == "1"
	_view.screen_size = _screen
	_view.size = _size
	_sub.add_child(_view)
	var t0 := float(OS.get_environment("RW_DEMO_T0")) if OS.has_environment("RW_DEMO_T0") else 0.0
	while _t < t0:
		_advance(minf(_t + 1.0 / 60.0, t0))


## The exits of run node `spec` as the run scene would give them, or `<n>x`: n made-up doors to unknown rooms (the layout of 1 to 4).
func _demo_exits(spec: String) -> Array:
	if spec.ends_with("x") and spec.length() == 2:
		var out: Array = []
		var dirs := ["right", "up", "left", "up"]
		var scenes := ["corridor", "art", "dorm", "courtyard"]
		for i in clampi(int(spec.substr(0, 1)), 0, 4):
			out.append({"id": "demo.%d" % i, "route": "demo.%d" % i, "scene": scenes[i], "world": "", "dir": dirs[i], "default": i == 0})
		return out
	var data := RunData.load_default()
	var hs := RunHotspots.new(data, {}, {})
	hs.begin_scene(spec, 60.0)
	return RunMinigameHost.room_exits(data, hs, spec, func(map_id: String) -> StoryMap: return StoryMap.load_chapter(map_id, false) if map_id != "" else null)


func _parse(key: String, into: Array) -> void:
	for part in OS.get_environment(key).split(",", false):
		var bits := part.strip_edges().split("@")
		if bits.size() == 2:
			into.append({"id": bits[0], "t": float(bits[1]) * BEAT, "done": false})


func _process(_delta: float) -> void:
	_screen = size
	_view.screen_size = size
	_advance(_t + _step)
	_back.queue_redraw()


func _advance(t: float) -> void:
	_t = t
	for w in _wobbles:
		if not w["done"] and _t >= float(w["t"]):
			w["done"] = true
			_activity.set_wobble(int(w["id"]), float(w["t"]))
	if _fall >= 0.0 and _t >= _fall:
		_fall = -1.0
		_activity.interrupt("fall", _t)
	for tap in _taps:
		if not tap["done"] and _t >= float(tap["t"]):
			tap["done"] = true
			_do_tap(str(tap["id"]), float(tap["t"]))
	_activity.update(_t)


func _do_tap(id: String, t: float) -> void:
	var keep := _t
	_t = t
	_activity.update(t)
	var rects := _view.target_rects()
	var sent := false
	if rects.has(id):
		var c: Vector2 = (rects[id] as Rect2).get_center()
		var hit := _view.hit(Vector2(c.x * _screen.x / _size.x, c.y * _screen.y / _size.y))
		if hit != "":
			_activity.tap(hit, t)
			sent = true
	if not sent:
		_activity.tap(id, t)
	_t = keep


func _room(ci: Control) -> void:
	var s := _size
	var u := s.y / 230.0
	if _backdrop != null:  # the stage band of a 16:9 capture (the stage is the top 460 of 720 lines)
		var bs := _backdrop.get_size()
		ci.draw_texture_rect_region(_backdrop, Rect2(Vector2.ZERO, s), Rect2(0, 0, bs.x, bs.x * s.y / s.x))
		return
	ci.draw_rect(Rect2(0, 0, s.x, 112.0 * u), WALL)
	ci.draw_rect(Rect2(0, 96.0 * u, s.x, 16.0 * u), WALL_DARK)
	var tile := roundf(16.0 * u)
	var y := roundf(112.0 * u)
	var row := 0
	while y < s.y:
		var x := 0.0
		var col := row % 2
		while x < s.x:
			ci.draw_rect(Rect2(x, y, tile, tile), FLOOR_A if col == 0 else FLOOR_B)
			x += tile
			col = 1 - col
		y += tile
		row += 1
	# the room's coloured spill from the left and the right
	BlackjackDraw.dither_fill(ci, BlackjackDraw.ell_tris(0.0, 70.0 * u, 120.0 * u, 80.0 * u), Color("8a3c88"), BlackjackDraw.D_QUARTER)
	BlackjackDraw.dither_fill(ci, BlackjackDraw.ell_tris(s.x, 70.0 * u, 120.0 * u, 80.0 * u), Color("2c7c8a"), BlackjackDraw.D_QUARTER)
