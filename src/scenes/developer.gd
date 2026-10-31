extends Control
## Developer and testing area, kept out of the player's way: the legacy two-sided duel (free play, schema 1 packs, for
## a later multiplayer mode), a rhythm-only playtest of any mission, the installed content and what is still
## placeholder (read-only; the build runs on the PC), and the unlock-all switch status.


func _ready() -> void:
	var parts := UiStyle.screen(self, "Developer", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var c := Session.campaign
	content.add_child(UiStyle.note("Unlock-all: %s (data/campaign/campaign.json \"unlock_all\" or RW_UNLOCK_ALL=1)" % ("ON" if c.unlock_all else "off"),
		UiStyle.WARN if c.unlock_all else UiStyle.MUTED))
	var packs := Session.available_packs()
	content.add_child(UiStyle.note("FREE PLAY: the legacy duel", UiStyle.ACCENT, 22))
	for p in packs:
		if int(p["schema"]) == 1:
			content.add_child(UiStyle.button("Duel: %s" % p["title"], func() -> void:
				Session.pack_dir = p["dir"]
				Session.chart_id = ""
				Session.selection = {}
				Session.battle_on = true
				Session.practice = false
				Session.campaign_level_id = ""
				get_tree().change_scene_to_file("res://src/scenes/play.tscn"), 0, 56))
	content.add_child(UiStyle.note("RHYTHM PLAYTEST: a mission's default choices, battlefield hidden", UiStyle.ACCENT, 22))
	for p in packs:
		if int(p["schema"]) == 3:
			content.add_child(UiStyle.button("Playtest: %s" % p["title"], func() -> void:
				Session.pack_dir = p["dir"]
				Session.chart_id = ""
				Session.selection = {}
				Session.battle_on = false
				Session.practice = true
				Session.practice_phase = -1
				Session.campaign_level_id = ""
				get_tree().change_scene_to_file("res://src/scenes/play.tscn"), 0, 56))
	content.add_child(UiStyle.note("INSTALLED CONTENT (rebuild with python tools/content/build.py on the PC)", UiStyle.ACCENT, 22))
	for p in packs:
		if int(p["schema"]) == 3:
			var ct: Dictionary = p["content"]
			content.add_child(UiStyle.note("%s: %d stem files, %d placeholder, %d owner renders" % [p["title"], int(ct.get("files", 0)),
				int(ct.get("placeholder_files", 0)), int(ct.get("owner_files", 0))], UiStyle.TEXT, 18))


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
