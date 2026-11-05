# Three new paths and faces that tell the story: the plan

> **Status (5 November 2026): stages 1a to 6 are done.** What was built, where it diverged from this plan, what was verified and what is open: `docs/HANDOVER.md` and `docs/paths/`.

Written 5 November 2026 from the owner's brief (the "Rhythm Warfare: Three New Musical Adventures" discussion) and a read of `main` at `5efcfd2`.
This is the document the local agent executes. It makes every design call the owner has already made (section 1), leaves nothing routine to re-ask, and is
ordered so that `main` is playable and the tests green at the end of every stage. Where the agent must diverge, it says so in the commit message and in
`docs/HANDOVER.md`.

**The brief in one line.** Three new storylines branch off the Warehouse, each with its own music (house at 124, dubstep at 140, psytrance at 145), its own
rooms, people, decisions and endings; and across the whole game, including the five worlds that already exist, the people's faces and actions carry the story
so that nothing has to be read while playing.

## 0. Read first, in this order

1. `README.md` (layout, commands) and `docs/CONTINUOUS_RUN.md` (the phase, the route map, the door walk, the route lock, `run.json`).
2. `docs/VISUAL_RHYTHM_ADVENTURE_HANDOVER.md` and `docs/VisualChoicePlan.md` sections 1 and 2 (the governing design: touch the world, the music decides).
3. `src/run/hotspot_contract.gd` (the hotspot data contract this plan extends), `content/run/hotspots/warehouse.json` (examples), `src/run/run_hotspots.gd`.
4. `docs/FACE_POLISH.md`, `docs/STORY_ART.md` "The people" (the pixel rig, wardrobe, sheets, `StoryCharacter.STATES`, `FACE_OF`, `SHEET_CYCLES`), `tools/story/art/people.py`.
5. `docs/MUSIC_IMPORT.md` and `tools/content/beatshaper.py` (how packs are imported, checked and assigned; the `BPM = 174` constant and the profiles table).
6. `docs/TRIAL_OPENING.md` "how the Bassment is entered and left" (the model for entering and leaving a path on the same pads).
7. `docs/NEXT_AGENT_PROMPT.md` "Working rules" (the machine, the Godot console binary, Python, how to run the tests). The stage list in that file is old; ignore it.

## 1. Decisions already made (do not re-ask)

| # | Decision | Why |
| --- | --- | --- |
| D1 | **Each new path is a sister run with its own tempo.** A path is its own `run.json` (`timing.bpm` 124 / 140 / 145), its own `music.json`, hotspot files and packs, run by the same `RunEngine`, `RunAudio`, `RunPlay`, `HotspotView` and stage code. The existing 174 BPM run is not changed. A path is entered from a Warehouse hotspot through the passage frame with a **tempo handoff** and returns to the Warehouse floor the same way. | The engine's tempo is global (`RunData` rejects a pack at another BPM; `RunAudio.silent_loop` is the clock). Re-gridding the clock mid-run would risk every existing world and test; authoring house at 174 would not be house. |
| D2 | **Original names and worlds for paths 2 and 3.** The structures of the owner's brief are kept (a bombardier trapped by an absurd regulation; a small carrier bearing a cursed thing across a dangerous land to be rid of it), with original characters, places and names (sections 5 and 6). The Gospel path keeps its source: it is public domain. Nothing in the art depicts a character from a published book or film. | The game may be published. |
| D3 | **No text during play, anywhere.** The scene title card, the HUD captions (BASS ENTERS, RISER, FALL, ROUTE CHOSEN), the world and room names in the HUD, the numeric countdown and the Bassment's caption band all go. Menus, pause, settings, the result screens and the F3 debug line keep text. `RW_DEV_TEXT=1` restores the play text for debugging and for the tests that read it. | The owner's request: story through faces and actions, not text popping up. |
| D4 | **Order: the acting system on the five existing worlds first, then the Gospel path as the pilot, then the other two.** Stages 1 to 6 below; every stage ends in a commit on `main` with the tests green and proof shots. | The acting system is shared by all eight worlds and is the quickest visible win; the pilot path proves the sister-run machinery before two more are built on it. |
| D5 | **Music supply.** The owner generates the loops with an AI music tool from the prompts in sections 4 to 6 (one prompt per scene, eight-bar seamless loop, separate MIDI tracks) and drops the exports into `content/imports/<path>/<scene>/`. Until a scene has its loop it plays a **synthesised placeholder** at the path's tempo, marked `"temporary": true` in the path's `music.json` exactly as the Underworld's stand-ins are today. Visual work never waits for music. | The agent cannot generate audio; the owner's pipeline (`beatshaper.py`) already handles imports and stand-ins. |
| D6 | **Branch and rejoin, success and failure.** Every scene offers one or two touchable things (plus the default way on); a success goes where the touch intended, a failure goes the other way, to a setback scene or to an alternative ending, exactly in the existing hotspot contract (`on_success` / `on_failure`). No unwinnable states, no failure loop without a way out. | The brief; the contract already enforces the 2 to 4 rule, a default exit and recoverable energy costs. |
| D7 | **The player is never seen.** The camera is the hero (Jesus, the bombardier, the carrier). Everyone else reacts to the camera: that is how the acting system tells the story. | On-rails first person is the existing engine. |
| D8 | **Art budget per path: four maps, about ten views in all.** Scenes share a view with a different time of day (`stage.views` light), a different prop set (`stage.pieces` on/off) and a different crowd. A path is roughly the art of the existing chapter campaign; the agent should expect several sessions per path and may stop at any committed stage. | Honest scoping: the five existing worlds took that long. |
| D9 | **One tempo per path, 64-beat phases, 16-beat blocks**, the same stage and mix table, the same judgement and energy numbers as `content/run/run.json` unless a path's `run.json` says otherwise. A phase is 31.0 s at 124, 27.4 s at 140, 26.5 s at 145. | The gameplay is proven; only the tempo changes. |
| D10 | **Flags.** A path's endings and the meeting of its people are `keep:` flags (`keep:path_gospel_tomb`, `keep:path_gospel_road` ...) in `RunProgress.flags`, so the Warehouse portal can show a different look once a path has been finished and the home screen can list the path's worlds under Start from a reached level. | The contract's `keep:` prefix already persists flags. |

## 2. The acting system (Stage 1): faces and actions that carry the story

Today a person has four faces (`neutral`, `happy`, `cheer`, `sad`, chosen by `StoryCharacter.FACE_OF` from the activity) and the only directed act is
`StoryCrowd.beckon` (a `wave` while a character hotspot is on show). The story needs people who can be told what to do and what to feel, at a beat, towards something.

### 2.1 Faces: fourteen expressions

Extend `tools/story/art/people.py` (the face decal: brows, lids, eye shape, mouth, cheeks) and `people_sheets.py` with ten new faces. The face is already part of the frame key, so
a new face costs frames only for the states that use it. Each face must read at the full size (17 x 13 head) **and** at LOD 2; at LOD 4 it falls back to the nearest of the
four old ones (table below). Draw them on the existing per-actor traits (brow shape, eye shape, lips) so every actor keeps their own face.

