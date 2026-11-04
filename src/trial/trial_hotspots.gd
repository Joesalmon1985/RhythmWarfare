class_name TrialHotspots
extends RefCounted
## The Bassment's hotspots (content/trial/hotspots.json, written by tools/trial/make_hotspots.py from passages.json; the contract is docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md section 2):
## one per choice, keyed by passage. This is the data side for the scene: which hotspots a player holding some items may see, where an anchor stands in its zone map, and a check that the
## file and the passages agree (validate). The engine workstream's validator covers the shared contract; this one covers what only the Bassment knows.

const PATH := "res://content/trial/hotspots.json"
const GROUND_LIFT := 1.0  # a waypoint anchor (a doorway, a gap) is hit about a metre above the floor

var raw: Dictionary = {}
var by_passage: Dictionary = {}  # int passage -> Array of hotspot dictionaries (in choice order)
var errors: Array = []


static func load_default() -> TrialHotspots:
	var h := TrialHotspots.new()
	if not FileAccess.file_exists(PATH):
		h.errors.append("%s not found" % PATH)
		return h
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(v) != TYPE_DICTIONARY:
		h.errors.append("%s is not a JSON object" % PATH)
		return h
	h.raw = v
	for k in (v.get("hotspots", {}) as Dictionary):
		h.by_passage[int(k)] = v["hotspots"][k]
	return h


func count() -> int:
	var n := 0
	for k in by_passage:
		n += (by_passage[k] as Array).size()
	return n


func kinds() -> Dictionary:
	var out := {}
	for k in by_passage:
		for h in by_passage[k]:
			out[str(h["kind"])] = int(out.get(str(h["kind"]), 0)) + 1
	return out


## The hotspots of passage `n` that a player holding `flags` may see, each as {hs, index} where index is the position in TrialFlow.choices() (the list the engine selects from).
func visible(n: int, flags: Array) -> Array:
	var out: Array = []
	var idx := 0
	for h in by_passage.get(n, []):
		var need: Array = (h.get("available", {}) as Dictionary).get("flags_all", [])
		var ok := true
		for f in need:
			if str(f) not in flags:
				ok = false
		if ok:
			out.append({"hs": h, "index": idx})
			idx += 1
	return out


## Where an anchor stands in its zone map: {ok, pos: Vector3 (x, y, z), ground: float}. A waypoint is hit a metre above the floor; a thing at its own height.
static func anchor_point(hs: Dictionary, m: StoryMap) -> Dictionary:
	var a: Dictionary = hs.get("anchor", {})
	if a.has("waypoint"):
		if not m.has_waypoint(str(a["waypoint"])):
			return {"ok": false}
		var w: Dictionary = m.waypoint(str(a["waypoint"]))
		var floor_y := float(m.sector(str(w["sector"])).get("floor", 0.0))
		var at: Vector2 = w["at"]
		return {"ok": true, "pos": Vector3(at.x, floor_y + GROUND_LIFT, at.y), "ground": floor_y}
	if a.has("thing"):
		for t in m.things:
			if str(t["id"]) == str(a["thing"]):
				var floor_t := float(m.sector(str(t["sector"])).get("floor", 0.0))
				var at2: Vector2 = t["at"]
				return {"ok": true, "pos": Vector3(at2.x, floor_t + float(t.get("y", float(t.get("size", 1.0)) * 0.5)), at2.y), "ground": floor_t}
	return {"ok": false}


