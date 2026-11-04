# Importing music for the story run

One workflow for every level: export a Beat Shaper set, run one command, validate. Nothing in the game code changes and no loadout or
library registration is involved. Recordings are only ever read; everything the game plays is a generated copy under `songs/packs/<id>/`.

## 1. Export

Per level, one *set* in the format you already use: `Beat Shaper - <project>-Drums`, `-Bass`, `-Synth`, each as `.wav` and `.mid`.
Variants of a project keep the ` (1)`, ` (2)` suffix on all three of their files; files are grouped by project name and suffix, never by
position. Put the files in a folder (e.g. `NewMusic/`) or a ZIP, anywhere. `docs/MUSIC_HANDOFF.md` lists the exact project names and file
names each level expects, how many sets are needed and what each level plays today.

What the importer needs from a set:

| | |
| --- | --- |
| WAV | 48 kHz (16/24-bit PCM or 32-bit float, mono or stereo). Not resampled, never stretched. Different lengths per stem are fine. |
| Length | 16 quarter notes of music plus any release tail (a tail up to one phrase long is folded onto the loop start). |
| Tempo | Rendered at 87 BPM (a quarter = two game beats, the verified Lv1 Warehouse profile) or at 174 BPM (a quarter = one game beat, the verified Lv2 Alien Spaceship profile). The MIDI header may say anything (the exports say 120): it is ignored. |
| Drum MIDI | Kick = 36, snare = 38 or 40. Other notes (hats, toms, claps) stay in the audio and are not cues. Other mappings: `--kick 39 --snare 43`. |
| Bass MIDI | Every note is a hold; pads follow pitch (lowest on pad 1). Dense lines are thinned for the easier levels. |
| Synth | Backing. Enters quietly with the bass. |

## 2. Check, import, assign

```bash
python tools/content/beatshaper.py scan  NewMusic                    # sets found, paired files, missing or odd files
python tools/content/beatshaper.py check NewMusic --set "Lv2 Alien Spaceship"          # timing and cues of one set, writes nothing
python tools/content/beatshaper.py apply NewMusic --node mothership --set "Lv2 Alien Spaceship" --id lv2_alien_spaceship
python tools/content/beatshaper.py validate
```

`check` and `apply` fit the drum transients against the kick and snare notes at each known tempo profile. The profile that agrees (within 0.25 BPM
with every kick and snare inside 12 ms) is used; if none does the import stops and says what it measured, so a later pack is never forced onto the
Warehouse tempo by assumption. The bass is checked against the bass MIDI too (a median error over the limit stops the import; single outliers are
warnings, because a wobbling bass is hard to place). It then:

* writes `songs/packs/<id>/loops/{drums,bass,other}.wav` (16-bit, exactly one phrase long, tails folded onto the start), `pack.json` (stems, tempo
  profile, source files, the four difficulty tiers of cues) and `timing_report.json` (what was measured);
* with `apply`, points the node at the pack in `content/story/music.json` (`audio` and `chart`). `--audio-only` keeps the level's chart and uses only
  the new recordings: use it for a sibling level that should *sound* different over the same chart (the MIDI must be identical; `validate` compares).

Re-running an import with the same `--id` rewrites the same files (ids and outputs are stable). Level and route ids never change; only
`content/story/music.json` says which pack a level plays, and `treatment` (a filter, distortion or reverb chosen in `content/run/run.json`)
colours the same recordings when no alternate render exists. `temporary: true` marks stand-ins.

## 3. What `validate` checks

* every set's three WAV/MIDI pairs exist (missing or ambiguous files are listed by name);
* pack ids are unique and equal their folder names; every stem exists and is exactly the loop length at 48 kHz;
* the phrase (16, 32 or 64 game beats) tiles the 64-beat phase;
* every cue sits on a real pad inside the phrase, and chart rules (same-pad spacing, thumb moves, at most two touches) hold for all four tiers;
* every level in `run.json` has an entry in `music.json` and both packs exist, with equal phrase lengths;
* levels at one depth share one chart, and an alternate render has the same cues as the chart it plays under.

The last four beats of every 16-beat block are cue-free by design (hit windows and hold tails resolve before the focus changes), so cues that fall
there in the source MIDI are not charted; the validator counts them.

## 4. Worked example: giving a later level its own recordings

The Ward (depth 3) plays Lv1 Warehouse (1) with the `ward` treatment as a labelled stand-in. To give it its own sound over the Hospital's chart:

```bash
python tools/content/beatshaper.py scan  NewMusic
python tools/content/beatshaper.py apply NewMusic --node ward --set "Lv3 The Ward" --id lv3_ward --audio-only --treatment none
python tools/content/beatshaper.py validate
```

The output below is the real output of this workflow run on a ZIP of the existing Lv1 Warehouse (1) files standing in for the new export.

```text
$ python tools/content/beatshaper.py scan Lv3_export.zip
Lv3_export.zip: 6 files, 1 sets
  lv3_the_ward                 Lv3 The Ward  paired

$ python tools/content/beatshaper.py apply Lv3_export.zip --node ward --set "Lv3 The Ward" --id lv3_ward --audio-only --treatment none
Lv3 The Ward
  header 120.0 BPM; profile beat_shaper_87x2: drums fit 86.993 BPM, 30/30 hits, max 8.24 ms, offset 5.6 ms
  phrase 32 game beats, loop 529655 frames (11.0345 s)
  bass: beat 0 +0.6 ms, beat 4.25 -80.0 ms, beat 8 -2.0 ms, beat 12 -14.0 ms
  tier 1: 23 drum cues, 4 bass cues
  tier 2: 23 drum cues, 4 bass cues
  tier 3: 31 drum cues, 4 bass cues
  tier 4: 31 drum cues, 4 bass cues
  WARNING bass: some note changes could not be placed within the limit (the detector reads a wobbling bass loosely): [{"beat": 4.25, "pitch": 38, "error_ms": -80.0, "how": "largest spectral change nea
written songs/packs/lv3_ward
node ward now plays lv3_ward

$ python tools/content/beatshaper.py validate
pack lv2_alien_spaceship_v2: Lv2 Alien Spaceship (2), 16-beat phrase, profile beat_shaper_174x1; cues in the block guard (not charted): tier 1 bass 1, tier 1 dr
pack lv3_ward: Lv3 The Ward, 32-beat phrase, profile beat_shaper_87x2; cues in the block guard (not charted): tier 1 drums 6, tier 2 drums 6, tier 3 drums 10, t
music.json: 7 nodes assigned
OK
```

The level then played the imported pack in the game (a scripted run starting at the Ward reached its second level on the new recordings). The assignment was reverted afterwards so the repository keeps its lean stand-in.

To undo an assignment, point the node back: `python tools/content/beatshaper.py assign --node ward --audio lv1_warehouse_v1 --treatment ward`.

## 5. Tests

`python -m unittest discover -s tools/content -p "test_beatshaper.py"` builds synthetic exports (87 and 174 BPM, a 130 BPM one that must be
refused, zips with `(1)`/`(2)` variants, missing files) and checks grouping, tempo verification, loops, tiers, the validator and assignment.
