class_name LaneInput
extends Node
## Turns touches and keys into button press/release events (buttons 1 to 4) with stable touch identifiers, so a
## bass hold on one button can coexist with taps on the others. Key repeat, a finger that stays down and extra
## fingers on a button never produce extra presses: each touch id presses once on the way down and releases once
## on the way up. Desktop keys (D, F, J, K) use the same rules as touch (negative touch ids). Button rectangles
## come from the lane view.

signal button_pressed(button: int, touch_id: int)
signal button_released(button: int, touch_id: int)

const KEY_TOUCH_ID := {1: -1, 2: -2, 3: -3, 4: -4}

var enabled := true
var rect_provider: Callable  # returns Dictionary button (int) -> Rect2 in viewport coordinates, queried on each touch
var _touch_button: Dictionary = {}  # touch index -> button
var _key_down: Dictionary = {1: false, 2: false, 3: false, 4: false}


static func action_name(button: int) -> String:
	return "button_%d" % button


## Runs in _input, before the GUI: a screen-sized Control would otherwise consume every touch and click and
## the buttons would never hear them. Only touches inside a button and the button keys are marked handled.
func _input(event: InputEvent) -> void:
	if not enabled:
		return
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		if t.pressed:
			if _touch_button.has(t.index):
				return
			var button := _button_at(t.position)
			if button <= 0:
				return
			_touch_button[t.index] = button
			button_pressed.emit(button, t.index)
			get_viewport().set_input_as_handled()
		else:
			if _touch_button.has(t.index):
				var button: int = _touch_button[t.index]
				_touch_button.erase(t.index)
				button_released.emit(button, t.index)
				get_viewport().set_input_as_handled()
	elif event is InputEventKey:
		var k := event as InputEventKey
		if k.echo:
			return
		for button in KEY_TOUCH_ID:
			var action := action_name(button)
			if k.is_action_pressed(action, false, true):
				if not _key_down[button]:
					_key_down[button] = true
					button_pressed.emit(button, KEY_TOUCH_ID[button])
				get_viewport().set_input_as_handled()
			elif k.is_action_released(action, true):
				if _key_down[button]:
					_key_down[button] = false
					button_released.emit(button, KEY_TOUCH_ID[button])
				get_viewport().set_input_as_handled()


## Release everything (pause, scene end). Emits releases so holds can be cleaned up by the owner if needed.
func clear(emit_releases: bool = false) -> void:
	for idx in _touch_button.keys():
		if emit_releases:
			button_released.emit(_touch_button[idx], idx)
	_touch_button.clear()
	for button in _key_down:
		if _key_down[button] and emit_releases:
			button_released.emit(button, KEY_TOUCH_ID[button])
		_key_down[button] = false


func is_button_down(button: int) -> bool:
	if _key_down.get(button, false):
		return true
	for idx in _touch_button:
		if _touch_button[idx] == button:
			return true
	return false


func _button_at(pos: Vector2) -> int:
	if not rect_provider.is_valid():
		return 0
	var rects: Dictionary = rect_provider.call()
	for button in rects:
		if (rects[button] as Rect2).has_point(pos):
			return int(button)
	return 0
