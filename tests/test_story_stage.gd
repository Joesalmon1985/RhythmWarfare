extends TestCase
## Story art and stage: the manifest and every texture it names, the six archetypes with all four emotion states, the poses they
## strike, and the stage populated and driven through a whole set on the virtual clock.

const ARCHETYPES := ["groover", "ponytail", "hoodie", "curly", "bob", "punk"]
const FACES := ["neutral", "happy", "cheer", "sad"]


func test_manifest_and_textures_exist() -> void:
	var a := StoryAssets.load_default()
	assert_true(a.ok(), str(a.errors))
	if not a.ok():
		return
	for arch in ARCHETYPES:
		var ad: Dictionary = a.manifest["archetypes"].get(arch, {})
		assert_false(ad.is_empty(), "archetype %s" % arch)
		assert_true(ad.get("variants", {}).size() >= 2, "%s has two variants" % arch)
		for v in ad.get("variants", {}):
			var rig: Dictionary = ad["variants"][v]
			assert_true(rig["parts"].size() >= 9, "%s/%s has a full set of parts" % [arch, v])
			for p in rig["parts"]:
				assert_true(a.texture(str(p["file"])) != null, "%s/%s part %s imports" % [arch, v, p["name"]])
			for f in FACES:
				assert_true(rig["faces"].has(f), "%s/%s has face %s" % [arch, v, f])
				assert_true(a.texture(str(rig["faces"][f]["file"])) != null, "%s/%s face %s imports" % [arch, v, f])
			for j in ["hips", "torso", "head", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "hip_l", "hip_r"]:
				assert_true(ad["joints"].has(j), "%s joint %s" % [arch, j])
	for id in ["backdrop", "speaker_l", "speaker_r", "riser", "desk_top"]:
		assert_false(a.layer(id).is_empty(), "layer %s" % id)
		assert_true(a.texture(str(a.layer(id)["file"])) != null, "layer %s imports" % id)
	for id in ["woofer", "fixture", "disco_ball", "glowstick", "door_open", "spot_pool", "haze_a", "haze_b", "glow", "beam", "vignette", "pad_bezel",
			"platter", "knob", "fader_slot", "fader_cap", "desk_lip_glow"]:
		var s := a.sprite(id)
		assert_false(s.is_empty(), "sprite %s" % id)
		if not s.is_empty():
			assert_true(s["tex"] != null, "sprite %s imports" % id)
	assert_false(a.manifest["stage"].has("anchors"), "the 2D rooms' anchors are gone from the manifest: the map places everything")
	assert_true(a.manifest.has("textures") and a.manifest["textures"].size() >= 16, "the world's texture tiles are listed")
	assert_eq(a.manifest["silhouettes"].size(), 3, "three rear silhouette shapes")
	assert_true(a.errors.is_empty(), "no missing textures: %s" % str(a.errors))


func test_every_archetype_acts_all_four_states_with_moving_limbs() -> void:
	var a := StoryAssets.load_default()
	for arch in ARCHETYPES:
		var rig: Dictionary = (a.manifest["archetypes"][arch]["variants"]["a"] as Dictionary).duplicate()
		rig["joints"] = a.manifest["archetypes"][arch]["joints"]
		var c := StoryCharacter.new()
		c.setup(a, rig, arch, 7)
		var idle := c.sample("idle", 3.3, 0.5)
		var dance := c.sample("dance", 3.3, 0.5)
		var cheer := c.sample("cheer", 3.3, 0.5)
		var sad := c.sample("sad", 3.3, 0.5)
		assert_true(float(cheer["arm_l"]) > float(dance["arm_l"]) and float(dance["arm_l"]) > float(idle["arm_l"]), "%s: arms rise idle < dance < cheer" % arch)
		assert_true(float(sad["head_drop"]) > 0.0 and float(sad["arm_l"]) < float(dance["arm_l"]), "%s: sad slumps" % arch)
		assert_true(float(cheer["jump"]) >= 0.0 and float(dance["leg_l"]) != 0.0, "%s: legs and jump move" % arch)
		# animation really moves limbs over a bar, not a vertical bob only
		var lo := 99.0
		var hi := -99.0
		for k in 32:
			var p := c.sample("dance", float(k) * 0.125, 0.6)
			lo = minf(lo, float(p["arm_l"]))
			hi = maxf(hi, float(p["arm_l"]))
		assert_true(hi - lo > 0.4, "%s: the arm swings through %.2f rad" % [arch, hi - lo])
		c.state = "cheer"
		assert_eq(c.face_name(), "cheer")
		c.state = "sad"
		assert_eq(c.face_name(), "sad")
		c.free()


