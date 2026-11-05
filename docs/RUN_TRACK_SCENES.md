# Track scenes: whole recorded tracks inside the run

The contract for the overnight audio overhaul of 5 to 6 November 2026. Everyone building it works to this
file. Background: `docs/GAME_GUIDE.md` (how the run fits together), `docs/TRACK_PACK_FORMAT.md` (what an
imported track is), `tools/audio_import/README.md` (how tracks are imported), `docs/MUSIC_TRACKS.md` and
`content/music/tracks/` (the catalogue).

## What the owner asked for

"Import all the music ... so we can use it in the game, and assign this music to the various levels and
scenes. Some scenes will need to be made longer potentially, handle this by having the options to remain in
an area or leave open up after a reasonable period of time, with the default being to stay until half way
through a song, when it switches to leave for the next scene."

Decisions the owner made when asked:
- Each scene has its own track, entered near its first drop (about 16 bars before it).
- Every scene gets new music: the main run's 36 scenes and the three side paths (Gospel, Squadron, Ember).
- The owner's pad model stands (they played it and approved it): one instrument at a time is the player's,
  all four pads play it, a miss silences only that instrument's stem and the rest keeps playing.
- Finished and verified work is merged into `main`.

My own assumptions, stated to the owner and not objected to: leaving is touching a door, as now, and staying
is doing nothing; half-way through the song is the limit; the run keeps its rhythm of 12 beats of cues and 4
beats of rest in every 16-beat block; no new in-play text. The Bassment dungeon, trials and the stub path are
not changed.

## The idea in one paragraph

A scene that has a track assigned, and whose pack is present on the machine, is a **track scene**. On
entering it the track starts playing from a chosen bar, at its own tempo, and keeps playing without a break
for as long as the player is in the scene. The scene lasts several 64-beat phases in a row (the engine's
existing "laps"). The first lap has no doors. From the second lap on, the doors open near the end of every
lap: touch one and you leave by it at the end of that lap; touch nothing and you stay for another lap. On the
last lap, which ends half-way through the song, the usual rule applies: the door you touched, or the default
exit if you touched nothing. The cues come from the track's chart: the focus instrument on all four pads. A
scene with no track, or whose pack is missing, plays exactly as it does today.

## Data

### Assignment: `content/run/track_scenes.json`

```json
{
  "format": "rhythm_warfare.track_scenes.v1",
  "defaults": {"entry": "drop1", "lead_in_bars": 16, "doors_from_lap": 2, "chart": "normal", "max_laps": 12},
  "paths": {
    "main": {
      "warehouse": {"track": "acuna_go_back", "alternates": [{"track": "annix_kingdom", "entry": "drop2"}]},
      "warehouse.bar": {"track": "bou_kasra_trenchfoot"}
    },
    "gospel": {"jordan": {"track": "paralel_in_the_clouds"}}
  }
}
```

- `paths` is keyed by path id (`main` for the main run, otherwise the `path.id` of
  `content/paths/<id>/run.json`), then by node id.
- A node entry: `track` (a track id from the catalogue), and optionally `entry`, `chart`, `start_bar`, `laps`,
  `doors_from_lap`, and `alternates` (a list of entries of the same shape without their own alternates).
- The scene plays `track` or one of its alternates, chosen by the run's seed in the same way a scene's
  arrangement alternates are chosen today, so a run is still reproducible from its seed. An alternate whose
  pack is missing is skipped; if none is present the scene is not a track scene.
- A node with no entry is not a track scene.

### Where packs are found

`RW_TRACKS_DIR` if set, otherwise `user://track_packs` (a folder or a link to one; on the owner's laptop it
links to `/home/joe/rw-audio-work/packs`). A pack is `<dir>/<track id>/track.json` plus its stems, format
`rhythm_warfare.track.v2`, loaded with the existing `TrackPack` loader. `RW_RUN_TRACKS=0` turns track scenes
off altogether. Nothing about the audio is ever in the repository.

