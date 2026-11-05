# Track packs: a whole recorded track, played one instrument at a time on four pads

Experimental (pilot branch `feature/ai-mp3-import-pilot`). This is the contract between the audio tools
(`tools/audio_import/`) and the game's track mode (`src/track/`). Either side may be rebuilt without the other
as long as this file holds.

Version 2. Version 1 gave each of four instruments its own pad; the owner tried it and asked for this instead:
the game finds the most prominent instrument and gives all four pads to it.

## What a track pack is

One finished recording (an MP3 or FLAC from outside the game), separated into stems, with a chart worked out
from the audio. The track plays from start to finish. The separated instruments are **voices**. At any moment
one voice is the **focus**: the instrument that is most prominent in that stretch of the music. All four pads
belong to the focus voice, and the chart asks the player to play that instrument's part across them. The
focus moves from voice to voice as the music changes. The other voices simply play. If the player misses, the
voice they are playing goes silent until they hit it again. Whatever the separation left over is **backing**
and always plays.

This is separate from the continuous run (8-bar loop packs at 174 BPM) and from missions. Nothing here changes
them.

## Where packs live

Outside the repository, because the audio is other people's music and must not be committed:

    /home/joe/rw-audio-work/packs/<id>/
        track.json
        stems/<key>.ogg          one per voice and per backing stem
        preview/                 optional listening files (never read by the game)

The game is given the pack folder as an absolute path (`RW_TRACK=/abs/path/to/<id>`). Nothing under
`rw-audio-work` is ever added to Git. Only tools, game code, tests, docs and tiny synthetic test fixtures are
committed.

## track.json

All times are **seconds from the start of the audio files** (floats). Tempo is informational: the game does
not need it to place a cue.

```json
{
  "format": "rhythm_warfare.track.v2",
  "id": "acuna_go_back",
  "title": "Go Back",
  "artist": "Acuna",
  "duration_s": 298.559,
  "tempo": {
    "bpm": 174.0032,
    "first_downbeat_s": 0.0013,
    "beats_per_bar": 4,
    "confidence": 0.78
  },
  "voices": [
    {"key": "drums",  "label": "Drums",  "kind": "drums",   "stem": "stems/drums.ogg",  "gain": 1.0},
    {"key": "bass",   "label": "Bass",   "kind": "pitched", "stem": "stems/bass.ogg",   "gain": 1.0},
    {"key": "other",  "label": "Synths", "kind": "pitched", "stem": "stems/other.ogg",  "gain": 1.0},
    {"key": "vocals", "label": "Vocals", "kind": "pitched", "stem": "stems/vocals.ogg", "gain": 1.0}
  ],
  "backing": [
    {"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}
  ],
  "sections": [
    {"id": "intro1", "role": "intro", "start_s": 0.0, "end_s": 66.21}
  ],
  "focus": [
    {"start_s": 0.0,   "end_s": 66.21,  "voice": "other", "lanes": ["Low", "", "", "High"]},
    {"start_s": 66.21, "end_s": 110.34, "voice": "drums", "lanes": ["Kick", "Hat", "Perc", "Snare"]},
    {"start_s": 110.34, "end_s": 132.41, "voice": "bass", "lanes": ["Low", "", "", "High"]}
  ],
  "charts": {
    "normal": [
      {"t": 66.552, "pad": 1, "dur": 0.0,  "conf": 0.91, "voice": "drums"},
      {"t": 110.69, "pad": 2, "dur": 0.69, "conf": 0.74, "voice": "bass"}
    ]
  },
  "default_chart": "normal",
  "rules": {"restore_after_idle_beats": 8},
  "source": {}
}
```

### Rules the file must obey (both sides check them)

Header
- `format` is exactly `rhythm_warfare.track.v2`. `id` equals the folder name: lower case letters, digits and
  underscores.
- `duration_s` > 0 and equals the real decoded length of the stems to within 5 ms (write it from the encoded
  files, not from the source recording).

Voices and stems
- `voices` has one to six entries. `key` is unique across voices and backing: lower case letters, digits,
  underscores. `label` is a short name shown to the player. `kind` is `drums` or `pitched` and says how the
  voice's part is laid across the pads (see Charts). A voice has no pad of its own.
- `backing` has zero or more entries. A backing stem is never muted.
- Every `stem` is a relative path inside the pack (no `..`, no leading `/`), an Ogg Vorbis file, 48 kHz, stereo.
  All stems have the same length to within 5 ms and start at the same instant: sample 0 of every file is the
  same moment of the recording.
- Played together at their `gain`s, the stems are the whole track. Nothing of the recording is left out and
  nothing is in two stems. Because the stems are lossy files this holds approximately: their sum must match
  the recording to -30 dB or better (the tools reach about -38 dB with Vorbis quality 10).
- A separated stem can be louder than full scale on its own even though the sum is not, so the tools store
  every stem scaled down by one common factor and write the inverse as `gain`. The game sums the stems before
  any clipping and puts a limiter on its music bus, since the summed track can still peak a little above full
  scale where the original master does.
- `gain` is linear, 0 to 2, default 1.