| face | brows | eyes | mouth | extras | LOD 4 falls back to |
| --- | --- | --- | --- | --- | --- |
| `neutral`, `happy`, `cheer`, `sad` | as today | | | | itself |
| `fear` | raised, inner ends up | wide, whites showing above the iris | small open O, drawn down | a pale cheek (skin2 off) | sad |
| `anger` | down and in, a furrow pixel between | narrowed, lid line heavy | tight line, corners down, or bared teeth (brutes) | a flush | sad |
| `plea` | inner ends up, arched | wide, looking up one pixel | lips parted, corners down | hands come from the act | sad |
| `doubt` | one brow up, one flat | one eye narrower | mouth pulled to one side | | neutral |
| `relief` | up and relaxed | closing, crescent | soft open smile, lower lip loose | shoulders drop (act) | happy |
| `awe` | high | wide, iris centred, catch-light | open, slack | | cheer |
| `grief` | inner ends high, drawn together | closed or half, a tear pixel (`extra` material) | turned down, chin puckered | | sad |
| `laugh` | up | crescent, closed | wide open, teeth, lower lip | head back (act) | cheer |
| `resolve` | flat, slightly down | steady, lids straight | closed, firm, a lit lower lip | chin up one pixel (act) | neutral |
| `shame` | flat | down, looking at the floor | small, corners down | head down (act) | sad |

Species keep their vocabulary (greys, cyclops, insects, blobs, skeletons, demons): give each face a species rule in the same place the current four have theirs; a skeleton's
`fear` is its jaw dropped, a grey's `anger` is its eyes narrowed to slits. Proof: `tools/story/face_sheets.py` gains the fourteen columns; `docs/shots/faces/<chapter>_acting.jpg`.

### 2.2 Acts: what a person can be told to do

Add these states to `StoryCharacter.STATES`, with a pose in `sample()`, a cycle in `SHEET_CYCLES`, a default face in `FACE_OF`, and the facings they need (front and side; `bow`,
`kneel`, `collapse` also from the back). Several exist already and only gain a face parameter (`wave`, `point`, `stare`, `hug`, `clap`, `cheer`, `sad`, `rock`, `check`).

| act | pose (one cycle) | beats, frames | default face | reads as |
| --- | --- | --- | --- | --- |
| `beckon` | the `wave` arm but drawn towards the body twice, weight forward | 2, 8 | happy | come here |
| `nod` | head down and up twice, shoulders still | 2, 4 | happy | yes / agreed |
| `shake_head` | head left-right twice, a hand half-raised | 2, 6 | doubt | no / don't |
| `recoil` | a step back, arms up before the face, then held | 2, 6 | fear | afraid of you / of it |
| `bow` | from the hips, hands together, hold, rise | 4, 8 | neutral | respect, thanks |
| `kneel` | one knee down, head down, hold | 4, 6 | plea | worship, surrender, begging |
| `offer` | both hands out, palms up, holding a prop when the actor has one | 4, 4 | happy | take this, help me with this |
| `plead` | hands clasped at the chest, leaning in | 2, 6 | plea | please |
| `collapse` | knees fold, down to sitting, head in hands | 4, 8 | grief | overcome |
| `salute` | hand to the brow, snap, hold, drop | 2, 6 | resolve | military |
| `block` | arms folded, feet apart, chin up | 8, 4 | anger | you are not coming through |
| `cover_face` | both hands over the face, shoulders shaking | 4, 8 | grief | weeping, shame |
| `stamp` | one foot stamped on the kick, fists down | 1, 4 | anger | rage, protest |
| `laugh` | head back, a hand on the belly, bounce | 2, 8 | laugh | mocking or merry (face decides) |
| `point` (exists) | gains `look_at`: the arm points at the thing or waypoint | 2, 8 | resolve | that way, that one |
| `stare` (exists) | gains face | 16, 4 | neutral | watching you |
| `write` | the `check` clipboard pose, pen hand moving | 4, 8 | neutral | the stamp, the ledger, the chart |
| `sleep` (exists), `lie` (exists) | unchanged | | | |

Sheet size: a directed act is baked **only for the actors that are directed** (section 2.3 lists them in data), not for the whole crowd. `people_sheets.py` reads the run's
hotspot and cast files to know which actor needs which acts; `check_assets.py` fails when a directed actor lacks a state or a face. Budget: at most +15 % on each
chapter's sheets; report the before/after bytes in the commit message as `docs/FACE_POLISH.md` did.

### 2.3 The acting contract: how data directs a person

Two additions to the data, both validated in `HotspotContract` (new constants `FACES`, `ACTS`, `ACTING_PHASES`, `LOOK_TARGETS`).

**(a) `acting` on a hotspot** whose anchor is an actor (or that names one): what the person does in each state of the hotspot, and after the outcome.

```json
"acting": {
  "actor": "h02",
  "available": {"act": "beckon", "face": "plea", "look_at": "camera"},
  "selected":  {"act": "nod", "face": "relief"},
  "committed": {"act": "point", "face": "resolve", "look_at": "to_garden"},
  "success":   {"act": "cheer", "face": "cheer", "beats": 8},
  "failure":   {"act": "shake_head", "face": "doubt", "beats": 8, "then": {"act": "stare", "face": "sad"}}
}
```

* `actor` defaults to `anchor.actor`; a hotspot anchored on a thing or waypoint may still name an actor (the bouncer by the door).
* `look_at` is `camera`, an actor id, a thing id or a waypoint id (`LOOK_TARGETS`); the crowd already turns people towards a target, reuse `StoryCrowd`'s facing.
* `beats` is how long the act holds after the outcome (default 8); `then` is what the actor settles into afterwards (default: their normal activity).
* `available` replaces the hard-coded `beckon`: `RunPlay` calls `StoryCrowd.direct(actor, act, face, t0, until, look_at)` instead of `beckon`, and `stand_down` as now.

**(b) `cast` on a scene node in `run.json`**: story beats that happen whether or not the player touches anything. The scene is a 64-beat phase; a cast line fires at
`at_beat` of the phase (block boundaries 0, 16, 32, 48 are the natural places; 60 is the last safe beat before the route commits).

```json
"cast": [
  {"actor": "h03", "at_beat": 0,  "act": "stare",  "face": "fear",  "look_at": "camera", "beats": 16},
  {"actor": "h03", "at_beat": 32, "act": "plead",  "face": "plea",  "look_at": "camera", "beats": 16},
  {"actor": "h02", "at_beat": 48, "act": "point",  "face": "resolve", "look_at": "to_garden", "beats": 12},
  {"actor": "h03", "at_beat": 48, "act": "cover_face", "face": "grief", "if_energy_below": 40}
]
```

* `if_energy_below` / `if_energy_above` and `if_flags_all` / `if_flags_none` make a beat conditional (the family weeps if you arrive played-out; the king bows only once
  you have met him). The crowd's mood already follows energy; the cast is the named people's story on top of it.
* `RunEngine` already emits block events on the clock; add a `cast` event per line at its beat, resolved by `RunPlay` into `StoryCrowd.direct`. Pure, deterministic,
  tested like the hotspot engine (`tests/test_run_cast.gd`: every shipped cast line fires once, in order, at the right beat; conditions hold; a scene with no cast is unchanged).

**(c) Outcome acting without a hotspot.** An outcome's `cinematic` (the run's `cinematics` table) gains optional `cast` lines with `at_beat` relative to the cinematic's start,
so a setback can be acted: the bouncer blocks and the crowd behind him laughs.

### 2.4 Silent HUD (D3)

* `RunHud`: no title card, no captions, no world or room name; the stage pips, the energy meter and the thin route-window bar (the Bassment's four-bar bar, reused for
  the 16-beat choice window instead of the numeric countdown) stay. The information the text carried is already in the world: BASS ENTERS is the bass coming in and
  the lights lifting; ROUTE CHOSEN is the hotspot's committed flash; a new room is the door walk plus a **light swell** on its downbeat (the room's lamps rise over two beats,
  `StoryStage` has the per-sector light; add a `room_swell` to the stage); RISER / FALL are audible.
