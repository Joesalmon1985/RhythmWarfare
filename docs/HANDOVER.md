# Rhythm Warfare: handover

State on 3 November 2026, after `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (four pads, sequence rewards, ten missions,
the loop library and the owner's drop-in content path), the rebuild of Mission 1 on the owner's own Ableton
recordings (`ToAddTry1/`, imported by `tools/content/import_ableton.py`) and the village version of Mission 1
(128 bars, civilians, tap-to-deploy sections, Red Alert sound effects) and the owner's first-play tweaks of the same
day (units fight on the move, a bigger zoomed-out village, the rally flag always shown, the bass chart by pitch,
a quieter battle mix, misses that silence the instrument) and then the loadout redesign of that night (one global
loadout, a loop library, missions as bases plus waves plus a form). Read this first, then `README.md` (layout and
commands), `docs/PRD.md` sections 15 and 16 (the mission rules; section 16 is the current content model; sections 1 to
13 describe the legacy duel) and
`docs/CONTENT_TO_RENDER.md` (the owner's render list). Everything is committed on `main` at
https://github.com/Joesalmon1985/RhythmWarfare.

## Three paths and the acting system: progress (docs/THREE_PATHS_AND_FACES_PLAN.md)

- **Stage 1a done (5 November 2026): fourteen faces and fifteen directed acts in the pixel people.** Faces `fear`, `anger`, `plea`, `doubt`, `relief`, `awe`, `grief`, `laugh`, `resolve`,
  `shame` on top of the four old ones, per species (`tools/story/art/people.py`); acts `beckon`, `nod`, `shake_head`, `recoil`, `bow`, `kneel`, `offer`, `plead`, `collapse`, `salute`, `block`,
  `cover_face`, `stamp`, `laugh`, `write` (`StoryCharacter.STATES`, `sample()`, `SHEET_CYCLES`, `FACE_OF`); baked only for the directed people (`content/story/directed_actors.json`, later the hotspots'
  `acting` blocks and the scenes' `cast` lines, `tools/story/art/directed.py`); `check_assets.py` fails when a directed person lacks an act, a face or a facing; proof in
  `docs/shots/faces/<chapter>_acting.jpg`; how it works in `docs/STORY_ART.md` "Acting". Divergences: the pose key `fwd` (a forward bend) was added to the dumped limb keys, because the pixel rig
  is 2D; `point` and `stare` keep their old default faces (neutral) for the crowd, the directed data names `resolve` where the story wants it; `look_at` on `point` is the existing `toward`
  (stage 1b resolves a target id into it); `StoryCharacter.face_override` and the `act@face` sheet key are the only runtime additions (`StoryCrowd.direct` is stage 1b).
  Not verified: how the acts and faces look moving in a real run on the owner's phone (only the sheets, the poses and the tests were checked).
- **Stage 1b done (5 November 2026): the acting contract** (`docs/CONTINUOUS_RUN.md` "Acting in the run"). `acting` on hotspots, `cast` on scene nodes and on cinematics, validated in `HotspotContract`
  (`FACES`, `ACTS`, `ACTING_PHASES`, `LOOK_TARGETS`, built from `StoryCharacter`, not copied; `StoryCharacter.DIRECTABLE_OLD` lists the older states a story may also direct) and `RunData._validate_casts`;
  `RunEngine` emits one `cast` event per line at `phase_t0 + at_beat * beat_s` (pure; conditions `if_energy_below/above`, `if_flags_all/none` read at that beat; cinematic cast from the commit);
  `RunActing` (pure helpers), `StoryCrowd.direct_actor` / `direct_chain` / `directing` / `look_point` / `stand_down(id, src)` (the crowd's `dir` carries `face`, `look_at`, `src`, `chain`),
  `HotspotView._manage_acting` (available and selected acts, replacing the hard-coded wave), `RunPlay._on_cast` and `_act_outcome`. Hotspots with no `acting` block behave exactly as before (the old wave).
  `tools/story/art/directed.py` now also reads cinematic `cast` lines and skips Bassment `figure` blocks (`tools/content/test_directed.py`). Divergences: the plan's `StoryCrowd.direct(actor, act, face, ...)` is
  `direct_actor` (the name `direct` is the crowd's group directive with twenty callers); `sheet_pick` choosing by state and face was already done in stage 1a; no acting or cast is authored yet (stage 1d), so
  the tests inject lines into the shipped data and "every shipped cast line" is vacuously the empty set today (the loop is in place and will cover the data the day it lands). Test run at the end of 1b: `bash tools/test.sh` green: 67513 checks, 0 failures (the run before stage 1b: 67007), and the 169 Python content tests.
- **Stage 1c done (5 November 2026): the silent HUD and the Bassment without its caption band** (`docs/CONTINUOUS_RUN.md` "The silent HUD"). With `RW_DEV_TEXT` unset the run draws no title card, captions,
  world or room name, stage label, numeric countdown, DRUMS / BASS banner or status line, and the Bassment shows no title, caption band, zone tag or banner; the stage pips, the energy meter and a new thin
  route-window bar stay, and a new room's lamps swell over two beats from its downbeat (`room_swell`). The pads' judgement words (PERFECT, GREAT, MISS) were kept as feedback, not story: if the owner
  wants those gone too it is one flag in `RunPlay._on_judge_event`. The Bassment's ten creatures carry `acting` authored from `CREATURE_ACTING` in `tools/trial/make_hotspots.py`
  (regenerated `content/trial/hotspots.json`) and play it as motions on the billboard (`RunActing.figure_motion`; the contract's `figure` key). `tests/test_run_hud_silent.gd`, `test_trial.gd` and
  `test_run_scene.gd` set `RW_DEV_TEXT=1` where they read text. Proof shots (look at them): `docs/shots/silent/` from `tools/run/shoot_silent.sh`. Test run at the end of 1c: `bash tools/test.sh` green: 67690 checks, 0 failures (the run before stage 1b: 67007), and the 169 Python content tests.
  Not verified: how the acts, faces, light swell and the thin bar look and feel on the owner's phone in real time (only the virtual clock, the tests and desktop screenshots were run), and nobody has
  listened to or watched a full run with the text gone. Divergence: the Bassment's caption text is hidden, not removed (the labels still carry it for `RW_DEV_TEXT`).
- **Stage 1d done (5 November 2026): the acting pass on the five worlds** (`docs/CONTINUOUS_RUN.md` "Acting in the run", "Authored (stage 1d)"). Authored in one table file, `tools/run/acting_data.py`
  (`ACTING`, `CAST`, `CINE_CAST`), copied into the generated hotspot files and `run.json` by `make_hotspots.py` / `make_scenes.py` (rerun `python3 tools/run/make_scenes.py`; its `write_music()` call is gone,
  `content/story/music.json` is `arrange.py`'s now): 28 character hotspots with a person to direct plus the Warehouse stranger carry all five states; all 36 scenes carry 2 to 4 `cast` lines (blocks 0, 16, 32, 48;
  21 lines conditional on energy); 15 existing success and setback cinematics carry the acted reactions of the people around (the circle turning its back, the bar laughing, the family weeping, the queue cowering).
  Unconditional cast lines use `core` people only (the continuous run brings no gatherer, early, late or peak person in by itself; the conditional high-energy lines may name them and simply do nothing when they are
  absent). The sheets bake exactly what the data uses: `content/story/directed_actors.json` is empty, `directed.py` derives everything, `tests/test_story_acts.gd` checks both directions.
  Proof: `bash tools/run/capture.sh --acting` (`docs/shots/acting/<hotspot>.jpg`: the five states side by side, the person framed at about twice the usual size; `contact_acting_<world>.jpg`). Its screenshot aids:
  `RW_STORY_CAM=actor:<id>:<m>:<pitch>` (StoryStage; a standpoint with nobody in the way, the free look ignored), `RW_RUN_CLEAN=1` (no notes, no HUD), `RW_RUN_FLAGS=a,b`.
  **Divergences:** (1) the two wizard hotspots (`warehouse.wizard`, `warehouse.chill.wizard`) have no `acting`: the wizard is a billboard *thing*, not a baked person, so there is nobody to give a face to; making it
  act needs a figure-motion on a world thing (the Bassment's `RunActing.figure_motion` is the model), left for later. (2) Found while shooting: four hotspot people (`g07` the dancer, `g08` the grey, `court_g06` the queen,
  `e04` the Ward orderly) belong to groups the continuous run never brings in, so those hotspots anchored on nobody visible; `HotspotView._manage_acting` now calls the new `StoryCrowd.ensure_present` so the person fades in
  at their place when their hotspot is on show (nothing else about presence changed). (3) The plan's "committed" flash is one beat here (two left almost no time to see the result before the passage frame closes over
  routes to another world: a result is seen for about three beats at best, which is why the strongest act of a route-leaving hotspot is in its `success`/`failure`, shortly, not in `then`). (4) The plan's `acting.look_at` of
  a hotspot is used with `camera` and map ids only.
  Not verified: how any of it moves and reads on a phone in real time (only still frames from the virtual clock, desktop window), that an act at beat 50 and an outcome at beat 62 are seen by a player who is looking at the pads, and no
  listening or live-audio run at all. People-sheet page bytes (plan budget +15 % per chapter, against the rebuilt pre-1a heads): night_one 3,288,010 -> 3,555,788 (+8.1 %), mothership 9,441,871 -> 9,645,545 (+2.2 %), underworld 9,071,134 -> 9,236,297 (+1.8 %),
  hospital 8,666,621 -> 8,963,276 (+3.4 %), mental_hospital 9,692,138 -> 10,056,393 (+3.8 %); total 40,159,774 -> 41,457,299 (+3.2 %). Shots I am not happy with (`docs/shots/acting/`): `underworld_court_queen` (the queen is hidden in a
  crowd of dancers whatever the standpoint, her acts do not read), `ward_dorm_sleeper` (the sleeper's selected and committed acts do not show), `ward_late_exit_stare` (the acts are faces only), the two bouncers and `mothership_exit_exam`
  (the success and failure panels are in the passage frame: the world is already changing). Test run at the end of 1d: `bash tools/test.sh` green: 71389 checks, 0 failures (the run before stage 1d: 67690), and the 169 Python content tests;
  `tools/run/check_hotspots.py` 0 errors (the same 5 warnings as before).
- Stages 2 to 6 are not started by this agent (stage 2 is in another worktree).

## What the game is now

A landscape phone rhythm defense game. Four illuminated pads play along with a 174 BPM drum and bass track; every
sequence of two bars you pass builds one defense or sends one unit; your Red Alert base in the middle of the screen
must keep its required buildings alive until the song ends. The player has one **loadout** (drum pattern, fill, kick
sound, snare sound, bass line, bass sound, backing track) that plays in every one of the ten missions and decides
what a passed sequence builds: kick sounds make infantry, snare sounds defenses, bass sounds vehicles. A mission is a
battlefield, a set of waves and a form (which 8-bar phases are drums and which bass); it authors no music. Home:
Continue, Campaign, Practice, Loadout, Settings, and a small Developer area (legacy duel free play, rhythm playtest,
content status, unlock-all status). Normal progression is on.

## How the game plays now

- **Pads.** Four large pads at fixed positions: 1 and 2 under the left thumb, 3 and 4 under the right (keys D F J K).
  Each phase of a mission follows one family. Drum phases: the loadout's kick sound is pad 1 and its snare
  sound pad 4 (pads 2 and 3 are dim). Bass phases: the bass line's notes spread over all four pads by pitch, lowest
  on pad 1 (a line with one pitch sits on pad 2), taps only, at least 1440 ticks apart (`data/campaign/rules.json`
  `chart.bass`, `tools/content/chart.py`). A pad with
  nothing to play in the current phase is dim; each lit pad carries the friendly name of its sound and a shape (kick
  disc, snare diamond, bass bars) as well as its colour. At most two touches count at once.
- **Cues (falling notes).** Every cue is a translucent pad-sized shape that falls straight down the screen, over the
  battlefield, and sits exactly on its pad at the hit time; a hold is a tall bar whose bottom square lands at press
  time and passes through until the tail. The note speed setting (0.6 to 2.0 s, default 1.2 s; `RW_LEAD_IN`) is how
  long a note takes from the top of the screen to its pad. A hit note vanishes, a missed one keeps falling for a
  quarter second tinted red; the pad still pulses on the beat, fills while you hold and flashes at the tail. One bar
  before a mode change a banner names the incoming family (BASS NEXT); there is no roadmap. Everything is drawn from
  the one song clock (`src/ui/note_lane.gd`; the closing rings of the earlier builds are gone).
- **Recognition (generous).** Perfect within 45 ms, great 90 ms, accepted 140 ms either side. One press takes the
  nearest cue of its pad; a second finger on a held pad does nothing; a press with nothing in reach is a stray.
- **Holds (forgiving).** Released within 0.15 s of the tail (or still held there) = complete; earlier = the held
  fraction counts, nothing fails. Pause ends a hold where it stands.
- **Sequences.** Missions cut each phase into sequences of two bars (a hold may run across a sequence boundary but
  never across a mode change; the sequence resolves when the hold does). A sequence passes at credit / cues >= 0.6 (taps 1 or 0, holds their coverage). A pass
  earns its **one** reward, a fail earns nothing and costs nothing already built. It resolves when its last cue is
  final, so it never rewards early and resolves the same at any frame rate.
- **Precision only sets speed.** Mean onset error of the accepted cues + 25 ms per stray per cue: sharp (<= 35 ms)
  builds in 0.5 s, steady (<= 70 ms) 1.5 s, loose 3 s. Mashing passes at best as loose. The centre of the pad strip
  shows the current sequence's progress against its threshold and what it will earn; the line under it says what was
  earned and how fast; the battlefield shows the socket being prepared with a countdown ring.
- **Rewards.** The loadout decides them, not the mission. Drum sequence k (counted over the whole mission) calls on
  the kick sound's instrument when k is even and on the snare sound's when odd, a bass sequence on the bass sound's
  (`data/campaign/instruments.json`; shares expand in order, so 2:1 is A A B and the cycle repeats). With the default
  loadout the first drum sequence sends a rifle squad and the second builds a pillbox. A reward the base cannot make
  (vehicles in the village, which has a barracks and no war factory) becomes a repair crew. Buildings (pillbox, gun turret, flame tower) go to
  prepared sockets (`data/battlefields/defense_02.json` and `village_01.json`, five per approach flanking each route
  outside the wall, `sockets_per_point` open per mission), approach with the fewest defenses first (ties: the approach
  most enemies are walking towards, else the next wave's). Units (e1 to e4, jeep, APC with its gun only, light and
  medium tank, artillery, flak truck; squads `rifle_squad` and `grenadier_squad` are three at once) come out of the
  barracks or war factory and hold the point with the fewest defenders (at most `units_per_point`, 6 by default, 14 in
  mission 1); they may sortie up to 16 cells to hit an enemy shelling their point from beyond their 6-cell leash.
  Reward units leave the barracks on attack-move and fight whatever they meet on the way; a defender beyond its
  leash keeps firing at a target in range but never chases it, and walks home fighting (`_leash_holds` in
  `battle_sim.gd`, `_defender` in `defense_ai.gd`). At capacity a reward becomes a repair crew for the most damaged
  approach or, with nothing damaged, +50% health once for the oldest defense; the status line above the pads says which.
- **Loadout screen and briefing.** Home > Loadout: one row per slot of cards (unlocked first, a locked card says what
  unlocks it), a strip of unit icons on every sound card, Listen on every card; choosing a card re-resolves the whole
  loadout (a slot that no longer fits falls back) and saves it. The mission briefing (`mission_setup.gd`) shows the base
  (a warning where there is no war factory), approaches, villagers, wave count and length, the loadout with what its
  three instruments build (vehicles struck out without a factory), "Change loadout", and for practice the part to play.
  The result screen names what a clear added to the loadout. No per-mission choices exist any more.
- **Sections (tap to deploy).** A tap on the battlefield (or keys 1 2 3) makes the nearest approach by x the active
  section: every reward goes there while it has room (else the normal choice) and a move flash plays. The Red Alert
  rally flag always stands at the current rally point (`Match.rally_point()`: the tapped section, else the point
  rewards would go to), drawn at full sprite size whatever the zoom. Nothing else is drawn on the map: no circles,
  numbers, brackets, countdown rings or wave arrows. The mission screen has no text overlay: the flag marks the rally
  point, EVA announces waves, buildings carry their own health bars, and the result screen reports sequences, units,
  villagers and objective health.
- **Zoom.** A battlefield's `view.zoom` (village_01: 0.75; absent = 1.0) scales the cell size (18 px instead of 24)
  and every sprite; missions 2 to 10 keep 24 px. The village is 96 x 48 cells (`data/maps/field_96x48.json`), the
  view 72 x 27 cells, the rally points 7 cells outside the side walls and 6 above the top wall, the entries 5 cells
  beyond the window; `python tools/campaign/build_battlefield.py village_01` regenerates only the village files.
- **Bass chart.** The charting rule is global (`rules.json` `chart.bass`: `pads: pitch`, `min_gap_ticks: 1440`,
  `holds: false`; `tools/content/chart.py`): the bass line's pitches map to pads 1 to 4 from low to high and at most
  one note per 1.5 beats is cued, every cue a tap; the recording still plays every note. The cues are baked into the
  library index per clip (`songs/library/index.json`), so a new bass line is charted by the build.
- **Misses.** A missed cue (or a hold released with nothing held) silences that instrument's stems until the next hit
  on it (`Match._judge_to_stems`); the backing track never mutes; at a phase change every family the new phase does
  not cue comes back; a muted family's pad label draws at half alpha.
- **Civilians (mission 1).** The village map has ten houses (OpenRA `v01`..`v08`) and ten civilians (technicians
  drawn as `c1`, villagers `c2`) that wander between the houses, flee from enemies within 6 cells and die when shot;
  they never fight or repair, player units ignore them, and the result screen reports "Villagers lost x of y".
- **Sound.** `src/audio/battle_sfx.gd` plays the Red Alert effects in `assets/sfx/` (33 Ogg files extracted from the
  owner's install by `tools/extract_openra_sounds.py`) from the simulation events through `data/sfx_map.json`:
  weapon reports (M1 carbine, M60, Vulcan, grenade), kaboom and crumble on destruction, dedman screams, civilian
  cries, placbldg/build5 on pillboxes, EVA "unit ready", "enemy units approaching" (8 s before a wave), "base under
  attack", "unit lost", "mission accomplished/failed", an allied "acknowledged" on a section tap; 12 players, 8
  voices, cooldowns, EVA lines queued one deep. Mix (3 Nov, after the owner's first play): shots at −18 dB with a
  0.25 s cooldown per weapon and at most 3 weapon voices at once (`group_voices`), deaths −14/−12, explosions −10,
  build sounds −8, EVA −6, outcome −3, a limiter at −1 dB on the SFX bus, Effects slider default 50% (a saved
  settings file without `mix_version` 2 is reset to it once). Music plays on its own "Music" bus. Nobody has
  listened to the mix: the owner judges it.
- **Waves** are authored by bar per mission (`data/campaign/waves/level_NN.json`), never depend on accuracy, walk on
  from off screen at the left, top and right, attack-move via their approach's defense point to their objective and
  fight units **and defensive structures** on the way (not other buildings). A wave (or a group) may carry a
  `target` class: `defenses` (fight at the choke point and hold there), `civilians` (then the nearest house or
  villager), `core` (the objective, the default); a class falls through to the next inward one when nothing of it is
  left. A mission's level rules may add `start_units` (mission 1: five riflemen at each point) and `units_per_point`.
  Required objectives: the command core (missions 2 to 10), the barracks (mission 1), plus the power plant (6, 10) or
  radar dome (8, 10). Survive to the end of the song to win; lose a required objective and the run ends.
- **Progression.** Clearing mission n unlocks mission n+1 and the library items (clips and sounds) listed in its
  `new_options` (`data/campaign/campaign.json`); the default loadout is always available; no accuracy threshold blocks
  the ladder. The save (`user://campaign.json`) is version 3 `{cleared, loadout, last_played}`; versions 1 and 2 migrate
  on load (clears and bests kept, per-mission selections dropped, the loadout becomes the defaults; the old file is
  kept as `.v1` or `.v2`); settings v1 keep
  calibration and the last pack, and the cue lead-in starts at its default (the old note-approach time measured
  something else).