Tempo and sections (information for tools and HUD; the game must work if `sections` is empty)
- `tempo.bpm` > 0 (a float; it is whatever the recording is, never forced to 174), `first_downbeat_s` >= 0,
  `beats_per_bar` 4, `confidence` 0 to 1.
- `sections` are in time order, do not overlap, lie inside the track. `role` is one of `intro`, `build`,
  `drop`, `breakdown`, `outro`, `other`.

Focus
- `focus` is a list of stretches `{start_s, end_s, voice, lanes}` in time order that do not overlap and lie
  inside the track. `voice` is the key of one of `voices`. There may be gaps between stretches (nothing to
  play there) and the same voice may have many stretches. At least one stretch exists.
- A stretch is at least 8 beats long. The tools make them much longer (whole phrases) and start and end them
  on bar lines.
- `lanes` is four short names, one per pad from pad 1 to pad 4, saying what each pad is in this stretch, for
  the player's display; a name may be empty. It is optional.
- The focus is the same for every chart of the pack.

Charts
- `charts` has at least the chart named by `default_chart`. Chart names are free; the tools write `easy`,
  `normal` and `hard` where they can.
- A cue is `{t, pad, dur, conf, voice}`: `t` the moment to press, `pad` 1 to 4, `dur` 0 for a tap or the
  length of a hold in seconds, `conf` 0 to 1 (how sure the analysis is; the game ignores it), `voice` the key
  of the voice this cue plays.
- Every cue lies inside a focus stretch, `voice` is that stretch's voice, and a hold ends inside the same
  stretch. There are no cues outside the focus stretches.
- Cues are sorted by `t`. Every cue lies inside the track: `t >= 1.0` (nothing in the first second) and
  `t + dur <= duration_s - 0.5`.
- A cue means its voice audibly plays something at `t`. The tools must not place cues where the voice is
  silent. `t` is the audible attack where there is one; for a legato part with no attack (a bass line sliding
  to a new note) it is the nearest 16th-note grid line to the pitch change.
- How a voice's part is laid across the pads (the tools' job; the game only reads `pad`):
  - `drums`: the kick on pad 1, the snare on pad 4, hats and other percussion on pads 2 and 3;
  - `pitched`: lower notes to the left, higher to the right, so the pads follow the shape of the line. The
    same note in the same stretch is always the same pad, and a phrase that repeats gets the same pads again.
- Pads 1 and 2 are the left thumb, pads 3 and 4 the right (keys D F J K on a keyboard).
- Playability, with B = one beat = 60 / `tempo.bpm` seconds:
  - same pad: two cues at least 0.5 B apart, and a cue never starts inside a hold on its own pad or sooner
    than 0.25 B after that hold ends;
  - same thumb, different pad (1 and 2, or 3 and 4): at least 0.5 B apart, and never while the other pad of
    that thumb is held;
  - at most two pads at once (so at most one per thumb);
  - a hold is at least 0.5 B long.

`rules.restore_after_idle_beats` (default 8): see "What the game does".

`source` is free-form: what the tools record about how the pack was made (input file name, model, per-voice
separation notes, why each focus stretch was chosen, tool version). The game ignores it.

## What the game does with it (track mode)

- Loads the pack from `RW_TRACK`, refuses it with a clear message if a rule above is broken, and plays all
  stems as one synchronised stream so they cannot drift.
- Shows the four pads and the cues of the chosen chart (`RW_TRACK_CHART`, default `default_chart`) arriving in
  time, using the game's existing pad view, input and timing (latency and calibration as everywhere else).
- Shows which voice the player is playing now (the focus stretch's voice and its `lanes` on the pads), and
  announces a change of focus before it happens: from 8 beats ahead it shows the next voice's name and counts
  the beats down. Between stretches it shows that there is nothing to play.
- All voices start audible. A missed cue (the moment the press window closes, 0.14 s after the cue), or a
  hold let go early, mutes the cue's voice (the stem keeps running silently). The next cue hit for that voice
  brings it back. Backing never mutes. The other voices are not affected.
- A muted voice also comes back by itself: if, at the moment it is muted, its next cue is more than
  `restore_after_idle_beats` beats away (or it has no more cues), it returns that many beats after it was
  muted. It never returns by itself before a cue the player could still hit, and a second miss while muted
  restarts the wait. So a miss just before the focus moves on costs a few beats of silence, not the rest of
  the track.
- A hold counts as kept if it is released within 0.15 s of its end; released earlier, the voice mutes. A hold
  that was started and then let go is counted as a hit plus a "let go", not as a miss; a hold never started
  is a miss.
- Pressing a pad when no cue is near costs nothing.
- There is no failing and no battle: the track always plays to the end. At the end the game reports hits and
  misses per voice and how much of the time each voice was sounding.
- `RW_AUTOPLAY=perfect|accuracy:<0..1>|none` plays by itself; `RW_TRACK_START=<seconds>` starts part-way in.

## Checking a pack

    python3 tools/audio_import/validate_track.py /home/joe/rw-audio-work/packs/<id>

checks every rule in this file, including stem format and alignment, and prints per-voice cue counts and
densities and the focus timeline. The game's loader repeats the checks it can make without decoding analysis
data.
