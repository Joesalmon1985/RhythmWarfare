extends RefCounted
## Conformance cases 1 to 15 of INTEGRATION_CONTRACT.md section 9, written against TransitionPort only, so the same
## cases run on MockTransitionDirector (tests/test_port_mock.gd) and later on the real director with a virtual clock.
## Not a test_ file: it is driven by a test, which passes in a TestCase (for assertions) and a factory.
##
## THE FACTORY is a Callable:   factory.call(opts: Dictionary) -> Dictionary   (called once per case, fresh port)
##   opts   {"bpm": 174.0, "laps": 4, "doors_from_lap": 2, "lock_lead_beats": 3.5}: the first scene's tempo, its
##          length in laps, the first departure lap, and the lock lead (all four are always given).
##   result {
##     "port":    TransitionPort, already inside its first scene (virtual clock at 0.0), default destination {},
##     "advance": Callable(dt: float) -> void   moves the virtual clock and runs the director for dt seconds,
##     "switch":  Callable(name: StringName, value: Variant) -> bool   optional; sets a failure / staging switch and
##                returns true, or returns false if this implementation cannot provide it (then the case is
##                skipped, counted in `skipped` and printed). Names and values:
##        &"fail_load_ids"        Array[String] destination ids that close as &"unavailable"
##        &"not_ready_ids"        Array[String] destination ids deferred once with &"not_ready"
##        &"fail_after_lock_ids"  Array[String] destination ids that land on a fallback scene after the lock
##        &"miss_last_block"      bool          the lap's last block is missed (on_miss is taken)
##        &"blend_beats"          int           beats of the incoming scene before `completed` (0 = cut)
##        &"scene_specs"          Dictionary    {dest id: {"bpm": float, "laps": int, "doors_from_lap": int}}: scene data
##                                              of the destinations the case enters (others use the opts values)
##   }
## Time: cases step the clock by STEP seconds and allow EPS seconds of slack on times (a real director may act on the
## frame after a point). Departure laps are not hard-coded: cases ask next_boundary_t() and lock_t().
##
## Readings of the contract chosen here (also in the report that came with this file):
##  - Laps are counted from 1 (lead's ruling, 6 Nov 2026): doors_from_lap 2 with 4 laps has departure laps 2, 3 and 4;
##    the last lap of a scene is always a departure lap.
##  - Lock points exist only on departure laps, so &"doors_closed" deferrals are tolerated but not required (case 5).
##  - A block is 16 beats (lead's ruling, 6 Nov 2026); on a replace, closed(old) comes before acknowledged(new) (case 2);
##    tempo_changed comes before switched (case 13).

const STEP := 0.05
const EPS := 0.06
const OPTS := {"bpm": 174.0, "laps": 4, "doors_from_lap": 2, "lock_lead_beats": 3.5}

## Names of the cases skipped by the last runs (each also printed). A runner asserts it is empty for the mock.
static var skipped: Array[String] = []


