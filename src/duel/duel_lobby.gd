class_name DuelLobby
extends Control
## Wizard Duel home: practise alone against a scripted rival, or duel a friend on the same wifi. One phone chooses "Host a duel" and
## waits (it shows its address and shouts that it is there); the other sees the nearby game in a list (or types the address) and joins.
## When both are connected the host starts the duel. Scripted: RW_DUEL_AUTO=host|join (RW_DUEL_ADDR, RW_DUEL_NAME) skips the buttons.

const CFG_PATH := "user://duel.cfg"
const MENU := "res://src/scenes/main_menu.tscn"
const PLAY := "res://src/duel/duel_play.tscn"

var rules: DuelRules
var _content: VBoxContainer
var _name_edit: LineEdit
var _addr_edit: LineEdit
var _wifi_box: VBoxContainer
var _status: Label
var _signature := ""
var _poll := 0.0
var _auto := ""
var _auto_start_at := -1.0
var _starting := false


func _ready() -> void:
	rules = DuelRules.load_default()
	var parts := UiStyle.screen(self, "Wizard Duel", _back)
	_content = parts["content"]
	if not rules.errors.is_empty():
		_content.add_child(UiStyle.note("The duel data is invalid: " + "; ".join(PackedStringArray(rules.errors)), UiStyle.WARN))
		return
	var cfg := ConfigFile.new()
	cfg.load(CFG_PATH)
	var default_name := OS.get_environment("RW_DUEL_NAME") if OS.get_environment("RW_DUEL_NAME") != "" else str(cfg.get_value("duel", "name", _device_name()))
	_content.add_child(UiStyle.note("Two wizards, one song, the same notes. Pass a phrase to cast a spell at the other wizard. First to bring the other's health to zero wins.", UiStyle.MUTED, 18))
	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 10)
	_content.add_child(name_row)
	var name_label := Label.new()
	name_label.text = "Your wizard's name"
	name_label.add_theme_font_size_override("font_size", 20)
	name_row.add_child(name_label)
	_name_edit = LineEdit.new()
	_name_edit.text = default_name
	_name_edit.max_length = 14
	_name_edit.custom_minimum_size = Vector2(240, 48)
	_name_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(_name_edit)
	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 22)
	_content.add_child(cols)
	var left := _column(cols, "Practise alone")
	for skill in DuelPlay.SOLO_SKILLS:
		var sk: String = skill
		left.add_child(UiStyle.button("vs %s" % DuelPlay.SKILL_TITLES[sk], func() -> void: _practise(sk), 0, 56))
	left.add_child(UiStyle.note("Scripted rivals play the same notes through the same rules.", UiStyle.MUTED, 16))
	var right := _column(cols, "Over wifi")
	right.add_child(UiStyle.note("Both phones on the same wifi network.", UiStyle.MUTED, 16))
	_wifi_box = VBoxContainer.new()
	_wifi_box.add_theme_constant_override("separation", 10)
	right.add_child(_wifi_box)
	var addr_row := HBoxContainer.new()
	addr_row.add_theme_constant_override("separation", 10)
	right.add_child(addr_row)
	_addr_edit = LineEdit.new()
	_addr_edit.placeholder_text = "host's address, e.g. 192.168.1.20"
	_addr_edit.text = str(cfg.get_value("duel", "address", ""))
	_addr_edit.custom_minimum_size = Vector2(200, 48)
	_addr_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	addr_row.add_child(_addr_edit)
	addr_row.add_child(UiStyle.button("Join", func() -> void: _join(_addr_edit.text), 90, 48))
	_status = UiStyle.note("", UiStyle.WARN, 16)
	_content.add_child(_status)
	DuelNetwork.start_browsing()
	if DuelNetwork.state != DuelNetwork.State.IDLE and DuelNetwork.state != DuelNetwork.State.CONNECTED:
		DuelNetwork.close("")
	_auto = OS.get_environment("RW_DUEL_AUTO")
	if _auto == "host":
		_host()
	elif _auto == "join":
		_join(OS.get_environment("RW_DUEL_ADDR") if OS.get_environment("RW_DUEL_ADDR") != "" else "127.0.0.1")
	_rebuild()


func _column(parent: Control, heading: String) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box())
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	panel.add_child(col)
	col.add_child(UiStyle.title(heading, 24))
	return col


func _device_name() -> String:
	var n := OS.get_model_name()
	if n == "" or n == "GenericDevice":
		n = OS.get_environment("COMPUTERNAME")
	if n == "":
		n = "Wizard"
	return n.substr(0, 14)


func _my_name() -> String:
	var n := _name_edit.text.strip_edges() if _name_edit != null else ""
	return n if n != "" else "Wizard"


func _save() -> void:
	var cfg := ConfigFile.new()
	cfg.load(CFG_PATH)
	cfg.set_value("duel", "name", _my_name())
	cfg.set_value("duel", "address", _addr_edit.text.strip_edges())
	cfg.save(CFG_PATH)


