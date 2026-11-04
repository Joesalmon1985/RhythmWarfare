extends TestCase
## The camera in the world: one crowd per room, the crowd directions following the room the player walks into (and keeping the last crowd room when the player
## goes somewhere with no crowd), the room's own light, head glances on top of the rail, determinism at a given song time and restart. Uses the Mothership,
## which has four crowd rooms and a medical bay without one.


func _stage() -> StoryStage:
	var run := StoryRun.create({}, "res://content/story/mothership.json")
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art(run.data.art), run.data, run)
	return stage


func _move(stage: StoryStage, to: String, t0: float, bars := 2.0) -> void:
	stage.apply({"t0": t0, "bar": 1.0, "action": "player_move", "args": {"to": to, "style": "walk", "bars": bars}, "block": "", "source": "block"})


func test_a_chapter_has_a_crowd_in_every_room_that_holds_actors() -> void:
	var stage := _stage()
	assert_eq(stage.crowds.keys(), ["main", "gallery", "reactor", "bridge"])
	assert_eq(stage.current_view, "main")
	for id in stage.crowds:
		assert_true((stage.crowds[id] as StoryCrowd).world_mode, "%s: attached to the map" % id)
		assert_true((stage.crowds[id] as StoryCrowd).actors.size() >= 20, "%s is populated" % id)
	stage.free()


func test_the_crowd_directions_follow_the_player_between_rooms() -> void:
	var stage := _stage()
	assert_true(stage.crowd == stage.crowds["main"])
	_move(stage, "gallery_in", 1.0)
	assert_eq(stage.current_view, "gallery", "actions after the move direct the gallery's crowd")
	assert_true(stage.crowd == stage.crowds["gallery"])
	_move(stage, "medbay", 5.0)
	assert_eq(stage.current_view, "gallery", "the medical bay has no crowd: the directions stay with the last room that has one")
	_move(stage, "bridge_in", 9.0, 4.0)
	assert_eq(stage.current_view, "bridge")
	stage.reset()
	assert_eq(stage.current_view, "main", "a restart returns to the first room")
	stage.free()


func test_a_room_brings_its_own_light_with_the_player() -> void:
	var stage := _stage()
	stage.apply({"t0": 0.0, "bar": 1.0, "action": "lights_warm", "args": {}, "block": "", "source": "block"})
	assert_eq(stage.palette, "warm")
	_move(stage, "gallery_in", 1.0)
	assert_eq(stage.palette, "cool", "the gallery's palette")
	_move(stage, "deck_centre", 5.0)
	assert_eq(stage.palette, "warm", "and the deck's own light comes back")
	stage.free()


func test_every_crowd_updates_whichever_room_is_in_view() -> void:
	var stage := _stage()
	stage.update(2.0, 55.0)
	for id in stage.crowds:
		assert_near((stage.crowds[id] as StoryCrowd)._t_now, 2.0, 1e-6, "%s ran this frame" % id)
	stage.free()


func test_a_glance_turns_the_head_and_never_touches_the_route() -> void:
	var stage := _stage()
	stage.player.drift_on = false  # the idle drift would blur the exact turn
	var b := stage.bar_s()
	var base := stage.player.pose_at(5.0 * b)
	stage.apply({"t0": 4.0 * b, "bar": 4.0, "action": "player_look", "args": {"by": 30.0, "bars": 3}, "block": "", "source": "block"})
	assert_near(float(stage.player.pose_at(4.0 * b)["yaw"]), float(base["yaw"]), 1e-4, "no turn at its start")
	assert_near(float(stage.player.pose_at(5.5 * b)["yaw"]) - float(base["yaw"]), 30.0, 0.5, "the full turn half way")
	assert_near(float(stage.player.pose_at(7.0 * b)["yaw"]), float(base["yaw"]), 1e-4, "and back at its end")
	assert_eq(stage.player.pose_at(5.5 * b)["pos"], base["pos"], "the rail position is untouched")
	_move(stage, "gallery_in", 4.0 * b, 4.0)
	assert_true(stage.player.pose_at(6.0 * b)["moving"], "a glance during a move does not cancel it")
	assert_eq(stage.player.pose_at(9.0 * b)["pos"], stage.map.waypoint("gallery_in")["at"])
	stage.free()


func test_the_camera_is_a_function_of_song_time() -> void:
	var a := _stage()
	var c := _stage()
	var b := a.bar_s()
	for s in [a, c]:
		_move(s, "gallery_in", 1.0 * b, 3.0)
		s.apply({"t0": 2.0 * b, "bar": 2.0, "action": "player_look", "args": {"by": -20.0, "bars": 2}, "block": "", "source": "block"})
	for t in [0.5, 2.0 * b, 3.3 * b, 5.0 * b]:
		a.update(t, 50.0)
	c.update(5.0 * b, 50.0)
	assert_eq(a.player.pose_at(5.0 * b)["cam"], c.player.pose_at(5.0 * b)["cam"], "stepping or jumping gives the same pose")
	a.free()
	c.free()


func test_all_visible_figures_of_all_rooms_are_ordered_together_by_distance() -> void:
	var stage := _stage()
	var main: StoryCrowd = stage.crowds["main"]
	var gal: StoryCrowd = stage.crowds["gallery"]
	var near_in_gallery: Node = gal.actors[gal.actors.keys()[0]]["node"]
	var far_in_main: Node = main.actors[main.actors.keys()[0]]["node"]
	var mid_in_main: Node = main.actors[main.actors.keys()[1]]["node"]
	# keys are inverted millimetres: a bigger key is nearer. The gallery's dancer is nearest, then main's second, main's first is furthest.
	main.sort_items = [[3000000, far_in_main], [3600000, mid_in_main]]
	gal.sort_items = [[3800000, near_in_gallery]]
	stage._order_crowds()
	assert_true((far_in_main as CanvasItem).z_index < (mid_in_main as CanvasItem).z_index, "far before mid")
	assert_true((mid_in_main as CanvasItem).z_index < (near_in_gallery as CanvasItem).z_index, "a dancer of another room that is nearer draws over this room's")
	gal.sort_items = [[3300000, near_in_gallery]]
	stage._order_crowds()
	assert_true((far_in_main as CanvasItem).z_index < (near_in_gallery as CanvasItem).z_index and (near_in_gallery as CanvasItem).z_index < (mid_in_main as CanvasItem).z_index, "and interleaves by true distance through a doorway")
	stage.free()
