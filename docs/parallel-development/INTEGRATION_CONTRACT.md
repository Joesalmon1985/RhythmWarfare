# Integration contract

The single interface between the narrative / interaction side (the narrative stream) and the music side (the
music stream). The two streams are subagents of one lead session, each in its own git worktree on one Windows PC
(`ONE_PC_PLAN.md` section 4). Both implement against this file and against `contract/transition_port.gd`, which
is the same contract as code. If the two ever disagree, `transition_port.gd` wins and this file is corrected.

Contract version: 1. The clarifications at the end of this file (6 November 2026) narrow version 1 and do not
change it.

## 1. The four parts and what they map to in the repository

| Conceptual part | In this repository | Owner |
|---|---|---|
| InteractionManager: visible objects, taps, the pending pick, feedback | `RunHotspots` (`src/run/run_hotspots.gd`), `HotspotView` (`src/run/hotspot_view.gd`), `hotspot_contract.gd`, the input path in `RunPlay` | narrative stream |
| NarrativeGraph / QuestRouter: valid destinations, quest entry and exit, return checkpoints, saved route state | new: `src/narrative/` (`NarrativeGraph`, `QuestRouter`, `RouteState`), data in `content/narrative/`, saved through `Session.run_progress` | narrative stream |
| MusicalTransitionDirector: turns a requested destination into a transition at a musical boundary | new: `src/transition/transition_director.gd` (`TransitionDirector extends TransitionPort`), fed by `RunEngine` events | music stream |
| AdaptiveMusicTransport: playback, stems, tempo matching, crossfades, the clock | `RunAudio` (`src/run/run_audio.gd`), `SongClock`, `StemTransport`, `TrackTransport`, new code under `src/music/` | music stream |

`TransitionPort` (`src/transition/transition_port.gd`, copied from `contract/transition_port.gd` in stage 0.3
of the plan) is the only thing both sides see. Narrative code never calls `RunAudio`, `TrackTransport` or anything under `src/music/`.
Music code never reads `QuestRouter`, `RouteState`, `RunHotspots` or the save. There is no other shared
state: no new autoload, no shared global, no reaching through `RunPlay` fields.

`RunEngine` stays the keeper of time inside a scene (64-beat laps, blocks, decision beats). The director
does not replace it: it listens to the engine's events and drives the engine's existing choice API. That
mapping is in section 7 and is the director's private business.

## 2. Vocabulary

- **Scene**: one node of a run (`warehouse.bar`, `jordan`). A scene lasts one or more 64-beat **laps**.
- **Boundary**: the downbeat at the end of a lap at which the scene may be left. Its time is a song time in
  seconds.
- **Lock point**: the moment before a boundary after which the transition is fixed. Today it is 3.5 beats
  before the boundary (the engine's block decision at beat 60.5). The music side may move it earlier to get
  a longer run-in. Callers always ask `lock_t(boundary_t)` and never assume a number of beats.
- **Departure lap**: a lap whose end is a boundary. For a track scene these are laps from `doors_from_lap`
  on; for an ordinary scene, its last lap.
- **Selection is open**: `selection_open()` is true. The target (`docs/parallel-development/INTERACTION_DESIGN.md`) is that this covers at least 80% of active play: from the scene's first beat until
  each lock point, including laps that are not departure laps. A request made on a lap that is not a
  departure lap simply stays pending.

## 3. Destination

A `Dictionary` built only by `QuestRouter`:

| Key | Type | Meaning |
|---|---|---|
| `id` | String | Graph node id, `"<path>/<node>"`: `"main/warehouse.bar"`, `"gospel/jordan"`, `"bassment/<passage id>"`. Required. |
| `path` | String | `"main"`, a path id (`gospel`, `squadron`, `ember`) or `"bassment"`. Required. |
| `node` | String | Node id inside that path. Required. |
| `kind` | StringName | `&"scene"` (same path), `&"quest_entry"`, `&"quest_return"`. Required. |
| `quest` | String | Quest id for the two quest kinds, else `""`. |
| `when` | StringName | `&"lap_end"` (default) or `&"soonest"` (the next block boundary that still leaves a full lock lead; used by the Bassment entrance). |
| `on_miss` | Dictionary | Optional second destination of the same shape (without its own `on_miss`), taken when the lap's last block is missed. Quest entries and quest returns never have one: they are not gated by rhythm. |
| `fallback` | bool | Set only by the director on a `landed` dictionary. |

The music side uses `path` and `node` to find the destination's music (`RunTrackScenes.plan_of`, the scene's
loops) and `kind` to choose a transition style. It treats every other key as opaque.