* `TrialScene`: the caption band is off; the passage's narrative is acted (section 2.6).
* `RW_DEV_TEXT=1` draws all of it as before. Tests that read captions or title cards set it; tests that assert the HUD is text-free run without it
  (`tests/test_run_hud_silent.gd`: with the variable unset, the HUD draws no `draw_string` during a scripted two-phase run; hook the HUD's `_outlined` to count).

### 2.5 The acting pass on the five existing worlds

Every character hotspot gets `acting`; every scene gets two to four `cast` lines; every setback cinematic that involves a person gets its acted reaction. The named people
(`content/run/hotspots/*.json`, 30 character hotspots) and what their faces should say:

| world | hotspot | the story it must tell without words |
| --- | --- | --- |
| warehouse | `wizard` (thing `wizard_floor`), `chill.wizard` | beckon with a knowing `doubt` face; selected: nod and point at the hatch; success: bow; failure: `laugh` (mocking) then stare |
| warehouse | `dancer` (g07) | beckon `happy`; success: the circle cheers; failure: `recoil` then `shake_head`, the circle turns away |
| warehouse | `bar.bartender` (b01) | `offer` a drink; success: nod, `relief`; failure: `block`, `anger` (you are cut off) |
| warehouse | `balcony.promoter` (v03) | beckon, `offer` tickets, `resolve`; failure: `shake_head`, tickets withdrawn |
| warehouse | `exit.bouncer`, `exit.bouncer_vip` (d01) | `block` at `available`; selected: `stare`; success: steps aside with a nod; failure: `stamp` and `point` back at the floor |
| mothership | `grey` (g08) | `awe` and beckon; failure: `fear`, `recoil` |
| mothership | `dj` (m01) | beckon with the wrong-way headphones, `laugh`; failure: `shake_head`, `doubt` |
| mothership | `reactor.engineer` | `plead`, `point` at the reactor; success: `relief`; failure: `collapse` (the reactor dims) |
| mothership | `exit.exam` (med02) | `write` on the clipboard, `stare`; success: nod; failure: `block` |
| underworld | `bouncer`, `bouncer_grudge` | `block`, `anger`; grudge: `stamp`; success: `bow` (mocking, `laugh`) |
| underworld | `court.queen` | `stare` with `resolve`; selected: `beckon`; success: `nod`; failure: `point` at the pit, the court laughs |
| hospital | `nurse` (h02), `family` (h03), `corridor.trolley`, `dayroom.granny`, `cafeteria.kid`, `garden.mum` | the family's `fear` on arrival, `plea`; the nurse's `resolve`; the granny's `offer` (a sweet) with `relief`; the kid's `laugh`; the mum's `grief` turning to `relief` on success, `cover_face` on failure |
| hospital_late | `doctor` (h17), `cafe.kid` | the doctor `write`s, `doubt`; success: `nod`, `relief`; the kid beckons again, `happy` |
| ward | `orderly` (e04), `art.painter`, `dorm.sleeper`, `corridor.king`, `courtyard.chef` | the orderly `block`s then `shake_head`; the painter `offer`s the brush, `awe`; the sleeper's `sleep` broken into `fear`; the king `bow`s and expects a bow (success: `cheer`; failure: `stamp`); the chef `offer`s, `laugh` |
| ward_late | `treat.orderly`, `dorm.sleeper`, `exit.stare` (x09) | the orderly `write`s, then `point`; the sleeper; x09's `stare` becomes `awe` on success and `anger` on failure |

Proof for the stage: `tools/run/capture.sh` gains a `--acting` mode that screenshots every character hotspot in its five states (available, selected, committed, success,
failure) with the actor framed at 2x, into `docs/shots/acting/<world>_<hotspot>.jpg`, and a contact sheet per world. The owner judges readability from those.

### 2.6 The Bassment without its caption band

The 63 passages' captions become acts on the creatures and items that already stand as hotspots (`content/trial/hotspots.json`): a creature that will fight you `block`s
with `anger`; one that will trade `offer`s; a luck test's thing `pulse`s; a victory makes the creature `bow` or `collapse`; a defeat makes it `laugh`. The same `acting`
field, validated by the same contract (`trial_kind` stays). `tools/trial/make_hotspots.py` authors it from a table keyed by creature kind, so 63 passages are one table.

## 3. Sister runs (Stage 2): the engine work for a path at its own tempo

### 3.1 Data layout

```
content/paths/<path>/run.json          timing.bpm = the path's tempo; worlds, nodes, cinematics; "path": {"id", "title", "entry_from": "<warehouse hotspot id>", "returns_to": "warehouse"}
content/paths/<path>/music.json        one entry per scene, "temporary": true until the owner's loop lands
content/paths/<path>/hotspots/<world>.json
content/story/maps/<map>.json          the path's maps (the same map format as the five worlds)
assets/story/<map>/                    the path's art (manifest, source, processed, textures, people)
content/imports/<path>/<scene>/        the owner's drops (stems and MIDI); beatshaper imports them to songs/packs/<path>_<scene>/
songs/packs/<path>_<scene>/            packs at the path's tempo
```

`RunData.load_files(run_path, music_path, packs_dir)` already takes paths; add `RunData.load_path(id)` and keep `load_default()` for the Warehouse run. `beatshaper.py` gains
`--path <id>`: the profile table gains `<path>_x1` with `source_bpm` = the path's tempo, and `validate`/`check`/`assign` read the path's `run.json` for the tempo instead of the
`BPM = 174` constant.

### 3.2 Graph rules for a path

The run's validator insists on one entry and one exit scene per world and routes to other worlds only from the exit. The paths are branch-and-rejoin graphs (two scenes of
one world may both be reached from the world before), so for a path's `run.json`:

* a world may list several `entry` scenes (`entries: [...]`; the world's own id stays a valid start and means the first); the save still records worlds;
* several scenes may be `exit_scene`; routes to another world's entry scenes are allowed from any of them; the graph must still be acyclic except through `loop` routes;
* every scene must still reach some ending scene; an **ending scene** (`"ending": "<name>"`) has one default hotspot whose `on_success.route` is `run:warehouse` (new prefix,
  next to `trial:`) and sets `keep:path_<id>_<name>`.

The same validator (`RunData`, `tools/run/check_hotspots.py`) checks a path with these relaxations when `run.json` carries `"path"`; the Warehouse run keeps the strict rules.

### 3.3 Entering and leaving: the tempo handoff

* The three portals are hotspots in the Warehouse: the luminous figure under a projected star on the **balcony** (`warehouse.balcony.star` → `path:gospel`), the flickering
  military radio with a bomber's shadow on the wall of the **booth** (`warehouse.booth.radio` → `path:squadron`), a small warm ember in a glass on a table at the **bar**
  (`warehouse.bar.ember` → `path:ember`). They are `kind: secret` with `look.available: pulse`, never the default, and always count inside the 2 to 4 rule for their scene
  (the floor is full; that is why they are in the second rooms). Failure: the portal flickers out, a `-4` energy dip, the scene's default route (the player has lost nothing but
  that room's chance; the portal is `repeatable`).
* `RunPlay` handles `path:<id>` as it handles `trial:`: at the commit the passage frame closes over beats 62 to 64 of the Warehouse phase; **on the downbeat** `RunAudio` stops the
  174 clock loop and starts the path's clock (`silent_loop(64, bpm)`: generalise the sample rate so `frames_per_beat` is an integer at any tempo), the path's `RunEngine`
  begins at its start scene on drums alone and the frame opens on the path's first room. The old voices fade over the two beats inside the frame (the existing `fade_beats`).
  The pads and the judge are the same objects; only `beat_s` changes, read from the active engine.
* Returning (`run:warehouse` from an ending, or the pause menu's leave) is the reverse: the frame closes on the path's last downbeat, the 174 clock restarts, `RunEngine.resume("warehouse")`
  with a fresh rail as `trial_leave` does. Energy carries across (a path that ends badly leaves you tired on the floor).
* `RW_RUN_PATH=<id>` starts a path directly (tests, captures, the owner's review); `RW_RUN_START` then names one of its scenes.

### 3.4 Save, home screen, difficulty

* `user://story_run.json` (version stays 2; a missing key is added on load) gains `"paths": {"<id>": {"reached": [world ids], "endings": [names]}}`. Start from a reached level shows a
  path's worlds in a section of their own once reached; a locked card says how the path opens (the portal's room).
* Depth per path world is its order (1 to 4); tiers as today. A path never loops back into the late worlds; it ends and returns.

### 3.5 Placeholders (D5)

`tools/content/make_path_placeholders.py <path>` writes, for every scene in the path's `run.json` that has no import, a pack in `songs/packs/<path>_<scene>/` at the path's tempo: an
8-bar drum loop (kick, snare, hats with the genre's pattern: four-on-the-floor for house, half-time for dubstep, a 16th-note bass pulse for psytrance), a bass loop and a synth pad,
each as Ogg plus MIDI, in the pack format `beatshaper.py import` writes. Synthesised with numpy as `make_run_effects.py` does; labelled `temporary` in `music.json`; the chart is the
MIDI. When the owner's import for a scene lands, `beatshaper.py import --path <id>` replaces the placeholder and clears the flag.

### 3.6 Tests for the stage

`tests/test_run_paths.gd`: a path's `run.json` loads with the relaxed rules; `RunData` rejects a pack at the wrong tempo for its path; the portal routes, the handoff (the clock's
`beat_s` before and after, the phase starts on the downbeat, cue times on the new grid), the return, the save migration; the matrix (`--filter run_matrix`) run once per path
under every tap policy; `tools/run/walk_run.sh --path <id>` walks every scene; `check_hotspots.py --path <id>` reports reachability and the 2 to 4 rule.

## 4. Path 1: The Life of Jesus (`gospel`), house, 124 BPM (Stage 3, the pilot)

A Gospel-inspired adventure with deliberate alternative-history branches. The main route follows recognisable events; the choices are about compassion, confrontation,
companionship, retreat and sacrifice, never rhythm as a measure of virtue. The resurrection ending follows the Gospel; the escape ending is explicitly imaginative. 17 scenes.

### 4.1 Worlds and maps (four maps)

| world | map | scenes | views (shared, lit differently) | people |
| --- | --- | --- | --- | --- |
| `jordan` (depth 1) | `galilee_shore` (dawn) | J00 Bethlehem (prologue, a night sky and a stable seen from the road), J01 the Jordan, J02 the Wilderness, J03 Nazareth | the riverbank (J01), the rocks (J02), the workshop door (J03); J00 is the riverbank at night with the star piece on | the Baptist, the tempter (a tall figure in a dust-coloured robe, `doubt` and `laugh`), neighbours, a carpenter |
| `galilee` (depth 2) | `galilee_shore` (day) and `hillside` | J04 the Lakeshore, J05 Capernaum, J06 the Mount, J07 the Storm | the shore with boats (J04, J07 with the storm pieces and night light), a village street (J05), the hillside (J06) | fishermen (two brothers with nets), a sick child and parents, a crowd of villagers, the disciples (a cast of twelve recurring actors with stable ids `d01`..`d12`) |
| `road` (depth 3) | `bethany` | J08 Bethany, J09 Loaves and Fishes, J10 the Entry | a courtyard with a table (J08), the hillside at dusk with baskets (J09, reuses `hillside`), the city gate with palms (J10) | the sisters of Bethany, a traveller with a lantern, the crowd at the gate |
| `jerusalem` (depth 4) | `jerusalem` | J11 the Temple, J12 Gethsemane, J13 the Trial, J14 Golgotha, J15 the Tomb, J16 the Road Beyond | the temple court (J11), the olive grove at night (J12), the praetorium (J13), the hill (J14, dusk), the garden tomb at dawn (J15), the open road at morning (J16, reuses `galilee_shore` day with the boats off) | money-changers, guards, priests, the governor, the sleeping disciples, soldiers, the women at the tomb |

### 4.2 Scenes, touches and outcomes

Arrows are the success destination; a failure goes to the other route unless a setback is named. Each scene's two touches, the cast beats that tell its story, and the owner's
music prompt (verbatim from the brief).

| scene | touch → success (failure) | cast: what the faces say | music prompt |
| --- | --- | --- | --- |
| J00 Bethlehem: the Star | one default: the road → J01 | shepherds `kneel`, `awe`; a mother looks at the camera, `relief` | 124 BPM soulful house, 8-bar seamless loop. Soft kick, dusty claps, warm organ, gentle plucks, choir-like synth and rounded bass. Separate editable MIDI tracks. |
| J01 Baptism in the Jordan | the descending dove (feature) → J02; the Nazareth rooftops (exit) → J03 | the Baptist `bow`s, `awe`, then `point`s to the wilderness; the crowd on the bank `cheer`s on success, `doubt`s on failure | 124 BPM uplifting gospel house, 8-bar seamless loop. Shimmering keys, warm bass, handclaps, four-on-floor kick and sparkling water percussion. Separate editable MIDI tracks. |
| J02 Temptation in the Wilderness | the path through the rocks (exit) → J04; the village fires (exit) → J05 | the tempter `offer`s (bread), `laugh`s at a failure, `shake_head`s and `recoil`s on success, `anger` | 124 BPM minimal deep house, 8-bar seamless loop. Dry kick, hollow percussion, sparse organ, uneasy bass pulse and desert-wind synth. Separate editable MIDI tracks. |
| J03 Nazareth Workshop | a neighbour at the door (character) → J05; nets on a cart (object) → J04 | the carpenter `write`s (measures), `nod`s; the neighbour `plead`s then `relief` / `shame` | 124 BPM organic house, 8-bar seamless loop. Wooden percussion, warm piano chords, mellow bass, soft shaker and gentle handclaps. Separate editable MIDI tracks. |
| J04 Calling the Fishermen | the gathering fishermen (character) → J06; a boat offshore (object) → J07 | the brothers `stare`, then `awe`; success: they drop the nets, `cheer`, and walk after the camera (they join the disciple cast); failure: `doubt`, back to the nets | 124 BPM funky house, 8-bar seamless loop. Bouncy bass, crisp claps, rhythmic guitar-like synth, bright organ and rolling hi-hats. Separate editable MIDI tracks. |
| J05 Healing in Capernaum | the waiting family (character) → J06; a southbound caravan (exit) → J08 | the parents `plead`, `fear`; the child `lie`s; success: the child sits up, parents `collapse` into `relief`, then `cheer`; failure: `cover_face`, `grief`, a setback cinematic (the camera is led out by the elder, `shake_head`) → J06 with −8 energy | 124 BPM soulful deep house, 8-bar seamless loop. Tender electric piano, rounded bass, soft drums, hopeful strings and delicate melodic responses. Separate editable MIDI tracks. |
| J06 Sermon on the Mount | the hillside crowd (feature) → J09; a departing boat (object) → J07 | the crowd `sit`s, faces `awe`; a heckler `laugh`s then `shame`s on success; the disciples `point` at the boat | 124 BPM joyful gospel house, 8-bar seamless loop. Rich organ chords, celebratory claps, melodic bass, uplifting piano and spacious choir-like synth. Separate editable MIDI tracks. |
| J07 Storm on Galilee | the shore beacon (feature) → J09; the southern road (exit) → J08 | the disciples `recoil`, `fear`, `plead`; success: the storm pieces go off on the downbeat, `relief`, `awe`; failure: `collapse`, the boat beaches on the bad rail → J08 | 124 BPM dark progressive house, 8-bar seamless loop. Thunderous kick, rolling toms, tense sub-bass, stormy pads and urgent arpeggios. Separate editable MIDI tracks. |
| J08 Bethany: the Shared Table | the people at the table (character) → J09; a waiting donkey (object) → J10 | the sisters `offer` bread, `happy`; one `write`s nothing but `stare`s with `doubt` (the traitor among the twelve, `d12`, looks away: `shame`) | 124 BPM warm soulful house, 8-bar seamless loop. Gentle Rhodes, soft kick, hand percussion, expressive bass and intimate organ chords. Separate editable MIDI tracks. |
| J09 Loaves and Fishes | the bread baskets (object) → J10; a traveller's lantern (character) → J08 | the crowd `plead`s (hungry); success: baskets fill (pieces), `cheer`, `laugh`; failure: the crowd `shake_head`s and drifts off, `sad` | 124 BPM euphoric gospel house, 8-bar seamless loop. Layered piano stabs, warm bass, claps, jubilant synth harmonies and uplifting four-on-floor drums. Separate editable MIDI tracks. |
| J10 Entry into Jerusalem | the Temple steps (exit) → J11; the olive grove (exit) → J12 | the crowd waves palms (`wave`, `cheer`); priests at the gate `block`, `anger`; a child `offer`s a palm | 124 BPM festival house, 8-bar seamless loop. Triumphant brass-like synths, driving kick, crowd-style percussion, bright organ and energetic bass. Separate editable MIDI tracks. |
| J11 The Temple | the money-changers' tables (object) → J12; the approaching guards (encounter) → J13 | money-changers `write`, `laugh`; success: tables overturned (pieces), merchants `recoil`, priests `stamp` with `anger`; failure: guards `block`, the camera is walked out → J13 | 124 BPM tense tech house, 8-bar seamless loop. Metallic percussion, sharp claps, distorted bass, clipped organ stabs and escalating rhythmic tension. Separate editable MIDI tracks. |
| J12 Gethsemane | the sleeping disciples (character) → J13; the shadowed path (exit) → J16 | disciples `sleep`; at beat 32 one wakes, `shame`; the traitor arrives at beat 48 with guards, `nod`s to them (`resolve`), kisses nothing (no contact; he `point`s); guards `block` | 124 BPM melancholic deep house, 8-bar seamless loop. Muted kick, sparse piano, low bass heartbeat, haunting pads and restrained percussion. Separate editable MIDI tracks. |
| J13 The Trial | the guarded passage (exit) → J14; the open side gate (exit) → J16 | the governor `write`s, `doubt`, then `shake_head` and washes his hands (an `offer` with a bowl prop); the crowd `stamp`s, `anger`; one woman `cover_face` | 124 BPM cinematic dark house, 8-bar seamless loop. Heavy kick, ominous organ, slow chord changes, deep bass and tense metallic percussion. Separate editable MIDI tracks. |
| J14 Golgotha | on rails; one default → J15. Rhythm changes the staging: a passed block brings a witness forward (`kneel`, `grief`), a missed block a soldier's `laugh`; the sky pieces darken block by block | the women `cover_face`, `grief`; a soldier `stare`s then `awe` at beat 60 | 124 BPM atmospheric minimal house, 8-bar seamless loop. Sparse kick, distant bells, solemn organ, subdued sub-bass and slowly rising ambient strings. Separate editable MIDI tracks. |
| J15 The Empty Tomb (ending `tomb`) | the rolled stone (feature) → `run:warehouse`, sets `keep:path_gospel_tomb` | the women arrive `grief`, find the stone moved (piece), `fear` → `awe` → `cheer`; a gardener `point`s to the road; dawn light swells | 124 BPM uplifting melodic house, 8-bar seamless loop. Radiant piano, warm bass, soaring choir-like pads, bright claps and expansive harmonies. Separate editable MIDI tracks. |
| J16 The Road Beyond Jerusalem (ending `road`) | the open road (exit) → `run:warehouse`, sets `keep:path_gospel_road` | two followers walk with the camera, `relief`, `laugh`; a shepherd `bow`s; the city behind, guards `shake_head` and turn back | 124 BPM reflective organic house, 8-bar seamless loop. Gentle percussion, warm acoustic plucks, wandering bass melody, soft piano and hopeful atmospheric pads. Separate editable MIDI tracks. |

Routes within a world are door walks; J03→J04/J05, J07→J08, J10→J11/J12 cross worlds through the passage frame. J14 and J00 are single-way scenes (the window still opens; the one
lit way is the way), as the chill-out is today.

### 4.3 Art brief

Sunlit, dusty, warm: ochre, terracotta, olive, a cobalt sky, white limestone, the lake a flat silver-blue; night scenes indigo with oil-lamp amber; Jerusalem pale stone and
deep shadow; Golgotha a bruised sky that darkens block by block. People: robes and tunics in undyed wool, stripes, headscarves and shawls, sandals, the fishermen bare-armed
with nets, soldiers in a plain lamellar cuirass and plumeless helmet (no specific historical emblem), priests in white with a blue sash, the governor in a white toga with
one red band. Props: nets, baskets, bread, a lantern, palms, a bowl, coins and tables. Hair: beards and long hair common; no actor is drawn to resemble any painting or film.
Wardrobe archetypes in `wardrobe.py`: `fisher`, `villager`, `disciple`, `priest`, `soldier`, `merchant`, `woman_of_bethany`, `child`, `elder`, `governor`, `tempter`, `baptist`.

### 4.4 Done when

All 17 scenes play on placeholders at 124 BPM from the balcony portal and back; both endings reached by `walk_run.sh --path gospel` and set their flags; every scene's cast and
every character hotspot's acting is in data and shot into `docs/shots/acting/gospel_*`; `check_hotspots.py --path gospel` clean; `docs/MUSIC_HANDOFF.md` gains the path's 17-line
shopping list (regenerated by `music_handoff.py`); `docs/STORY_ART.md` gains the four maps' sections in its format.

## 5. Path 2: The Mission Count (`squadron`), dubstep, 140 BPM with a half-time feel (Stage 4)

An original story in the shape of the owner's brief: the player is a bombardier on a small Mediterranean island in a war that never ends, whose only wish is to go home.
Every way out runs into **the Clause**: a regulation that says anyone sane enough to ask to be grounded is sane enough to fly. The Flight Surgeon, the Quartermaster (who
runs a syndicate that sells the squadron its own supplies), the Colonel (who raises the mission count whenever anyone reaches it), the young Gunner, and the Clerk who stamps
everything. Chaotic and darkly comic; the environment itself behaves absurdly. 14 scenes.

**The central mechanic.** A *successful* rhythm can still be thwarted by the bureaucracy: the certificate scene (C06) resolves success with its own cinematic (the stamp slams,
the camera turns to the door, a second stamp lands the other way) and routes to a different scene than the touch intended, with the Clerk's `laugh` and the Surgeon's `shame`.
This is `on_success` carrying a `cinematic` and a `route` that is not the obvious one; the contract allows it. Use it in C06, C09 and C11 only, so the player learns the joke
and nowhere else is the success outcome ever the failure's.

### 5.1 Worlds and maps (four maps)

| world | map | scenes | views |
| --- | --- | --- | --- |
| `base` (1) | `airfield` | C01 Briefing Room, C02 the Flight Line, C03 the Hospital | the briefing hut (a board, a doorway onto the field), the line (a bomber's nose and ladder, crates), the hospital tent |
| `air` (2) | `airfield` (night) and `city` | C04 the Bombing Mission, C05 the Syndicate, C06 the Surgeon's Office | the bomber's interior (a view of the glass nose, the release lever, a fire), the Quartermaster's warehouse of crates and ledgers, the office with a desk, two doors and a stamp |
| `city` (3) | `city` | C07 the Gunner's Last Flight (the bomber interior again, red light), C08 the Old City streets, C09 the Colonel's Deal, C10 the Ruined City | an arched street with a staff car, the Colonel's office (a medal, a map), the ruined street at night with a train beyond |
| `escape` (4) | `harbour` | C11 Endless Missions (the briefing hut, the count painted higher), C12 Escape North, C13 the Neutral Coast (ending `free`), C14 Captured | a harbour with a boat and searchlights, a bright shore with birds and wind (the war's sounds gone), a cell with a window latch |

### 5.2 Scenes, touches and outcomes

| scene | touch → success (failure) | cast | music prompt |
| --- | --- | --- | --- |
| C01 Briefing Room | the mission board (object) → C02; the empty cot through the doorway (exit) → C03 | the Colonel `point`s at the board, `resolve`; airmen `salute` on the kick; one `shake_head`s, `fear` | 140 BPM dark dubstep, 8-bar seamless loop. Military radio synth, half-time snare, metallic kick, growling FM bass and eerie brass stabs. Separate editable MIDI tracks. |
| C02 The Flight Line | the bomber's ladder (object) → C04; the stacked crates (object) → C05 | the Gunner `wave`s from the hatch, `happy`; the Quartermaster `offer`s (an egg), `laugh`; a mechanic `stare`s, `doubt` | 140 BPM industrial dubstep, 8-bar seamless loop. Engine-like bass growls, marching percussion, heavy snare, mechanical synth pulses and rising tension. Separate editable MIDI tracks. |
| C03 The Hospital | the Surgeon's clipboard (character) → C06; the kitchen hatch (exit) → C05 | patients `lie`; the Surgeon `write`s, `doubt`; a soldier in plaster `laugh`s; success: `nod`; failure: `shake_head`, the hatch opens | 140 BPM minimal dubstep, 8-bar seamless loop. Muted half-time drums, heartbeat sub-bass, sterile bell synth, sparse percussion and uneasy atmospheric drones. Separate editable MIDI tracks. |
| C04 The Bombing Mission | the release lever (object) → C07; the emergency controls (object) → C03 | the crew `fear`; flak pieces flash on the drops; the Gunner `point`s at the ground; success: `relief` then `grief` as the Gunner is hit at beat 60; failure: the pilot `shake_head`s, the plane turns back (setback → C03, −6) | 140 BPM aggressive dubstep, 8-bar seamless loop. Explosive kick, distorted Reese bass, rapid metallic percussion, siren synths and terrifying wobble drops. Separate editable MIDI tracks. |
| C05 The Syndicate | the ledger (object) → C06; the departing truck (exit) → C08 | the Quartermaster `write`s with glee, `laugh`, `offer`s a share; clerks `nod` in time; failure: `block`, `anger`, the truck leaves without you | 140 BPM funky experimental dubstep, 8-bar seamless loop. Comical brass stabs, rubbery wobble bass, swung percussion, sharp snares and playful synth glitches. Separate editable MIDI tracks. |
| C06 The Surgeon's Office (the Clause) | the certificate (object): success → `cinematic squadron.double_stamp` → C09 (not the door the touch promised), the Clerk `laugh`s, the Surgeon `shame`; failure → C02 (another flight order, the Clerk `nod`s, `resolve`) | the Surgeon `plead`s with the Clerk; the Clerk `write`s and `stare`s, `neutral`, unmoved | 140 BPM glitch dubstep, 8-bar seamless loop. Stuttering drums, reversed synth stabs, elastic bass, mechanical clicks and deliberately disorienting rhythmic variations. Separate editable MIDI tracks. |
| C07 The Gunner's Last Flight | the bloodied jacket (object) → C10; the medical kit (object) → C03 | the Gunner `lie`s, `fear` then `neutral` (eyes close at beat 48); the crew `cover_face`; the pilot `stare`s ahead, `resolve`; no cheering in this scene whatever the play (cast only, the crowd mood is pinned `sad`) | 140 BPM cinematic dark dubstep, 8-bar seamless loop. Sparse kick, distant snare, deep sub-bass, mournful synth melody and ominous low drones. Separate editable MIDI tracks. |
| C08 The Old City | the damaged arch (exit) → C10; the staff car (object) → C09 | a street singer `laugh`s and `offer`s a hat; military police `block` at the arch, `stare`; a child `beckon`s through it | 140 BPM noir dubstep, 8-bar seamless loop. Jazzy piano stabs, muted trumpet-like synth, shuffled drums, gritty sub-bass and restless urban percussion. Separate editable MIDI tracks. |
| C09 The Colonel's Deal | the medal (object): success → `cinematic squadron.medal_pinned` → C11 (the count goes up anyway; the Colonel `laugh`s), failure → C12 (thrown out, the map falls into your hands); the escape map (object) → C12 | the Colonel `offer`s the medal, `resolve`; an aide `write`s; the Chaplain in the corner `shake_head`s, `grief` | 140 BPM sinister dubstep, 8-bar seamless loop. Clockwork percussion, distorted bass pulses, clipped military brass, sharp snare and suspenseful synth risers. Separate editable MIDI tracks. |
| C10 The Ruined City | the night train (object) → C12; the headquarters (exit) → C09 | survivors `collapse`, `grief`; a woman `plead`s for help; a drunk officer `laugh`s; the train's lamp pulses | 140 BPM atmospheric dubstep, 8-bar seamless loop. Broken piano notes, low wobble bass, distant metallic hits, mournful pads and restrained half-time drums. Separate editable MIDI tracks. |
| C11 Endless Missions (loop) | the aircraft (exit) → C02 (`loop`); the broken radio (object): success → C12, failure → `cinematic squadron.count_raised` (the Clerk paints the number higher, `laugh`) → C02 | the airmen `salute` slower each block (the cast slows the act's beats); the Colonel `point`s at the count; the Chaplain `cover_face` | 140 BPM relentless industrial dubstep, 8-bar seamless loop. Repeating alarm synths, pounding drums, grinding bass, harsh metallic stabs and cyclical tension. Separate editable MIDI tracks. |
| C12 Escape North | the waiting boat (object) → C13; the searchlights (exit) → C14 | a fisherman `beckon`s from the boat, `fear`, then `nod`; a sentry `stare`s, turns away (`shame`: he lets you go) on success, `point`s and `stamp`s on failure | 140 BPM suspenseful melodic dubstep, 8-bar seamless loop. Urgent bass pulses, soft piano, driving percussion, rising synth arpeggios and hopeful chord progression. Separate editable MIDI tracks. |
| C13 The Neutral Coast (ending `free`) | the shore (exit) → `run:warehouse`, sets `keep:path_squadron_free` | the fisherman `laugh`s with you, `relief`; the war pieces are off; birds (a crowd prop), wind; a woman on the quay `wave`s | 140 BPM uplifting melodic dubstep, 8-bar seamless loop. Warm chords, gentle sub-bass, airy synth leads, bright percussion and triumphant half-time drums. Separate editable MIDI tracks. |
| C14 Captured | the window latch (object) → C12; the stamped order (object) → C11 | a guard `block`s, `anger`; the Clerk `write`s, `laugh`; a cellmate `shake_head`s then `point`s at the latch | 140 BPM oppressive dark dubstep, 8-bar seamless loop. Heavy distorted bass, prison-door metallic percussion, ominous synth drones and slow half-time snare. Separate editable MIDI tracks. |

There is one escape ending; the loop C11 → C02 is the absurd ending the player lives until they break out through the radio or the map (D6: the loop always has the radio as a way out).

### 5.3 Art brief

Grainy, over-exposed Mediterranean daylight (bleached khaki, olive drab, a white sky, orange dust) against the bomber's green-black interior lit by instrument lamps; the
city in sepia and neon-less noir; the harbour a cold blue night cut by white searchlight beams; the neutral coast is the only saturated scene in the path. People: generic
1940s air-force khaki without insignia of any real force (no roundels, no real flags), the Quartermaster in an apron over his uniform, the Surgeon in a stained white coat,
the Clerk small with round glasses and a stamp, the Colonel broad with a chestful of ribbons drawn as coloured bars, the Gunner a boy. Wardrobe archetypes: `airman`, `officer`,
`clerk`, `surgeon`, `quartermaster`, `gunner`, `mp`, `civilian_city`, `fisherman`, `patient`. The bomber is drawn as an invented twin-engine type.

## 6. Path 3: The Ember Road (`ember`), psytrance, 145 BPM (Stage 5)

An original fantasy journey in the shape of the owner's brief. In the orchard village of the Hollow a grandmother dies and leaves the player the **Ember**: a coal that never
goes out, cut from the Forge under the Glass Mountain in the east, which warms whoever carries it and whispers to them to keep it. The Ashen Riders are coming for it. The only
way to be free of it is to carry it back and quench it in the Drowned Spring beneath the mountain. Companions: Bram the gardener (loyal, `happy`, `fear` easily), the Warden (a
ranger, `resolve`), the Lady of the Birch Hall (`awe`, `grief`); and the Hollow One, a starved former carrier who wants it back and guides you to get it. Hypnotic, atmospheric;
the whispering Ember is the bass. 15 scenes.

### 6.1 Worlds and maps (four maps)

| world | map | scenes | views |
| --- | --- | --- | --- |
| `hollow` (1) | `orchard` | E00 the Orchard (prologue), E01 the Ford at Night, E02 the Lantern Inn | the orchard at harvest, the ford under a black sky with riders on the far bank, the inn's common room |
| `north` (2) | `birch_hall` and `deep_halls` | E03 the Birch Hall, E04 the High Pass, E05 the Deep Halls, E06 the Falls | a white hall of birch pillars, a snow pass (the hall's map with the snow view), a pillared dark with a lake, the top of a waterfall with boats |
| `marsh` (3) | `ash_land` | E07 the Reed Marsh, E08 the Black Wall, E09 the Stair of Bells, E10 the Ash Plain | reeds and lights under water, a wall of black stone with a gate, a cliff stair hung with bells and a blind sentinel, a grey plain under a red sky |
| `mountain` (4) | `ash_land` (the mountain views) | E11 the Throat, E12 the Drowned Spring (ending `quenched`), E13 the Keeper (ending `kept`), E14 Taken (setback) | a tunnel lit red, a cavern with a black pool and a shaft of light, the same cavern lit by the Ember alone, the riders' camp |

### 6.2 Scenes, touches and outcomes

| scene | touch → success (failure) | cast | music prompt |
| --- | --- | --- | --- |
| E00 The Orchard | one default: the gate → E01 | the grandmother `lie`s, `offer`s the Ember, `relief`, eyes close at beat 48; Bram `cover_face`; the village `bow`s | 145 BPM progressive psytrance, 8-bar seamless loop. Soft rolling kick, warm plucked arpeggios, rounded bass pulse, harvest-bell chimes and airy pads. Separate editable MIDI tracks. |
| E01 The Ford at Night | the shallow crossing (exit) → E02; Bram's lantern (character) → E03 | riders on the far bank `stare`, `anger`, their horses stamp (a prop anim); Bram `plead`s; success: the river rises (pieces), riders `recoil`; failure: Bram `collapse`s (the Ember's cold reaches him), setback → E02 with −8 | 145 BPM dark psytrance, 8-bar seamless loop. Driving kick, galloping 16th bass, metallic hoof percussion, low horn drones and tense rising leads. Separate editable MIDI tracks. |
| E02 The Lantern Inn | the hooded man by the fire (character, the Warden) → E04; the back door (exit) → E03 | drinkers `laugh`; the innkeeper `write`s then `doubt`s; the Warden `stare`s, `resolve`, `beckon`s; a rider's shadow crosses the window at beat 48, the room `fear`s | 145 BPM full-on psytrance, 8-bar seamless loop. Punchy kick, bouncing bass, tavern-fiddle synth, clapping percussion and a whispering filtered lead. Separate editable MIDI tracks. |
| E03 The Birch Hall | the Lady's hand (character) → E05; the map on the table (object) → E04 | the Lady `offer`s a vial, `awe` then `grief` (she sees the road); the hall `bow`s; the Warden `point`s at the map; failure: the Lady `shake_head`s, `fear`, the vial withheld (flag `ember_no_vial`, which makes E09 harder: its failure is the setback) | 145 BPM atmospheric psytrance, 8-bar seamless loop. Deep kick, glassy arpeggios, choir-like pads, flowing bass and birch-wind textures. Separate editable MIDI tracks. |
| E04 The High Pass | the cave mouth (exit) → E05; the ridge path (exit) → E06 | Bram `recoil`s from the wind, `fear`; the Warden `beckon`s; success: the storm pieces calm; failure: a slide (bad rail), Bram `plead`s | 145 BPM hypnotic psytrance, 8-bar seamless loop. Relentless kick, howling filtered noise, icy plucks, low throbbing bass and sparse hollow percussion. Separate editable MIDI tracks. |
| E05 The Deep Halls | the far bridge (exit) → E06; the drowned thing's lake (feature, encounter) → setback E04 on failure, E06 on success | the companions `stare` into the dark, `awe`; drums from below (a prop); at beat 48 the thing rises (piece); the Warden `block`s it, `resolve`; on failure the Warden falls (`collapse`, flag `ember_warden_lost`, he is absent from here on) | 145 BPM dark progressive psytrance, 8-bar seamless loop. Cavernous kick, sub-bass drones, dripping water percussion, dissonant stabs and distant drum hits. Separate editable MIDI tracks. |
| E06 The Falls | Bram's boat (character) → E07; the Warden's horn (object) → E08 (if `ember_warden_lost`, the horn is a rider's horn: → E14) | the company `offer`s to come; the Ember whispers (bass); success: Bram `nod`s, `resolve`; failure: Bram `cover_face`, you go on alone (flag `ember_alone`) | 145 BPM melodic psytrance, 8-bar seamless loop. Cascading water arpeggios, deep kick, emotional lead, flowing bass and distant choir pads. Separate editable MIDI tracks. |
| E07 The Reed Marsh | the Hollow One (character) → E09; the lights in the water (feature) → E08 | the Hollow One `beckon`s, `plea`, then `laugh`s behind your back (a `then` act facing away, `anger`); the lights are faces (`stare`, `grief`) | 145 BPM swampy psytrance, 8-bar seamless loop. Wet kick, bubbling bass, croaking percussion, eerie whispered vocal synth and submerged pads. Separate editable MIDI tracks. |
| E08 The Black Wall | the gate (encounter) → E14 on failure, E10 on success; the crack in the wall (exit) → E09 | riders `block`, `anger`; the Hollow One `point`s at the crack, `doubt`; the gate's mouths `laugh` | 145 BPM industrial psytrance, 8-bar seamless loop. Hammering kick, grinding bass, iron-gate percussion, war-horn synth stabs and oppressive drones. Separate editable MIDI tracks. |
| E09 The Stair of Bells | the bells (feature: silence them) → E10; the blind sentinel (encounter) → E11 on success, E14 on failure (E14 also on a failed bells touch if `ember_no_vial`) | the sentinel `stare`s with no eyes (`neutral`), head tilting to the kick; the Hollow One `cover_face`s (`shame`: he led you here); success: the sentinel `bow`s and sleeps | 145 BPM minimal psytrance, 8-bar seamless loop. Tiptoe kick, muted bass pulse, tuned bell percussion, held breath pads and a single tense lead. Separate editable MIDI tracks. |
| E10 The Ash Plain | the mountain road (exit) → E11; the dark tower's light (feature) → E14 | riders cross in the distance; the Hollow One `plead`s for the Ember, `plea`; Bram (if present) `offer`s water, `relief` | 145 BPM driving psytrance, 8-bar seamless loop. Marching kick, scorched bass, dry rattling percussion, ash-wind noise sweeps and a distant tolling lead. Separate editable MIDI tracks. |
| E11 The Throat | the way down to the water (exit) → E12; the Ember's whisper (feature: listen) → E13 | the Hollow One follows, `stare`, `anger`; the walls pulse red with the bass | 145 BPM dark psytrance, 8-bar seamless loop. Pounding kick, molten bass growls, crackling fire percussion, volcanic drones and a hypnotic whispering lead. Separate editable MIDI tracks. |
| E12 The Drowned Spring (ending `quenched`) | the pool (feature) → `run:warehouse`, sets `keep:path_ember_quenched`; on failure the Hollow One snatches it and falls in with it (`cinematic ember.snatched`, the same ending reached another way, `grief` and `relief` together) | the Hollow One `plead`s then `recoil`s from the water; Bram `cheer`s; light swells white; the riders' horns stop | 145 BPM uplifting psytrance, 8-bar seamless loop. Clean kick, radiant arpeggios, warm bass, water-droplet percussion and a soaring resolving lead. Separate editable MIDI tracks. |
| E13 The Keeper (ending `kept`) | the Ember (feature: keep it) → `run:warehouse`, sets `keep:path_ember_kept` | Bram `recoil`s, `fear`, and backs away; the Hollow One `laugh`s and `bow`s to you; the cavern lit only by the Ember; the camera's own shadow lengthens | 145 BPM sinister psytrance, 8-bar seamless loop. Slow-burn kick, seductive warm bass, glowing pad swells, ember-crackle percussion and a lead that never resolves. Separate editable MIDI tracks. |
| E14 Taken (setback) | a loose stake (object) → E10; the riders' captain (encounter) → E08 | riders `laugh`, `stamp`; the captain `offer`s your life for the Ember, `resolve`; Bram (if present) `plead`s | 145 BPM oppressive psytrance, 8-bar seamless loop. Heavy kick, chained metallic percussion, low horn drones, grinding bass and cold rising sirens. Separate editable MIDI tracks. |

### 6.3 Art brief

Deep greens and harvest gold in the Hollow; white and silver in the Birch Hall; black-blue in the Deep Halls with a single cold light; the marsh in teal and bioluminescent
green; the ash lands red-grey under a smoke sky; the Drowned Spring black water and a white shaft. The Ember is the only warm light east of the ford and the bass makes it
pulse. People: hand-spun wool and leather in the Hollow, no pointed ears, no wizard hats or staves, the Warden in a grey hooded cloak with a plain sword, the Lady in white
with birch-leaf embroidery, the Hollow One gaunt, grey, barefoot, wrapped in rags with wide pale eyes (the greys' big-eye rule), the riders faceless in ash-grey hoods with
only a red glint. No ring, no eye, no map of a known land; the Glass Mountain is a black cone of obsidian with a single red vent. Wardrobe archetypes: `villager_hollow`,
`bram`, `warden`, `lady`, `birch_folk`, `innkeeper`, `drinker`, `hollow_one`, `rider`, `sentinel`, `captain`.

## 7. Stages, commits and proof

Each stage is one or more commits on `main`, `bash tools/test.sh` green before each, pushed. Commit messages name the stage and any divergence from this document.

| stage | work | done when | proof committed |
| --- | --- | --- | --- |
| 1a | faces (2.1), acts (2.2), sheet selection by directed actors, `check_assets` | fourteen faces and all acts bake for a test actor per chapter; sheets within +15 % | `docs/shots/faces/<chapter>_acting.jpg`, sizes in the commit |
| 1b | the acting contract (2.3): validator, engine events, `StoryCrowd.direct`, tests | `tests/test_run_cast.gd`, `test_hotspots_engine.gd` extended; every shipped hotspot still resolves both ways | test counts in the commit |
| 1c | silent HUD and Bassment (2.4, 2.6), `RW_DEV_TEXT` | `tests/test_run_hud_silent.gd` passes; the old caption tests pass with the variable | before/after shots of a scene change and the Bassment |
| 1d | the acting pass on the five worlds (2.5) | 30 character hotspots with `acting`, every scene with `cast`; `capture.sh --acting` | `docs/shots/acting/<world>_*.jpg` and contact sheets |
| 2 | sister runs (3): data layout, relaxed graph rules, the three portals, the tempo handoff, save, home, placeholders, beatshaper `--path` | `tests/test_run_paths.gd`; a stub path of two scenes at 124 BPM entered and left from the balcony on placeholders | a recording of the handoff checked by `check_run_audio.py` (the clock's beat grid before and after) |
| 3 | the Gospel path (4) | 4.4 | shots per scene, both endings walked |
| 4 | the Mission Count (5) | all 14 scenes, the Clause scenes' success cinematics, the loop with its way out | as above |
| 5 | the Ember Road (6) | all 15 scenes, three endings/setback, the flags that change later scenes | as above |
| 6 | handover: rewrite `docs/HANDOVER.md` (what was verified, what was not: the owner's phone run, the owner's real loops), update `README.md`, `docs/CONTINUOUS_RUN.md` (paths), `docs/STORY_ART.md` (the twelve new maps), `docs/MUSIC_HANDOFF.md` | | |

Stage 2 may be started before 1d is finished (different files); stages 3 to 5 are sequential and each may be the end of a session.

## 8. Things already known, so the agent does not rediscover them

* `HotspotContract.MAX_PER_SCENE` is 4 counted at start; the Warehouse floor is already full (two exits, the wizard, the dancer). That is why the portals are in the bar, balcony and booth.
* The route lock (`docs/CONTINUOUS_RUN.md`) compares the chart pack of block 0 of the next scene at beat 60.5; a path's siblings that play different packs lock exactly as the Warehouse's do. A path's scene table above never offers two routes to scenes whose block 0 differs in family, so the lock only greys a route after the tempo is already settled.
* `RunAudio.silent_loop` picks a sample rate so that a beat is a whole number of frames (8700 Hz at 174). At 124, 140 and 145 BPM choose the rate the same way (`60 / bpm * rate` integral): 8680, 8400, 8700 work; assert it in a test.
* The crowd's `dir` dictionary already carries `state`, `from`, `until`, `sync`, `force`; `direct` extends it with `face` and `look_at` and the character's `sheet_pick` chooses the frame by state **and** face.
* Faces are baked per state: an act with a non-default face is a separate frame set. Keep the per-actor act list small (2.2's rule) and the sheets stay in budget.
* `check_assets.py --determinism` rewrites `processed/` and `textures/` with bytes that differ on some machines; restore those with `git checkout`, as `docs/FACE_POLISH.md` says, and commit code and regenerated sheets separately.
* The owner's loops arrive as Beat Shaper or DAW exports; `beatshaper.py scan` tells you their tempo and `check` fits the drums to it. A loop at the wrong tempo for its path is the owner's to re-export, not the agent's to time-stretch.
* The Underworld still plays temporary Lv2 packs; that is not this plan's problem.
* No text in play means no text: not in a hotspot's look, not in a cinematic, not on a prop (a painted mission count is a number on a board in the world and allowed; a floating label is not).