## The ten missions (owner's view; the menus show names and locks only)

The missions are bases and waves now; the music is the player's loadout. Form = the 8-bar phases (D drums, B bass).
The last column is what clearing the mission adds to the loadout library (`new_options`; every mission also adds its
own backing track, named "<Mission> accompaniment").

| # | Mission | Length | Form | New for the player | Enemies (first appearances) | Objectives | Unlocks on clear |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | First Watch | 128 bars, 177 s | DDBDBDDBDBDBDDBD | the village map (three choke points with five riflemen each, ten houses and ten civilians, the barracks in the middle), tap-to-deploy sections; four acts: waves at the choke points, then the village, then raiders with jeeps, then the barracks | e1, e2, jeep | barracks | the starter kit and every first-set sound, groove and bass line (Half-Time, Double Step, Rolling, Sub Line, Reese Line, the nine bass sounds, three hats) |
| 2 | Second Pulse | 40 bars, 55 s | DDDDD | | e2 | core | Push, Straight, Crack Snare |
| 3 | Hold the Line | 48 bars, 66 s | DBDBDB | bass phases | e3, 1tnk | core | Patrol Sub, Reese, Long Line, Answer Line (ending) |
| 4 | Backbeat | 48 bars, 66 s | DDDDDD | | e4, apc | core | Two-Step, Siege Kick, Field Clap, Snare Run |
| 5 | Counterpoint | 56 bars, 77 s | DBDBDBD | | | core | Steps, Growl, Answer Line |
| 6 | Fortress | 56 bars, 77 s | DDDDDDD | | 2tnk, arty | core + power plant | Roller, Heavy Kick |
| 7 | Crossroads | 64 bars, 88 s | DBDBDBDB | | ftrk, v2rl | core | Command Saw, Octaves |
| 8 | Crossfire | 64 bars, 88 s | DDDDDDDD | | 3tnk | core + radar dome | Break, Rimshot |
| 9 | Iron Rhythm | 64 bars, 88 s | DDBDDBDD | | 4tnk | core | Kick Drop |
| 10 | Last Light | 80 bars, 110 s | DDBDBDBDBD | | all 13 ground actors | core + plant + dome | Hollow Sub |