## 4. Life of a request

```
            request()                      lock point                boundary              outgoing silent
  NONE ────────────────▶ PENDING ─────────────────────▶ LOCKED ───────────────▶ SWITCHED ───────────────▶ COMPLETED
                          │  ▲                                        (signal switched)        (signal completed)
        cancel / replaced │  │ deferred (stays pending,
        / unavailable     ▼  │ tried at the next boundary)
                        CLOSED
```

Rules, each of which is a test case in section 9:

1. **One slot.** At most one request is PENDING or LOCKED. `request()` while PENDING replaces it: the old id
   gets `request_closed(old, &"replaced")`, the new one `request_acknowledged(new, true, &"")`.
2. **Ids** are positive, strictly increasing for the life of the port, and never reused. Every signal
   carries the id. A consumer ignores a signal whose id is not the one it is waiting for.
3. **Acknowledgement is synchronous**: `request_acknowledged` is emitted before `request()` returns.
4. **Changing one's mind is free** until the lock. Nothing audible or visible that is specific to a
   destination may happen before `locked`, except the selected object's own feedback (narrative side) and
   silent preparation (music side). A build-up that does not depend on the destination is allowed.
5. **Cancel**: `cancel(id)` on the pending id closes it with `&"cancelled"` and returns true. After the
   lock it returns false and changes nothing.
6. **Lock**: at `lock_t(boundary_t)` of a departure lap, if a request is PENDING and the director can go,
   it emits `locked(id, dest, boundary_t, plan)` exactly once. `dest` is the request's destination or its
   `on_miss`. From here `request()` returns 0 with `&"locked"` until `switched`.
7. **Defer**: if a request is PENDING at a lock point but the director cannot go, it emits
   `deferred(id, next_boundary_t, reason)` and the request stays PENDING. The music side may defer for
   `&"not_ready"` at most once per request; at the following lock it must lock, with `plan.mode == &"cut"`
   if need be. Music never blocks a transition for longer than one lap.
8. **Default**: on the final lap of a scene with nothing pending, the director locks the destination given
   to `set_default()` under a fresh id (signals `request_acknowledged` then `locked`). If the default is
   `{}` the scene goes on for another lap.
9. **Switch**: when `song_time()` reaches `boundary_t` the scene changes and `switched(id, landed, t)` is
   emitted exactly once per `locked`, in the frame the new scene starts. `landed` equals the locked `dest`
   unless the destination failed after the lock, in which case it is the scene really entered with
   `landed["fallback"] == true`.
10. **Complete**: `completed(id)` is emitted exactly once after `switched`, when the outgoing music is
    silent. It must come before the incoming track's first drop
    (`docs/parallel-development/MUSIC_TRANSITIONS.md`). A new request may be made before `completed`, but no new lock happens until it.
11. **No duplicates**: there is never a second `locked` for the same boundary, nor a `locked` while another
    id is LOCKED.

## 5. Route state is transactional

`RouteState` (current mainline location, current quest, quest entry origin, return checkpoint, per-quest
progress, route history) has a committed copy, which is what is saved, and at most one pending change.

- `QuestRouter` computes the change when it builds a destination and holds it against the request id.
- The change is applied and saved **only in the handler of `switched`**, from `landed`, not from what was
  asked for. If `landed["fallback"]` is true the router recomputes the change for the scene really entered.