## Records every signal of a port with the clock and some port state at the moment of emission.
class Rec extends RefCounted:
	var events: Array[Dictionary] = []
	var port: TransitionPort

	func _init(p: TransitionPort) -> void:
		port = p
		p.request_acknowledged.connect(_on_ack)
		p.destination_ready.connect(_on_ready)
		p.request_closed.connect(_on_closed)
		p.deferred.connect(_on_deferred)
		p.locked.connect(_on_locked)
		p.switched.connect(_on_switched)
		p.completed.connect(_on_completed)
		p.tempo_changed.connect(_on_tempo)

	func _add(n: StringName, args: Array) -> void:
		events.append({"name": n, "args": args, "t": port.song_time(), "lap_beat": port.lap_beat(),
			"state": port.state(), "open": port.selection_open()})

	func _on_ack(id: int, ok: bool, reason: StringName) -> void:
		_add(&"request_acknowledged", [id, ok, reason])

	func _on_ready(id: int) -> void:
		_add(&"destination_ready", [id])

	func _on_closed(id: int, reason: StringName) -> void:
		_add(&"request_closed", [id, reason])

	func _on_deferred(id: int, nb: float, reason: StringName) -> void:
		_add(&"deferred", [id, nb, reason])

	func _on_locked(id: int, dest: Dictionary, boundary_t: float, plan: Dictionary) -> void:
		_add(&"locked", [id, dest, boundary_t, plan])

	func _on_switched(id: int, landed: Dictionary, t: float) -> void:
		_add(&"switched", [id, landed, t])

	func _on_completed(id: int) -> void:
		_add(&"completed", [id])

	func _on_tempo(bpm: float, beat_s: float, t: float) -> void:
		_add(&"tempo_changed", [bpm, beat_s, t])

	## Events called n whose first argument is id (any id when id < 0).
	func of(n: StringName, id: int = -1) -> Array[Dictionary]:
		var out: Array[Dictionary] = []
		for e in events:
			if e["name"] == n and (id < 0 or int((e["args"] as Array)[0]) == id):
				out.append(e)
		return out

	func first(n: StringName, id: int = -1) -> Dictionary:
		var l := of(n, id)
		return l[0] if not l.is_empty() else {}

	func has(n: StringName, id: int = -1) -> bool:
		return not of(n, id).is_empty()

	## Names of the events of one id in order, without the informational ones (destination_ready, tempo_changed).
	func seq(id: int) -> Array:
		var out: Array = []
		for e in events:
			var n: StringName = e["name"]
			if n == &"destination_ready" or n == &"tempo_changed":
				continue
			if int((e["args"] as Array)[0]) == id:
				out.append(n)
		return out

	func index_of(n: StringName, id: int) -> int:
		for i in events.size():
			if events[i]["name"] == n and int((events[i]["args"] as Array)[0]) == id:
				return i
		return -1


## ---------------------------------------------------------------- helpers

static func _d(node: String, extra: Dictionary = {}) -> Dictionary:
	var d: Dictionary = {"id": "main/" + node, "path": "main", "node": node, "kind": &"scene", "quest": "", "when": &"lap_end"}
	d.merge(extra, true)
	return d


static func _new(factory: Callable, opts: Dictionary = {}) -> Dictionary:
	var o: Dictionary = OPTS.duplicate()
	o.merge(opts, true)
	var rig: Dictionary = factory.call(o)
	rig["rec"] = Rec.new(rig["port"])
	return rig


static func _sw(rig: Dictionary, name: StringName, value: Variant) -> bool:
	if not rig.has("switch"):
		return false
	return bool((rig["switch"] as Callable).call(name, value))


static func _skip(case_name: String, reason: String) -> void:
	skipped.append(case_name)
	print("PortConformance SKIP %s: %s" % [case_name, reason])


static func _step(rig: Dictionary, dt: float = STEP) -> void:
	(rig["advance"] as Callable).call(dt)


static func _port(rig: Dictionary) -> TransitionPort:
	return rig["port"]


static func _rec(rig: Dictionary) -> Rec:
	return rig["rec"]


static func _lap_s(rig: Dictionary) -> float:
	return 64.0 * _port(rig).beat_s()


## Advance until pred is true; false when max_s of clock time passed first.
static func _until(rig: Dictionary, pred: Callable, max_s: float, dt: float = STEP) -> bool:
	var port := _port(rig)
	var t0 := port.song_time()
	while port.song_time() - t0 < max_s:
		if pred.call():
			return true
		_step(rig, dt)
	return pred.call()


static func _until_event(rig: Dictionary, n: StringName, id: int, max_laps: float = 8.0, dt: float = STEP) -> bool:
	var rec := _rec(rig)
	return _until(rig, func() -> bool: return rec.has(n, id), max_laps * _lap_s(rig), dt)


static func _until_time(rig: Dictionary, t: float) -> void:
	var port := _port(rig)
	while port.song_time() < t - 1e-9:
		_step(rig, minf(STEP, t - port.song_time()))


## ---------------------------------------------------------------- 1

