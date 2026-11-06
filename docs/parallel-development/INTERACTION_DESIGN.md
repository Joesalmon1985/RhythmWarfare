# Interaction design: choices, reactive objects, coverage

Status: planning document, written 6 November 2026 on the one-PC plan (`docs/parallel-development/ONE_PC_PLAN.md`). No game code is written here.
Read "Windows" in older documents as the music stream and "Ubuntu" as the narrative stream. This document belongs to the narrative stream.

Companions: `INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` (the one interface to the music side), `ONE_PC_PLAN.md` (stages N1 and N2 carry the work in section 9), `docs/CHOICE_CLARITY.md` (the legibility audit of the choice layer), `docs/STORY_25D_ART_DIRECTION.md` (the art pipeline's look).

How to read the status words:

| Word | Meaning |
|---|---|
| **existing** | In the repository now. The file or symbol is named and was checked in the worktree. |
| **partial** | Part of it exists. The gap is stated. |
| **proposed** | Does not exist. A name given for it is a suggestion for the work package that builds it. |

Numbers that come from a model, not from the running game, are marked **(model)**. Section 1.2 says what the model is.

---

## 0. The target in six lines

1. Every playable narrative scene shows at least three visibly different choices. A hub scene shows five or more.
2. At least 50% of the visible game world is covered by objects that react to a tap, for at least 80% of active play. Choices alone cover at least 25%.
3. One tap changes the intended destination at once. The old pick deselects. Music and rhythm play go on. The player can change their mind until the lock point before the next musical boundary.
4. No confirmation, no menu, no arrows, no navigation screen.
5. Targets are comfortable on an Android phone, never under the pads, never invisible.
6. The numbers are measured by a tool that runs in the real project, not argued about.

The owner has decided that objects which react to a tap but lead nowhere count towards the 50% (section 11).

---

## 1. Today

### 1.1 How selection works now (existing)

| Step | What happens | Where |
|---|---|---|
| Touch | A press event (touch or emulated click). A second event within 80 ms and 3 px is dropped. | `RunPlay._input`, `src/run/run_play.gd` |
| Pads first | `LaneInput` takes touches that start on a pad and marks them handled. Pad rectangles are the drawn pads grown by 8%. | `src/input/lane_input.gd`, `src/ui/pad_view.gd` (`button_rects()`) |
| Rejections | `hotspot_tap(pos)` returns at once if the point is outside the stage area, inside any pad rectangle, or a minigame is active. | `RunPlay.hotspot_tap` |
| Placement | `HotspotView.layout(items, map, crowds, pose, view, true)` projects every hotspot that is on show with the current camera pose. Each gets a circle (projected `radius_m`, never under `min_px / 2`, never over half the short side) and, with `rects` true, a rectangle from the staging's `touch` size standing on the floor. | `HotspotView.layout`, `src/run/hotspot_view.gd` |
| Hit | `HotspotView.hit` takes the nearest centre among the entries whose circle or rectangle holds the point. | `HotspotView.hit` |
| Select | `hotspot_select(id)` calls `RunHotspots.select`. It works while the hotspot is on show. A new pick replaces the old. There is no un-select. | `src/run/run_play.gd`, `src/run/run_hotspots.gd` |
| Feedback | Ring goes white-hot and thumps on the beat, four motes circle it, the other hotspots dim to 45% (`DIM_OTHERS`). The choice layer swaps within one beat (`SWAP_BEATS = 1.0` in `src/run/choice_staging.gd`): the person nods, the chosen door swings open with a round green lamp, the others shut with a square red lamp. | `HotspotView`, `ChoiceStaging`, `ChoiceProps` |
| Commit | At the last block's decision (beat 60.5 of 64) the pick resolves to its success or failure outcome. Nothing picked: the default exit. The scene changes at beat 64. | `RunHotspots.commit_final`, `src/run/run_engine.gd` |
| Empty tap | Nothing happens. A `tap_miss` entry goes to `hotspot_log`. | `RunPlay.hotspot_tap` |

The touch contract today (`src/run/hotspot_contract.gd`): `MIN_PX = 72`, `MIN_PER_SCENE = 2`, `MAX_PER_SCENE = 4`. `tools/run/check_hotspots.py` enforces 2 to 4 unless a node sets `max_hotspots`.

Choice staging sizes (`content/run/choice_staging.json`): touch rectangles in metres standing on the floor: person 1.2 x 2.1, door 1.7 x 2.6, object and feature 1.4 x 1.6, figure 1.4 x 2.0. The drawn door prop is 1.2 x 2.4 m.

When a hotspot can be touched (existing, from the engine and `docs/RUN_TRACK_SCENES.md`):

| Scene type | Touchable | Share of the scene |
|---|---|---|
| Ordinary scene (main run, one lap of 64 beats) | From the block-2 decision (beat 44.5) to the commit (beat 60.5) | 16 of 64 beats, 25% |
| Path scene (Gospel, Squadron, Ember: two laps by `path.laps`; three scenes override to one) | Last lap only | 16 of 128 beats, 12.5% |
| Track scene (doors from lap 2) | In the last block of every lap from lap 2 | 16 of 64 beats on laps 2 and later; none on lap 1 |
| Early (the wizard) | Blocks 0 and 1 only | 32 of 64 beats, two scenes |
| `window: any` (the card table) | Every block | Ward day room only |

`preselect` (existing, `run.json` `choice.preselect`) would let the player touch a staged option before its window. It is built and off by default. The decisions of 6 November replace it with selection open for the whole scene (section 2).

### 1.2 The numbers, and what kind of numbers they are

Nothing in the repository measures touch coverage. The figures below come from a Python model that re-implemented `HotspotView.resolve`, `StoryProjector.project`, `HotspotView.layout` and the staging touch sizes over the shipped data, and rasterised the union of circles and rectangles on a 1280 x 460.8 stage view (the default 36% pad strip). It had to assume a camera pose for each scene: the camera standing at the last stop of the node's good rail chain, looking where the window camera looks. Real play moves the camera.

**These are the report's model, not measurements.** The per-scene numbers in section 8 are the same model. They stay in this document until the measured baseline from `tools/run/coverage_audit.gd` (work package N1.5) replaces them. The model is trusted for its median, not for any single scene: a camera next to a hotspot swings one scene by tens of points.

| Quantity (model) | Value |
|---|---|
| Scenes | 82 (36 main run, 17 Gospel, 14 Squadron, 15 Ember) |
| Union of touch area, share of world: min / median / mean / max | 0.7% / 6.3% / 10.2% / 54.4% |
| Scenes at 50% or more | 1 (`warehouse.booth`, 54.4%, a near-camera artefact) |
| Scenes at 25% or more / at 10% or more / under 10% | 8 / 27 / 55 |
| Time touchable (ordinary scene) | 25% of the scene |
| Area times time, median ordinary scene | about 1.6% of world-area x time, against a target of 50% x 80% = 40% |
| Smallest touch target at the 72 px floor | 51 of 82 scenes; 61 of 82 are under 88 px |
| Edge beacons (anchor out of sight) | 38 of 117 final-window hotspots in the main run; 13 of 29 in Squadron |
| Scenes with fewer than three distinct destinations (flags off) | 81 of 82 (the Floor, `warehouse`, is the one with three) |
| Scenes with three or more touchable things at the window | 50 of 82, but the "things" are mostly people and props that stay in the room |
| Legibility verdict (`docs/CHOICE_CLARITY.md`, older camera) | 2 clear, 28 unclear, 52 invisible |

The gap to the target is about 8 times in area and 3 times in time (model).

### 1.3 Gaps against the owner's requirements

| Requirement | Today | Status |
|---|---|---|
| Three visibly different choices in every scene | Three touchable things in 50 of 82 scenes, but only one scene offers three different places to go | partial |
| Five or more in a hub scene | Cap of 4; no hub shows four quest entrances | missing |
| 50% of the world interactive, 80% of the time | Median 6% for 25% of the time (model) | missing |
| Visual coverage measured apart from touch coverage | No tool | missing |
| One tap changes the destination, object reacts, old pick deselects | Works in the window, up to one beat to show | existing, partial in time |
| Change of mind until a boundary | Works until beat 60.5 | existing |
| No confirmation, menus, arrows | True | existing |
| Comfortable targets | 72 px floor, about 41 dp on a 2400 x 1080 phone at 420 dpi; many sit on it | partial |
| No overlap with the pads | By construction: the stage is above the pad strip, layout clamps centres, `hotspot_tap` rejects pad rectangles | existing |
| Objects feel part of the scene | Doors, people nod and beckon, lamps; most hotspots have no object of their own | partial |
| Tool to measure | `tools/run/choice_audit.gd` measures legibility at four beats; nothing measures coverage | partial |

### 1.4 Where the decisions and the code or data disagree

These came up while the code and data were checked. Each is resolved in the section named.

| # | Finding | Resolved in |
|---|---|---|
| 1 | The decisions raise the hotspot cap from 4 to 8, but a hub needs six or seven choices and then reactive objects on top. The cap cannot count reactive objects. | 2.5 |
| 2 | The two touch-size rules cannot both hold for a small object. A target of 88 px needs a visual of at least 40 px a side under the "bounds plus 24 px" rule, and then its touch area is 4.8 times its visual area against the 1.5 times limit. | 3.6 |
| 3 | The staging rectangles are in metres, so the margin around an object grows as the camera nears it. The door's touch rectangle (1.7 x 2.6 m) over its drawn prop (1.2 x 2.4 m) is 25 cm a side: 24 px at 5 m, 39 px at 3 m. | 3.6 |
| 4 | 88 px is "about 50 dp" only up to 440 dpi. At 480 dpi it is 44 dp. 48 dp is 7.6 mm at any density. | 3.5, 7 |
| 5 | The Floor holds only one quest entrance itself (the wizard). The other three live in the Bar, Balcony and Booth, behind flags and rhythm gates. The hub rule read literally adds 19 entrance objects, not 16. | 5.2, 9 |
| 6 | `choice_audit.gd` places hotspots in a 1152 x 648 view, at four beats (4, 30, 50, 56), for every hotspot whatever its flags. The coverage tool needs 1280 x 720 and 1600 x 720, every beat, and only what is on show. | 4 |
| 7 | The code enforces `MIN_PX = 72` and a test checks it. The decisions say 88. | 9 (N2.1 changes both) |
| 8 | Squadron has no one-lap scenes (all 14 play two laps). Only `jordan`, `jerusalem.golgotha` and `hollow` are one-lap path scenes. | 8 |
| 9 | `docs/HANDOVER.md` says "at most two touches count at once". `LaneInput` as read caps nothing. | 7 |

---

## 2. The interaction model

### 2.1 Two kinds of object

| Kind | What a tap does | Port | Counts to the 50% |
|---|---|---|---|
| **Choice** | Selects a destination (a scene, a quest entrance, a quest return). Exactly one choice is selected at a time. | `request`, `cancel` | Yes |
| **Reactive object** | Reacts visibly (a dancer turns, a light flares, a prop answers) and leads nowhere. | None | Yes (owner's decision of 6 November) |

A choice is a visible object that leads to a distinct destination. "Stay" is not a choice. A reactive object never changes, replaces or clears the selected choice.

### 2.2 Selection is open for the whole scene

`port.selection_open()` (existing in the contract, `contract/transition_port.gd`; the real director and the mock are not built yet) is true from the scene's first beat until each lock point (`lock_t(next_boundary_t())`, 3.5 beats before the boundary today). It is false from the lock to the boundary, and during documented cinematics.

| Fact | Value |
|---|---|
| Selection open, ordinary one-lap scene | beats 0 to 60.5 of 64, 94.5% |
| Share closed by the lock window | 3.5 / 64 = 5.5% |
| Requirement | 80% of active play |
| Request on a lap that is not a departure lap | Accepted, stays pending, tried at the next boundary (conformance case 5) |
| Request on a lap whose doors are closed | Same; the object stays selected |

The hotspot layer stops asking `RunHotspots.shown(block, final_open)` whether a choice may be touched. It shows every available choice from the first beat (N2.1).

### 2.3 What a tap does

The same table for every scene. "Pending" is the port's current request.

| Scene state | Tap on | Result | Port |
|---|---|---|---|
| Nothing selected | A choice | It becomes selected. The scene's default destination is still the fallback. | `request(dest)`; `request_acknowledged(id, true, "")` |
| Nothing selected | A reactive object | It reacts. Pending stays empty. | none |
| Nothing selected | Empty world | Nothing. `tap_miss` logged. | none |
| Something selected | Another choice | New pick selected, old one deselects. | `request(new)`; the old id gets `request_closed(old, &"replaced")` |
| Something selected | The selected choice again | Stays selected; a small thump on the beat. | none (**assumption** A1) |
| Something selected | A reactive object | It reacts. The selection is untouched. | none |
| Something selected | Empty world | Nothing. | none |
| Locked (lock point to boundary) | A choice | Not accepted. The object gives the refused reaction once. | `request` returns 0 with `&"locked"` |
| Locked | A reactive object | It reacts (it is only a picture). | none |
| Refused at once or closed `&"unavailable"` | The same choice | The object plays the refused reaction and is not selected. The scene's default applies. | `request_acknowledged(id, false, reason)` or `request_closed(id, &"unavailable")` |
| Cinematic or minigame | Anything | The activity's rules. Declared as an exception. | none |

Where choices and reactive objects overlap, the choice wins (**assumption** A7).

Timing of the answer (proposed): the first sign of the tap shows on the next frame (a ring flash at the touch point on the object), the object's full reaction lands on the next beat. Today the swap is up to one beat (about 0.34 s at 174 BPM).

### 2.4 The states of an object

Choices go through all six. A reactive object uses idle, hinting and a short "reacting" in place of selected. `unavailable` and `refused` are choice states.

| State | Meaning | Enters when | Port call or signal | Look today | Look new |
|---|---|---|---|---|---|
| **idle** | Visible, tappable, nothing special | Scene entry; deselected; refusal ended | none | `look.available`: glow, pulse, beckon, flicker, open, crack (existing, `HotspotContract`) | Same, plus the destination tint (6) |
| **hinting** | The object asks for attention | A timed cue, one object at a time, on the downbeat of every fourth bar; and for the default exit (proposed) | none | The default exit is lit green, others red (`CURRENT_COL`, `OTHER_COL`) inside the window | Hint begins on beat 0, not at the window |
| **selected** | This is the pending destination | `request_acknowledged(id, true, "")` | Pending request equals this object's destination | Ring white-hot, motes, door open and green lamp, person nods and cheers | Same; others dim; light path shows (6) |
| **locked** | The transition is fixed | `locked(id, dest, boundary_t, plan)` | `locked` | White flash 0.3 s (`FLASH_S`), pool settles 0.9 s, door walk from beat 61 | Same; the other choices go quiet |
| **refused** | The tap was not accepted | `request_acknowledged(…, false, reason)`; `request_closed(id, &"unavailable")`; request while locked | Reason: `&"locked"`, `&"invalid"`, `&"unavailable"` | None (a miss shows nothing today). The claim look has a refusal for the card table (`CLAIM_REFUSE_S`) | A short recoil: a shake or a shut door, 0.4 s |
| **unavailable** | Cannot be chosen now | Flags, energy or `once` (existing `available` rules); destination not loadable | none (data) | Hidden until available | Hidden or shown shut, never lit |

Mapping rules for the narrative code (proposed): the object's state is derived from `port.current()`, the last signals and the scene's data. `HotspotView` reads the selected id from the port, not from `RunHotspots.selected`. A state change that comes from a signal is applied in the frame the signal arrives.

### 2.5 The hotspot cap and the reactive list

The cap of 8 per scene (decision, replaces `MAX_PER_SCENE = 4`) counts **choices**. A hub has six or seven (section 5.2), so 8 is enough. Reactive objects are held apart so that they never count against the cap, never need a default, and never take part in the "one default exit" rule: a `reactives` array in the scene's hotspot file with the fields id, anchor, a reaction name, an optional touch size, and an optional existing effect (proposed; the exact shape is for N2.1). Cosmetic by default (**assumption** A5).

### 2.6 Keys

Desktop keys 1 to 4 select the first four choices on show (existing, `run_play.gd`). With up to eight choices they become 1 to 8 (proposed, trivial).

---

## 3. Coverage: precise definitions

### 3.1 World area

The world is the stage view: the picture above the pad strip.

| Setting | Viewport | Pad share | World (px) | Area (px²) |
|---|---|---|---|---|
| 16:9, small pads | 1280 x 720 | 30% | 1280 x 504.0 | 645,120 |
| 16:9, **default** | 1280 x 720 | 36% | 1280 x 460.8 | **589,824** |
| 16:9, large pads | 1280 x 720 | 42% | 1280 x 417.6 | 534,528 |
| 20:9, small | 1600 x 720 | 30% | 1600 x 504.0 | 806,400 |
| 20:9, default | 1600 x 720 | 36% | 1600 x 460.8 | 737,280 |
| 20:9, large | 1600 x 720 | 42% | 1600 x 417.6 | 668,160 |

The project uses `canvas_items` stretch with `expand` (`project.godot`). A 2400 x 1080 phone (20:9) gets a 1600 x 720 viewport: the extra width is extra world, the height and the camera's vertical field of view are unchanged. The pad shares are `Session.PAD_SIZES = [0.30, 0.36, 0.42]`.

Excluded from the world (taken out of the denominator and the numerator): the pad strip; the pause button (72 x 56 px, top right); the route-window bar on the bottom edge; the debug label; any other HUD rectangle. The falling-cue lane is drawn over the world but ignores the mouse, so it neither adds nor takes away touch area.

### 3.2 Touch region and visual bounds

| Term | Definition |
|---|---|
| **Touch region** of an object | The set of points in the world where `HotspotView.hit` would return that object's id: its circle or its rectangle, clipped to the world, minus the HUD rectangles. |
| **Usable** | A region counts at a sampled beat only if a tap there would do something at that beat: the choice is available and selection is open, or the object is a reactive object that is on show. A choice in the lock window or an unavailable choice does not count. |
| **Visual bounds** of an object | The screen rectangle of the object's own sprite, billboard or prop, projected for the camera pose, clipped to the world. Glow, ring, shaft and motes are effects, not the object. |
| **Touch union** | The area of the union of all usable touch regions. Overlapping hitboxes count once. The sum is reported next to it as a check. |
| **Choice union** | The union of the usable touch regions of choices only. |
| **Visual union** | The union of the visual bounds of all usable objects. Measured and reported on its own. |
| **Edge beacon** | The stand-in for a choice whose anchor is out of sight (existing, `HotspotView.layout` with `edge: true`). It is a 72 px circle at the picture's side. It counts for reachability and for the touch union, not for the visual union, and it never satisfies the "three visible choices" rule (**assumption** A6). |

### 3.3 Active play and sampled frames

| Term | Definition |
|---|---|
| **Active play** | Song time from a scene's `phase_start` to its last lock point, over all laps (ordinary 1, path 2, track scenes 2 to 12), minus declared exceptions (3.7). |
| **Sampled frame** | One sample on each beat of that span, taken on the virtual clock with the camera the player really has. |
| **Share of sampled frames** | Beats passing the test divided by beats sampled. |
| **Lock window** | The 3.5 beats from lock to boundary. Excluded from active play as a transition (**assumption** A3), and also reported: coverage including the window is a column of the report. |

### 3.4 Targets as numbers

| # | Target | Value | Applies |
|---|---|---|---|
| T1 | Touch union | 50% or more of the world in 80% or more of sampled frames | Every scene, every cell of 3.1 |
| T2 | Choice union | 25% or more of the world in 80% or more of sampled frames | Same |
| T3 | Distinct visible choices | 3 or more in every sampled frame with selection open; hubs 5 or more | Same |
| T4 | Smallest touch target | 88 px in the 1280 x 720 design, in both directions | Every usable region |
| T5 | Touch against visual | Within the object's visual bounds grown by 24 px on each side; area at most 1.5 times (reading in 3.6) | Every region |
| T6 | Pad overlap | 0 px² against every pad rectangle (grown 8%) and every HUD rectangle | Every region |
| T7 | Selection open | 80% or more of active play (94.5% by design) | Every scene |
| T8 | Visual union | Reported, no threshold (the check on invisible hitboxes is T5) | Every scene |
| T9 | Edge beacons | 0 for choices in hub scenes; others reported | Reported |

### 3.5 Minimum size, with the arithmetic

The design height is 720 px. A 2400 x 1080 phone shows it at 1080 / 720 = 1.5 device pixels per design pixel.

| Quantity | Design px | Device px | At 420 dpi (2.625) | At 440 dpi (2.75) | At 480 dpi (3.0) |
|---|---|---|---|---|---|
| Minimum target T4 | 88 | 132 | 50.3 dp, 8.0 mm | 48.0 dp, 7.6 mm | 44.0 dp, 7.0 mm |
| Today's floor (`MIN_PX`) | 72 | 108 | 41.1 dp | 39.3 dp | 36.0 dp |
| Margin of 24 px (T5) | 24 | 36 | 13.7 dp | 13.1 dp | 12.0 dp |
| Gap of 16 px between choices (7) | 16 | 24 | 9.1 dp | 8.7 dp | 8.0 dp |

dp = device px / (dpi / 160). 48 dp is 48 / 160 inch = 7.6 mm. 88 px meets 48 dp up to 440 dpi: 88 x 1.5 x 160 / 48 = 440. Above that it falls short (A8 offers 96 px).

The distance at which a standing object is 88 px wide (focal length 472.4 px for the 460.8 px stage and 52 degrees vertical): person (1.2 m) 6.4 m, door (1.7 m) 9.1 m, object (1.4 m) 7.5 m. Beyond that the object has to be larger or nearer, or it is not a target.

### 3.6 No invisible hitboxes

The decisions give two limits: the touch region lies within the object's bounds plus at most 24 px, and the touch area is at most 1.5 times the visual area. Read together:

- **T5a, the primary rule:** every side of the touch region is within 24 px (design pixels, per frame) of the visual bounds.
- **T5b:** the area ratio is checked for objects whose visual bounds are at least 88 px in both directions. Below that, T5a alone decides, because a target of 88 px round an object of 40 px has a ratio of 4.8 by arithmetic and cannot be both small and large. An object with a visual shorter than 40 px on its short side cannot be a target: it is made bigger or nearer, or it is not interactive (**assumption** A4).
- The touch rectangle is built on screen from the visual rectangle (proposed), not from metres on the floor. Today's metre rectangle breaks T5a at close range (finding 3).
- An invisible region is a failure whatever its size. A touch region with no visual bounds at all is a failure, with one exception: the edge beacon, which is drawn.

### 3.7 Declared exceptions

An exception is declared in the narrative overlay (`content/narrative/graph.json`, `exceptions`, proposed key) with: scene, kind, beats (from, to), the rule waived, the reason. The tool reads the file, removes the beats from active play and prints the exception with the share of time it takes.

| Kind | Examples | Waives |
|---|---|---|
| Transition | The lock window, the door walk, the passage iris | Everything for those beats |
| Brief cinematic | An `on_success` or `on_select` cinematic, a title card | T1 to T3 for its beats |
| Minigame | The card table seat (`minigames.active()`) | T1 to T3 while active |
| Other system | The Bassment passages (`src/trial`, own tap handler, 62 of 64 with fewer than three choices) | All; named as a later piece of work |
| Scene | A scene that cannot reach 50% with honest objects | T1 only, listed by name |

A scene may not exclude more than 25% of its beats (**assumption** A9). The fallback in the plan stands: a documented exception for the scene, never an invisible enlarged hit area.

---

## 4. The measurement tool: `tools/run/coverage_audit.gd`

Status: proposed. Another work package (N1.5) builds it from these notes. This section is its specification in prose. It follows `tools/run/choice_audit.gd` (existing) and the decision on the measurement tool.

### 4.1 Inputs

| Input | Value |
|---|---|
| Scenes | Every node of `content/run/run.json` and of each path's `run.json` (82), as `choice_audit.gd` reads them. Optional filter by run and by scene id. |
| Views | 16:9 as a 1280 x 720 viewport and 20:9 as a 1600 x 720 viewport (the shape of a 2400 x 1080 phone). |
| Pad settings | `Session.pad_size` 0, 1, 2 (30, 36, 42% of the height). |
| Cells | 2 views x 3 pad sizes = 6 cells per scene. |
| Tracks | `RW_RUN_TRACKS=0` until the track audio is wired (milestone M1). With it every scene is an ordinary scene and the run is silent and virtual. Afterwards the tool also runs with tracks on, where scene length and laps come from the pack. |
| Players | Perfect bot (takes the good rail chain), failing bot (misses the last block of every lap, takes the bad chain), and a tapping bot that picks a choice at beat 2 and another at mid-scene. |
| Exceptions | The overlay's `exceptions` (3.7). |

Run (same shape as `choice_audit.gd`, through the Godot queue wrapper `tools/dev/godot.sh`, existing since stage 0, because only one Godot runs at a time on this PC):

```
tools/dev/godot.sh --headless --path . -s tools/run/coverage_audit.gd -- [main|gospel|squadron|ember|all] [scene filter]
```

with `RW_RUN_VIRTUAL=1`, `RW_RUN_TRACKS=0`, `RW_PAD_SIZE` and the host size set per cell. It needs no pixels: `StoryProjector.project` is pure GDScript, which is why `choice_audit.gd` already runs headless. Visual bounds therefore come from sprite and prop dimensions through the same projection, not from reading the screen.

### 4.2 Method

For each scene and each cell:

1. Build `RunPlay` in a host control of the cell's size, start at the scene (`RW_RUN_START`, `RW_RUN_PATH`), as `choice_audit.gd._start` does. The host must be 1280 x 720 or 1600 x 720; `choice_audit.gd` uses 1152 x 648.
2. Step the virtual clock (`_step_virtual`, 1/30 s) to every beat from beat 0 to the last lock point of the last lap.
3. At each beat take the real pose (`RunPlay._exit_pose()`), the items on show (`RunPlay.hotspot_items()`; after N2.1 the choices and the reactive objects that the engine reports as usable), and call `HotspotView.layout(items, st.map, st.crowds, pose, rect.size, true)`, with `rect` the stage host's rectangle. Nothing is re-implemented: the audit measures what a tap at that moment would hit.
4. Get the pad rectangles from `pad_view.button_rects()` and the HUD rectangles from the HUD nodes.
5. Rasterise at 1 px, or by exact rectangle union, the touch regions (clipped to the world, minus HUD), the choice regions and the visual bounds. Compute the unions, the sum of areas, the overlaps, the smallest target, the margins, the area ratios and the overlap with the pads.
6. Count the distinct destinations among usable choices, edge beacons, and whether `selection_open` held.
7. Remove the beats that fall in a declared exception.

The tool never taps. The tapping bot is a second pass for the single-tap tests (10), not for coverage.

### 4.3 Output

One JSON object per scene and cell on stdout, prefixed `COVER ` (as `choice_audit.gd` prefixes `AUDIT `). A Python summary (`tools/run/coverage_audit.py`, proposed) reads the lines and writes the tables, as `choice_audit.py` does.

| Column | Meaning |
|---|---|
| scene, run, view, pad, player | The cell |
| beats, beats_excluded | Sampled beats and beats removed as exceptions, with the exception ids |
| touch_min, touch_median, touch_mean | Touch union as % of the world, over sampled beats |
| share_t1 | Share of beats with touch union at or above 50% |
| choice_median, share_t2 | Choice union and the share at or above 25% |
| visual_median | Visual union |
| sum_over_union | Sum of region areas divided by the union (overlap check) |
| choices_min, choices_hub_needed | Fewest distinct visible choices at a sampled beat, and 3 or 5 |
| beacons | Edge beacons at their most |
| min_target_px | Smallest target over all beats and regions |
| max_margin_px, max_area_ratio | Worst T5a and T5b |
| pad_overlap_px2, hud_overlap_px2 | Must be 0 |
| selection_open_share | Share of active play |
| incl_lock_share_t1 | Share of T1 with the lock window counted |
| verdict | PASS, FAIL, EXCEPTION |
| fail_rules | The targets (T1 to T9) that failed |

### 4.4 Pass and fail

- A scene-cell is **PASS** when T1, T2, T3, T4, T5, T6 and T7 all hold. T8 and T9 only report, except T9 for hub choices.
- A scene is **PASS** when all six cells pass. The report names the failing cell. The default cell for reading the tables is 16:9 at 36%.
- **EXCEPTION** is a scene with a declared scene exception (3.7). It is listed and counted, never silent.
- The game passes when no scene is FAIL. The report also gives the time-weighted share: the beats passing T1 over all sampled beats of all scenes.
- Exit code: 0 if no FAIL; 1 otherwise. A `--baseline` file turns the tool into a ratchet while the content is still being made: it fails only on a scene that was better before.

### 4.5 Consistency with the model, and with the later stages

- N1.5 is accepted when its baseline for all 82 scenes is in line with the model of 1.2 (median about 6%) and says plainly where it differs. Before N2.1 the engine shows choices only in the window, so the baseline measures that: share_t1 will be near zero, selection_open_share near 25%. That is the point of the baseline.
- Section 8 is regenerated from the tool's output when it exists. Until then its coverage columns are the model.
- A `--candidates` mode (proposed) lists, per scene and beat, the map things and people that would be at least 88 px wide on screen and are not yet interactive. N2.6 uses it to choose reactive objects.

### 4.6 How it becomes a test

| Piece | File (proposed) | Runs in |
|---|---|---|
| Pure geometry: union, overlap, margins, ratio, smallest target, with synthetic rectangles | `tools/run/coverage_geometry.gd` and `tests/test_interaction_coverage.gd` | The normal suite (`tools/test.sh`) |
| One-scene smoke: `warehouse` in one cell, checks the columns exist | Same test file | The normal suite |
| Full audit, 82 scenes, 6 cells | `tools/run/coverage_audit.gd` | X3 of the plan, and per world at N2.4 to N2.6 (acceptance there is "50% or more of the world in 80% or more of sampled frames; choices alone 25% or more; exceptions listed") |

<!-- NEXT -->