Each mission's design notes are in its `note` fields (`content/missions/level_NN.json`, `data/campaign/waves/level_NN.json`).
Missions 5 to 10 carry start units, prebuilt defenses and bigger objective hp from the loadout retune (3 November, night).
The coverage matrix of every ground actor and building is in `docs/BALANCE.md`, with the per-seed results.

## Content: loop library, missions, the one build command

- `content/library/<clip>/`: mission-independent clips at 174 BPM 4/4 with stable ids (31 clips: grooves and fills
  with kick and snare parts, bass lines, backing tracks), one MIDI per part, a `clip.json`. **Eight clips are the
  owner's Ableton exports** (`ToAddTry1/`, manifest `content/imports/first_watch.json`): three eight-bar grooves
  (Half-Time, Double Step, Rolling), two bass lines (Sub Line with five recordings, Reese Line with four) and three
  audio-only backings (Driving, Busy, Offbeat Hats). Each declares the sounds it was recorded with (`sounds`), so it
  plays only its own recordings. The rest are cut from the First_Three MIDI (hashes checked on every build) or
  generated; they play placeholders until the owner renders them.
- `content/sounds.json`: 30 sounds (14 synthesised, 16 recorded). `data/campaign/instruments.json` says what each
  sound produces in battle (reward ids with shares) and its blurb; the build refuses a sound without an entry.