static func case_01_lifecycle(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var blended := _sw(r, &"blend_beats", 8)
	var id := port.request(_d("a"))
	t.assert_true(id > 0, "request returns a positive id")
	var acks := rec.of(&"request_acknowledged", id)
	t.assert_eq(acks.size(), 1, "acknowledged before request() returned")
	if acks.size() == 1:
		t.assert_eq((acks[0]["args"] as Array)[1], true, "accepted")
		t.assert_eq((acks[0]["args"] as Array)[2], &"", "no reason on accept")
	t.assert_eq(port.state(), TransitionPort.State.PENDING)
	var cur := port.current()
	t.assert_eq(int(cur.get("id", -1)), id, "current() names the request")
	t.assert_eq(str((cur.get("dest", {}) as Dictionary).get("id", "")), "main/a")
	t.assert_true(port.selection_open(), "selection open while pending")
	var nb := port.next_boundary_t()
	var lt := port.lock_t(nb)
	t.assert_true(nb < INF and lt < nb and lt > port.song_time(), "boundary and lock point lie ahead")
	t.assert_true(_until_event(r, &"completed", id), "completed arrives")
	t.assert_eq(rec.seq(id), [&"request_acknowledged", &"locked", &"switched", &"completed"], "order, one id")
	var lk := rec.first(&"locked", id)
	var sw := rec.first(&"switched", id)
	var co := rec.first(&"completed", id)
	if lk.is_empty() or sw.is_empty() or co.is_empty():
		return
	var la: Array = lk["args"]
	var plan: Dictionary = la[3]
	t.assert_near(float(lk["t"]), lt, EPS, "locked at the lock point")
	t.assert_near(float(la[2]), nb, 1e-6, "locked boundary is the announced next boundary")
	t.assert_eq(str((la[1] as Dictionary)["id"]), "main/a", "locked dest")
	t.assert_false(bool(lk["open"]), "selection closed from the lock")
	t.assert_eq(int(lk["state"]), TransitionPort.State.LOCKED)
	t.assert_true(plan.get("mode", &"") in [&"blend", &"halftime_blend", &"echo_out", &"cut"], "plan mode is one of four")
	t.assert_true(float(plan.get("complete_t", -1.0)) >= nb, "plan.complete_t not before the boundary")
	var sa: Array = sw["args"]
	t.assert_eq((sa[1] as Dictionary).get("id"), "main/a", "landed on the destination")
	t.assert_false(bool((sa[1] as Dictionary).get("fallback", false)), "not a fallback")
	t.assert_near(float(sa[2]), nb, EPS, "switched at the boundary")
	t.assert_true(float(sw["t"]) >= float(lk["t"]), "switched after locked")
	t.assert_true(rec.index_of(&"switched", id) < rec.index_of(&"completed", id), "completed after switched")
	t.assert_true(float(co["t"]) >= float(sw["t"]), "completed not before switched in time")
	if blended:
		t.assert_true(float(co["t"]) > float(sw["t"]), "with a blend, completed comes later than switched")
		t.assert_near(float(co["t"]), float(plan["complete_t"]), EPS, "completed at plan.complete_t")


## ---------------------------------------------------------------- 2

static func case_02_replace(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var a := port.request(_d("a"))
	_step(r, 1.0)
	var b := port.request(_d("b"))
	t.assert_true(a > 0 and b > a, "ids increase")
	var closed := rec.of(&"request_closed", a)
	t.assert_eq(closed.size(), 1, "old request closed once")
	if closed.size() == 1:
		t.assert_eq((closed[0]["args"] as Array)[1], &"replaced")
	t.assert_true(rec.index_of(&"request_closed", a) >= 0 and rec.index_of(&"request_closed", a) < rec.index_of(&"request_acknowledged", b),
		"closed(old, replaced) is emitted before acknowledged(new) (lead's ruling, 6 Nov 2026)")
	var acks := rec.of(&"request_acknowledged", b)
	t.assert_eq(acks.size(), 1, "new request acknowledged")
	if acks.size() == 1:
		t.assert_eq((acks[0]["args"] as Array)[1], true)
	t.assert_eq(int(port.current().get("id", -1)), b, "the slot holds the new request")
	t.assert_false(port.cancel(a), "the replaced id can no longer be cancelled")
	t.assert_true(_until_event(r, &"completed", b), "new request completes")
	t.assert_eq(rec.of(&"locked").size(), 1, "exactly one lock")
	t.assert_false(rec.has(&"locked", a), "the replaced id never locks")
	t.assert_false(rec.has(&"switched", a), "the replaced id never switches")
	t.assert_eq(str((rec.first(&"locked", b)["args"] as Array)[1]["id"]), "main/b")


## ---------------------------------------------------------------- 3

static func case_03_cancel_before_lock(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var dflt := _d("dflt")
	port.set_default(dflt)
	var id := port.request(_d("a"))
	_step(r, 1.0)
	t.assert_true(port.cancel(id), "cancel on the pending id returns true")
	t.assert_eq(rec.of(&"request_closed", id).size(), 1)
	t.assert_eq((rec.first(&"request_closed", id)["args"] as Array)[1], &"cancelled")
	t.assert_eq(port.state(), TransitionPort.State.NONE, "slot empty")
	t.assert_false(port.cancel(id), "second cancel returns false")
	t.assert_true(_until_event(r, &"switched", -1), "the scene's default applies")
	var locks := rec.of(&"locked")
	t.assert_eq(locks.size(), 1, "one lock only")
	if locks.size() == 1:
		var la: Array = locks[0]["args"]
		t.assert_true(int(la[0]) != id and int(la[0]) > id, "default locks under a fresh id")
		t.assert_eq(str((la[1] as Dictionary)["id"]), "main/dflt")
		t.assert_near(float(la[2]), 4.0 * _lap_s(r), 1e-3, "at the end of the final (fourth) lap")
	t.assert_false(rec.has(&"locked", id), "cancelled id never locks")


## ---------------------------------------------------------------- 4

static func case_04_refused_after_lock(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	_sw(r, &"blend_beats", 8)
	var id := port.request(_d("a"))
	t.assert_true(_until_event(r, &"locked", id), "locks")
	t.assert_false(port.cancel(id), "cancel after the lock returns false")
	t.assert_eq(port.state(), TransitionPort.State.LOCKED, "cancel changed nothing")
	t.assert_false(port.selection_open(), "selection closed while locked")
	var n_before := rec.events.size()
	var id2 := port.request(_d("b"))
	t.assert_eq(id2, 0, "request after the lock returns 0")
	t.assert_eq(port.last_refusal(), &"locked")
	t.assert_eq(rec.events.size(), n_before + 1, "exactly one signal for the refusal")
	var ack: Dictionary = rec.events[rec.events.size() - 1]
	t.assert_eq(ack["name"], &"request_acknowledged")
	t.assert_eq(ack["args"], [0, false, &"locked"], "acknowledged(0, false, locked)")
	t.assert_eq(int(port.current().get("id", -1)), id, "the locked transition is untouched")
	t.assert_true(_until_event(r, &"completed", id), "locked transition completes")
	t.assert_false(rec.has(&"request_closed", id), "never closed")
	t.assert_eq((rec.first(&"switched", id)["args"] as Array)[1]["id"], "main/a", "lands on A")
	t.assert_eq(rec.of(&"locked").size(), 1, "no lock for the refused request")
	t.assert_true(port.state() != TransitionPort.State.LOCKED, "slot free again")


## ---------------------------------------------------------------- 5

static func case_05_request_off_departure_lap(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var lap := _lap_s(r)
	_step(r, 0.5)
	var id := port.request(_d("a"))
	var nb := port.next_boundary_t()
	t.assert_true(nb >= 2.0 * lap - EPS, "the first boundary of a scene is not the end of lap one")
	_until_time(r, lap + 2.0)
	t.assert_false(rec.has(&"locked"), "nothing locked on the first lap")
	t.assert_eq(port.state(), TransitionPort.State.PENDING, "still pending past the end of lap one")
	t.assert_eq(int(port.current().get("id", -1)), id)
	for e in rec.of(&"deferred"):
		# Tolerated, not required (the mock has no lock point on a lap that is not a departure lap).
		t.assert_eq((e["args"] as Array)[2], &"doors_closed", "only doors_closed may be deferred here")
	t.assert_true(_until_event(r, &"locked", id), "locks on a departure lap")
	var lk := rec.first(&"locked", id)
	t.assert_near(float((lk["args"] as Array)[2]), nb, 1e-6, "on the first departure boundary")
	t.assert_true(_until_event(r, &"switched", id), "switches")
	t.assert_eq(rec.of(&"locked").size(), 1)


## ---------------------------------------------------------------- 6

static func case_06_default_locks(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	# Lead's ruling, 6 Nov 2026: a scene entry clears the default, so it is set again on every scene (begin_scene).
	port.set_default(_d("dflt"))
	t.assert_eq(port.state(), TransitionPort.State.NONE)
	t.assert_true(_until_event(r, &"completed", -1), "default transition completes")
	var locks := rec.of(&"locked")
	t.assert_eq(locks.size(), 1, "one lock")
	if locks.size() != 1:
		return
	var la: Array = locks[0]["args"]
	var id := int(la[0])
	t.assert_true(id > 0, "fresh id")
	t.assert_eq(str((la[1] as Dictionary)["id"]), "main/dflt")
	t.assert_near(float(la[2]), 4.0 * _lap_s(r), 1e-3, "final lap boundary")
	t.assert_eq(rec.seq(id), [&"request_acknowledged", &"locked", &"switched", &"completed"],
		"acknowledged then locked, then the usual")
	t.assert_eq((rec.first(&"request_acknowledged", id)["args"] as Array)[1], true)
	t.assert_eq((rec.first(&"switched", id)["args"] as Array)[1]["id"], "main/dflt")


## ---------------------------------------------------------------- 7

static func case_07_empty_default_stays(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var lap := _lap_s(r)
	# Lead's ruling, 6 Nov 2026: a final lap with an empty default is extended by one lap without any signal.
	port.set_default({})
	# Find the final lap's boundary: the scene has 4 laps.
	_until_time(r, 3.0 * lap + 1.0)
	var nb := port.next_boundary_t()
	t.assert_near(nb, 4.0 * lap, 1e-3, "the final boundary is announced")
	_until_time(r, nb + 2.0)
	t.assert_false(rec.has(&"locked"), "nothing locks with an empty default")
	t.assert_false(rec.has(&"switched"), "the scene goes on")
	t.assert_eq(port.state(), TransitionPort.State.NONE)
	var nb2 := port.next_boundary_t()
	t.assert_near(nb2, nb + lap, 1e-3, "next_boundary_t moved one lap")
	t.assert_true(port.selection_open(), "selection still open")
	# The extra lap is now the final one: a default set now is taken at its end.
	port.set_default(_d("late"))
	t.assert_true(_until_event(r, &"switched", -1), "default taken after the extra lap")
	var locks := rec.of(&"locked")
	t.assert_eq(locks.size(), 1)
	if locks.size() == 1:
		t.assert_near(float((locks[0]["args"] as Array)[2]), nb2, 1e-3, "at the end of the extra lap")


## ---------------------------------------------------------------- 8

static func case_08_unavailable(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	if not _sw(r, &"fail_load_ids", ["main/bad"] as Array[String]):
		_skip("case_08_unavailable", "factory cannot make a destination fail to load")
		return
	var id := port.request(_d("bad"))
	# Lead's ruling, 6 Nov 2026: either refused at once (id 0) or acknowledged and closed later is allowed.
	if id == 0:
		# Also allowed by transition_port.gd: refused at once.
		t.assert_eq(port.last_refusal(), &"unavailable")
		t.assert_true(rec.has(&"request_acknowledged", 0))
	else:
		_until(r, func() -> bool: return rec.has(&"request_closed", id), 2.0)
		var cl := rec.first(&"request_closed", id)
		t.assert_false(cl.is_empty(), "closed")
		if not cl.is_empty():
			t.assert_eq((cl["args"] as Array)[1], &"unavailable")
			t.assert_true(float(cl["t"]) < port.next_boundary_t() - 20.0, "well before the lock")
	t.assert_false(rec.has(&"locked"), "never locks")
	t.assert_eq(port.state(), TransitionPort.State.NONE, "state back to NONE")
	t.assert_true(port.current().is_empty(), "slot empty")
	var good := port.request(_d("good"))
	t.assert_true(good > id, "the next request gets a fresh, larger id")
	t.assert_true(_until_event(r, &"completed", good), "the next request works")
	t.assert_eq((rec.first(&"switched", good)["args"] as Array)[1]["id"], "main/good")
	t.assert_false(rec.has(&"switched", id), "the failed id never switches")


## ---------------------------------------------------------------- 9

static func case_09_not_ready_defers_once(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	if not _sw(r, &"not_ready_ids", ["main/slow"] as Array[String]):
		_skip("case_09_not_ready_defers_once", "factory cannot make a destination not ready")
		return
	var id := port.request(_d("slow"))
	var nb := port.next_boundary_t()
	var lap := _lap_s(r)
	t.assert_true(_until_event(r, &"deferred", id), "deferred at the lock point")
	var df := rec.first(&"deferred", id)
	if df.is_empty():
		return
	var da: Array = df["args"]
	t.assert_eq(da[2], &"not_ready")
	t.assert_near(float(df["t"]), port.lock_t(nb), EPS, "at the lock point of the first boundary")
	t.assert_true(float(da[1]) > nb and float(da[1]) <= nb + lap + 1e-3, "retried at most one lap later")
	t.assert_eq(port.state(), TransitionPort.State.PENDING, "request stays pending")
	t.assert_eq(int(port.current().get("id", -1)), id)
	t.assert_false(rec.has(&"locked"), "not locked yet")
	t.assert_true(_until_event(r, &"completed", id), "then completes")
	t.assert_eq(rec.of(&"deferred", id).size(), 1, "deferred exactly once")
	t.assert_eq(rec.seq(id), [&"request_acknowledged", &"deferred", &"locked", &"switched", &"completed"])
	var la: Array = rec.first(&"locked", id)["args"]
	t.assert_near(float(la[2]), float(da[1]), 1e-6, "locks at the announced next boundary")
	t.assert_eq((la[3] as Dictionary).get("mode"), &"cut", "forced cut")
	t.assert_eq((la[3] as Dictionary).get("blend_beats"), 0, "no blend in a cut")
	t.assert_eq((la[1] as Dictionary)["id"], "main/slow", "still the requested destination")


## ---------------------------------------------------------------- 10

static func case_10_failure_after_lock(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	if not _sw(r, &"fail_after_lock_ids", ["main/doomed"] as Array[String]):
		_skip("case_10_failure_after_lock", "factory cannot make a destination fail after the lock")
		return
	_sw(r, &"blend_beats", 8)
	var id := port.request(_d("doomed"))
	t.assert_true(_until_event(r, &"completed", id), "completed still fires")
	t.assert_eq(rec.seq(id), [&"request_acknowledged", &"locked", &"switched", &"completed"])
	var lk := rec.first(&"locked", id)
	var sw := rec.first(&"switched", id)
	if lk.is_empty() or sw.is_empty():
		return
	t.assert_eq(((lk["args"] as Array)[1] as Dictionary)["id"], "main/doomed", "the lock named the destination")
	var landed: Dictionary = (sw["args"] as Array)[1]
	t.assert_eq(landed.get("fallback", false), true, "landed carries fallback == true")
	t.assert_true(landed.has("id") and landed["id"] != "main/doomed", "landed is a scene really entered, not the failed one")
	t.assert_near(float((sw["args"] as Array)[2]), float((lk["args"] as Array)[2]), EPS, "still at the boundary")
	t.assert_eq(rec.of(&"completed", id).size(), 1)


## ---------------------------------------------------------------- 11

static func case_11_on_miss(t: TestCase, factory: Callable) -> void:
	for missed in [false, true]:
		var r := _new(factory)
		var port := _port(r)
		var rec := _rec(r)
		if not _sw(r, &"miss_last_block", missed):
			_skip("case_11_on_miss", "factory cannot stage a missed last block")
			return
		var id := port.request(_d("hit", {"on_miss": _d("miss")}))
		t.assert_true(_until_event(r, &"completed", id), "completes (missed=%s)" % str(missed))
		var expect := "main/miss" if missed else "main/hit"
		var lk := rec.first(&"locked", id)
		t.assert_false(lk.is_empty())
		if lk.is_empty():
			continue
		t.assert_eq(((lk["args"] as Array)[1] as Dictionary)["id"], expect, "locked dest (missed=%s)" % str(missed))
		t.assert_eq(((rec.first(&"switched", id)["args"] as Array)[1] as Dictionary)["id"], expect, "landed (missed=%s)" % str(missed))
		t.assert_eq(rec.of(&"locked").size(), 1, "one lock")


## ---------------------------------------------------------------- 12

static func case_12_soonest(t: TestCase, factory: Callable) -> void:
	# NOT in the contract: how long a block is. The case only needs that a block boundary exists inside a lap, so it
	# asserts "at least a lock lead away" and "sooner than the end of the lap", for several moments in the lap.
	for offset_beats: float in [10.0, 13.0, 13.9, 14.5, 30.2]:
		var r := _new(factory)
		var port := _port(r)
		var rec := _rec(r)
		var nb0 := port.next_boundary_t()
		var beat := port.beat_s()
		var t_req := nb0 - _lap_s(r) + offset_beats * beat
		_until_time(r, t_req)
		var id := port.request(_d("a", {"when": &"soonest"}))
		var t_at := port.song_time()
		t.assert_true(id > 0)
		t.assert_true(_until_event(r, &"completed", id), "completes (offset %.1f)" % offset_beats)
		var lk := rec.first(&"locked", id)
		if lk.is_empty():
			continue
		var b := float((lk["args"] as Array)[2])
		t.assert_true(b >= t_at + 3.5 * beat - 1e-6, "boundary leaves a full lock lead (offset %.1f)" % offset_beats)
		t.assert_true(b < nb0 - beat, "boundary is sooner than the lap's end (offset %.1f)" % offset_beats)
		t.assert_true(float(lk["t"]) >= t_at - 1e-6 and float(lk["t"]) <= b - 3.4 * beat, "locked a lead before it")
		t.assert_near(float((rec.first(&"switched", id)["args"] as Array)[2]), b, EPS, "switched at that boundary")
		t.assert_near(float(rec.first(&"switched", id)["lap_beat"]), 0.0, 1e-3, "new scene starts at beat 0")


## ---------------------------------------------------------------- 13

static func case_13_clock_and_tempo(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var specs: Dictionary = {
		"main/b": {"bpm": 140.0, "laps": 2, "doors_from_lap": 1},
		"main/c": {"bpm": 140.0, "laps": 2, "doors_from_lap": 1},
		"main/d": {"bpm": 174.0, "laps": 2, "doors_from_lap": 1},
	}
	var tempo_ok := _sw(r, &"scene_specs", specs)
	if not tempo_ok:
		_skip("case_13_clock_and_tempo (tempo part)", "factory cannot give scenes another tempo")
	var prev := port.song_time()
	var went_back := false
	var bad_beat := false
	var ids: Array[int] = []
	for node in ["b", "c", "d"]:
		var id := port.request(_d(node))
		ids.append(id)
		var guard := 0
		while not rec.has(&"completed", id) and guard < 20000:
			guard += 1
			_step(r)
			var now := port.song_time()
			if now < prev:
				went_back = true
			prev = now
			var lb := port.lap_beat()
			if lb < 0.0 or lb >= 64.0:
				bad_beat = true
		t.assert_true(rec.has(&"completed", id), "transition to %s completes" % node)
		var sw := rec.first(&"switched", id)
		if not sw.is_empty():
			t.assert_near(float(sw["lap_beat"]), 0.0, 1e-3, "lap_beat() is 0 at switched (%s)" % node)
	t.assert_false(went_back, "song_time never decreased")
	t.assert_false(bad_beat, "lap_beat stayed within [0, 64)")
	if not tempo_ok:
		return
	var tempos := rec.of(&"tempo_changed")
	t.assert_eq(tempos.size(), 2, "tempo_changed only when the tempo differs (174 -> 140, 140 -> 140 none, 140 -> 174)")
	if tempos.size() == 2:
		var ta: Array = tempos[0]["args"]
		t.assert_near(float(ta[0]), 140.0, 1e-6)
		t.assert_near(float(ta[1]), 60.0 / 140.0, 1e-6, "beat_s argument")
		var sw_b := rec.first(&"switched", ids[0])
		t.assert_near(float(ta[2]), float((sw_b["args"] as Array)[2]), EPS, "at the switch of b")
		var ti := rec.events.find(tempos[0])
		t.assert_true(ti >= 0 and ti + 1 < rec.events.size() and rec.events[ti + 1]["name"] == &"switched",
			"tempo_changed is emitted directly before switched (lead's ruling, 6 Nov 2026)")
		t.assert_near(float((tempos[1]["args"] as Array)[0]), 174.0, 1e-6)
		var sw_d := rec.first(&"switched", ids[2])
		t.assert_near(float((tempos[1]["args"] as Array)[2]), float((sw_d["args"] as Array)[2]), EPS, "at the switch of d")
	t.assert_near(port.bpm(), 174.0, 1e-6, "bpm() follows the scene")
	t.assert_near(port.beat_s(), 60.0 / 174.0, 1e-6, "beat_s() follows the scene")


## ---------------------------------------------------------------- 14

static func case_14_blending_defers(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	# Lead's ruling, 6 Nov 2026: a &"blending" deferral may repeat until the blend has completed.
	# 250 beats is longer than the two to three laps of the next scene before its lock points.
	if not _sw(r, &"blend_beats", 250):
		_skip("case_14_blending_defers", "factory cannot set a long blend")
		return
	var a := port.request(_d("a"))
	t.assert_true(_until_event(r, &"switched", a), "first transition switches")
	var b := port.request(_d("b"))
	t.assert_true(b > a)
	t.assert_false(rec.has(&"completed", a), "the blend of the first is still running")
	t.assert_true(_until_event(r, &"locked", b, 12.0), "the second eventually locks")
	var defs := rec.of(&"deferred", b)
	t.assert_true(defs.size() >= 1, "at least one deferral while blending")
	var first_complete := rec.first(&"completed", a)
	t.assert_false(first_complete.is_empty(), "the first completed before the second locked")
	var lk := rec.first(&"locked", b)
	for d in defs:
		var da: Array = d["args"]
		t.assert_eq(da[2], &"blending", "deferral reason")
		t.assert_true(float(da[1]) > float(d["t"]), "next boundary lies ahead")
		if not first_complete.is_empty():
			t.assert_true(float(d["t"]) < float(first_complete["t"]) + EPS, "deferred only while the blend ran")
	if not first_complete.is_empty() and not lk.is_empty():
		t.assert_true(rec.index_of(&"completed", a) < rec.index_of(&"locked", b), "completed(first) before locked(second)")
		t.assert_true(float(lk["t"]) >= float(first_complete["t"]) - EPS, "no lock before the first completed")
	var plan_a: Dictionary = (rec.first(&"locked", a)["args"] as Array)[3]
	if not first_complete.is_empty():
		t.assert_near(float(first_complete["t"]), float(plan_a["complete_t"]), EPS, "completed at plan.complete_t")
	t.assert_true(_until_event(r, &"completed", b, 12.0), "the second completes too")


## ---------------------------------------------------------------- 15

static func case_15_ids_increase(t: TestCase, factory: Callable) -> void:
	var r := _new(factory)
	var port := _port(r)
	var rec := _rec(r)
	var last_id := 0
	var seen := {}
	var stale := 0
	var ok_all := true
	for i in 10:
		var from_idx := rec.events.size()
		var id := port.request(_d("n%d" % i))
		var allowed: Array[int] = [id]
		if i % 3 == 0:
			_step(r, 0.5)
			var id2 := port.request(_d("m%d" % i))
			t.assert_true(id2 > id, "replacement id is larger")
			allowed.append(id2)
			id = id2
		t.assert_true(id > last_id, "request %d: id %d greater than %d" % [i, id, last_id])
		t.assert_false(seen.has(id), "id never reused")
		seen[id] = true
		last_id = id
		if not _until_event(r, &"completed", id, 8.0, 0.1):
			ok_all = false
			t.assert_true(false, "transition %d completes" % i)
			break
		for k in range(from_idx, rec.events.size()):
			var e: Dictionary = rec.events[k]
			if e["name"] == &"tempo_changed":
				continue
			if not allowed.has(int((e["args"] as Array)[0])):
				stale += 1
	t.assert_eq(stale, 0, "no signal carried an id of another transition")
	if ok_all:
		var lock_ids: Array[int] = []
		for e in rec.of(&"locked"):
			lock_ids.append(int((e["args"] as Array)[0]))
		t.assert_eq(lock_ids.size(), 10, "ten locks")
		for k in range(1, lock_ids.size()):
			t.assert_true(lock_ids[k] > lock_ids[k - 1], "lock ids strictly increase")
		var closed := rec.of(&"request_closed")
		t.assert_eq(closed.size(), 4, "four replaced requests closed (i = 0, 3, 6, 9)")
		for e in closed:
			t.assert_eq((e["args"] as Array)[1], &"replaced")
