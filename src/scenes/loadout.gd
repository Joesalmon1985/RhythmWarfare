extends Control
## Pre-song loadout for a campaign level: one row per active musical slot, the equippable instruments of its family
## with their sound state (placeholder or rendered), unit mix and unlock level, validation of the PRD section 14 rules
## (family, unlocked, distinct within a family, required slots, caps 2 kick / 2 snare / 3 bass, a render for this song),
## and Play (the campaign chart with the battle) or Practice (rhythm only, nothing saved).

var campaign: Campaign
var level: Level
var data: Dictionary
var selection: Dictionary = {}
var _choices: Dictionary = {}  # slot -> Array of profile ids in the option button's order
var _mix_labels: Dictionary = {}
var _validation: Label
var _play: Button
var _practice: Button


func _ready() -> void:
	campaign = Session.campaign
	data = campaign.level_data(Session.loadout_level_number)
	var pack := "res://songs/%s" % data.get("pack", "")
	var loaded := LevelLoader.load_pack(pack, {"chart_id": str(data.get("campaign_chart", ""))})
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.anchor_left = 0.1
	scroll.anchor_right = 0.9
	scroll.offset_top = 20
	scroll.offset_bottom = -20
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 10)
	scroll.add_child(box)
	if loaded["level"] == null:
		box.add_child(_label("Level could not be loaded:\n" + "\n".join(PackedStringArray(loaded["errors"])), 18))
		box.add_child(_button("Back", _back))
		return
	level = loaded["level"]
	box.add_child(_label("Level %d: %s" % [int(data["number"]), data["title"]], 40))
	box.add_child(_label("%s\n%.0f seconds, %d bars. Battle: %s." % [data["learning_goal"], level.duration_seconds(), int(data["bars"]), data["battle_goal"]], 18))
	if level.is_placeholder_audio():
		var warn := _label("PLACEHOLDER SOUND: these are synthesised stand-ins; the owner's rendered instruments replace them one file per slot and profile.", 16)
		warn.modulate = Color(1.0, 0.85, 0.5)
		box.add_child(warn)
	selection = campaign.loadout_for(level.level_id, level.loadout_default, level.loadout_active_slots)
	for slot in level.loadout_active_slots:
		box.add_child(_slot_row(str(slot)))
	_validation = _label("", 18)
	box.add_child(_validation)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	_play = _button("Play", _on_play)
	_practice = _button("Practice (rhythm only)", _on_practice)
	row.add_child(_play)
	row.add_child(_practice)
	row.add_child(_button("Back", _back))
	box.add_child(row)
	_refresh()
	_play.grab_focus()


func _label(text: String, size: int) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 56)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.add_theme_font_size_override("font_size", 22)
	b.pressed.connect(cb)
	return b


func _family_of(slot: String) -> String:
	for p in level.parts:
		if str(p.get("slot_id", "")) == slot:
			return str(p["family"])
	return ""


func _slot_row(slot: String) -> Control:
	var family := _family_of(slot)
	var col := VBoxContainer.new()
	var title := _label("%s  (%s)" % [slot.replace("_", " ").to_upper(), family], 20)
	title.modulate = Color(0.75, 0.85, 1.0)
	col.add_child(title)
	var opt := OptionButton.new()
	opt.custom_minimum_size = Vector2(0, 48)
	opt.add_theme_font_size_override("font_size", 18)
	var ids: Array = []
	var unlocked := campaign.unlocked_profiles()
	for id in campaign.catalogue.profiles_of_family(family):
		var text := "%s: %s" % [campaign.catalogue.display_name(id), campaign.catalogue.unit_mix_text(id)]
		var disabled := false
		if not unlocked.has(id):
			text = "%s: unlocks after level %d" % [campaign.catalogue.display_name(id), campaign.catalogue.unlock_level(id) - 1]
			disabled = true
		elif not level.renders.get(slot, {}).has(id):
			text = "%s: no sound rendered for this song yet" % campaign.catalogue.display_name(id)
			disabled = true
		else:
			var render: Dictionary = level.renders[slot][id]
			text += "   [%s]" % ("placeholder sound" if render.get("placeholder", false) else "rendered")
		opt.add_item(text)
		opt.set_item_disabled(opt.item_count - 1, disabled)
		ids.append(id)
	_choices[slot] = ids
	opt.select(maxi(ids.find(selection.get(slot, "")), 0))
	opt.item_selected.connect(func(index: int) -> void:
		selection[slot] = ids[index]
		_refresh())
	col.add_child(opt)
	var mix := _label("", 15)
	_mix_labels[slot] = mix
	col.add_child(mix)
	return col


func _refresh() -> void:
	for slot in selection:
		var id := str(selection[slot])
		var tags: Array[String] = []
		for t in campaign.catalogue.required_producers(id):
			tags.append(str(t).replace("_", " "))
		if _mix_labels.has(slot):
			_mix_labels[slot].text = "Each successful note makes: %s. Needs: %s. Mutes when that is destroyed." % [campaign.catalogue.unit_mix_text(id), ", ".join(PackedStringArray(tags))]
	var errors := campaign.validate_loadout(level, selection)
	_validation.text = "Loadout ready." if errors.is_empty() else "\n".join(PackedStringArray(errors))
	_validation.modulate = Color(0.7, 1.0, 0.7) if errors.is_empty() else Color(1.0, 0.55, 0.5)
	_play.disabled = not errors.is_empty()
	_practice.disabled = not errors.is_empty()


func _on_play() -> void:
	campaign.store_loadout(level.level_id, selection)
	_start(str(data["campaign_chart"]), true, false, level.level_id)


func _on_practice() -> void:
	var chart := str(data.get("practice_chart", ""))
	if chart.is_empty():
		chart = str(data["campaign_chart"])
	_start(chart, false, true, "")


func _start(chart: String, battle: bool, practice: bool, level_id: String) -> void:
	Session.pack_dir = "res://songs/%s" % data["pack"]
	Session.chart_id = chart
	Session.battle_on = battle
	Session.practice = practice
	Session.campaign_level_id = level_id
	Session.loadout = selection.duplicate()
	get_tree().change_scene_to_file("res://src/scenes/play.tscn")


func _back() -> void:
	get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_back()
