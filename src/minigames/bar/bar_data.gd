class_name BarData
extends RefCounted
## The bar's per-theme content (bedsit brief section 6): four ingredients, the recipes, the customers. Pure data, no nodes.
##
## Where it comes from, first match wins:
##   1. content/bedsit/themes.json, key "bar", key <theme>: {ingredients: [{id, color, shape} x4], recipes: [[ingredient id, ...], ...], customers: [{id, body, kind}]}
##   2. the activity config's own "ingredients" (the rave's theme file, four of {id, color, icon?, shape?}), "recipes", "customers"
##   3. the built-in space set below (a theme-less request, such as the test scene).
## A recipe is a list of ingredient ids of 2 or 3 entries; a recipe naming an unknown ingredient, or the same ingredient twice running, is dropped. A theme with no usable recipe of a length
## gets recipes generated from its ingredients (BarActivity).

const THEMES_PATH := "res://content/bedsit/themes.json"
const SHAPES := ["swirl", "comet", "star", "crescent", "rainbow", "cloud", "gem", "spiky", "leaf", "flame", "hex", "egg", "can", "ring", "shaker", "lemon"]
const FALLBACK_SHAPES := ["star", "gem", "hex", "egg"]  # by position, for an ingredient with no shape of its own (four distinct silhouettes)
## Where the bar's things stand in the room's map (tests/fixtures/bar_scene/bar_room.json is the test map); a theme's themes.json "bar" entry or the config's "layout" may override any key.
## Metres: `at` is [x, z] on the ground plane, `y` the height of the thing's centre above the floor, `size` [w, h].
const LAYOUT := {
	"map": "bar_test", "sector": "bar_room",
	"customer_at": [-1.2, 1.4], "customer_glass_at": [-0.8, 1.7],
	"glass_at": [0.0, 2.0], "glass_y": 1.25, "glass_size": [0.3, 0.5],
	"bubble_at": [-1.2, 1.4], "bubble_y": 2.35, "bubble_size": [0.9, 0.9],
	"counter_piece": "bar_counter", "shelf_prefix": "bar_shelf_",
}
const BUILT_IN := {
	"ingredients": [
		{"id": "nebula_syrup", "color": "#8a4fd6", "shape": "swirl"},
		{"id": "comet_ice", "color": "#f4fbff", "shape": "comet"},
		{"id": "star_dust", "color": "#ffd84a", "shape": "star"},
		{"id": "moon_milk", "color": "#a8c8ff", "shape": "crescent"},
	],
	"recipes": [],
	"customers": [{"id": "green_alien", "body": "#6fcf7f", "kind": "antenna"}],
}


## {ingredients: [{id, color (Color), shape, index}] (exactly 4), recipes: [[int, ...]] (indices), customers: [{id, body (Color), kind}], source: "themes" | "config" | "built_in"}.
static func resolve(config: Dictionary, theme: String, themes_path := THEMES_PATH) -> Dictionary:
	var raw: Dictionary = {}
	var source := "built_in"
	var all := _read(themes_path)
	var bar: Variant = all.get("bar", {})
	if theme != "" and typeof(bar) == TYPE_DICTIONARY and typeof((bar as Dictionary).get(theme, null)) == TYPE_DICTIONARY:
		raw = (bar as Dictionary)[theme]
		source = "themes"
	elif _four(config.get("ingredients", null)):
		raw = {"ingredients": config["ingredients"], "recipes": config.get("recipes", []), "customers": config.get("customers", [])}
		source = "config"
	else:
		raw = BUILT_IN
	if not _four(raw.get("ingredients", null)):
		raw = BUILT_IN
		source = "built_in"
	var ings: Array = []
	var by_id := {}
	for i in 4:
		var d: Dictionary = (raw["ingredients"] as Array)[i]
		var shape := str(d.get("shape", ""))
		if shape not in SHAPES:
			shape = FALLBACK_SHAPES[i]
		var e := {"id": str(d["id"]), "color": Color.from_string(str(d.get("color", "#ffffff")), Color.WHITE), "shape": shape, "index": i}
		ings.append(e)
		by_id[e["id"]] = i
	var recipes: Array = []
	var rs: Variant = raw.get("recipes", [])
	if typeof(config.get("recipes", null)) == TYPE_ARRAY and source != "themes":
		rs = config["recipes"]
	for r: Variant in (rs if typeof(rs) == TYPE_ARRAY else []):
		var idx := recipe_indices(r, by_id)
		if not idx.is_empty():
			recipes.append(idx)
	var customers: Array = []
	var cs: Variant = raw.get("customers", [])
	for c: Variant in (cs if typeof(cs) == TYPE_ARRAY else []):
		if typeof(c) == TYPE_DICTIONARY and str((c as Dictionary).get("id", "")) != "":
			var cd: Dictionary = c
			customers.append({"id": str(cd["id"]), "body": Color.from_string(str(cd.get("body", "")), _hash_color(str(cd["id"]))), "kind": str(cd.get("kind", "antenna"))})
	if customers.is_empty():
		customers = [{"id": "regular", "body": Color("6fcf7f"), "kind": "antenna"}]
	return {"ingredients": ings, "recipes": recipes, "customers": customers, "source": source}


## The layout of theme `theme`: LAYOUT with the theme's, then the config's, overrides.
static func layout(config: Dictionary, theme: String, themes_path := THEMES_PATH) -> Dictionary:
	var out: Dictionary = LAYOUT.duplicate(true)
	var bar: Variant = _read(themes_path).get("bar", {})
	if theme != "" and typeof(bar) == TYPE_DICTIONARY and typeof((bar as Dictionary).get(theme, null)) == TYPE_DICTIONARY:
		var l: Variant = ((bar as Dictionary)[theme] as Dictionary).get("layout", {})
		if typeof(l) == TYPE_DICTIONARY:
			out.merge(l, true)
	if typeof(config.get("layout", null)) == TYPE_DICTIONARY:
		out.merge(config["layout"], true)
	return out


## A recipe as ingredient indices: [] when it is not 2 or 3 known ingredients or repeats one twice running.
static func recipe_indices(r: Variant, by_id: Dictionary) -> Array:
	if typeof(r) != TYPE_ARRAY or (r as Array).size() < 2 or (r as Array).size() > 3:
		return []
	var out: Array = []
	for x: Variant in r:
		var k := str(x)
		if not by_id.has(k) or (not out.is_empty() and int(out[-1]) == int(by_id[k])):
			return []
		out.append(int(by_id[k]))
	return out


static func _four(v: Variant) -> bool:
	if typeof(v) != TYPE_ARRAY or (v as Array).size() != 4:
		return false
	for e: Variant in v:
		if typeof(e) != TYPE_DICTIONARY or str((e as Dictionary).get("id", "")) == "":
			return false
	return true


static func _read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return d if typeof(d) == TYPE_DICTIONARY else {}


static func _hash_color(s: String) -> Color:
	var h := absi(s.hash())
	return Color.from_hsv(float(h % 360) / 360.0, 0.45, 0.85)
