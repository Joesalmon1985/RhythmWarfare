class_name DevText
extends RefCounted
## The play-text switch (docs/THREE_PATHS_AND_FACES_PLAN.md D3, 2.4). During play nothing is written on the screen: no title card, no captions, no world or room names, no numeric
## countdown, no Bassment caption band. `RW_DEV_TEXT=1` restores all of it for debugging and for the tests that read it. Menus, the pause panel, settings, the result screens and the
## F3 debug line are not play text and always draw. The Debug / Playtest list (docs/DEBUG_MODE.md) can switch it on for a session (PlaytestMode.dev_text). Read at call time, so a test may set it before it builds a scene.


static func on() -> bool:
	return OS.get_environment("RW_DEV_TEXT") == "1" or PlaytestMode.dev_text  # (the Debug / Playtest list's "show the old play text" option)
