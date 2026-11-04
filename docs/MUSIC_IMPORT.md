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
| Drum MIDI | Kick = 36, snare = 38 or 40. Other notes (hats, toms, claps) stay in the audio and are not cues. When none of 36/38/40 is present the importer picks them (below); `--kick 39 --snare 43` overrides. |
| Bass MIDI | Every note is a hold; pads follow pitch (lowest on pad 1). Dense lines are thinned for the easier levels. |
| Synth | Backing. Enters quietly with the bass. Optional: a set without a Synth export imports with a silent backing (reported). |
| Needed | Drums.wav + Drums.mid and Bass.wav + Bass.mid. The Synth MIDI is never read. A set with only WAVs (no MIDI) is refused with the file names to export: the cues are charted from the MIDI, never from the audio alone. |

## 2. Check, import, assign

```bash
python tools/content/beatshaper.py scan   NewMusic                   # sets found, paired files, missing or odd files
python tools/content/beatshaper.py survey NewMusic                   # every set measured: what was found, decided automatically, or why it is refused (writes nothing)
python tools/content/beatshaper.py check NewMusic --set "Lv2 Alien Spaceship"          # timing and cues of one set, writes nothing
python tools/content/beatshaper.py apply NewMusic --node mothership --set "Lv2 Alien Spaceship" --id lv2_alien_spaceship
python tools/content/beatshaper.py validate
```

`check` and `apply` fit the drum transients against the kick and snare notes at each known tempo profile. A profile **verifies strictly** when the fitted
tempo is within 0.25 BPM and every kick and snare is inside 12 ms; it **verifies loosely** when the tempo is within 0.25 BPM, at least 85% of the hits are
inside 12 ms and none is further than 40 ms (a soft or ghosted snare is reported as an outlier, not a refusal). The best verifying profile is used; if
none verifies the import stops and says what it measured, so a pack is never forced onto a tempo by assumption.

What the loosened importer decides on its own, always reported (`survey`/`check` print it, `timing_report.json` keeps it under `import_report` and
`timing.bass_timing`):

* **Bass timing.** The bass WAV is checked against the bass MIDI. If the audio detector cannot place the notes within the limit (median over 12 ms: it reads
  a wobbling bass loosely and gives up at +-80 ms), the bass is charted **from the MIDI timing** with a warning (`bass_timing.mode = "midi_fallback"`).
  `--trust-midi` asks for this explicitly (`"midi_flag"`) even when the detector would have agreed. Otherwise `"audio_checked"`. The loop audio is never
  moved either way: only the bass cue times come from the MIDI.
* **Kick and snare notes.** 36 is the kick and 38/40 the snare. When the drum MIDI has none of them, hats (42, 44, 46) and cymbals are skipped, the most
  common note of the lower half of the remaining pitches is the kick and the most common of the upper half is the snare (`drum_notes.mode = "auto"`, the
  choice and the note counts are printed). Auto-mapped notes have softer transients, so tempo verification then accepts 70% of the hits inside the limit but
  needs the fitted tempo within 0.1 BPM. `--kick`/`--snare` always override (`"explicit"`). A set with only one of the two (e.g. snares but no 36) charts
  that one with a note.
* **Phrase length.** A MIDI that ends at 15.75 or 16.5 quarters is the 16-quarter phrase; cues that start after the loop's end are left out and reported.
* **Missing Synth** (silent backing) and **missing MIDI** (refused, with the files to export) as in the table above.

It then:

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
* an alternate render (a node whose `audio` differs from its `chart`) has the same cues as the chart it plays under. Levels at one depth **may** chart
  different packs (each world its own song): that is a `WARNING` line in the validator's output (and a warning in `RunData`), not an error. See "Tiers".

The last four beats of every 16-beat block are cue-free by design (hit windows and hold tails resolve before the focus changes), so cues that fall
there in the source MIDI are not charted; the validator counts them.

## 3b. Tiers: how the difficulty lines up across worlds

Every pack carries four tiers of cues and a node at depth d plays tier `min(d, 4)` of *its own* chart pack, so siblings at one depth always play the same
tier even when they chart different packs. Tiers are nested (each contains the one below): tier 1 keeps whole-beat cues at least a beat apart (bass: two
beats); tier 4 keeps everything the chart rules allow (half a beat apart); tiers 2 and 3 add a third and two thirds of the extra cues in between
(`BASE_GAP`, `FULL_GAP`, `TIER_SHARE` in `beatshaper.py`). Before this the tiers 1/2 and 3/4 were nearly identical in most packs; now each step adds cues
wherever the MIDI has syncopation to give. The absolute density still depends on the song (the Asylum is sparse by design), see `docs/RUN_DUNGEON_MUSIC_PLAN.md`
section 7 for the measured numbers.

## 4. Worked example: giving a later level its own recordings

Historical example, from when the Ward was still a stand-in (Lv1 Warehouse (1) with the `ward` treatment); the Ward now has its own Lv5 Asylum set and siblings may chart their own packs, so `--audio-only` is only for a render of the *same* MIDI. To give a level its own sound over another level's chart:

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
refused, zips with `(1)`/`(2)` variants, missing files, a late bass, a ghosted snare, other kick/snare notes, a missing Synth, WAVs without MIDI) and checks
grouping, tempo verification (strict and loose), the bass fallback and `--trust-midi`, note auto-detection, loops, nested tiers, the validator and assignment.
Without `mido` installed the importer and the tests use a small built-in MIDI reader/writer, so they run anywhere with numpy.
