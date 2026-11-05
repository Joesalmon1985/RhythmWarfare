# The Gospel path (`gospel`): Stage 3 of docs/THREE_PATHS_AND_FACES_PLAN.md

House, 124 BPM, 17 scenes in four worlds, entered from the star on the Warehouse balcony and left by either of two endings back onto the Warehouse floor. Written by the Stage 3 agent;
Stage 6 merges the parts of this file that belong in `docs/CONTINUOUS_RUN.md`, `docs/STORY_ART.md`, `docs/MUSIC_HANDOFF.md` and `docs/HANDOVER.md` (none of those was edited here, on purpose).

## What is where

| What | Where |
| --- | --- |
| the run: 17 scenes, 4 worlds, cast, set pieces, block staging, 23 cinematics | `content/paths/gospel/run.json` (written by `tools/content/make_gospel.py`) |
| the hotspots (43; every character hotspot carries `acting`) | `content/paths/gospel/hotspots/{jordan,galilee,road,jerusalem}.json` |
| music assignment (temporary placeholders) and the owner's prompts, verbatim | `content/paths/gospel/music.json` (`prompt` per scene), `prompts.json` |
| extra walks (both endings, the branches) | `content/paths/gospel/walks.json` |
| the four maps and their people | `content/story/maps/{galilee_shore,hillside,bethany,jerusalem}.json`, `content/story/<map>.json` (written by `tools/story/art/gospel_maps.py`) |
| the art: 40 textures and skies, 67 billboard sprites and set pieces, baked people | `assets/story/<map>/` (built by `tools/story/build_gospel_art.py` from `gospel_tex.py`, `gospel_things_a.py`, `gospel_things_b.py`, `wardrobe.gospel()`) |
| placeholder music: 17 packs at 124 BPM | `songs/packs/gospel_<scene>/` (`tools/content/make_path_placeholders.py gospel`) |
| tests | `tests/test_gospel.gd` (12 tests), `tools/content/test_gospel.py` (5), `tests/test_run_paths.gd` (the portal test now follows the data), `check_hotspots.py --path gospel`, `walk_run.sh --path gospel` |
| proof shots | `docs/shots/gospel/<scene>_a|b.jpg` (`tools/run/shoot_gospel.sh`), `docs/shots/acting/gospel_*.jpg` (`tools/run/acting_gospel.py`) |

Regenerate everything: `python3 tools/story/build_gospel_art.py --people` (maps, story data, textures, sprites, people sheets), `python3 tools/content/make_gospel.py`,
`python3 tools/content/make_path_placeholders.py gospel`, `python3 tools/content/make_gospel.py --music-only`, then `godot --headless --path . --import`.

## Worlds, maps and scenes

