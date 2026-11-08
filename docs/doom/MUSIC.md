# Music of the Doom worlds

With `RW_DOOM_WORLDS=1` each of the eight worlds is a TRACK SCENE (docs/RUN_TRACK_SCENES.md): it plays one imported recording, at the track's own tempo, from its first drop, instead of the procedural
`warehouse_1` arrangement every world used before. The entries are in `content/run/track_scenes.json`, `paths.main`, keyed by the scene id (each world is one scene whose id is the world id).
They use the file's defaults (entry `drop1`, 16 lead-in bars, normal chart) and have no alternates, so a world always plays the same track. With track scenes off (`RW_RUN_TRACKS=0`) or a pack missing
from the machine, the scene falls back to its procedural arrangement as before. Without the flag the entries are ignored (the legacy campaign has no such scenes).

Change the music here and in the JSON together: one line per world, `"doom_<world>": {"track": "<pack id>"}`. The pack id is the folder name in the packs folder (`RW_TRACKS_DIR` or `<RW_AUDIO_WORK>\packs`).

| World (scene) | Pack id | Title | bpm | Why |
| --- | --- | --- | --- | --- |
| The Floor (`doom_warehouse`) | `origin_unknown_valley_of_the_shadows_chase_status_remix` | Valley of the Shadows (Chase & Status Remix) | 174 | The brief's opening Warehouse track (DOOM_WORLDS_BRIEF). Full build and two drops. |
| Copper Bar (`doom_bar`) | `floodlight_dnb_aid_for_pakistan_warm_roller_memory` | Warm Roller "Memory" | 174 | Title says it: a warm rolling groove for the brick and copper room. |
| Chill-out Lounge (`doom_lounge`) | `paralel_in_the_clouds` | In The Clouds | 175 | Deep, airy, smooth: the least pushy of the set (intro, drop, breakdown, drop). |
| DJ Booth (`doom_booth`) | `metrik_t_2000` | T-2000 | 174 | Tight, mechanical, technical Metrik; the control-room glass and desks. |
| Loading Dock (`doom_dock`) | `ac13_shostakovich` | Shostakovich | 175 | A classical-leaning, brooding title for the rain street; moody. |
| Balcony (`doom_balcony`) | `nectax_zephyr` | Zephyr | 172 | Wide and atmospheric by name; the shortest pack (213 s), with two builds. |
| Mothership (`doom_mothership`) | `k_motionz_simula_phantasm_original_mix` | Phantasm (Original Mix) | 174 | Cold, alien, twitchy; long structure with four drops for the big hub. |
| Underworld (`doom_underworld`) | `teddy_killerz_teddy_killerz_night_train_t3ggcfz1vs` | Teddy Killerz - Night Train | 175 | Heavy, dark neuro; the lava plateau. |

Honest limit: these picks were made from titles, artists, tempos and section structure read out of each pack's `track.json`, not by listening. The owner or the lead should audition them and swap any row
(a world's track can be any of the 61 packs; prefer 172 to 177 bpm so the downbeat lands on the stage's 174 clock).

Tests: `tests/test_doom_views.gd`, the `test_music_*` block (eight entries, eight different packs that exist in `RW_TRACKS_DIR`, each scene resolves to a plan naming its pack). Rule: an entry for a `doom_*`
scene that the run does not have (the flag is off) is skipped, not an error (`RunTrackScenes._read`).
