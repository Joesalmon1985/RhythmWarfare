class_name StoryLowRes
extends Control
## The window onto the 3D world: a SubViewport rendered at a low internal resolution (one internal pixel is window height / LINES screen pixels tall, so 270
## lines is 480 x 270 at 16:9 over a full-height window) and shown with nearest filtering. Holds the StoryWorld and its Camera3D. The 2D crowd joins this viewport
## in WP4 so dancers pixelate like the world.

const FOV_V := StoryProjector.FOV_V
const LINE_CHOICES := [360, 270, 180]

var lines := 360  # internal vertical resolution of a full-height window (RW_STORY_LINES overrides)
var sub: SubViewport
var rect: TextureRect
var camera: Camera3D
var world: StoryWorld
var _env_node: WorldEnvironment
var post: ShaderMaterial  # queasy wobble, dimming and strobe on the finished low-res image (StoryLight.post_state feeds it)


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	if OS.has_environment("RW_STORY_LINES"):
		lines = int(OS.get_environment("RW_STORY_LINES"))
	sub = SubViewport.new()
	sub.name = "Low"
	sub.own_world_3d = true
	sub.msaa_3d = Viewport.MSAA_DISABLED
	sub.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	sub.use_taa = false
	sub.transparent_bg = false
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sub.handle_input_locally = false
	sub.gui_disable_input = true
	sub.size = Vector2i(480, 160)
	add_child(sub)
	rect = TextureRect.new()
	rect.name = "Screen"
	rect.texture = sub.get_texture()
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	post = ShaderMaterial.new()
	post.shader = load("res://src/story/world/story_post.gdshader")
	rect.material = null  # the post-process is only on while something needs it (apply_post)
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(rect)
	camera = Camera3D.new()
	camera.name = "Eye"
	camera.fov = FOV_V
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	camera.near = StoryProjector.NEAR
	camera.far = 90.0
	sub.add_child(camera)
	resized.connect(_fit)


## A CanvasLayer inside the low-res viewport for the 2D crowd: it is drawn into the same small image, so dancers pixelate like the world.
func add_overlay(node: Node, layer_name := "Overlay") -> CanvasLayer:
	var layer := CanvasLayer.new()
	layer.name = layer_name
	layer.layer = 1
	sub.add_child(layer)
	if node.get_parent() != null:
		node.get_parent().remove_child(node)
	layer.add_child(node)
	return layer


## The steady vignette over the image (the chapter's own vignette sprite).
func set_vignette(tex: Texture2D) -> void:
	if tex == null:
		return
	var v := TextureRect.new()
	v.name = "Vignette"
	v.texture = tex
	v.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	v.stretch_mode = TextureRect.STRETCH_SCALE
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.modulate = Color(1, 1, 1, 0.9)
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(v)


func attach(p_world: StoryWorld) -> void:
	world = p_world
	sub.add_child(world)
	_env_node = WorldEnvironment.new()
	_env_node.environment = world.env
	sub.add_child(_env_node)
	camera.current = true
	_fit()


## Internal size for this control: (control size) / (window height / lines).
func internal_size() -> Vector2i:
	var win_h := maxf(get_viewport_rect().size.y if is_inside_tree() else size.y, 1.0)
	var px := maxf(win_h / float(lines), 1.0)
	return Vector2i(maxi(int(ceil(size.x / px)), 16), maxi(int(ceil(size.y / px)), 16))


func _fit() -> void:
	if size.x < 1.0 or size.y < 1.0:
		return
	sub.size = internal_size()


## Put the Camera3D where the rail's pose says. Roll is the pose's bob roll (degrees), the free-look offset turns the head (degrees).
func apply_pose(pose: Dictionary, look_offset_deg := 0.0) -> void:
	var cam: Vector3 = pose["cam"]
	camera.position = cam
	camera.rotation_degrees = Vector3(float(pose.get("pitch", 0.0)), float(pose["yaw"]) + look_offset_deg, float(pose["roll"]))
	if world != null:
		world.follow(cam)


## Feed the post-process from StoryLight.post_state (and the palette's colour for the bloom).
func apply_post(st: Dictionary, flash_color := Color(0.6, 0.7, 1.0)) -> void:
	var active := float(st["queasy"]) > 0.001 or float(st["dim"]) > 0.004 or float(st["strobe"]) > 0.001 or float(st["flash"]) > 0.002 or float(st["vignette"]) > 0.001
	rect.material = post if active else null  # a plain nearest-filtered blit is cheaper than the shader
	post.set_shader_parameter("queasy", float(st["queasy"]))
	post.set_shader_parameter("time_s", float(st["time"]))
	post.set_shader_parameter("dim", float(st["dim"]))
	post.set_shader_parameter("strobe", float(st["strobe"]))
	post.set_shader_parameter("flash", float(st["flash"]))
	post.set_shader_parameter("vignette", float(st["vignette"]))
	post.set_shader_parameter("flash_color", Vector3(flash_color.r, flash_color.g, flash_color.b))


func projector_pose(pose: Dictionary, look_offset_deg := 0.0) -> Dictionary:
	return {"cam": pose["cam"], "yaw": float(pose["yaw"]) + look_offset_deg, "pitch": float(pose.get("pitch", 0.0))}