**The test suite never depends on the machine's packs.** Under the test runner track scenes are off unless a
test turns them on and points at the synthetic fixture (`tests/fixtures/track_fixture`, or fixtures the test
writes). With track scenes off, every existing run is identical to before this work: same events, same times,
same charts, same audio schedule. That is the safety net for the whole change and must be shown by a test
that compares a run with the feature compiled in but off against recorded expectations of the existing tests
(all existing run tests staying green is the minimum).

### The scene plan (computed when the scene is entered, from the pack's `track.json`)

With B = 60 / `tempo.bpm` seconds per beat, a bar = 4 beats, and bars counted from `tempo.first_downbeat_s`:

- **Tempo**: the scene runs at the track's `tempo.bpm`, a float, whatever the path's own tempo is.
- **Entry bar** E: for `entry: "drop1"`, the first bar of the first section whose role is `drop`, minus
  `lead_in_bars`, not below 0. For `"drop2"`, the same from the second `drop` section (falling back to drop1
  if there is only one). For `"start"`, 0. A track with no `drop` section enters at the first bar of its
  loudest section minus the lead-in. `start_bar` in the assignment overrides all of this.
- **Phases**: lap k (counting from 1) covers bars E + 16(k-1) to E + 16k of the track. Scene time 0 is the
  downbeat of bar E.
- **Laps** (how long the scene lasts by default): for a drop1 or start entry, the number of whole laps that
  brings the scene's end nearest to half-way through the track (`duration_s / 2`), at least 2. For a drop2
  entry, the number of whole laps that fit before the track's last 2 bars, at least 2. Never more than
  `max_laps`, never past the end of the audio. `laps` in the assignment overrides.
- **Doors**: closed on laps before `doors_from_lap` (default 2), so the first lap is always played through.
  If the plan has fewer laps than that, doors open on the last lap.
