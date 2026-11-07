extends MinigameActivity
## A stub overlay activity for the engine tests (CONTRACTS.md 4, 5 and 8; hooks H4.2, H5.4): it keeps every judge event, block result and region tap it is
## given, and finishes when told to (`finish_now`) with a race result. Not the race: the real one is the gameplay stream's (src/minigames/race).

var judged: Array = []  # [{ev, t}]
var blocks: Array = []  # the block_result events
var taps: Array = []  # [{target, t}]
var finish_now := false
var wobbles: Array = []


func on_judge(ev: Dictionary, t: float) -> void:
	judged.append({"ev": ev, "t": t})


func on_block(result: Dictionary) -> void:
	blocks.append(result)


func targets() -> Array:
	return ["region:top", "region:bottom", "region:left", "region:right", "exit"]


func tap(target: String, t: float) -> bool:
	taps.append({"target": target, "t": t})
	if target == "exit":
		request_leave(t)
		return true
	return target.begins_with("region:")


func set_wobble(level: int, t: float) -> void:
	super.set_wobble(level, t)
	wobbles.append({"level": level, "t": t})


func update(_t: float) -> void:
	if finish_now:
		_finish("done")


func result() -> Dictionary:
	var r := super.result()
	r["score"] = blocks.size()
	r["race"] = {"won": true, "position": 1, "time_s": 70.0}
	return r
