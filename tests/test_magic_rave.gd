extends "res://tests/rave_theme_test.gd"
## The Magic and unicorns rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; facing south): the Space rave's test for the lounge (tests/rave_theme_test.gd holds the body).


func _init() -> void:
	cfg = {"theme": "magic", "prefix": "magic", "map": "magic_rave", "art": "rave_magic", "facing": "S", "cloak_hold_sector": "t0_5", "bar_hold_sector": "t0_3",
		"lights": ["mg_aurora", "mg_sparkle_ring", "mg_orb_dome"]}