- **Chart**: the pack chart named by `chart` (default `normal`; fall back to the pack's `default_chart`).

Worked example, "Go Back" (174.0032 BPM, drop1 at bar 56, 298.6 s so half-way is bar 108): E = 40, laps =
round((108 - 40) / 16) = 4, so the scene is bars 40 to 104 of the track and lasts 88 s; doors open near the
end of laps 2, 3 and 4, so the player can leave after 44 s, 66 s or, by default, 88 s.

## Behaviour

### Engine (timing, laps, doors)

- A track scene keeps the run's phase structure unchanged: 64 beats, 4 blocks of 16, cues in the first 12
  beats of a block, the block judged at beat 12.5, doors touchable from the third block's decision, the
  choice made at beat 60.5, the door walk from beat 61. Only the length of a beat changes (the track's
  tempo) and the number of laps.
- Tempo changes at a scene boundary the way the path hand-off does it today (a fresh beat grid whose origin
  is the new scene's first downbeat). Beat-synced visuals (dancers, lights, the rail, cast timings) take the
  scene's tempo; nothing may pop or jump at the change beyond what the path hand-off already does.
- Laps for track scenes: allowed on every path including the main run, up to `max_laps`. The stage, cast
  and audio carry across laps as they do for path scenes today.
- Doors on a lap that is not the last ("an open lap"): the window opens at the same beat as on a last lap.
  If the player touches an exit (or any hotspot that leads out of the scene) before beat 60.5, that lap
  becomes the last lap: the choice is committed, judged and walked exactly as a last lap's is. If they touch
  nothing, nothing is committed, the hotspots reset for the next lap, and the scene goes on. On the plan's
  final lap the existing rule applies in full, default exit included.
- Hotspots that are not exits (the wizard, the card table, portals with their own windows) keep their own
  rules on every lap they would have had them on a single-lap scene. Where a rule says "first lap only" or
  "last lap only" today, say in your report what you chose for the middle laps and why.
- A minigame that holds the run (the card table) holds a track scene too: the track keeps playing and the
  laps keep counting. If the hold outlasts the plan, the scene goes on lap by lap until the track has fewer
  than 16 bars left, then the track starts again from bar E. It must never fall silent or stop the run.
- A path's scenes that today play 2 laps with authored acts over both keep those acts in their first two
  laps; later laps repeat the second lap's acts or play none, whichever the existing code makes simpler.
  Say which.

### Cues

- The scene's cues are the chart's cues that fall inside the scene, moved to scene time (track time minus
  the time of bar E's downbeat). A cue belongs to the lap and block its time falls in.
- Cues whose time falls in the last 4 beats of a block are left out. A hold is cut so it ends by beat 12 of
  its block; if that leaves it shorter than half a beat it becomes a tap.
- Each cue keeps its `pad` and its `voice` (the focus instrument it plays). They are judged by the run's
  existing judge with the run's windows.
- A block is passed or failed as today (mean credit of its cues against `pass_credit`) and the result
  drives what it drives today: energy, the stage step (which now only drives lights and crowd, see Audio),
  the camera rail, hotspot success, minigame wobble.
- A block with no cues (the focus has a gap, or the instrument rests) is neutral: it passes, the rail and
  the acts go on, but it gives no energy and does not step the stage.

### Audio

- All the pack's stems (voices and backing) play as one synchronised group from the downbeat of bar E, at
  their pack gains, through the music bus with the run's limiter, and keep playing across laps with no
  restart. At the scene's end the group fades with the door as a scene's music does today, while the next
  scene's music starts on its own downbeat.
- The run's stage gains (drums alone, then bass, and so on) do not apply to a track scene: every stem
  sounds from the start. The stage still steps on passed blocks and still fires the events the lights and
  crowd listen to.
- A missed cue, or a hold let go early, mutes that cue's voice. The next cue hit for that voice restores
  it. A muted voice also returns by itself 8 beats after it was muted if its next cue is further away than
  that (the rule in `docs/TRACK_PACK_FORMAT.md`). Backing never mutes. Mutes ramp over 30 ms.
- The riser and fall at the window, the hotspot dip and the world treatments apply if they can be applied
  to the group simply; otherwise leave them out for track scenes and say so.
- Cue times and audio must agree to within the run's existing accuracy for loop voices (one mix chunk).
  Measure it and report the number.
- Loading: the packs a scene can lead to are loaded ahead of time off the main thread once that scene's
  doors first open; entering a scene must not stall the frame. If a pack is not ready in time the scene
  plays as it does today (loops) rather than wait. Measure the load time of a real pack and report it.
- A scene that is not a track scene sounds exactly as today, including when it follows or precedes a track
  scene.

### Energy

Scenes are several times longer, so a player meets several times as many blocks per scene. The per-block
rule must be rebalanced for track scenes so that a player of a given accuracy survives about as many scenes
as they do today, not a fraction of them. Do it with data (new numbers under `energy` in `run.json`, used
only by track scenes), justify it with the existing balance method (bot players at a range of accuracies,
as in `docs/HANDOVER.md` A12), and give the table.

### What the player sees

No new text. On a lap whose doors are open the doors and their lights behave as they do today on a final
lap, and on a lap with closed doors as they do today on a first lap of a two-lap scene. The run HUD's window
bar follows. The developer overlay (playtest/debug) should show the track id, lap k of n and the entry bar.

## Not in scope

The Bassment, trials, the stub path, the mission and duel modes, any change to how tracks are imported or
charted (that is `tools/audio_import/`), Android export of packs, and the option of cues running through all
16 beats of a block.

## Checks that decide whether it is merged

1. The whole test suite green with track scenes off, and every existing run test unchanged.
2. New tests green: the plan arithmetic, laps and open-lap doors (leave early, stay, default at the end),
   cues from a chart (lap and block tags, the 12-beat rule, holds), neutral blocks, mutes and restores in
   the run, missing-pack fallback, seed-reproducible alternates, tempo change between scenes, the hold
   case, on synthetic fixture packs.
3. An automated player (`RW_RUN_BOT`) completes a main-run pass and one pass of each path with real packs
   present, with no script errors, and the event log shows track scenes of the planned lengths.
4. `python3 tools/run/check_hotspots.py` and the Python content tests as before.
