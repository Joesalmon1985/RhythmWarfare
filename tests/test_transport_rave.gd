extends "res://tests/rave_theme_test.gd"
## The Transport rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4; facing west): the Space rave's test for the wet forecourt, the tracks and the depot hall (tests/rave_theme_test.gd holds the body).


func _init() -> void:
	cfg = {"theme": "transport", "prefix": "transport", "map": "transport_rave", "art": "rave_transport", "facing": "W", "cloak_hold_sector": "hall", "bar_hold_sector": "hall",
		"lights": ["tr_signal_beams", "tr_track_lights", "tr_headlamp_dome"]}
