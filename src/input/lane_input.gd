class_name LaneInput
extends Node
## Turns touches and keys into lane press/release events with stable touch identifiers, so a bass hold can
## coexist with kick and snare taps. Key repeat, a finger that stays down and extra fingers on a lane never
## produce extra presses: each touch id presses once on the way down and releases once on the way up.
## Desktop keys use the same rules as touch (negative touch ids). Button rectangles come from the lane view.

signal lane_pressed(lane: String, touch_id: int)
signal lane_released(lane: String, touch_id: int)

const KEY_TOUCH_ID := {"kick": -1, "bass": -2, "snare": -3}

var enabled := true
var rect_provider: Callable  # returns Dictionary lane -> Rect2 in viewport coordinates, queried on each touch
var _touch_lane: Dictionary = {}  # touch index -> lane
var _key_down: Dictionary = {"kick": false, "bass": false, "snare": false}


## Runs in _input, before the GUI: a screen-sized Control would otherwise consume every touch and click and
## the lanes would never hear them. Only touches inside a lane button and the lane keys are marked handled.
func _input(event: InputEvent) -> void:
	if not enabled:
		return
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		if t.pressed:
			if _touch_lane.has(t.index):
				return
			var lane := _lane_at(t.position)
			if lane.is_empty():
				return
			_touch_lane[t.index] = lane
			lane_pressed.emit(lane, t.index)
			get_viewport().set_input_as_handled()
		else:
			if _touch_lane.has(t.index):
				var lane: String = _touch_lane[t.index]
				_touch_lane.erase(t.index)
				lane_released.emit(lane, t.index)
				get_viewport().set_input_as_handled()
	elif event is InputEventKey:
		var k := event as InputEventKey
		if k.echo:
			return
		for lane in KEY_TOUCH_ID:
			if k.is_action_pressed("lane_" + lane, false, true):
				if not _key_down[lane]:
					_key_down[lane] = true
					lane_pressed.emit(lane, KEY_TOUCH_ID[lane])
				get_viewport().set_input_as_handled()
			elif k.is_action_released("lane_" + lane, true):
				if _key_down[lane]:
					_key_down[lane] = false
					lane_released.emit(lane, KEY_TOUCH_ID[lane])
				get_viewport().set_input_as_handled()


## Release everything (pause, scene end). Emits releases so holds can be cleaned up by the owner if needed.
func clear(emit_releases: bool = false) -> void:
	for idx in _touch_lane.keys():
		if emit_releases:
			lane_released.emit(_touch_lane[idx], idx)
	_touch_lane.clear()
	for lane in _key_down:
		if _key_down[lane] and emit_releases:
			lane_released.emit(lane, KEY_TOUCH_ID[lane])
		_key_down[lane] = false


func is_lane_down(lane: String) -> bool:
	if _key_down.get(lane, false):
		return true
	for idx in _touch_lane:
		if _touch_lane[idx] == lane:
			return true
	return false


func _lane_at(pos: Vector2) -> String:
	if not rect_provider.is_valid():
		return ""
	var rects: Dictionary = rect_provider.call()
	for lane in rects:
		if (rects[lane] as Rect2).has_point(pos):
			return lane
	return ""
