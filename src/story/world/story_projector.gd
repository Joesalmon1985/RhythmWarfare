class_name StoryProjector
extends RefCounted
## Pinhole projection in pure GDScript, the same camera the 3D world renders with (a Camera3D with a vertical field of view of FOV_V degrees, no pitch),
## so the 2D crowd can stand in the world: a world point and a camera pose give a screen position, a depth and a pixels-per-metre scale.
## Pose: {cam: Vector3 (x, eye height, z), yaw: degrees (0 looks toward -z, positive turns left)}. Roll is ignored (it is a few tenths of a degree).

const FOV_V := 52.0
const NEAR := 0.15


static func focal_px(viewport_h: float, fov_v := FOV_V) -> float:
	return viewport_h * 0.5 / tan(deg_to_rad(fov_v) * 0.5)


static func forward(yaw_deg: float) -> Vector2:
	var r := deg_to_rad(yaw_deg)
	return Vector2(-sin(r), -cos(r))


static func right(yaw_deg: float) -> Vector2:
	var r := deg_to_rad(yaw_deg)
	return Vector2(cos(r), -sin(r))


## Project the world point (x, height, z). {visible, screen: Vector2, depth: metres along the view axis, scale: pixels per metre at that depth}.
static func project(world: Vector3, pose: Dictionary, viewport: Vector2, fov_v := FOV_V) -> Dictionary:
	var cam: Vector3 = pose["cam"]
	var yaw := float(pose["yaw"])
	var d := Vector2(world.x - cam.x, world.z - cam.z)
	var depth := d.dot(forward(yaw))
	if depth < NEAR:
		return {"visible": false, "screen": Vector2.ZERO, "depth": depth, "scale": 0.0}
	var f := focal_px(viewport.y, fov_v)
	var sx := viewport.x * 0.5 + f * d.dot(right(yaw)) / depth
	var sy := viewport.y * 0.5 - f * (world.y - cam.y) / depth
	var on_screen := sx > -viewport.x * 0.25 and sx < viewport.x * 1.25 and sy > -viewport.y * 0.5 and sy < viewport.y * 1.5
	return {"visible": on_screen, "screen": Vector2(sx, sy), "depth": depth, "scale": f / depth}


## A ground point of a standing figure: where its feet are on screen and how many pixels tall one metre is there.
static func project_ground(x: float, z: float, ground_y: float, pose: Dictionary, viewport: Vector2, fov_v := FOV_V) -> Dictionary:
	return project(Vector3(x, ground_y, z), pose, viewport, fov_v)


## The ground point (at height ground_y) under a screen position, or null above the horizon.
static func unproject_ground(screen: Vector2, ground_y: float, pose: Dictionary, viewport: Vector2, fov_v := FOV_V) -> Variant:
	var cam: Vector3 = pose["cam"]
	var f := focal_px(viewport.y, fov_v)
	var dy := (viewport.y * 0.5 - screen.y) / f  # view-space up per unit depth
	if absf(dy) < 1.0e-9:
		return null
	var depth := (ground_y - cam.y) / dy
	if depth < NEAR:
		return null
	var lateral := (screen.x - viewport.x * 0.5) / f * depth
	var yaw := float(pose["yaw"])
	var p := Vector2(cam.x, cam.z) + forward(yaw) * depth + right(yaw) * lateral
	return Vector2(p.x, p.y)


## Nearest first: indices of `depths` sorted far to near is the draw order (painter's algorithm); this returns the sort for far-to-near drawing.
static func draw_order(depths: Array) -> Array:
	var idx: Array = range(depths.size())
	idx.sort_custom(func(a: int, b: int) -> bool: return float(depths[a]) > float(depths[b]) if depths[a] != depths[b] else a < b)
	return idx
