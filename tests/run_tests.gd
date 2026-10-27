extends SceneTree
## Headless test runner:  godot --headless --path . -s tests/run_tests.gd -- [--filter name]
## Discovers tests/test_*.gd, runs every test_* method (coroutines are awaited), prints a summary, exits 0 on success.

var _filter := ""


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	for i in args.size():
		if args[i] == "--filter" and i + 1 < args.size():
			_filter = args[i + 1]
	_run()


func _run() -> void:
	await process_frame
	var total_checks := 0
	var total_failures: Array[String] = []
	var files := _test_files()
	files.sort()
	for path in files:
		if not _filter.is_empty() and not path.contains(_filter):
			continue
		var script: GDScript = load(path)
		if script == null:
			total_failures.append("%s: failed to load" % path)
			continue
		var count := 0
		for m in script.get_script_method_list():
			var name: String = m["name"]
			if not name.begins_with("test_"):
				continue
			var case: TestCase = script.new()
			case.tree = self
			case.set_current("%s.%s" % [path.get_file(), name])
			await case.call(name)
			count += 1
			total_checks += case.checks
			total_failures.append_array(case.failures)
		print("%-40s %d tests" % [path.get_file(), count])
	print("")
	print("%d checks, %d failures" % [total_checks, total_failures.size()])
	for f in total_failures:
		print("  FAIL ", f)
	quit(0 if total_failures.is_empty() else 1)


func _test_files() -> Array[String]:
	var out: Array[String] = []
	var dir := DirAccess.open("res://tests")
	if dir == null:
		return out
	dir.list_dir_begin()
	var name := dir.get_next()
	while not name.is_empty():
		if name.begins_with("test_") and name.ends_with(".gd") and name != "test_case.gd":
			out.append("res://tests/" + name)
		name = dir.get_next()
	return out