- `content/missions/level_NN.json`: one mission, nothing else: `level_id`, `number`, `title`, `pack`, `bars`, `seed`,
  `form`, `battle` (battlefield, waves, rules), `intros`, `note`. `content/missions_legacy/` keeps the old authoring
  (choices, phases, stems); only `tools/content/export_midi.py` still reads it.
- **The build, one command**: `python tools/content/build.py [level_NN ...]` (`--check` validates only). It builds
  the library first: `songs/library/index.json` (sounds with their rewards, clips with cues per part and the loop file
  per part and sound, defaults) and `songs/library/loops/` (**117 loops, 5.9 MB**, one Ogg per clip part and sound,
  exactly 8 bars, backings 16; unchanged loops are not re-encoded), then every mission's `songs/mNN_*/level.json`
  (schema 4: phases, waves, rules, base, intros; no audio), `content/REPORT.md`, `docs/CONTENT_TO_RENDER.md` and
  `data/campaign/library_names.json`. **About 23 s from scratch**, under a second when nothing changed; the index and
  packs are byte-identical when nothing changed. After editing a waves file rebuild that mission (`level_NN`, about a
  second) and run `--import` once. Schema 3 packs and the 9-minute stem assembly are gone.
- **Charts and checks**: kick cues are pad 1, snare cues pad 4, bass cues by pitch (above). The build checks every clip
  against the pad gap rules (same pad 480 ticks, same thumb 480 between pads) and every groove together with every
  fill (the groove's bars 1 to 7 and the fill's bar 8); an error names the clip or the pair. It does not test the loop
  seams (a tail that rings past bar 8 is folded onto bar 1 by construction; nobody has listened).
