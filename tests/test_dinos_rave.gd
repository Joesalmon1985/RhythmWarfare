extends "res://tests/rave_theme_test.gd"
## The Dinosaurs rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; facing east): the Space rave's test for the lava ledge and its causeway (tests/rave_theme_test.gd holds the body).


func _init() -> void:
	cfg = {"theme": "dinos", "prefix": "dino", "map": "dino_rave", "art": "rave_dinos", "facing": "E", "cloak_hold_sector": "isle_w", "bar_hold_sector": "isle_e",
		"lights": ["dn_lava_sheets", "dn_fire_ring", "dn_ember_dome"]}
