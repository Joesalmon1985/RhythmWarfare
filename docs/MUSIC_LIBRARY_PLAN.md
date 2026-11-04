# Music library and arrangement system: implementation plan (Fable, 2026-11-04)

Executes the owner's brief `docs/MusicImportPlan.md` on the game as it stands on `main` (`3b74c67e`). Branch `feature/music-library`.
Companion plan: `docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md` runs in parallel on `feature/visual-adventure`; the two meet at `content/story/music.json`
(a scene names what it plays) and must not edit each other's files (section 6).

## 1. What exists (do not rebuild)

| Piece | Where | Used by |
| --- | --- | --- |
| Beat Shaper importer: tempo fit (87 and 174 profiles), loop cut, tails folded, kick/snare/bass cues in 4 tiers, `survey`, `validate`, built-in MIDI reader | `tools/content/beatshaper.py` | the run, the Bassment |
| 20 packs: `songs/packs/<id>/{loops/{drums,bass,other}.wav, pack.json, timing_report.json}` | `songs/packs/` | `RunData`, `RunAudio` |
| Per-scene assignment: `audio`, `chart`, `treatment`, `temporary` for 36 run scenes and the trial | `content/story/music.json`, `content/trial/passages.json` `music` | `RunData` |
| The run's audio: one silent 64-beat loop is the clock, per-phase voice groups (drums, bass, synth) started on the grid, gains ramped at block boundaries, riser/fall, treatments, pack preload on a thread | `src/run/run_audio.gd` | `run_play.gd` |
| The chapters' audio: `StemTransport` (four stems, gain switches at phase boundaries) playing a mission pack (`songs/m01..m10`, `songs/story_n1_warehouse`) | `src/audio/stem_transport.gd` | `story_play.gd` |
| The loop library (31 clips, 30 sounds, 8-bar Oggs) built from Ableton exports with `import_ableton.py` + `build.py` (needs the `mido` module, absent here) | `songs/library/`, `content/library/` | the military missions' loadout |
| Recording checks: `record_music.gd` + `check_run_audio.py` / `check_trial_audio.py` | `tools/story/`, `tools/trial/` | verification |

## 2. Source material (never modified; `.asd` ignored)

`ToAddTry2/` (129 files, imported already), `ToAddTry3/Cold/` (60 files) and `ToAddTry3/Meta/` (32 files). Two formats:
- **Beat Shaper sets** (`Beat Shaper - <project>-{Drums,Bass,Synth}[ (n)].{wav,mid}`, 32-bit float, 48 kHz, 174 or 87 BPM): Cold Fusion Interface x4, Metaverse Ready Fusion x2, plus the
  Lv1 to Lv5 and DD sets already imported. `survey` fits all the Cold sets today.
- **Ableton renders** (`Bass<N><Timbre>.wav` with `Bass<N>.mid`, `Kick<N>`, `Snare<N>`, `Other<N>`; 44.1 kHz 16-bit; 4 or 16 bars, some with tails): Cold has Bass2 to Bass5 each in
  HardHarmonic, FlaringAnger and Trap renders (same MIDI, three timbres = one family each), Kick2, Snare2, Other2; Meta has Snare1, Other1, Other2 and more.

## 3. Deliverables and work packages

### M1 Catalogue (Sonnet, worktree, owns `tools/content/catalogue.py`, `content/music/catalogue.json`, `docs/MUSIC_CATALOGUE.md`)
- Recursive discovery of `ToAddTry1`, `ToAddTry2`, `ToAddTry3` (configurable list); WAV via numpy (PCM 16/24/32-bit and float, any rate), MIDI via the built-in reader in
  `beatshaper.py` (factor it into `tools/content/midi_reader.py`; `common.py` already imports mido optionally; nothing new to install).
- Per file: sha256, provenance (folder, export group, variant suffix), paired WAV/MIDI, measured tempo (drum-transient fit against the MIDI as the importer does; bass by spectral change),
  profile (174x1, 87x2), bar count, leading silence, release tail, sample rate, duration, role (kick/snare/perc/bass/synth/pad/fx from the name and spectrum), MIDI notes (positions,
  durations, velocities, density per bar), pitch classes and an estimated tonal centre (chroma over the bass and synth; marked `confidence`), rhythmic density and syncopation
  measures, loudness (RMS, peak, clipping count), and a `family` (the export group: a Beat Shaper project and its variants; an Ableton pattern and its timbres).
- Compatibility table: pairs within a family are compatible (strongest evidence); across families only when bar length and profile match and the tonal centres agree or either part is
  atonal (drums), with `uncertain: true` where the estimate's confidence is low; never a claim from tempo alone. Output `catalogue.json` (machine) and `MUSIC_CATALOGUE.md` (human,
  with the per-folder tables and the flagged pairings for the owner's ear).
- Tests: synthetic fixtures (as `test_beatshaper.py` builds) for discovery, pairing, tempo detection at both profiles, tail detection, role detection, determinism of the catalogue.

### M2 Importers (Sonnet, same worktree after M1; owns `tools/content/beatshaper.py`, `import_ableton.py`, `library.py`, `build.py`, `songs/packs/`, `songs/library/`, `content/library/`)
- Beat Shaper: import the Cold and Meta sets with stable ids (`cold_fusion`, `cold_fusion_v1..v3`, `meta_fusion`, `meta_fusion_v1`); keep the four-tier charts.
- Ableton renders into the loop library without `mido` (the built-in reader), 44.1 to 48 kHz through the existing SoX path, clip length 4 bars where the render is 4 bars (the library
  format allows `bars`), timbre renders registered as `sounds` of one clip (Bass2 = one clip, three sounds), Kick/Snare/Other as the drum clips they are; `build.py` runs. Record
  gain staging per family as the manifest does. Both catalogues updated. `check_assets`-style determinism: rebuild is byte-identical.
