# Mission 9: Iron Rhythm

- Mission length: 64 bars at 174 BPM, 4/4, key C# minor (960 PPQ, bar 1 = tick 0).
- Default content: groove groove_twostep, with the fill fill_break replacing bar 8; bass line bass_octaves; backing acc_iron (8 bars).

## Files

| File | Bars | What it is |
|---|---|---|
| Kick_A.mid | 8 | The default groove (groove_twostep) tiled to 8 bars, with the fill fill_break replacing bar 8; kick notes only (any pitch 48 kick of the push groove is kept) (17 notes). |
| Snare_A.mid | 8 | The same groove and fill, snare notes only (25 notes). |
| Bass_A.mid | 8 | The mission's default bass line, bass_octaves, tiled over 8 bars (it is already 8 bars) (24 notes). |
| Other_Pad.mid | 8 | The backing's chords (everything except pitches 42 and 46) from acc_iron (26 notes). |
| Other_Hats.mid | 8 | The backing's hi-hats (pitches 42 closed and 46 open) from acc_iron (64 notes). |
| Kick_B.mid, Kick_C.mid | 8 | Alternatives of Kick_A: one hit added, moved or dropped every two bars. |
| Snare_B.mid, Snare_C.mid | 8 | Alternatives of Snare_A: a ghost added, a backbeat moved to beat 3 and, or a hit added on beat 4. |
| Bass_B.mid, Bass_C.mid | 8 | Alternatives of Bass_A: a note moved to the fifth or the octave, a long note split or two notes tied; always C# natural minor. |
| Arrangement_A.mid | 64 | Reference only, do not render: four tracks (Kick, Snare, Bass, Other) laying out the whole mission phase by phase with the default choices, exactly as it plays.  |

## What the alternatives change

Each alternative differs from its A in at least one note per two bars and in at most a quarter of A's notes (a sparse part may reach one edit per two bars), keeps every note inside the 8 bars and keeps the same-pad gap (no two notes of one part closer than 480 ticks, none overlapping). B and C are made from the mission's seed, so they are the same every time the exporter runs.

Kick_B:
- bars 1-2: moved the kick at bar 2 beat 3-and to bar 2 beat 3
- bars 3-4: moved the kick at bar 3 beat 3-and to bar 3 beat 4
- bars 5-6: moved the kick at bar 5 beat 3-and to bar 5 beat 3-e
- bars 7-8: added a pickup on the and of beat 4: kick at bar 7 beat 4-and

Kick_C:
- bars 1-2: added a pickup on the and of beat 4: kick at bar 2 beat 4-and
- bars 3-4: moved the kick at bar 3 beat 3-and to bar 3 beat 3-a
- bars 5-6: moved the kick at bar 5 beat 3-and to bar 5 beat 3
- bars 7-8: added an extra eighth before beat 3: kick at bar 7 beat 2-and

Snare_B:
- bars 1-2: moved the backbeat at bar 2 beat 4 to bar 2 beat 3-and
- bars 3-4: moved the backbeat at bar 3 beat 2 to bar 3 beat 3-and
- bars 5-6: added a ghost (velocity 46) at bar 5 beat 1-and, an eighth before the backbeat at bar 5 beat 2
- bars 7-8: added a ghost (velocity 46) at bar 7 beat 3-and, an eighth before the backbeat at bar 7 beat 4

Snare_C:
- bars 1-2: added a ghost (velocity 46) at bar 2 beat 3-and, an eighth before the backbeat at bar 2 beat 4
- bars 3-4: added a ghost (velocity 46) at bar 3 beat 3-and, an eighth before the backbeat at bar 3 beat 4
- bars 5-6: moved the backbeat at bar 5 beat 2 to bar 5 beat 3-and
- bars 7-8: added a ghost (velocity 46) at bar 8 beat 1-and, an eighth before the backbeat at bar 8 beat 2

Bass_B:
- bars 1-2: moved C#1 at bar 1 beat 1 to the fifth (G#1)
- bars 3-4: moved A0 at bar 3 beat 3 to the fifth (E1)
- bars 5-6: moved E2 at bar 5 beat 4-and to the fifth (B1)
- bars 7-8: moved B0 at bar 7 beat 1 to the fifth (F#1)

Bass_C:
- bars 1-2: split C#1 at bar 2 beat 1 into two notes
- bars 3-4: moved A1 at bar 3 beat 4-and to the octave (A0)
- bars 5-6: moved E2 at bar 5 beat 4-and to the octave (E1)
- bars 7-8: split B0 at bar 8 beat 1 into two notes

## Render rules (Ableton)

- Import each MIDI file into a clip at 174 BPM, 4/4, with the project start as bar 1 (no pre-roll).
- Render each part to a WAV: 48 kHz, stereo, 16-bit, starting at bar 1, 8 bars plus at most one bar of tail (the importer keeps the 8 bars and any tail that still sounds, up to one bar, and never stretches).
- Name the WAV after its MIDI file: Kick_A.mid -> Kick_A.wav, Snare_B.mid -> Snare_B.wav, Other_Pad.mid -> Other_Pad.wav, and so on. Put the WAVs in this folder (they are ignored by git).
- A second recording of the same part with another instrument is Kick_A2.wav: add it to `content/imports/level_09.json` as a sound (`{"id": "m09_kick_a2", "family": "kick", "name": "..."}`) and as a second entry in that clip's `renders` (`"m09_kick_a2": "Kick_A2.wav"`).
- Every WAV the manifest names must exist. If you skip a part, delete its sounds and clip from the manifest first.

## Then run

```
python tools/content/import_ableton.py content/imports/level_09.json --check
python tools/content/import_ableton.py content/imports/level_09.json
python tools/content/build.py level_09
```

The import makes the clips m09_groove_a/b/c, m09_bass_a/b/c and m09_backing in content/library/. The mission is then rewired to the imported clips in a follow-up, as mission 1 was; until then level_09 plays the placeholder library clips as before.
