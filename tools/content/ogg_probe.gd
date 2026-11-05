extends SceneTree
## Decodes every .ogg in a folder with Godot's own Ogg Vorbis player and writes what it hears (docs/REPO_SIZE.md, Part 2; driver: tools/content/ogg_check.py).
##   GODOT --headless --path <repo> -s tools/content/ogg_probe.gd -- <in_dir> <out_dir>
## For each <name>.ogg:
##   <name>.once.f32  the stream played once, not looping (interleaved stereo float32); `mixed` in the json is the frames the player produced before it stopped;
##   <name>.loop.f32  the stream with loop = true, 2 * L frames, L = round(length * mix rate), the loop period as the engine states it;
##   <name>.json      {length_s, rate, L, mixed}.

const CHUNK := 4096


func _pull(s: AudioStreamOggVorbis, want: int) -> PackedFloat32Array:
	var pb := s.instantiate_playback()
	pb.start(0.0)
	var out := PackedFloat32Array()
	var n := 0
	var guard := 0
	while n < want and guard < 200000:
		var chunk: PackedVector2Array = pb.mix_audio(1.0, mini(CHUNK, want - n))
		if chunk.is_empty():
			break
		for v in chunk:
			out.append(v.x)
			out.append(v.y)
		n += chunk.size()
		guard += 1
	return out


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var in_dir := args[0]
	var out_dir := args[1]
	DirAccess.make_dir_recursive_absolute(out_dir)
	var dir := DirAccess.open(in_dir)
	for f in dir.get_files():
		if f.get_extension() != "ogg":
			continue
		var base := f.get_basename()
		var s := AudioStreamOggVorbis.load_from_file(in_dir.path_join(f))
		var rate := AudioServer.get_mix_rate()
		var l := int(round(s.get_length() * rate))
		var once := _pull(s, l + 4096)  # asks for more than the stream holds: it stops at its end
		var s2 := AudioStreamOggVorbis.load_from_file(in_dir.path_join(f))
		s2.loop = true
		var looped := _pull(s2, 2 * l)
		for pair in [["once", once], ["loop", looped]]:
			var fh := FileAccess.open(out_dir.path_join("%s.%s.f32" % [base, pair[0]]), FileAccess.WRITE)
			fh.store_buffer((pair[1] as PackedFloat32Array).to_byte_array())
			fh.close()
		var jf := FileAccess.open(out_dir.path_join(base + ".json"), FileAccess.WRITE)
		jf.store_string(JSON.stringify({"length_s": s.get_length(), "rate": rate, "L": l, "mixed": once.size() / 2}))
		jf.close()
	quit(0)