- Tests extended; `validate` covers the new packs.

### M3 Arrangement system (Sonnet, worktree; owns `tools/content/arrange.py`, `content/music/arrangements/*.json`, `src/run/run_audio.gd` (extension only), `src/run/run_data.gd` (music fields only), `tests/test_run_audio_sections.gd`, `tests/test_arrangements.py`)
- An **arrangement** is data: `{id, family, seed, sections: [{bars: 8|16, pack: <pack id> | stems: {drums, bass, synth: <library clip/sound>}, mix: <recipe name or gains>, fills: [...], role: intro|build|drop|breakdown|variation|ending}]}`,
  built offline by `arrange.py` from the catalogue with a seeded, deterministic generator that respects the family rules (one family per arrangement unless the catalogue says compatible),
  changes on 8-bar boundaries, keeps one identity per scene, and never selects at random per bar. Each chapter identity gets a palette (Night One warehouse energy; Mothership electronic;
  Underworld dark neurofunk; Hospital fragile then uplifting; Ward unsettling industrial) expressed as catalogue filters, not filenames.
- **Run playback**: a scene's `music.json` entry may name an `arrangement` instead of one pack; `RunAudio` plays its sections in order across the scene's 64-beat phase (two 8-bar sections per
  phase or one 16-bar), switching pack voices on the section boundary with the same grid-scheduled start it uses for phases, gains from the section's mix on top of the phase mix; charts
  follow the section's pack (the chart for block N is the section playing then; the route lock compares the *chart pack of block 0 of the next scene*, unchanged). Determinism: the same
  seed gives the same sections and chart. Replays may pick another arrangement of the same family by a per-run seed (`RunProgress` stores it; `RW_RUN_SEED` overrides).
- **Chapter playback**: `arrange.py render` pre-renders a whole-chapter arrangement (56 to 128 bars) to a mission-format pack (`songs/story_<chapter>_<n>/` with three stems and a chart,
  like `story_n1_warehouse`) by concatenating section loops with crossfades at boundaries, peak-limited, with the chart's cues from the sections' MIDI; `content/story/<chapter>.json`
  names which to play (several per chapter, seeded choice at start, Night One's existing recording kept as arrangement 0). No runtime mixing beyond `StemTransport`.
- **Audition previews**: `arrange.py audition` writes `docs/audition/<arrangement>.wav` (16-bit, 48 kHz, 30 to 60 s) for every arrangement, plus a `docs/audition/README.md` index. Not
  committed if over 30 MB total: then written to `audition/` in `.gitignore` and the README says how to regenerate.
- Recording checks on the run (a section switch inside a phase keeps one voice group per section, no restart, delay within one mix chunk) and on a chapter pack.

### M4 Populate (Sonnet, same worktree as M3 after it lands; owns `content/story/music.json`, `content/story/<chapter>.json` music fields, `docs/MUSIC_HANDOFF.md`, `docs/MUSIC_REPORT.md`)
- Every run scene gets an arrangement from its world's family (entry scenes: the base identity; later scenes: variations; exit scenes: an ending or drop), the Underworld from the
  Cold family (dark, the nearest match the catalogue offers until Lv3 Hell has MIDI), the Bassment ambient and fight sets from DD Part1/Part2 plus Meta where it fits, the chapters two
  arrangements each. Night One's recording untouched. No stand-in treatments where a real family exists.
- `docs/MUSIC_REPORT.md`: which music plays where and why (family, catalogue evidence), before/after metrics (playable variations per scene, source files used of files available,
  asset size on disk), limitations, and the import instructions for future folders (one command: catalogue, import, arrange, assign, validate).

### M5 Verification (inside M4)
Full suite; `walk_run.sh`, `walk_trial.sh`, `walk_campaign.sh`; `beatshaper.py validate`; the arrangement tests (legality of every chart: same-pad spacing, no overlaps, density per tier,
no gaps over six beats; loop boundaries; peak levels; determinism); recordings; the policy matrices; frame numbers unchanged within 1 ms.

## 4. Order and parallelism
M1 then M2 (one agent, sequential); M3 in parallel with M2 (a second agent, against the catalogue schema fixed in M1's first commit); M4 after M2 and M3; M5 inside M4.

## 5. Risks and calls
- Key estimation is advisory: families from export groupings decide; estimates only flag. Decided.
- The run's phase mix (drums alone, bass reveal) stays the gameplay; arrangements vary *which* loops and *how* they are mixed under it, never the cue families per block. Decided.
- Chapters get pre-rendered packs, not runtime arrangements (the brief allows it; `StemTransport` stays). Decided.
- `mido` is not installed and will not be: the built-in reader replaces it where needed; the three old content tests that import mido are rewritten to use it.

## 6. File ownership (no overlap with the visual plan)
Music owns: `tools/content/*`, `content/music/*`, `content/library/*`, `songs/*`, `content/story/music.json`, the `music` fields of `content/story/<chapter>.json` and `content/trial/passages.json`,
`src/run/run_audio.gd`, `src/audio/*`, `src/run/run_data.gd` music validation only, `docs/MUSIC_*.md`, `docs/audition/`. Visual owns everything else under `src/run`, `src/trial`, `src/story`,
`content/run`, `content/trial` (except `music`), `content/story/maps`, `assets/`, `tools/run`, `tools/trial`, `tools/story`.
