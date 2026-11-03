extends Control
## The Loadout screen: the player's one loadout (drum pattern, fill, kick, snare, bass line, bass sound, backing),
## applied to every mission. One row per slot of cards; an equipped card is lit, a locked one says what unlocks it.
## A sound card shows what its instrument builds (a strip of unit icons); every card can be auditioned. Choosing a
## card re-resolves the whole loadout, so a slot that no longer fits (the sounds of another pattern) falls back, and
## saves it.

const TITLES := {"groove": "Drum pattern", "fill": "Fill", "kick_sound": "Kick", "snare_sound": "Snare",
	"bass": "Bass line", "bass_sound": "Bass sound", "backing": "Backing"}
const SOUND_PART := {"kick_sound": "kick", "snare_sound": "snare", "bass_sound": "bass"}
const INTRO := "Your loadout plays in every mission. A passed drum sequence calls on the kick or the snare, a bass sequence on the bass sound."

var _index: LibraryIndex
var _content: VBoxContainer
var _rows: VBoxContainer
var _loadout: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _listening := ""
var _listen_buttons: Dictionary = {}  # item id -> its Listen button


func _ready() -> void:
	var parts := UiStyle.screen(self, "Loadout", _back)
	_content = parts["content"]
	_index = Session.library()
	for _i in 2:
		var p := AudioStreamPlayer.new()
		p.bus = AudioServer.get_bus_name(StemTransport.ensure_music_bus())
		add_child(p)
		_players.append(p)
	_content.add_child(UiStyle.note(INTRO, UiStyle.MUTED, 18))
	if _index.is_empty():
		_content.add_child(UiStyle.note("The loop library is missing. Rebuild it with tools/content/build.py.", UiStyle.WARN))
		return
	_loadout = Session.loadout()
	_rebuild()


# --- the card model (pure) -----------------------------------------------------------------------------------------

## What a slot's row shows for the loadout `current`: the ids that fit the other picks, plus the equipped one (always),
## each as {id, name, key, meta, locked, lock_text, equipped, icons, blurb, listenable}. Unlocked items come first,
## locked ones after them, each group in library order. `unlocked` is Campaign.unlocked_items() and `locks` maps an id
## to the text saying what unlocks it (an id missing from `locks` that is not available gets "Locked").
static func row_items(index: LibraryIndex, unlocked: Array, locks: Dictionary, slot: String, current: Dictionary) -> Array:
	var ids: Array = index.compatible(slot, current).duplicate()
	var equipped := str(current.get(slot, ""))
	if not ids.has(equipped) and (slot == "fill" or not equipped.is_empty()):
		ids.append(equipped)
	var free: Array = []
	var held: Array = []
	for id in ids:
		var item := _item(index, unlocked, locks, slot, str(id), str(id) == equipped)
		(held if bool(item["locked"]) else free).append(item)
	return free + held


static func _item(index: LibraryIndex, unlocked: Array, locks: Dictionary, slot: String, id: String, equipped: bool) -> Dictionary:
	var item := {"id": id, "name": "None" if id.is_empty() else index.name(id), "key": "", "meta": "", "locked": false,
		"lock_text": "", "equipped": equipped, "icons": [], "blurb": "", "listenable": not id.is_empty()}
	if not Loadout.is_available(index, unlocked, id):
		item["locked"] = true
		item["lock_text"] = str(locks.get(id, "")) if not str(locks.get(id, "")).is_empty() else "Locked"
	if id.is_empty():
		item["meta"] = "No fill: the groove plays on"
	elif SOUND_PART.has(slot):
		item["icons"] = UiStyle.reward_icons(index, id)
		item["blurb"] = str(index.sounds.get(id, {}).get("blurb", ""))
	else:
		item["key"] = str(index.clips.get(id, {}).get("key", ""))
		item["meta"] = _clip_meta(index, id)
	return item


## "12 cues / 8 bars" for a pattern; "16 bars" for a backing track (it has no cues).
static func _clip_meta(index: LibraryIndex, id: String) -> String:
	var clip: Dictionary = index.clips.get(id, {})
	var cues := 0
	var by_part: Variant = clip.get("cues", {})
	if typeof(by_part) == TYPE_DICTIONARY:
		for part in by_part:
			cues += (by_part[part] as Array).size()
	var bars := index.clip_bars(id)
	return "%d cues / %d bars" % [cues, bars] if cues > 0 else "%d bars" % bars


## `current` with `slot` set to `id`, resolved against the library and the unlocked items: whatever no longer fits the
## new pick falls back (a pattern change falls back its sounds; a bass line change its bass sound and backing).
static func with_pick(index: LibraryIndex, unlocked: Array, current: Dictionary, slot: String, id: String) -> Dictionary:
	var wanted := current.duplicate()
	wanted[slot] = id
	var warnings: Array = []
	return Loadout.resolve(index, unlocked, wanted, warnings)


# --- the screen ----------------------------------------------------------------------------------------------------