- `request_closed` and `deferred` discard or keep the pending change; they never touch the committed copy.
- The save is written atomically (write a temporary file, then rename).
- Consequence for existing code: effects that are persisted at the lock today (a `keep:` flag is saved at
  beat 60.5) move to `switched`. Energy and in-run flags that are part of the block's result stay where
  they are; they are gameplay results, not route state.

A destination that cannot be loaded is found out **before** the lock: the director validates and loads on
`request()`, and closes the request with `&"unavailable"` if that fails. The narrative side then deselects
the object and shows its refused state. After the lock a failure is a defect, handled by failing forward to
`landed` so the player is never stranded and the saved state matches where they are.

## 6. Plan (the fourth argument of `locked`)

| Key | Type | Meaning |
|---|---|---|
| `mode` | StringName | `&"blend"`, `&"halftime_blend"`, `&"echo_out"` or `&"cut"`. |
| `fallback` | bool | True when the mode was forced by missing metadata or unready audio. |
| `outgoing_bpm`, `incoming_bpm` | float | Tempos of the two scenes. |
| `blend_beats` | int | Beats of the incoming scene over which the outgoing music fades; 0 for a cut. |
| `complete_t` | float | Song time by which `completed` will have fired. |

The narrative side may use `mode` and `blend_beats` to time visuals. It must work for every mode, and must
not depend on a plan being anything other than `&"cut"`.

## 7. How the director sits on the existing engine (music side's private mapping)

| Contract | Existing code it rides on |
|---|---|
| `request()` | `RunHotspots.select_route` / `RunEngine.choose` for destinations in the same run; a held destination for quest entries and returns, applied at the lock |
| lock point | the block decision at beat 60.5 of a departure lap: events `hotspot_commit`, and `track_last_lap` on an open lap of a track scene |
| `deferred` | `RunEngine.hold` / `track_extend`: the scene goes on for one more lap |
| `switched` | `route_commit` then `phase_start` of the new scene; for another path, `path_handoff` and `RunPlay._path_swap`; for a return, the `RunEngine.resume` route |
| `completed` | new: reported by `RunAudio` when the outgoing group has faded |
| `tempo_changed` | the engine's `tempo` event |
| clock | `SongClock` through `RunPlay`; `lap_beat()` from `RunEngine` |

The first deliverable of the music stream (milestone M1) installs this seam with `mode` always `&"cut"`,
which reproduces today's behaviour exactly. Everything after M1 on the music side happens behind it.

## 8. The mock

`tests/mocks/mock_transition_director.gd`, `class_name MockTransitionDirector extends TransitionPort`, owned
by the narrative stream. No audio, no engine. Status on 6 November 2026: it is written (work package N1.4).

- `MockTransitionDirector.new(bpm := 174.0, laps := 4, doors_from_lap := 2, lock_lead_beats := 3.5)`
- `advance(dt: float)` moves `song_time()` and emits every signal the real director would, in order.
- `begin_scene(dest: Dictionary, bpm: float, laps: int, doors_from_lap: int)` is called by the mock itself
  on a switch, and by a test to set the first scene.
- Switches for failure cases: `fail_load_ids: Array[String]` (those destinations close as `&"unavailable"`),
  `not_ready_ids: Array[String]` (deferred once with `&"not_ready"`), `fail_after_lock_ids: Array[String]`
  (land on `fallback_dest` with `fallback = true`), `blend_beats: int` (delay before `completed`),
  `miss_last_block: bool` (take `on_miss`).
- `log: Array[Dictionary]`: every signal emitted, `{signal, args, t}`, for assertions.

## 9. Conformance cases

`tests/port_conformance.gd` (owned by the narrative stream; a plain script with one function per case taking a factory that
returns a `TransitionPort` and a way to advance time). `tests/test_port_mock.gd` runs it on the mock. At
integration (stage X1) `tests/test_port_real.gd` runs the same cases on the real director with a virtual clock.
Status on 6 November 2026: the cases and the mock test are written; the real-director test is not.