Divergence from the plan's table 4.1 (the engine has one map per run world: a door walk inside a world never changes stage): the worlds are `jordan` -> `galilee_shore`, `galilee` -> `hillside`
(the shore with boats, the village street, the slope and the storm all stand on the one map, so the plan's "galilee_shore day" is `hillside`'s lakeshore and `galilee_shore` is the Jordan's alone),
`road` -> `bethany` (the courtyard, the dusk hill with the baskets and the city gate), `jerusalem` -> `jerusalem` (six views). 17 views in all (the plan counted about ten: a view per scene is what lets
a scene have its own light, sky, crowd and set pieces), 130 people (`d01`..`d12` recur with the same look in every map: `wardrobe.dress` seeds a disciple from "gospel/dNN").

| scene id | view (map) | touches and where they lead (success / failure) | set pieces |
| --- | --- | --- | --- |
| `jordan` J00 Bethlehem | `bank_night` (galilee_shore) | the road -> J01 (default); the shepherd (a second hotspot: the contract needs two) | `star` on |
| `jordan.baptism` J01 | `bank_dawn` | the dove (feature) J02 / J03; Nazareth's rooftops (exit, default) J03 | `dove` on |
| `jordan.wilderness` J02 | `rocks` | the path through the rocks (default) J04; the village fires J05; the tempter reacts to either | |
| `jordan.nazareth` J03 | `workshop` | the road (default) J04; the neighbour (character) J05 / J04; the nets on the cart J04 / J05 | |
| `galilee` J04 | `lakeshore` (hillside) | the road to the hillside (default) J06; the fishermen J06 / J07; a boat offshore J07 / J06 | |
| `galilee.capernaum` J05 | `street` | the road to the hillside (default) J06; the family J06 / J06 with the setback cinematic `led_out` (-8); the caravan J08 | |
| `galilee.mount` J06 | `slope` | the road (default) J09; the crowd J09 / J07; a departing boat J07 / J09 | |
| `galilee.storm` J07 | `storm` | the road (default) J09; the southern road J08; the shore beacon J09 / J08 | storm cloud, rain, lightning on; the beacon's success switches them off |
| `road` J08 Bethany | `courtyard` (bethany) | the road (default) J09; the people at the table J09 / J10; the donkey J10 / J09 | |
| `road.loaves` J09 | `hill_dusk` | the road (default) J10; the baskets J10 / J08 (a loop); the traveller's lantern J08 / J10 | baskets fill on success |
| `road.entry` J10 | `gate` | the Temple steps (default) J11; the olive grove J12 | |
| `jerusalem` J11 Temple | `temple` (jerusalem) | the garden (default) J12; the tables J12 / J13 with `walked_out`; the guards J13 / J12 | tables stand, then fall on success |
| `jerusalem.gethsemane` J12 | `grove` | the road (default) J13; the sleeping disciples J13 / J16; the shadowed path J16 | the traitor and the guards (group `late`) are brought in by their cast beats |
| `jerusalem.trial` J13 | `praetorium` | the guarded passage (default) J14; the open side gate J16 | |
| `jerusalem.golgotha` J14 | `hill` | on rails: the hill (default) J15; the women (a second hotspot, no route) | `dark1`..`dark3` and the block staging |
| `jerusalem.tomb` J15 (ending `tomb`) | `tomb` | the garden way (default) and the rolled stone, both `run:warehouse`, both set `keep:path_gospel_tomb` | the stone rolls at block 0 |
| `jerusalem.road` J16 (ending `road`) | `road` | the road (default) `run:warehouse`, sets `keep:path_gospel_road`; the followers | |

Other divergences. (1) J00 and J14 are single-way scenes in the plan; the contract needs two hotspots in every scene, so each has a second, harmless one (the shepherd, the women: energy only).
(2) A path's exit scene may also lead on inside its world and a route may lead to a non-entry scene of its own world (`RunData`: `is_path()` relaxes two checks; J05, J06, J07 route within `galilee` and out of it).
(3) `tools/run/check_hotspots.py`: for a path a route needs *some* hotspot that leads to it (a feature, an object, a person), not an exit of its own; the main run keeps the strict rule.
(4) The scene shots do not show the plan's "hotspot acting at beats" in motion: only still frames from the virtual clock exist (see below).

## The acting

Every scene has 3 to 9 `cast` lines (the plan's 4.2 column, in `tools/content/make_gospel.py`): shepherds `kneel` with `awe` while the mother looks at the camera with `relief`; the Baptist `bow`s and `point`s
to the wilderness; the tempter `offer`s, `laugh`s at a failure and `recoil`s on success; the carpenter `write`s; the brothers `stare` and then `awe`; the parents `plead` with `fear`, the child `lie`s and sits
up on success (a cast line on the flag `gospel_healed`), a setback cinematic where the elder leads the camera out; the sermon crowd `sit`s with `awe` and the heckler `laugh`s, then `shame`s on success; the
disciples `recoil` and `plead` in the storm, `relief` and `awe` when it is calmed; the sisters `offer` bread while `d12` looks away with `shame`; the hungry crowd `plead`s, then `cheer`s and `laugh`s or
`shake_head`s; the priests `block` at the gate; the money-changers `write` and `laugh`, then `recoil` when the tables fall while the priests `stamp`; the sleepers sleep, `d11` wakes with `shame`, the traitor `nod`s
to the guards and `point`s (no contact); the governor `write`s, `shake_head`s and `offer`s the bowl while the crowd `stamp`s and one woman `cover_face`s; Golgotha (below); the women's `grief` -> `fear` -> `awe` -> `cheer`
at the tomb and the gardener `point`s to the road; the followers `laugh`, the shepherd `bow`s and the guards `shake_head`.
Every character hotspot (shepherd, neighbour, fishermen, family, the sermon crowd's person, table, lantern, guards, sleepers, women, followers) has all five `acting` states, and so do the exits and features that name a
person (the tempter at J02, the Baptist at the dove, a disciple at the beacon, the gardener at the stone). Only what the data names is baked into the sheets (`tools/story/art/directed.py` now also reads every `content/paths/*`).

**The Golgotha rule** (`block_fx` on `jerusalem.golgotha`): at each block's boundary the staging follows the play. Every block the sky darkens whatever happens (`dark1`, `dark2`, `dark3`); a passed block brings
a witness forward (`x1`, `x2`, `x3` `kneel` with `grief`), a missed block makes a soldier `laugh` (`s1`, `s2`, `s3`); the fourth block's boundary is the last word (a witness `bow`s, or a soldier laughs); a soldier `stare`s, then
`awe` at beat 60 by a plain cast line. `tests/test_gospel.gd` plays it both ways.

## Engine and tool additions (for `docs/CONTINUOUS_RUN.md`, Stage 6)

* **A path's first stage is built in a cue-free guard** (the Stage 2 item): `RunPlay._prebuild_in_guard` builds the art world a path portal in the current room opens on, one build per guard, and `_prewarm_routes` decodes
  its people sheets ahead; a world names its story data with the run.json world key `"story": "res://content/story/<map>.json"` (`RunPlay._story_entry`), so a path's maps are not chapters and never appear in the Story chapters menu.
  `build_log` records the phase and the scene of each build. Pushed first (`91f0a611`), so the sister paths could rebase onto it.
* **Set pieces** (`HotspotContract.validate_pieces`, `RunPlay._apply_pieces`): a map thing with `"piece": "<id>"` (the manifest `stage.pieces` names its file and blend) is shown while it is on. A scene node may carry
  `"pieces": {"on": [...]}` (listed pieces are on from the downbeat, every other piece of the stage is off), an outcome `"pieces": {"on": [...], "off": [...]}` (applied at the commit), and a scene `"block_fx": [{"block": 0..3,
  "pass": {pieces?, cast?}, "miss": {...}}]` (applied at that block's boundary; cast lines use `at_beat` 0 and the usual conditions). Validated by `RunData._validate_stage_fx`; `RunPlay.piece_log` records every switch.
* **A cast line brings its person in**: `RunPlay._on_cast` calls `StoryCrowd.ensure_present` (the grove's traitor and guards are group `late` and stand in the dark from the beat that names them).
* **A sector may name its sky and its haze** (`StoryMap` sector keys `sky` and `fog`, map `sky.by_name`, `StoryWorld.set_atmosphere`, called by `StoryStage` when the camera's sector changes): one map holds a night room and a dawn one.
* **Path graph rules** (`RunData`): a path's exit scene may lead on inside its world and to a non-entry scene of it. `check_hotspots.py` (paths): a route needs some hotspot that leads to it, and accepts the outcome key `pieces`.
* **Art tools**: `wardrobe.gospel()` (robes, tunics, fishers, priests, soldiers, merchants, governor, tempter, baptist ...), the hats `helmet` and `turban` in `people.py`, `directed.py` reads every `content/paths/*`.

## Art: the four maps, in STORY_ART.md's format

All of it is original and drawn by code (the textures and sprites by `gospel_tex.py`, `gospel_things_a.py`, `gospel_things_b.py`, seeded, byte-identical on a rebuild); no SVG rigs: a Gospel map is textures, billboards and baked people.

### Map `galilee_shore` (assets/story/galilee_shore/): the world `jordan`
Views side by side 18 m apart (x -8..8, z -12..4, the camera at z 1 to 3 looking toward -z) behind a spine road (z 4..8) with a portal in each view's back wall: the rail walks from any room to any other through it.
`bank_night` (J00): a night road in `floor_dust`, a thatched stable lit from inside (`thing_stable`, a lamp light), the star over it (the piece `star`, additive), a campfire (`flicker`), sheep, a far hill town, the stars of `sky_night`;
`bank_dawn` (J01): a sand bank and a river band (`floor_water`, scrolled, 0.4 m lower, an open step between), reeds, palms, the Baptist standing in the water, the dove (the piece `dove`), a far town (Nazareth's rooftops) as the exit;
`rocks` (J02): the wilderness, boulders (`thing_rock_a/b/c`), the tempter, a basket of bread on a rock, the village fires far off; `workshop` (J03): a clay yard, a limestone house with a door, the bench, planks, the cart with nets.
Palette: ochre, olive, limestone, the lake silver-blue; night indigo with oil-lamp amber (`TOD` in `gospel_maps.py`: light 0.34 and tint #4a5ab0 at night, #ffc89a at dawn).

### Map `hillside` (assets/story/hillside/): the world `galilee`
`lakeshore` (J04): shingle shore, two boats, nets drying on poles, a fish rack, a lake band with boats far out; `street` (J05): a cobbled Capernaum street between limestone houses, the family, the child on a mat, the caravan far down the road;
`slope` (J06): a grassy slope with the crowd seated, the disciples standing, a far hill, a lake band; `storm` (J07): a shore at night under `sky_storm`, a boat with the disciples before it, the beacon fire, the pieces `storm_cloud`, `rain`, `lightning`.

### Map `bethany` (assets/story/bethany/): the world `road`
`courtyard` (J08): clay court between mud-brick walls, the laid table (`thing_table_meal`), stools, the donkey, the sisters and the disciples; `hill_dusk` (J09): a hillside at dusk (`sky_dusk`, #ff9a60), baskets empty (`thing_basket`) and the full ones as pieces,
the crowd seated, a lantern; `gate` (J10): a paved road to the city gate (`thing_citygate`, `wall_city`), four palms, the steps, the olive tree, the waving crowd and the priests at the gate.

### Map `jerusalem` (assets/story/jerusalem/): the world `jerusalem`
`temple` (J11): flagstones, colonnades (`wall_columns`), the portico far off, three money-changers' tables (`t1_up`..`t3_up`) and the same tables overturned (`t1_over`..`t3_over`) as pieces; `grove` (J12): olive trees on dark soil at night, torches far off;
`praetorium` (J13): pale walls with the red band, the dais with the seat, the bowl and jug, braziers; `hill` (J14): bare rock under `sky_dusk`, three plain crosses (`thing_cross`), the sky pieces `dark1`..`dark3` (bruised gradients, alpha 0.35 / 0.6 / 0.82);
`tomb` (J15): a garden of cypress and flowers, the rock tomb (`thing_tomb`), the stone closed and rolled (`stone_closed`, `stone_rolled`), `sky_morning`; `road` (J16): a paved road in the morning, the city hazy behind, sheep.

### The people (`wardrobe.gospel`)
Archetypes by `wear`: `fisher` (bare-armed, bandana, bare feet, belt), `villager` and `woman`/`sister`/`mother` (long tunics in undyed wool or dye, stripes, headscarves), `disciple` (twelve recurring robes with sashes and cloaks),
`priest` (white, blue sash, turban), `soldier` (plain lamellar-pattern cuirass, shoulder plates, plumeless helmet, boots, no emblem), `merchant` (striped, gilet, turban), `child`, `elder` (grey, cloaked), `governor` (white with one red band),
`tempter` (tall, dust-coloured, hooded), `baptist` (camel-hair tunic, long hair and beard), plus `shepherd`, `carpenter`, `gardener`. Sheets: galilee_shore 19 people, hillside 35, bethany 29, jerusalem 47 (the live Night One rig stands in
only as a fallback: the actors name a Night One archetype so that `StoryCrowd` creates them).

## Music

17 placeholders at 124 BPM (`songs/packs/gospel_<scene>`, WAV, `temporary` in music.json), house: four on the floor, claps on 2 and 4, offbeat open hats. **The bass is the clearly loudest tonal element** (RMS dBFS: drums -20, bass -12, pad -28;
50 to 62 % of the bass stem's energy under 90 Hz, checked by the generator and by `test_the_placeholder_mix_is_bass_forward`). The owner's prompts, verbatim, one per scene (also `content/paths/gospel/prompts.json`):

| scene | prompt |
| --- | --- |
| J00 `jordan` | 124 BPM soulful house, 8-bar seamless loop. Soft kick, dusty claps, warm organ, gentle plucks, choir-like synth and rounded bass. Separate editable MIDI tracks. |
| J01 `jordan.baptism` | 124 BPM uplifting gospel house, 8-bar seamless loop. Shimmering keys, warm bass, handclaps, four-on-floor kick and sparkling water percussion. Separate editable MIDI tracks. |
| J02 `jordan.wilderness` | 124 BPM minimal deep house, 8-bar seamless loop. Dry kick, hollow percussion, sparse organ, uneasy bass pulse and desert-wind synth. Separate editable MIDI tracks. |
| J03 `jordan.nazareth` | 124 BPM organic house, 8-bar seamless loop. Wooden percussion, warm piano chords, mellow bass, soft shaker and gentle handclaps. Separate editable MIDI tracks. |
| J04 `galilee` | 124 BPM funky house, 8-bar seamless loop. Bouncy bass, crisp claps, rhythmic guitar-like synth, bright organ and rolling hi-hats. Separate editable MIDI tracks. |
| J05 `galilee.capernaum` | 124 BPM soulful deep house, 8-bar seamless loop. Tender electric piano, rounded bass, soft drums, hopeful strings and delicate melodic responses. Separate editable MIDI tracks. |
| J06 `galilee.mount` | 124 BPM joyful gospel house, 8-bar seamless loop. Rich organ chords, celebratory claps, melodic bass, uplifting piano and spacious choir-like synth. Separate editable MIDI tracks. |
| J07 `galilee.storm` | 124 BPM dark progressive house, 8-bar seamless loop. Thunderous kick, rolling toms, tense sub-bass, stormy pads and urgent arpeggios. Separate editable MIDI tracks. |
| J08 `road` | 124 BPM warm soulful house, 8-bar seamless loop. Gentle Rhodes, soft kick, hand percussion, expressive bass and intimate organ chords. Separate editable MIDI tracks. |
| J09 `road.loaves` | 124 BPM euphoric gospel house, 8-bar seamless loop. Layered piano stabs, warm bass, claps, jubilant synth harmonies and uplifting four-on-floor drums. Separate editable MIDI tracks. |
| J10 `road.entry` | 124 BPM festival house, 8-bar seamless loop. Triumphant brass-like synths, driving kick, crowd-style percussion, bright organ and energetic bass. Separate editable MIDI tracks. |
| J11 `jerusalem` | 124 BPM tense tech house, 8-bar seamless loop. Metallic percussion, sharp claps, distorted bass, clipped organ stabs and escalating rhythmic tension. Separate editable MIDI tracks. |
| J12 `jerusalem.gethsemane` | 124 BPM melancholic deep house, 8-bar seamless loop. Muted kick, sparse piano, low bass heartbeat, haunting pads and restrained percussion. Separate editable MIDI tracks. |
| J13 `jerusalem.trial` | 124 BPM cinematic dark house, 8-bar seamless loop. Heavy kick, ominous organ, slow chord changes, deep bass and tense metallic percussion. Separate editable MIDI tracks. |
| J14 `jerusalem.golgotha` | 124 BPM atmospheric minimal house, 8-bar seamless loop. Sparse kick, distant bells, solemn organ, subdued sub-bass and slowly rising ambient strings. Separate editable MIDI tracks. |
| J15 `jerusalem.tomb` | 124 BPM uplifting melodic house, 8-bar seamless loop. Radiant piano, warm bass, soaring choir-like pads, bright claps and expansive harmonies. Separate editable MIDI tracks. |
| J16 `jerusalem.road` | 124 BPM reflective organic house, 8-bar seamless loop. Gentle percussion, warm acoustic plucks, wandering bass melody, soft piano and hopeful atmospheric pads. Separate editable MIDI tracks. |

The owner's loops drop into `content/imports/gospel/<scene>/` and `beatshaper.py --path gospel import` replaces the placeholder (`docs/MUSIC_IMPORT.md` section 7). The placeholders are 8.6 MB a pack (146 MB for the 17, about 110 MB compressed in git): a size the owner may want to cut by dropping the placeholders
once the loops are in.

### The Stage 2 audio finding (the 88.6 ms phase-change offset inside the stub path)
Re-recorded on this machine today (`tools/story/record_music.gd`, `check_run_audio.py`, dummy driver). The hypothesis "the dummy driver's 4096-frame chunk, so a main-run phase change would show it too" is **not supported**: a plain main-run
phase change (balcony -> chill -> exit, 78 s) shows a delay spread of 8.8 ms and no jump; the stub started directly (`RW_RUN_PATH=stub`) 11.4 ms; the handoff recording (balcony star -> stub -> back) reproduces the jump exactly at its first
in-path phase change (stub -> stub.end, delays -83.3 then -171.9 ms, the shift persists into the Warehouse that follows). Here the dummy driver mixes in chunks of about 29.4 ms (every `lateness_ms` in the recorded voice log is a multiple of 29.4 ms plus a
constant) and the jump is three of them (88.2 ms), so the size is a quantisation but the cause is something the first phase change after a tempo handoff does and an ordinary one does not: most likely the new clock stream's playback position settling at its
first wrap. **The checker tolerance was not changed.** If a phone shows cues arriving a fraction of a second early from the second room of a path on, this is the place to look (`RunAudio._swap_clock`, the first wrap of the clock loop).

## Verified and not verified

**Verified (5 November 2026, this PC, virtual clock and headless unless stated):**
* `bash tools/test.sh`: the Godot suite 72,457 checks at the last full run with 3 failures, all three tests that assumed the gospel path did not exist yet (`test_hotspots_engine` accepted no `path:` route, `test_run_paths` expected the star
  hidden); fixed so they follow the data and re-run by filter green (`run_paths` 308 checks, `hotspots_engine` 1,428, `gospel` 446); the Python content tests run without failures. A last full run was made after the rebase onto `origin/main` before the push (see the commit log).
* `python3 tools/run/check_hotspots.py --path gospel`: 0 errors (17 of 17 scenes reachable, 30 routes taken, 14 flags settable, both endings left by `run:warehouse`; 15 warnings are the route lock between sibling charts); the main run's check: 0 errors.
* `bash tools/run/walk_run.sh --path gospel` (real scenes, virtual clock, isolated save): seven walks, **17 of 17 scenes visited, `run walk-through: OK`**: `perfect` (every default route to the tomb and on to the Warehouse), `road_end` (the road ending), `branch_a`, `branch_b`, `branch_c`
  (every other scene and the J09 -> J08 loop), `sloppy`, `none`; the saves hold the path's worlds under `paths`, never `reached`.
* The balcony star opens the path for real, without `RW_PATH_REMAP` (`test_the_balcony_star_opens_the_path_for_real...`): 174 -> 124 BPM on the downbeat, the first stage already built.
* The prebuild fix in a real-time headless run (dummy audio driver): the `galilee_shore` stage was built in phase 1, inside a guard of the Warehouse balcony (75 ms), not behind the closed frame; no stall at the handoff.
* Looked at (Read tool): all 34 scene shots in `docs/shots/gospel`, 16 acting strips and the contact sheet in `docs/shots/acting/gospel_*`; people are told apart (robes, fishers, soldiers, priests), faces are readable, the camera no longer walks up to the crowd.

**Not verified / known weak:**
* No phone, no real output latency, no listening to anything (the placeholders were measured, never heard; the owner's loops are not here). The tempo handoff and its 88 ms finding are measured with the dummy driver only.
* Nothing was played by hand: the acts, faces, set-piece fades and the Golgotha staging are only seen as still frames from the virtual clock; whether a player who is watching the pads sees an act at beat 50 and an outcome at beat 62 is unknown.
* Shots I am not happy with: the acting strips of the route-leaving hotspots (`gospel_jordan_wilderness_*`, the exits) show their success and failure panels inside the passage frame (the tempter's `recoil` and `laugh` do not read), and for `galilee.capernaum.family` and `galilee.fishermen` the committed and success panels
  differ little from `available`; the dusk and night views (J09, J12) are dark and the far crowd of the grove is a few pixels; the wall tiles `wall_hill` and `wall_columns` read as flat bands and heavy shadow; the sky is built from large dither cells at this resolution.
* The sky pieces of Golgotha (`dark1`..`dark3`) are billboards at 12 m: they dim the sky behind the hill but not the people in front; the grove's torch and the Bethlehem fire are lights, not animated art.
* Mix of the placeholders: bass-forward by measurement; whether it is prominent enough on a phone speaker is the owner's to judge.
* `tools/story/check_assets.py` still lists the five old chapters only; the gospel sheets are checked by `tests/test_gospel.gd` and `tools/content/test_gospel.py`.
