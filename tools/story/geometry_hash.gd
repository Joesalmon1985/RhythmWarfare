extends SceneTree
## The built geometry of every story map as one hash per map (the renderer's regression check, docs/story/HEIGHTS_AND_PATHS.md): each map is built by StoryWorld and every
## mesh it makes (vertices, UVs, vertex colours, indices, and each surface's material settings) is hashed in node order. Run it before and after a renderer change: an
## unchanged hash means the map is drawn exactly as before.
##   godot --headless --path . -s tools/story/geometry_hash.gd -- [map id ...]        (no ids: every map in content/story/maps)
## Prints "GEOHASH <map> <hash> <meshes> <triangles>" per map.


func _initialize() -> void:
	var ids: Array = Array(OS.get_cmdline_user_args())
	if ids.is_empty():
		for f in DirAccess.get_files_at("res://content/story/maps"):
			if f.ends_with(".json"):
				ids.append(f.get_basename())
	ids.sort()
	for id in ids:
		var m := StoryMap.load_chapter(str(id))
		if not m.errors.is_empty():
			print("GEOHASH %s ERRORS %s" % [id, m.errors])
			continue
		var w: Node3D = load("res://src/story/world/story_world.gd").new()  # (by path: a SceneTree script compiles before the autoloads the world's dependencies name)
		w.build(m, StoryAssets.load_art(m.art))
		var ctx := HashingContext.new()
		ctx.start(HashingContext.HASH_MD5)
		var meshes := 0
		for c in w.get_children():
			if not (c is MeshInstance3D):
				continue
			var mi := c as MeshInstance3D
			ctx.update(str(mi.name).to_utf8_buffer())
			ctx.update(var_to_bytes(mi.position))
			var mesh := mi.mesh
			if mesh is ArrayMesh:
				meshes += 1
				for k in mesh.get_surface_count():
					var arr: Array = mesh.surface_get_arrays(k)
					for slot in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_COLOR, Mesh.ARRAY_INDEX]:
						ctx.update(var_to_bytes(arr[slot]))
					var mat := mesh.surface_get_material(k) as StandardMaterial3D
					if mat != null:
						ctx.update(var_to_bytes([mat.transparency, mat.texture_filter, mat.cull_mode, mat.shading_mode, mat.alpha_scissor_threshold,
							mat.albedo_texture.resource_path if mat.albedo_texture != null else ""]))
			elif mesh is QuadMesh:
				ctx.update(var_to_bytes((mesh as QuadMesh).size))
		print("GEOHASH %s %s %d %d" % [id, ctx.finish().hex_encode(), meshes, w.triangle_count])
		w.free()
	quit(0)