func _locks() -> Dictionary:
	var out := {}
	for id in _index.clips:
		out[id] = Session.campaign.item_lock(str(id))
	for id in _index.sounds:
		out[id] = Session.campaign.item_lock(str(id))
	return out


func _rebuild() -> void:
	var unlocked := Session.campaign.unlocked_items()
	var locks := _locks()
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", UiStyle.GAP)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_listen_buttons.clear()
	for slot: String in Loadout.SLOTS:
		var title := UiStyle.note(str(TITLES[slot]), UiStyle.ACCENT, 22)
		title.autowrap_mode = TextServer.AUTOWRAP_OFF
		rows.add_child(title)
		var flow := HFlowContainer.new()
		flow.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		flow.add_theme_constant_override("h_separation", UiStyle.GAP)
		flow.add_theme_constant_override("v_separation", UiStyle.GAP)
		rows.add_child(flow)
		for item: Dictionary in row_items(_index, unlocked, locks, slot, _loadout):
			var card := UiStyle.card(item)
			var id := str(item["id"])
			(card["button"] as Button).pressed.connect(_pick.bind(slot, id))
			if card["listen"] != null:
				(card["listen"] as Button).pressed.connect(_listen.bind(slot, id))
				_listen_buttons[id] = card["listen"]
			flow.add_child(card["root"])
	var old := _rows
	var scroll := (_content.get_parent() as ScrollContainer).scroll_vertical if _content.get_parent() is ScrollContainer else 0
	_rows = rows
	_content.add_child(rows)
	if old != null:
		_content.remove_child(old)
		old.queue_free()
	_show_listening()
	if scroll > 0:
		_restore_scroll.call_deferred(scroll)


func _restore_scroll(value: int) -> void:
	if _content != null and _content.get_parent() is ScrollContainer:
		(_content.get_parent() as ScrollContainer).scroll_vertical = value


func _pick(slot: String, id: String) -> void:
	_stop()
	var unlocked := Session.campaign.unlocked_items()
	_loadout = with_pick(_index, unlocked, _loadout, slot, id)
	Session.campaign.store_loadout(_loadout)
	_rebuild.call_deferred()


# --- listening -----------------------------------------------------------------------------------------------------

## The loop files a card plays: [path, ...] (the two drum parts of a pattern together).
func listen_paths(slot: String, id: String) -> Array:
	var out: Array = []
	match slot:
		"groove", "fill":
			var picks := _loadout.duplicate()
			picks[slot] = id
			for s in ["kick_sound", "snare_sound"]:
				var options := _index.compatible(s, picks)
				var sound := str(_loadout.get(s, ""))
				if not options.has(sound):
					sound = str(options[0]) if not options.is_empty() else ""
				out.append(_index.loop_path(id, str(SOUND_PART[s]), sound))
		"kick_sound", "snare_sound", "bass_sound":
			var clip := str(_loadout.get("bass" if slot == "bass_sound" else "groove", ""))
			out.append(_index.loop_path(clip, str(SOUND_PART[slot]), id))
		"bass":
			var options := _index.compatible("bass_sound", {"bass": id})
			var sound := str(_loadout.get("bass_sound", ""))
			if not options.has(sound):
				sound = str(options[0]) if not options.is_empty() else ""
			out.append(_index.loop_path(id, "bass", sound))
		"backing":
			var parts: Variant = _index.clips.get(id, {}).get("parts", [])
			out.append(_index.loop_path(id, str((parts as Array)[0]) if typeof(parts) == TYPE_ARRAY and not (parts as Array).is_empty() else "other", ""))
	return out.filter(func(p: Variant) -> bool: return not str(p).is_empty())


func _listen(slot: String, id: String) -> void:
	if _listening == id:
		_stop()
		return
	_stop()
	var paths := listen_paths(slot, id)
	var started := 0
	for i in mini(paths.size(), _players.size()):
		var stream := LevelLoader.load_stream(str(paths[i]))
		if stream == null:
			continue
		if stream is AudioStreamOggVorbis:
			(stream as AudioStreamOggVorbis).loop = true
		elif stream is AudioStreamMP3:
			(stream as AudioStreamMP3).loop = true
		_players[i].stream = stream
		started += 1
	if started == 0:
		return
	for i in started:
		_players[i].play()
	_listening = id
	_show_listening()


func _stop() -> void:
	for p in _players:
		p.stop()
		p.stream = null
	_listening = ""
	_show_listening()


func _show_listening() -> void:
	for id in _listen_buttons:
		var b: Button = _listen_buttons[id]
		if is_instance_valid(b):
			b.text = "Stop" if str(id) == _listening else "Listen"


# --- leaving -------------------------------------------------------------------------------------------------------

func _back() -> void:
	_stop()
	var tree := get_tree()
	var target := "res://src/scenes/main_menu.tscn"
	if str(tree.get_meta("loadout_return", "")) == "mission_setup":
		target = "res://src/scenes/mission_setup.tscn"
	tree.remove_meta("loadout_return")
	tree.change_scene_to_file(target)


func _exit_tree() -> void:
	for p in _players:
		if is_instance_valid(p):
			p.stop()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_back()
