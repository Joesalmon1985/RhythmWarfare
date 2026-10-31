# Content: the loop library and the missions

Everything the ten missions play is built from this folder by one command:

```
python tools/content/build.py            # all missions (about a minute); --check validates without writing audio
```

- `sounds.json`: every sound a mission can offer (id, family kick / snare / bass / other, friendly name).
- `library/<clip_id>/`: one musical clip at 174 BPM in 4/4. `clip.json` says its kind (`groove`, `fill`, `bass`,
  `accompaniment`), friendly name, length in bars, key (pitched clips) and where its MIDI came from. One MIDI file per
  part (`kick.mid`, `snare.mid`, `bass.mid`, `other.mid`) and one WAV per part and sound:
  - `library/<clip_id>/<part>__<sound_id>.wav`: **your render** (drop-in; the build only reads it),
  - `library/<clip_id>/placeholder/<part>__<sound_id>.wav`: the generated placeholder (open it in Ableton to hear what the
    file should contain; the build rewrites it, never your files).
- `missions/level_NN.json`: one mission: its choices, phases (which clip and sound plays where, which family is cued),
  sequences and rewards, accompaniment and battle data.
- `build_state.json`: written by the build (which MIDI each of your WAVs was rendered from). Commit it with your WAVs.
- `REPORT.md`: written by the build: what is still placeholder, warnings, listening checkpoints.

The exact list of files to render, with bar ranges and export settings, is `docs/CONTENT_TO_RENDER.md`. The rules the
build enforces are `docs/PRD.md` section 15. Godot ignores this folder (`.gdignore`); the game plays the Ogg stems the
build writes into `songs/`.