- **Owner renders** still go to `content/library/<clip>/<part>__<sound>.wav` (48 kHz stereo 16-bit, from the clip's
  bar 1, at most one bar of tail), then rebuild; a MIDI edited in Ableton regenerates the clip's cues and the build
  refuses WAVs rendered from the old MIDI. The exact list is `docs/CONTENT_TO_RENDER.md` (31 clips, 117 renders, 18
  of them the owner's recordings already in place), rewritten by `python tools/content/render_list.py`.
- **The importer path** for an Ableton batch is unchanged: `python tools/content/import_ableton.py <manifest>
  [--check]` files 44.1 to 48 kHz exports into the library (SoX resampler, no time-stretch; MIDI cut to the clip's bars
  at 960 PPQ with 174 BPM written in; WAVs cut to the bars plus a sounding tail of at most one bar; gain rules, a global
  trim and a 10 ms end fade; originals untouched). `content/README.md` has the manifest format and the steps for new
  phrases; a new clip also needs `produces` entries only if it brings a new sound.
- **MIDI for the owner's renders (missions 2 to 10)**: `python tools/content/export_midi.py` reads `content/missions_legacy/`
  and writes `midi_export/level_NN_<slug>/` (3 November 2026): 8-bar loops `Kick_A/B/C`, `Snare_A/B/C`, `Bass_A/B/C`,
  `Other_Pad`, `Other_Hats` and a reference `Arrangement_A.mid` per mission, a README per folder and a manifest template
  `content/imports/level_NN.json`. Under the loadout model the exported loops are simply more library clips once the owner
  renders and imports them; `tools/content/test_export.py` proves determinism, the bounds and a synth round trip.
- **Placeholder WAVs** for reference are in `content/library/<clip>/placeholder/` (git-ignored, regenerated
  identically by the build on a fresh checkout); the game plays the Ogg loops in `songs/library/loops/`.

## Verified and not verified

Verified (31 October 2026, this PC, headless unless stated):
- `bash tools/test.sh`: 1,793 GDScript checks and 9 content build tests, 0 failures. One expected
  `Parse JSON failed` line is the corrupt-save test. Covered: cue and hold recognition, generous acceptance versus
  precision speed, sequence pass/fail and one reward each, mash and duplicate presses, pause and retry determinism,
  phase continuity of the stems, socket placement and capacity, all ten missions loading with every option and
  completing (perfect wins every sequence, no input loses), progression and unlocks, save v1 migration, the legacy duel.
- The 18 First_Three MIDI hashes match `campaign/Musical_Source_Integrity.json` (checked by the build and a test).
- Seeded balance (`docs/BALANCE.md`): perfect 60 of 60 and beginner 60 of 60 wins over seeds 1 to 6, sloppy 27 of 30,
  no input 0 of 30.
- Sample-exact clip placement in the assembled stems (content test, within one sample).
- Screens looked at by the agent in real windows at 1280 x 720 and 1600 x 720: home, missions, mission setup
  (mission 1, 7 with locks, 10 with every choice), settings, play with pads and holds, pause, result. Not by a person.
- Desktop real-window run of mission 10 with perfect autoplay: see `docs/BALANCE.md` (frame time).
- Exports: see "Exports" below.

Verified (3 November 2026, evening: falling notes, no top bar, rewards every 2 bars with doubled waves, the MIDI
export; this PC; see `docs/BALANCE.md` "Rewards every 2 bars, every wave doubled"):
- `bash tools/test.sh` green: 10,730 GDScript checks and 48 content tests (12 of them `tools/content/test_export.py`).
  New: `test_note_lane.gd` (the shape equals the pad at the hit time, leaves the screen top at the note speed, holds
  grow upward, visibility window and states, the duel path); the mission tests now expect 64 sequences, 9 or 10
  built, 36 units, repairs, every wave destroyed under perfect play; the content tests 64 sequences, at least 260
  enemies, 6 jeeps; the export tests determinism, bar counts, A equals the library, B/C within bounds, manifests,
  and a synth round trip through `import_ableton.py --check` on mission 4.
- Seeded balance recorded (seeds 1 to 3, no retune): missions 1 to 5, 7, 9 win under perfect and beginner play;
  mission 6 drops one beginner seed; missions 8 and 10 lose under perfect play with the doubled waves (known,
  retune after the loadout round). Mission 1: 64 of 64 sequences, all 278 enemies destroyed, villagers 0 of 10 lost.
- Real 1280 x 720 window with perfect autoplay to VICTORY (mission 1) and into act 2 (mission 3): the notes fall
  over the village and sit on their pads at the hit time, no band at the top, the flag on the map, the centre meter
  and "Pillbox ready" line still there, the result screen with 64 of 64. Not by a person: nobody has felt the note
  speed (default 1.2 s), the reward pace or the doubled waves by hand; the MIDI has not been opened in Ableton.

Verified (3 November 2026, later: the first-play tweaks, this PC; see `docs/BALANCE.md` "after the owner's first play"):
- `bash tools/test.sh` green: 10,472 GDScript checks and 36 content tests. New or rewritten: `test_village_sim.gd`
  (a reward unit fights an enemy on its way to its point and still arrives; a defender beyond its leash walks home
  without chasing), `test_miss_mute.gd` (miss mutes, hit restores, bass miss leaves kick alone, backing never mutes,
  phase change restores, restart unmuted), `test_battle_sfx.gd` (shots −18 dB, every rule at most −3 dB, weapon
  group cap 3, limiter on the SFX bus), the mission 1 tests (252 default cues, 72 bass taps on pads 1 to 4 at
  least 1440 ticks apart, no holds, perfect play still destroys all 25 waves, villagers lost at most 4),
  `test_mission_layout.gd` and `test_rewards.gd` through `BattleView.cell_px`, the content tests (`BassChartTests`,
  the village battlefield values).
- Seeded balance, seeds 1 to 3: mission 1 perfect, beginner and sloppy 3/3 each with all 139 enemies destroyed, no
  input loses at about 1:41; missions 2 to 10 re-run with the new defender behaviour: three late losses appeared,
  two fixed by raising objective hp (mission 5 core 130,000, mission 8 radar dome 70,000); mission 10's core went
  to 185,000 and its beginner seed 3 still falls at 108.0 s of 110.3 (known, see `docs/BALANCE.md`).
- Real 1280 x 720 window with perfect autoplay to VICTORY: screenshots of the zoomed village (wall ring, all three
  points and the rally flag on screen, the flag moving with the suggestion; the "RALLY: LEFT (auto)" top-bar text of that build is gone), a bass phase with "Deep
  Sub" on all four pads, act 2 fighting at the left point, the result screen. Not by a person; nobody has heard the
  mix, the miss muting or the bass chart; nobody has tapped by hand.
- Latent build bug fixed in passing: since 2 November `python tools/content/build.py` failed on missions 8 and 10
  ("choice kick_sound pairs with several clip choices") because their kick and snare sound choices are shared by the
  groove and the fill; `_choice_entries` now follows only a restricted parent. Both packs rebuild again.

Verified (3 November 2026, the village level, this PC; see `docs/BALANCE.md` "The village level"):
- `bash tools/test.sh` green: new suites `test_village_sim.gd` (civilians, start units, target classes, squads, the
  active section), `test_civilian_art.gd`, `test_section_input.gd`, `test_battle_sfx.gd`, the rewritten mission 1
  tests (128 bars, 32 sequences, every wave destroyed by perfect play for every groove and bass line, villagers lost
  at most 4, no input loses), `tools/test_extract_openra_sounds.py` and the content tests for the village map.
- Seeded balance, seeds 1 to 3: perfect 3/3 with all 139 enemies destroyed, beginner 3/3, sloppy 2/3, no input 0/3
  (the barracks falls at about 97 s). Missions 2 to 10 produce byte-identical harness reports to before.
- Real 1280 x 720 window with perfect autoplay to VICTORY; screenshots of the village, the flag after a tap on each
  section, the move flash, the acts and the result screen with villagers. Not by a person; no sound heard by anyone.

Verified (2 November 2026, the Mission 1 rebuild, this PC):
- `bash tools/test.sh`: 2,854 GDScript checks and 20 content build tests, 0 failures. New: `tests/test_mission_one_content.gd`
  (all 81 combinations of groove x bass line x bass sound x backing load with their own stems and cues; a Sub recording
  asked for with the Reese line is swapped for the first Reese recording with a warning; defaults, 12 sequences, 6
  phases, 102 notes with every bass note a hold on pad 2, pad names from the bound sounds, both intro lines; perfect
  play wins with 12 of 12 sequences, 7 pillboxes, 5 jeeps and all 56 enemies destroyed for every groove and line; no
  input loses) and `tools/content/test_import.py` (11 tests on synthetic 44.1 kHz exports: format and length, attack
  timing against the MIDI, MIDI cut and tempo, gain, trim and fade, declarations, idempotence, pairing in the pack,
  refusals, the mode-change warning, `--check` writes nothing).
- The imported audio, by analysis (not by ear): every render is exactly 8 bars at 174 BPM (529,655 frames at 48 kHz),
  drum onsets match the MIDI within about 5 ms, the exact worst-case mix over all 81 combinations peaks at -3.03 dBFS
  and the default mix at -4.26 dBFS, the assembled stems have no clipping and no step at a loop or phase boundary
  larger than the file's own 99.9th-percentile sample step, the tail after the song end is below -43 dBFS.
- Seeded balance of the new Mission 1 (`docs/BALANCE.md`): perfect 3 of 3 wins with every wave destroyed, beginner 3
  of 3, sloppy 3 of 3, no input 0 of 3.
- Real 1280 x 720 window, `RW_MISSION=1 RW_SCENE=play RW_AUTOPLAY=perfect`: plays to VICTORY (12 of 12, holds 30 of
  30, 7 defenses, 5 units), 4 streams, 3,964 frames, average 16.7 ms, 2 frames over 33 ms (loading), 53 MB static.
  Screens looked at by the agent: mission setup with the four rows (Drum groove, Bass line, Bass sound filtered by
  the line, Backing track) before and after switching to the Reese line, the play screen in a drum phase and in a
  bass phase, the result screen. Not by a person.

Verified (3 November 2026, night: loadouts; this PC; see `docs/BALANCE.md` "Loadouts"):
- `bash tools/test.sh` green: 11,663 GDScript checks and 62 content tests. New or
  rewritten: `test_library_index.gd`, `test_loadout.gd`, `test_loadout_screen.gd`, `test_transport.gd` (loops, longest
  first, unwrapped position), `test_campaign.gd` (save v3 and the v2 migration), `test_mission_one_content.gd`,
  `test_all_missions.gd` (782 checks: every mission loads and perfect play wins it).
- Seeded balance, default loadout, seeds 1 to 3: perfect 30 of 30, beginner 29 of 30 (mission 9 seed 3 loses at 87.2 s of
  88.3), no input 0 of 30, sloppy 14 of 30; seeds 4 to 6: perfect 30 of 30, beginner 28 of 30 (mission 8 seeds 4 and 5).
  Mission 1 perfect destroys 266 to 271 of 278 enemies (96 to 97%) and loses 0 of 10 villagers. Heavy loadout, untuned:
  perfect 30 of 30, beginner 30 of 30, no input 0 of 30; mission 1 destroys 213 to 237 of 278.
- The finding behind the loop engine: Godot's player position wraps at the loop length over looping
  `AudioStreamSynchronized` substreams (test output `FINDING: ... WRAPS`), so the transport unwraps it.
- **Not verified, loadouts:** nobody has heard the loops switching at phase boundaries, the fill bar or the loop seams
  (the build checks lengths and cues, not the sound); nobody has used the Loadout screen or the briefing by hand
  (the agent ran the scene tests only); nothing has run on a phone; the 117 loops include 99 placeholders.

**Not verified:** any phone run (touch feel, the two-thumb layout, frame time and memory with 16 Ogg streams on a
phone CPU, load time of mission 10), any listening check by ear (the build and the importer check sample positions,
lengths and headroom only; nobody has listened to the assembled Mission 1, its previews or the Red Alert effects in
the game), any human playtest of the cues, sequences, difficulty or the tap-to-deploy feel (the beginner and sloppy
policies are models; the harness taps the suggested section every frame), real owner renders for missions 2 to 10
(none exist yet; Mission 1's are real), the screens on a real phone's safe areas and DPI, the `make` animation on a
rewarded pillbox (only plays if the actor has that sequence).

## How to run the phone check (the owner's)

1. Install: `adb install -r build\android\RhythmWarfare-debug.apk` (or rebuild it first, `docs/EXPORT.md`).
2. Open the app, Settings > Calibrate once, then play mission 1 (Continue). For the heaviest case set
   `"unlock_all": true` in `data/campaign/campaign.json` and re-export, or play through, and run mission 10.
3. `adb logcat -s godot` prints a `PERF {...}` line when a run ends (p95 frame time, frames over 33 ms, peak units).
   Report that line, whether any press felt missed, whether the pads sit well under the thumbs, and the cue lead-in
   that felt right.
4. Settings has pad size, cue lead-in, high contrast, reduced effects, vibration and music volume.

## Owner decisions that are settled (do not re-ask)

From `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` Part A (31 Oct 2026): pads only (lane view dropped), one pad per bass
voice (the level 3 four-button bass chart and the thumb-gap rules are archived), a loop library at 174 BPM with
stable ids, offline assembly by one build command (no runtime clip engine, no in-game import screen), sequence rewards
replace per-note recipes, loadout caps and round robin, the legacy duel stays, holds are forgiving, early rewards are
static defenses first, wave units fight defenses, no slow practice, generated music for all ten missions, normal
progression on by default with `unlock_all` as a developer switch, the save migrates. Earlier: standalone Godot 4.5.1;
DuelMasterBattle is an asset source only; OpenRA pixel art and behaviour; work on `main`.

From the loadout redesign (3 Nov 2026, night; the owner's four answers): all music comes from the player's loadout (a
mission authors none); the arrangement is the pattern (the clip's own cues, tiled over the phases, are what is
played); instruments decide the units by family (kick sounds infantry, snare sounds defenses, bass sounds vehicles);
recordings are tied to their patterns (a clip plays only the sounds it was recorded with). Earlier loadout choices of
the 31 October brief (per-mission pools and counts) are retired with them.

## Decisions made in this build (routine design details)

1. Pad mapping and windows as above (`data/campaign/rules.json` holds every number).
2. Sequence threshold 0.6; precision grades 35 / 70 ms; 25 ms per stray per cue.
3. Placeholder WAVs are not committed (133 MB); the build regenerates them deterministically.
4. Missions 1 to 3 keep their First_Three bar counts; missions 4 to 10 grow from 48 to 80 bars.
5. `fix` (service depot) is not used: the simulation has no unit-repair behaviour. `agun`/`sam` are AA-only and unused
   (no air threat). The APC is named "APC (gun only)" because it carries no troops.
6. Defenses measure range from their footprint edge in missions (flame towers could not reach riflemen otherwise);
   defenders sortie against outranging artillery and V2s. Both are mission-only, so the duel's results are unchanged.
7. Practice is the same mission with the battlefield hidden and nothing saved; the setup screen can practise one phase.
8. Mission 10's pools were trimmed to keep it at 16 streams and about 14 MB of Ogg.
9. Village level (3 Nov 2026, owner's calls): infantry only for the player, a few enemy jeeps in act 3; civilians are
   atmosphere (wander, flee, die, counted; never repair; never required); a tap sets the active section until the next
   tap (rewards before any tap are placed as before); rewards are pillboxes and rifle squads, grenadier squads from act
   3; 128 bars; the barracks is the one required objective with 60,000 hp; civilians are side-0 entities with a
   `civilian` flag (never a third side: every sim array is indexed by side); the sim uses a separate `civ_rng` for
   wandering so combat outcomes of other missions are unchanged; the autoplay harness taps sections only on levels
   with civilians (`RW_SECTION=auto|none|fixed:<i>`), because tapping the next wave's point every frame makes mission
   5 lose.
10. First-play tweaks (3 Nov 2026, owner's calls): bass pads by pitch low to high, taps only, one cue per 1.5 beats
    (the owner asked for one per beat; at one per beat the Reese line kept all 23 of its notes, so the gap is 1440
    ticks); a miss silences the instrument until the next hit on it; zoom three quarters with the rally points
    further out; units fight on the move but a defender never chases beyond its leash.
11. No top bar in missions (3 Nov 2026): the owner found it noise; nothing is drawn over the map but the flag and the
    units' own bars. The wave warning line went with it (the EVA voice still warns).
12. Falling notes (3 Nov 2026, owner's call): the closing rings did not work for the owner; notes fall over the
    battlefield from the top of the screen so the map and pads keep their size (a lane band between them would have
    shrunk the map the owner had just zoomed out). The shape equals the pad at the hit time.
13. Rewards every 2 bars with every wave doubled (3 Nov 2026, owner's calls); the threshold stays 0.6, so a drum
    sequence needs 3 of 4 or 5 taps and a bass sequence 2 of 3. Capacity is the first balance lever (mission 1 keeps
    14 units per point; missions 6, 8 and 10 got 12), objective hp the second; wave counts and sequence length are
    not touched by balance.
14. MIDI export choices: the exported loops mirror what the missions play (the default groove tiled with the default
    fill in bar 8), alternatives are rule-based and seeded by the mission seed (at least one edit per two bars, at
    most a quarter of the notes), ghosts go an eighth before a backbeat because a sixteenth would break the pad gap,
    missions without a bass phase get a root-note `Bass_A` so the owner can add bass later.
15. Loop engine (3 Nov 2026, night): the game plays 8-bar Ogg loops (one per clip part and sound) as substreams of the
    one `AudioStreamSynchronized`, `loop = true`, longest first, gain switched per bar by the pack's gain program;
    no assembled per-mission stems. The finding: the player's playback position wraps at the loop length, so the
    transport counts wraps (`song_base + wraps x loop_seconds + raw`) and everything else keeps one unwrapped clock.
    A fill plays in bar 8 of every eight (its stems on, the groove's off).
16. Even/odd rule: a drum sequence k takes the kick instrument's next reward when k is even and the snare's when odd
    (counted over the whole mission), a bass sequence the bass instrument's; each cycle advances once per use. Chosen
    because it needs no mission data and keeps both drum sounds in play.
17. Defaults: the default loadout is mission 1's kit (Half-Time, no fill, Half-time kick, Backbeat snare, Sub line,
    Deep sub, Driving hats); the player's saved loadout starts there; `loadouts.json` also has `village` (the same) and
    `heavy` for the tools.
18. The village has no war factory, so bass sounds (vehicles) give repair crews there; the briefing says so and strikes
    the vehicles out of the unit strip. Missions 2 to 10 have a factory.
19. Acc backings cut to 16 bars: the generated backing clips were 32 to 48 bars, the loop library keeps their first 16
    (10 ms fade); a backing loops under the whole song.
20. The campaign ladder lists every pickable library item (clips and sounds, 57 ids): mission 1 lists 26 (the starter
    kit and its first set), missions 2 to 10 a few each plus their own backing track.
21. Loadout retune (3 Nov 2026, night): missions 5 to 10 got start units (five riflemen per point, rocket soldiers and
    medium tanks in 9 and 10), prebuilt pillboxes and turrets, bigger objective hp and `units_per_point` 12 (mission
    10: 20); start units count against `units_per_point`, so the default 6 turned reward squads into repairs. Wave
    counts, timing, the sequence length, the threshold and the instruments were not touched.

## How the code is organised

- `src/core/`: `library_index.gd` (reads `songs/library/index.json`: clips, sounds, cues, loops, compatibility),
  `loadout.gd` (the slots, `resolve`, reward cycles), `mission_loader.gd` (schema 4: loadout -> stems, cues, sequences,
  gain program; schema 2 and 3 packs are refused), `mission_rules.gd` (rules.json),
  `sequence_tracker.gd`, `match.gd` (mission flow: judge -> sequences -> rewards in the tick loop; and the duel flow),
  `campaign.gd` (ladder, unlocks, save v3 with the v1 and v2 migrations, the loadout), `session.gd` (settings v2, `start_mission`, env
  overrides), `level.gd`, `level_loader.gd` (schema 1 duel and dispatch; schema 2 is refused as retired), `song_clock.gd`.
- `src/input/pad_judge.gd` (missions), `judge.gd` (duel), `lane_input.gd` (touches and keys D F J K).
- `src/sim/battle_sim.gd` (deterministic 25 Hz OpenRA simulation; mission sockets, rewards with `count`, capacity,
  walls, prebuilt defenses, `start_units`, civilians and village buildings, wave target classes, the active section),
  `defense_ai.gd` (defenders hold and sortie, waves walk via their point then chase their class's goal, civilians
  wander and flee), `bot_ai.gd` (duel only).
- `src/ui/`: `pad_view.gd`, `battle_view.gd` (sprites only, three layers: neutral civilians, blue, red; the rally flag
  and move flash), `hud.gd` (the legacy duel's bar only; missions have no text overlay), `section_picker.gd`, `ui_style.gd`, `settings_panel.gd`, `sprite_bank.gd`.
- `src/audio/`: `stem_transport.gd` (the song: looping substreams, the unwrapped position, the gain program, on the "Music" bus), `battle_sfx.gd` (effects on the "SFX" bus from
  `data/sfx_map.json` and `assets/sfx/`).
- `tools/extract_openra.py` (sprites from the owner's OpenRA content, allow-list `NEEDED`, aliases `flagfly`),
  `tools/extract_openra_sounds.py` (AUD decoder and the sound list), `tools/campaign/build_battlefield.py`
  (`defense_01`, `defense_02`, `village_01`).
- `src/scenes/`: `main_menu`, `missions`, `mission_setup` (the briefing), `loadout` (`loadout.gd`/`.tscn`, the Loadout
  screen), `play`, `result`, `settings`, `calibration`, `developer`.
- `tools/content/`: `build.py`, `library.py`, `mission.py`, `chart.py` (the pitch-to-pad bass chart), `synth.py`,
  `common.py`, `render_list.py`, `export_midi.py` (reads `content/missions_legacy/`), `make_fixtures.py`,
  `test_content.py`. `tools/autoplay.gd` (harness), `tools/balance_missions.py`, `tools/shoot.gd`.
- Retired and removed: schema 2 and 3 packs and their assembled stems and previews (the schema 3 paths in `songs/mNN_*/audio`
  and `preview`), per-mission choices, schema 2 packs, the 30 October loadout screen (the current Loadout screen is new), `lane_view.gd`, the instrument catalogue, the campaign wave
  generators and `audio_preflight.py`. `docs/CAMPAIGN_PLAN.md` is kept with a superseded banner.

## Exports

Rebuilt on 31 October 2026 per `docs/EXPORT.md` (`build/` is git-ignored):
- `build/android/RhythmWarfare-debug.apk`: 95.8 MB (was 42.8 MB with three missions), debug-signed, arm64-v8a, all ten
  mission packs inside. Not installed on a phone by the agent.
- `build/windows/RhythmWarfare.exe`: re-exported 3 November 2026 with the village level, 232 MB (the 27 MB mission 1
  pack and the sounds); `[ DONE ] savepack`. Not smoke-tested that day: Windows Application Control blocked the fresh
  exe from the agent's shell, so the owner runs it. The 31 October smoke test was `RW_MISSION=10 RW_SCENE=play
  RW_AUTOPLAY=perfect RhythmWarfare.console.exe --headless` (mission 10 to the end with 16 streams, no errors).
- The Android APK was not rebuilt on 3 November (the owner declined on 2 November); it still holds the 48-bar mission 1.
- The APK grew because every offered combination of every mission is pre-assembled (67 MB of Ogg). If that is too
  large, trim the option pools of missions 7, 9 and 10 or lower the Ogg quality in `tools/content/common.py`.

## Known issues and backlog

1. Real stems for missions 2 to 10, the phone run and a human playtest (above). Retune waves after the owner has
   played; the numbers are a harness's, and outcomes from mission 5 on are seed-sensitive.
1a. Mission 1 on the owner's recordings: the 16 sound names and 8 clip names are provisional; the Sub Line's last note
   ends on the bar line where the next drum phase's first kick is cued (bars 25 and 41, same thumb: the build warns,
   the game credits a release up to 0.15 s early, mission 3 has the same shape); the bass sound row offers nine
   recordings, shown five or four at a time by bass line; the pads are two thumbs wide apart and the bass phases use
   pad 2 only, so a phone's feel is unknown; `content/REPORT.md` reports the loudest-options bound (-1.59 dBFS, a
   10 ms block envelope) while the exact worst case is -3.03 dBFS.
2. Wave units of one group can stack on one exact point while grinding a target (they separate when moving).
3. A wave jeep can loiter inside the base targeting the core without doing damage (seen once while tuning mission 7).
4. The autoplay report's `reached_s` equals the spawn time for left-entry waves (a report bug, not a game bug).
5. Headroom is checked for each mission's default selection only; louder combinations (for example Heavy Kick with
   Command Saw in missions 7 and 9) may clip slightly. Owner renders change this anyway.
6. (Gone: the library build takes 23 s and re-encodes only changed loops.)
7. Mission setup on very wide screens leaves the right half of the cards area empty (functional, not pretty).
8. Duel backlog items (idle fidgets, ruins, title art) still apply; the duel has no sound effects (the sound layer is
   wired in the mission play scene only).
9. Village level: a unit behind a house can draw over it (civilians and houses are one layer under both armies); the
   "defenses" waves that hold a choke point count as uncleared when the player never retakes it (sloppy runs); the
   pack is 27 MB of Ogg (18 stems x 129 bars); the sounds `reinfor1`, `bleep11`, `cashturn` are extracted but
   unused; no positional panning; at zoom 0.75 sprites are decimated with nearest filtering (linear would break the
   faction remap shader); the rally flag is small on a phone; the Reese line leaves pad 4 unused.
10. (Superseded by the loadout retune: mission 10 now holds under perfect and beginner play with core 400,000 and a bigger
    start army, `docs/BALANCE.md`.) Mission 10 beginner seed 3 lost at 108.0 s of 110.3 with the old reward lists.
11. (Done in the loadout retune, 3 Nov 2026, night: missions 6, 8 and 10 hold under perfect play with the default
    loadout; see items 14 and 15 for what is left.) With every wave doubled the evening run had lost them.
12. The falling notes are pad-sized and at alpha 0.4 read as solid blocks over the dark field; if the owner finds
    them heavy, `NoteLane.FILL_ALPHA` and the outline are the knobs. The hold bar of a two-bar hold is taller than
    the screen (by design: it keeps passing through the pad).
13. Loop seams: the build checks loop lengths and cues, not how a seam sounds; a ringing tail is folded onto bar 1 and
    nobody has listened to it, to the gain switches at phase boundaries or to the fill bar.
14. Heavy loadout (untuned, `docs/BALANCE.md` "Loadouts"): wins every mission under perfect and beginner play, but
    in mission 1 perfect play destroys only 213 to 237 of 278 enemies (77 to 85%) because its infantry is grenadiers and
    rocket soldiers; a retune for it would need start units or waves, not done.
15. Default loadout, known losses after four tuning rounds: mission 9 beginner seed 3 (87.2 s of 88.3, overwhelmed late),
    mission 8 beginner seeds 4 and 5 (the radar dome falls at 81 to 82 s); sloppy play loses most of missions 2, 4, 6, 8.
16. The bass sounds make vehicles, which the village (mission 1) cannot build: its bass sequences are repair crews.
17. The Windows and Android exports predate the loadout redesign (the packs shrank: no stems, 5.9 MB of loops); re-export
    before the next owner run.

## Everyday commands

```
bash tools/test.sh                                          # all headless tests + content build tests (about 1 min)
python tools/content/import_ableton.py content/imports/first_watch.json --check   # file an Ableton batch into the library (drop --check to write)
python tools/content/export_midi.py                         # MIDI loops + alternatives for missions 2 to 10 into midi_export/ (deterministic)
python tools/extract_openra.py --no-map                     # sprites from the owner's OpenRA content (allow-list NEEDED in the script)
python tools/extract_openra_sounds.py --check               # Red Alert sounds to assets/sfx (drop --check to write)
python tools/campaign/build_battlefield.py                  # regenerate the maps and battlefields (defense_02 and village_01)
RW_SECTION=none <godot> --headless --path . -s tools/autoplay.gd -- res://songs/m01_first_watch perfect 1.0 1   # harness without section taps
python tools/content/build.py                               # library (117 loops) + all ten packs, about 23 s; or name missions: level_05
python tools/balance_missions.py --loadout heavy --seeds 1 2 3 --jobs 4 > out.md   # trials with a preset of data/campaign/loadouts.json (default: "default"; about 80 s)
<godot> --headless --path . -s tools/autoplay.gd -- res://songs/m06_fortress perfect 1.0 1 loadout:heavy   # harness with a preset (or a JSON loadout); RW_LOADOUT=heavy does the same
python tools/content/render_list.py                         # rewrite docs/CONTENT_TO_RENDER.md
RW_MISSION=10 RW_SCENE=play RW_AUTOPLAY=perfect <godot> --path .    # scripted run in the real play screen, prints PERF
RW_MISSION=3 RW_SCENE=play RW_PRACTICE=1 <godot> --path .           # practice run (battlefield hidden)
RW_UNLOCK_ALL=1 <godot> --path .                            # every mission and option open for one run
RW_LEAD_IN=1.5 <godot> --path .                             # note speed override (0.6 to 2.0 s: time from screen top to pad)
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk     # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that. In
Godot 4.5 `var x := dict["k"]` is a parse error: annotate the type. In this shell, long quoted Python in heredocs
fails when it contains apostrophes: write scripts to files.