func _back() -> void:
	DuelNetwork.stop_browsing()
	DuelNetwork.close("left")
	get_tree().change_scene_to_file(MENU)


func _practise(skill: String) -> void:
	_save()
	DuelNetwork.my_name = _my_name()
	DuelNetwork.stop_browsing()
	DuelNetwork.close("")
	DuelNetwork.my_name = _my_name()
	DuelPlay.solo_skill = skill
	get_tree().change_scene_to_file(PLAY)


func _host() -> void:
	_save()
	DuelNetwork.round_no = 1
	var err := DuelNetwork.host_game(_my_name())
	_status.text = DuelNetwork.last_error if err != OK else ""


func _join(address: String) -> void:
	if address.strip_edges() == "":
		_status.text = "Type the host's address, or pick a game from the list."
		return
	_save()
	DuelNetwork.round_no = 1
	var err := DuelNetwork.join_game(address, _my_name())
	_status.text = DuelNetwork.last_error if err != OK else "Connecting to %s..." % address


func _start_duel() -> void:
	if _starting:
		return
	_starting = true
	DuelNetwork.send({"t": "start", "r": DuelNetwork.round_no})
	_go_play()


func _go_play() -> void:
	DuelNetwork.stop_browsing()
	get_tree().change_scene_to_file(PLAY)


# --- the wifi box follows the link's state ---------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if _wifi_box == null:
		return
	for msg in DuelNetwork.drain():
		match str(msg.get("t", "")):
			"start":
				if not _starting:
					_starting = true
					_go_play()
					return
			"closed":
				_status.text = _closed_text(str(msg.get("why", "")))
	_poll -= delta
	if _poll <= 0.0:
		_poll = 0.25
		var sig := _signature_now()
		if sig != _signature:
			_signature = sig
			_rebuild()
	if _auto == "host" and DuelNetwork.state == DuelNetwork.State.CONNECTED and not _starting:
		if _auto_start_at < 0.0:
			_auto_start_at = float(Time.get_ticks_msec()) / 1000.0 + 1.2
		elif float(Time.get_ticks_msec()) / 1000.0 >= _auto_start_at:
			_start_duel()


func _closed_text(why: String) -> String:
	match why:
		"left":
			return "The other wizard left."
		"lost":
			return "Lost the connection."
		"failed":
			return DuelNetwork.last_error
		"version":
			return DuelNetwork.last_error
	return "Disconnected."


func _signature_now() -> String:
	var keys := DuelNetwork.games.keys()
	keys.sort()
	return "%d|%s|%s|%s" % [DuelNetwork.state, DuelNetwork.opp_name, ",".join(PackedStringArray(keys)), DuelNetwork.last_error]


func _rebuild() -> void:
	for c in _wifi_box.get_children():
		c.queue_free()
	match DuelNetwork.state:
		DuelNetwork.State.IDLE, DuelNetwork.State.CLOSED:
			_wifi_box.add_child(UiStyle.button("Host a duel", _host, 0, 56))
			var any := false
			for k in DuelNetwork.games:
				any = true
				var g: Dictionary = DuelNetwork.games[k]
				var addr := str(g["address"])
				_wifi_box.add_child(UiStyle.button("Join %s  (%s)" % [str(g["name"]), addr], func() -> void: _join(addr), 0, 56))
			if not any:
				_wifi_box.add_child(UiStyle.note("No games found yet. Ask a friend to host, or type their address below.", UiStyle.MUTED, 16))
			if DuelNetwork.last_error != "" and _status.text == "":
				_status.text = DuelNetwork.last_error
		DuelNetwork.State.HOSTING:
			var addrs := DuelNetwork.local_addresses()
			var where := ", ".join(addrs) if addrs.size() > 0 else "(connect to wifi to get an address)"
			_wifi_box.add_child(UiStyle.note("Waiting for a wizard...\nYour address: %s" % where, UiStyle.GOOD, 20))
			_wifi_box.add_child(UiStyle.button("Cancel", func() -> void: DuelNetwork.close(""), 0, 52))
		DuelNetwork.State.JOINING:
			_wifi_box.add_child(UiStyle.note("Connecting...", UiStyle.GOOD, 20))
			_wifi_box.add_child(UiStyle.button("Cancel", func() -> void: DuelNetwork.close(""), 0, 52))
		DuelNetwork.State.CONNECTED:
			_wifi_box.add_child(UiStyle.note("Connected to %s." % DuelNetwork.opp_name, UiStyle.GOOD, 22))
			if DuelNetwork.role == "host":
				_wifi_box.add_child(UiStyle.button("Start the duel", _start_duel, 0, 64))
			else:
				_wifi_box.add_child(UiStyle.note("Waiting for %s to start..." % DuelNetwork.opp_name, UiStyle.MUTED, 18))
			_wifi_box.add_child(UiStyle.button("Leave", func() -> void: DuelNetwork.close("left"), 0, 52))


func _exit_tree() -> void:
	if not _starting:
		DuelNetwork.stop_browsing()