func _stage(policy: String) -> Dictionary:
	var run := StoryRun.create({})
	var assets := StoryAssets.load_default()
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(assets, run.data, run)
	return {"run": run, "stage": stage}


func test_stage_is_populated_and_driven_through_the_whole_set() -> void:
	var ctx := _stage("perfect")
	var run: StoryRun = ctx["run"]
	var stage: StoryStage = ctx["stage"]
	assert_true(stage.crowd.present_count() >= 12, "the room is never empty at the start: %d" % stage.crowd.present_count())
	var harness: Script = load("res://tools/autoplay.gd")
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var plan: Array = harness.plan_inputs(run.level, "perfect", rng)
	var k := 0
	var t := -1.0
	var peak := 0
	var min_after_start := 999
	var cheering_end := 0
	var down := {}
	while t < run.level.duration_seconds() + 6.0:
		t += 1.0 / 30.0
		while k < plan.size() and float(plan[k]["t"]) <= t:
			var e: Dictionary = plan[k]
			if e["down"]:
				down[e["pad"]] = e["id"]
				run.match_ref.press(int(e["pad"]), float(e["t"]), int(e["pad"]))
			elif down.get(e["pad"], null) == e["id"]:
				down.erase(e["pad"])
				run.match_ref.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
			k += 1
		var r := run.step(t)
		for ev in r["events"]:
			if ev["kind"] == "sequence":
				stage.on_sequence(ev["result"], float(ev["result"]["resolve_time"]))
		for a in r["actions"]:
			stage.apply(a)
		stage.update(t, run.crowd.energy)
		var n := stage.crowd.present_count()
		peak = maxi(peak, n)
		if t > 0.5:
			min_after_start = mini(min_after_start, n)
	var counts := stage.crowd.state_counts()
	cheering_end = int(counts.get("cheer", 0)) + int(counts.get("hands_up", 0))
	assert_true(peak >= 24 and peak <= 48, "24 to 48 visible crowd members at the peak: %d" % peak)
	assert_true(min_after_start >= 12, "the stage is never blank: %d" % min_after_start)
	assert_eq(stage.ending(), "legendary_set")
	assert_true(cheering_end >= 20, "a visibly ecstatic crowd at the Legendary tableau (%s)" % str(counts))
	stage.queue_free()


func test_no_input_leaves_a_subdued_crowd_after_the_full_song() -> void:
	var ctx := _stage("none")
	var run: StoryRun = ctx["run"]
	var stage: StoryStage = ctx["stage"]
	var t := -1.0
	while t < run.level.duration_seconds() + 6.0:
		t += 1.0 / 30.0
		var r := run.step(t)
		for ev in r["events"]:
			if ev["kind"] == "sequence":
				stage.on_sequence(ev["result"], float(ev["result"]["resolve_time"]))
		for a in r["actions"]:
			stage.apply(a)
		stage.update(t, run.crowd.energy)
	assert_eq(stage.ending(), "lost_the_floor")
	var counts := stage.crowd.state_counts()
	var lively := int(counts.get("cheer", 0)) + int(counts.get("hands_up", 0)) + int(counts.get("dance", 0))
	var subdued := int(counts.get("sad", 0)) + int(counts.get("look", 0)) + int(counts.get("idle", 0))
	assert_true(subdued > lively, "mostly subdued: %s" % str(counts))
	assert_true(stage.crowd.present_count() >= 12, "still populated")
	stage.queue_free()
