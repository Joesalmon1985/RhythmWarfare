# Mission 2: Second Pulse

- Mission length: 40 bars at 174 BPM, 4/4, key C# minor (960 PPQ, bar 1 = tick 0).
- Default content: groove groove_push, no fill (this mission's phases use none); bass none in the mission (new root line below); backing acc_second_pulse (40 bars).

## Files

| File | Bars | What it is |
|---|---|---|
| Kick_A.mid | 8 | The default groove (groove_push) tiled to 8 bars, no fill (this mission's phases use none); kick notes only (any pitch 48 kick of the push groove is kept) (12 notes). |
| Snare_A.mid | 8 | The same groove and fill, snare notes only (8 notes). |
| Bass_A.mid | 8 | NEW: this mission has no bass phase, so this is a root-note line, one note per two bars at the root of the backing's chord (taken from bars 1-8 of the backing), in the C#1 register (Ableton names, MIDI pitches 32 to 42). The mission does not play it today (4 notes). |
| Other_Pad.mid | 40 | The backing's chords (everything except pitches 42 and 46) from acc_second_pulse (120 notes). The backing is that long in this mission, so it is not shortened to 8 bars. |
| Other_Hats.mid | 40 | The backing's hi-hats (pitches 42 closed and 46 open) from acc_second_pulse (144 notes). The backing is that long in this mission, so it is not shortened to 8 bars. |
| Kick_B.mid, Kick_C.mid | 8 | Alternatives of Kick_A: one hit added, moved or dropped every two bars. |
| Snare_B.mid, Snare_C.mid | 8 | Alternatives of Snare_A: a ghost added, a backbeat moved to beat 3 and, or a hit added on beat 4. |
| Bass_B.mid, Bass_C.mid | 8 | Alternatives of Bass_A: a note moved to the fifth or the octave, a long note split or two notes tied; always C# natural minor. |
| Arrangement_A.mid | 40 | Reference only, do not render: four tracks (Kick, Snare, Bass, Other) laying out the whole mission phase by phase with the default choices, exactly as it plays. The Bass track is empty: this mission has no bass phase. |

The two Other files keep the backing's full 40 bars (render all of them, plus at most one tail bar; the other parts are 8). The manifest content/imports/level_02.json imports the first 8 bars (its `bars` is 8); to import the whole backing later use a second manifest with `"bars": 40`.

## What the alternatives change

Each alternative differs from its A in at least one note per two bars and in at most a quarter of A's notes (a sparse part may reach one edit per two bars), keeps every note inside the 8 bars and keeps the same-pad gap (no two notes of one part closer than 480 ticks, none overlapping). B and C are made from the mission's seed, so they are the same every time the exporter runs.

Kick_B:
- bars 1-2: added an extra eighth before beat 3: kick at bar 2 beat 2-and
- bars 3-4: added a pickup on the and of beat 4: kick at bar 4 beat 4-and
- bars 5-6: added an extra eighth before beat 3: kick at bar 5 beat 2-and
- bars 7-8: added an extra eighth before beat 3: kick at bar 8 beat 2-and

Kick_C:
- bars 1-2: added an extra eighth before beat 3: kick at bar 1 beat 2-and
- bars 3-4: added a pickup on the and of beat 4: kick at bar 3 beat 4-and
- bars 5-6: added a pickup on the and of beat 4: kick at bar 6 beat 4-and
- bars 7-8: added an extra eighth before beat 3: kick at bar 7 beat 2-and

Snare_B:
- bars 1-2: added a ghost (velocity 46) at bar 2 beat 2-and, an eighth before the backbeat at bar 2 beat 3
- bars 3-4: added a hit on beat 4 of bar 4: snare at bar 4 beat 4
- bars 5-6: moved the backbeat at bar 5 beat 3 to bar 5 beat 3-and
- bars 7-8: added a hit on beat 4 of bar 8: snare at bar 8 beat 4

Snare_C:
- bars 1-2: moved the backbeat at bar 1 beat 3 to bar 1 beat 3-and
- bars 3-4: moved the backbeat at bar 3 beat 3 to bar 3 beat 3-and
- bars 5-6: added a ghost (velocity 46) at bar 5 beat 2-and, an eighth before the backbeat at bar 5 beat 3
- bars 7-8: added a ghost (velocity 46) at bar 7 beat 2-and, an eighth before the backbeat at bar 7 beat 3

Bass_B:
- bars 1-2: moved C#1 at bar 1 beat 1 to the fifth (G#1)
- bars 3-4: moved A0 at bar 3 beat 1 to the fifth (E1)
- bars 5-6: moved E1 at bar 5 beat 1 to the fifth (B1)
- bars 7-8: moved B0 at bar 7 beat 1 to the fifth (F#1)

Bass_C:
- bars 1-2: moved C#1 at bar 1 beat 1 to the octave (C#2)
- bars 3-4: moved A0 at bar 3 beat 1 to the octave (A1)
- bars 5-6: moved E1 at bar 5 beat 1 to the octave (E2)
- bars 7-8: moved B0 at bar 7 beat 1 to the octave (B1)

## Render rules (Ableton)

- Import each MIDI file into a clip at 174 BPM, 4/4, with the project start as bar 1 (no pre-roll).
- Render each part to a WAV: 48 kHz, stereo, 16-bit, starting at bar 1, 8 bars plus at most one bar of tail (the importer keeps the 8 bars and any tail that still sounds, up to one bar, and never stretches).
- Name the WAV after its MIDI file: Kick_A.mid -> Kick_A.wav, Snare_B.mid -> Snare_B.wav, Other_Pad.mid -> Other_Pad.wav, and so on. Put the WAVs in this folder (they are ignored by git).
- A second recording of the same part with another instrument is Kick_A2.wav: add it to `content/imports/level_02.json` as a sound (`{"id": "m02_kick_a2", "family": "kick", "name": "..."}`) and as a second entry in that clip's `renders` (`"m02_kick_a2": "Kick_A2.wav"`).
- Every WAV the manifest names must exist. If you skip a part, delete its sounds and clip from the manifest first.

## Then run

```
python tools/content/import_ableton.py content/imports/level_02.json --check
python tools/content/import_ableton.py content/imports/level_02.json
python tools/content/build.py level_02
```

The import makes the clips m02_groove_a/b/c, m02_bass_a/b/c and m02_backing in content/library/. The mission is then rewired to the imported clips in a follow-up, as mission 1 was; until then level_02 plays the placeholder library clips as before.