1. request, lock, switch, complete, in that order, with one id.
2. replace before the lock: old id closed `&"replaced"`, only the new one locks.
3. cancel before the lock: no `locked`; the scene's default applies on the final lap.
4. cancel and request after the lock are refused; the locked transition still completes.
5. a request on a lap that is not a departure lap stays pending and locks on the first departure lap.
6. nothing pending, default set, final lap: default locks under a fresh id.
7. nothing pending, default `{}`: the scene goes on; `next_boundary_t()` moves one lap.
8. unavailable destination: closed before the lock, state returns to NONE, the next request works.
9. not ready at the lock: `deferred` once, then locks at the next boundary with `mode == &"cut"`.
10. failure after the lock: `switched` carries a `landed` with `fallback == true`; `completed` still fires.
11. `on_miss`: a missed last block locks the `on_miss` destination.
12. `when == &"soonest"`: the boundary is the next block boundary at least a lock lead away.
13. `song_time()` never decreases; `lap_beat()` is 0 at every `switched`; `tempo_changed` fires when the
    new scene's tempo differs.
14. a second transition cannot lock before the first has `completed`; it is deferred with `&"blending"`.
15. ids are strictly increasing over ten consecutive transitions and no signal carries a stale id.

## 10. Examples

Enter a quest from a hub and come back:

```gdscript
# narrative side, on a tap (QuestRouter built the destination and holds the pending change)
var dest := router.destination_for(hotspot_id)   # {"id":"gospel/jordan","path":"gospel","node":"jordan","kind":&"quest_entry","quest":"gospel"}
var id := port.request(dest)
if id == 0:
	view.show_refused(hotspot_id, port.last_refusal())

# narrative side, connected once
func _on_request_closed(id: int, reason: StringName) -> void:
	router.discard(id)
	view.deselect_if(id, reason)

func _on_locked(id: int, dest: Dictionary, boundary_t: float, plan: Dictionary) -> void:
	view.commit_feedback(id, boundary_t)          # the walk to the object, timed to the boundary

func _on_switched(id: int, landed: Dictionary, t: float) -> void:
	router.commit(id, landed)                     # the only place route state changes; saves
	port.set_default(router.default_destination())
```

The player taps the dungeon door, then the stranger, then nothing more: two `request()` calls, one
`request_closed(first, &"replaced")`, and at the next departure lap's lock one `locked(second, ...)`.

## 11. Changing this contract

In stage 0.3 of the plan the lead copied `contract/transition_port.gd` and `contract/transition_port.gd.uid` to
`src/transition/`, byte for byte (`cmp` must report no difference). The `.uid` file is copied too so that
Godot does not invent a different one in each worktree, which would conflict at the merge.

Neither stream edits `src/transition/transition_port.gd`. An agent that needs a change reports the need to
the lead and carries on with what the contract allows. Only the lead amends `contract/transition_port.gd` and
this file, bumps `VERSION`, copies the file to `src/transition/` again, and tells both streams.

## Clarifications (6 November 2026)

Six readings fixed by the lead (`LEAD_RULINGS.md`, rulings 9 to 14) after the mock and the conformance cases were
written. They narrow version 1 and do not change it: no signal, argument, state, rule or conformance case above
changes meaning, and `VERSION` stays 1.

1. **Laps are numbered from 1**, as in the engine. `doors_from_lap` 2 with 4 laps gives departure laps 2, 3 and 4. The last lap of a scene is always a departure lap.
2. **A block is 16 beats.** `when == &"soonest"` means the next 16-beat block boundary that is at least a lock lead away.
3. **On a replace, `request_closed(old, &"replaced")` comes before `request_acknowledged(new, true, &"")`** (rule 1).
4. **At a switch, `tempo_changed` comes before `switched`.**
5. **An unavailable destination may be refused at once** (`request()` returns 0, reason `&"unavailable"`) **or acknowledged and then closed `&"unavailable"` before the lock.** Either way nothing is left pending.
6. **A `&"blending"` deferral may repeat** at each lock point while the last blend has not completed. `begin_scene` clears the default, so the narrative side sets the default again in its `switched` handler (as the example in section 10 does). A final lap reached while a blend is still running is extended by one lap, without a signal.