## Every hotspot against the passages and the zone maps; the errors name the hotspot. Empty when the two agree.
func validate(d: TrialData) -> Array:
	var errs: Array = errors.duplicate()
	var seen := {}
	for n in d.passages:
		var p: Dictionary = d.passages[n]
		var cs: Array = p.get("choices", [])
		var hs: Array = by_passage.get(n, [])
		if hs.size() != cs.size():
			errs.append("passage %d: %d hotspots for %d choices" % [n, hs.size(), cs.size()])
			continue
		var m := TrialData.map_of(str(p.get("map", "")))
		var defaults := 0
		var shown := 0
		for i in cs.size():
			var c: Dictionary = cs[i]
			var h: Dictionary = hs[i]
			var id := str(h.get("id", ""))
			if id != "trial.%d.%d" % [n, i] or seen.has(id):
				errs.append("passage %d: hotspot %d has id '%s'" % [n, i, id])
			seen[id] = true
			if str(h.get("scene", "")) != str(n) or str(h.get("map", "")) != str(p.get("map", "")) or int(h.get("choice", -1)) != i:
				errs.append("%s: scene, map or choice does not match the passage" % id)
			if bool(h.get("default", false)) != bool(c.get("default", false)):
				errs.append("%s: default disagrees with the choice" % id)
			if bool(h.get("default", false)) and str(c.get("requires", "")) == "":
				defaults += 1
			var req: Array = (h.get("available", {}) as Dictionary).get("flags_all", [])
			if req != ([str(c["requires"])] if str(c.get("requires", "")) != "" else []):
				errs.append("%s: availability disagrees with the choice's requirement" % id)
			if str(c.get("requires", "")) == "":
				shown += 1
			var kind := str(h.get("kind", ""))
			var want := "encounter" if c.has("encounter") else ("feature" if c.has("test") else "")
			if want != "" and kind != want:
				errs.append("%s: a %s choice must be a %s hotspot, not %s" % [id, "fight" if want == "encounter" else "luck test", want, kind])
			if kind not in ["exit", "encounter", "object", "feature"]:
				errs.append("%s: kind '%s' is not one the Bassment uses" % [id, kind])
			if int(h.get("min_px", 0)) < 72:
				errs.append("%s: min_px is at least 72" % id)
			var ap := anchor_point(h, m)
			if not bool(ap["ok"]):
				errs.append("%s: anchor %s is not in map %s" % [id, h.get("anchor", {}), p.get("map", "")])
			if c.get("to", null) == null:
				if (h["on_success"] as Dictionary).get("exit", "") != str(c.get("exit", "")) or h.get("challenge", null) != null:
					errs.append("%s: an exit choice leaves the dungeon with no challenge" % id)
			else:
				var ch: Variant = h.get("challenge", null)
				var ph: Dictionary = d.phrases.get(str(c["phrase"]), {})
				if typeof(ch) != TYPE_DICTIONARY or str(ch["family"]) != str(ph.get("family", "")) or int(ch["tier"]) != int(ph.get("tier", -1)):
					errs.append("%s: the challenge is not the choice's phrase family and tier" % id)
				var to_ok := int(c["test"]["pass"]) if c.has("test") else int(c["to"])
				if str((h["on_success"] as Dictionary).get("route", "")) != str(to_ok):
					errs.append("%s: on_success routes to %s, the choice to %d" % [id, (h["on_success"] as Dictionary).get("route", ""), to_ok])
				var fail: Variant = h.get("on_failure", null)
				if typeof(fail) != TYPE_DICTIONARY:
					errs.append("%s: a phrase can be failed: on_failure is needed" % id)
				elif c.has("test"):
					if str(fail.get("route", "")) != str(int(c["test"]["fail"])):
						errs.append("%s: a luck test's miss goes the other way (%d)" % [id, int(c["test"]["fail"])])
				else:
					if not bool(fail.get("hold", false)) or not bool(fail.get("make_default", false)):
						errs.append("%s: a failed choice holds the place and becomes the default" % id)
					if c.has("encounter") and str((fail.get("on_defeat", {}) as Dictionary).get("route", "")) != "0":
						errs.append("%s: a lost fight leads to passage 0" % id)
		if defaults != 1:
			errs.append("passage %d: exactly one default hotspot without a requirement (found %d)" % [n, defaults])
		if shown < 1 or shown > 4:
			errs.append("passage %d: %d hotspots are shown without an item (1 to 4)" % [n, shown])
	return errs
