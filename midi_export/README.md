# MIDI for missions 2 to 10

Mission 1 was rebuilt on your own Ableton recordings. Missions 2 to 10 still play placeholder clips from the loop library.
This folder gives you MIDI to record the same way: one sub-folder per mission, `level_NN_<title>/`.

## What is in a mission folder

Each folder has a README with the details, plus:

- 8-bar loops at 174 BPM, 4/4: `Kick_A`, `Snare_A` (the mission's default groove, with its fill in bar 8), `Bass_A` (its default
  bass line; missions 2, 4, 6 and 8 have no bass phase, so theirs is a new root-note line) and `Other_Pad` / `Other_Hats`
  (the backing, split into chords and hi-hats; missions 2 and 3 keep their 40 and 48 bars).
- Alternatives `Kick_B`, `Kick_C`, `Snare_B`, `Snare_C`, `Bass_B`, `Bass_C`: small rule-based variations of A (a pickup, a
  ghost, a note moved to the fifth). They are generated from the mission's seed, so re-running the exporter never changes them.
- `Arrangement_A.mid`: a four-track reference of the whole mission with the default choices. Listen to it, do not render it.

## How to use them

1. Load a loop into Ableton, play it with your instrument and render a WAV: 48 kHz stereo 16-bit, from bar 1 with no
   pre-roll, 8 bars plus at most one bar of tail. Name it after the MIDI file (`Kick_A.mid` gives `Kick_A.wav`) and keep it in the
   same folder. A second recording of one part is `Kick_A2.wav`; add it to the mission's manifest.
2. The manifest `content/imports/level_NN.json` already lists every file and sound id. Check it, then import:
   `python tools/content/import_ableton.py content/imports/level_NN.json --check`, then the same without `--check`, then
   `python tools/content/build.py level_NN`. The importer converts, trims, gain-stages and writes the clips into content/library/.
3. Every WAV a manifest names must exist, so delete the parts you do not record from the manifest first.

The `.wav` files are not committed (`midi_export/**/*.wav` is ignored); the MIDI and READMEs are.

## What happens next

Importing only adds clips to the library. The missions are rewired to the imported clips in a follow-up per mission, as mission 1
was: the choices, phases and sounds of `content/missions/level_NN.json` then point at the new clips and the placeholder ones
step aside. To regenerate this folder: `python tools/content/export_midi.py` (the same bytes every time).
