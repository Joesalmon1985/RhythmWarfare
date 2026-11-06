# Audio import: finished recordings to track packs

Turns finished recordings (FLAC, MP3, WAV: anything ffmpeg reads)
into track packs as defined in `docs/TRACK_PACK_FORMAT.md` (version 2): the recording separated into voices
(drums, bass, other, vocals) and a backing stem, a **focus** timeline saying which voice is the player's at each
moment (the most prominent one, decided automatically), and `easy` / `normal` / `hard` charts that lay the focus
voice's part across all four pads by height. There is no MIDI and no AI in the loop: everything is measured
from the recording by one repeatable command. Nothing is time-stretched and no tempo is forced.

## Install (once per machine)

CPU only, in its own venv (never the system Python):

    python3 -m venv /home/joe/.venvs/rw-audio
    printf 'torch==2.15.0+cpu\ntorchaudio==2.11.1+cpu\n' > /home/joe/rw-audio-work/constraints.txt
    /home/joe/.venvs/rw-audio/bin/pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu torch==2.15.0+cpu torchaudio==2.11.1+cpu
    /home/joe/.venvs/rw-audio/bin/pip install --no-cache-dir -c /home/joe/rw-audio-work/constraints.txt \
        demucs librosa soundfile

Also needed: `/usr/bin/ffmpeg` and `/usr/bin/ffprobe` (with libvorbis and soxr; Ubuntu's build has both).
The first separation downloads the Demucs weights to `~/.cache/huggingface/hub` (the tool then runs with
`HF_HUB_OFFLINE=1`). Versions used: Python 3.12.3, torch 2.15.0+cpu, torchaudio 2.11.1+cpu, demucs 4.1.0,
librosa 1.0.0, numpy 2.5.4, scipy 1.18.1, soundfile 0.14.0. Version 2 added no package.

## Use

One track:

    cd /home/joe/Projects/MusicGame
    OMP_NUM_THREADS=3 nice -n 10 /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py \
        "/path/to/Artist - Title.flac" [--id artist_title] [--out /home/joe/rw-audio-work] \
        [--model htdemucs|htdemucs_ft|htdemucs_6s] [--from STAGE | --only STAGE] \
        [--min-bars 8] [--focus VOICE] [--focus-at WHERE=VOICE ...] [--focus-auto]
        [--skip-imported] [--prune-cache]
    ... import_track.py --rechart [ID ...]       # re-chart existing packs, see below

A batch: give several files and/or folders (every audio file directly inside a folder is taken, in name order):

    OMP_NUM_THREADS=3 nice -n 10 /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py \
        /home/joe/Projects/MusicGame/ToAddTry5/ "/elsewhere/One More.mp3"

Tracks are processed one after another (about 13 minutes each, 7 of them Demucs). A file that fails is reported
and the batch goes on. The run ends with one line per track, also written to
`/home/joe/rw-audio-work/batch_summary.txt` (and a time-stamped copy next to it):

    acuna_go_back | 174.00 BPM constant (drift 8 ms, conf 0.78) | sep other:clean bass:clean drums:clean vocals:clean
      | focus other 0-24, drums 24-32, vocals 32-48, ... | cues easy:... normal:... hard:... | ok

The id defaults to `artist_title` from the tags or the file name (`--id` only with one input). Every stage
caches its result; a rerun skips what is done, and once a stage runs every later stage runs too. `--from chart`
reruns the chart and everything after it; `--only preview` reruns one stage.

### Play an imported track

    tools/audio_import/play_track.sh <id>                 # the pack's default chart (normal)
    tools/audio_import/play_track.sh <id> easy 70         # another chart, starting 70 s in
    RW_AUTOPLAY=accuracy:0.7 tools/audio_import/play_track.sh <id>    # watch it play itself

Keys D F J K. The game's side of this is track mode, `src/track/README.md`. The first time after pulling new
code, run Godot's import once (`$GODOT --headless --path . --import`) so the new scripts are registered.

### A whole folder overnight

    OMP_NUM_THREADS=4 nice -n 10 /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py \
        /home/joe/Projects/MusicGame/ToAddTry4/ --skip-imported --prune-cache

`--skip-imported` leaves alone any recording whose pack already exists and validated, so the same command can
be run again after an interruption and carries on where it stopped. `--prune-cache` deletes a recording's
cached separated audio (about 1 GB each) once its pack is written and validated; without it 60 recordings need
60 GB of cache. What stays in `cache/<id>/` is small: the JSON of every stage and `stem_src/`, the encoded
voices and backing as separated (hard links to the pack's own stems, so it costs disk only for a voice folded
into the backing). That is enough to re-chart the track without separating it again.

Files that would get the same id (same artist and title tags, two masters of one tune) never overwrite each
other: the second gets `_2` (then `_3`), the summary line says so, and the same file keeps the same id on later
runs (`cache/<id>/source.txt` records which file an id belongs to). A file with no tags gets its id from the
file name (`Artist - Title.ext`, a leading track number dropped).

### Re-chart after a rule change (no Demucs, no recordings needed)

    OMP_NUM_THREADS=3 nice -n 10 /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py --rechart
    ... import_track.py --rechart acuna_go_back ac13_shostakovich      # only these packs

reruns focus, chart, pack, preview and validate for every pack under `<out>/packs` (or the ids given) from the
cached analysis and events and the encoded stems, and prints the usual summary. `--from focus` (or `--from
chart`) on a pruned recording works the same way. Earlier stages (analyse, voices, events) need the separated
audio: a rule change there means importing the recordings again.

### What the end of a batch says

Every line ends with the time the track took and one verdict:
- `ok`: imported, valid, nothing to check.
- `ok with warnings`: imported and valid (the game will load it); something is worth a listen (see the
  warnings on the line). Warnings never change the exit code.
- `FAILED`: not imported (an error; the traceback is above the summary) or the pack breaks the format
  (validator violations; see `packs/<id>/report.txt`).
The first line counts each verdict. The exit code is 0 when every track is `ok` or `ok with warnings`, 1 when a
pack has validator violations, 2 when a track failed with an error.

### The catalogue (metadata in the repository)

    /home/joe/.venvs/rw-audio/bin/python tools/audio_import/catalogue_tracks.py /home/joe/Projects/MusicGame/ToAddTry4

writes `content/music/tracks/catalogue.json` (every recording: tags, length, and a quick look at tempo,
loudness, bass weight, brightness, busyness and a rough loud/quiet map), one `content/music/tracks/<id>.json`
per imported recording (measured tempo, bar-accurate sections, which instrument is played when, cue counts)
and `docs/MUSIC_TRACKS.md` (the same as tables). Metadata only, never audio: this is what is committed, so
that work on the game can choose and place tracks without having the recordings. It takes about three seconds
per recording and is cached; run it again after importing more and commit the result.

### The summary line and its warnings

- `NNN.NN BPM constant|NOT constant (drift over N of M 8-bar windows, conf)`: the tempo, the largest drift of
  8-bar windows from one constant grid (judged only on windows with at least 24 drum onsets, after a running
  median of three windows, and never carried across a drumless gap: so sparse drums do not raise a false alarm),
  and the grid confidence. **WARNING tempo not constant**: the track speeds up or slows down
  (or the drums are too sparse to tell); cues come from detected beats and need an ear.
  **WARNING tempo confidence**: the grid or the downbeat is uncertain.
- `sep drums:clean bass:fair ...`: separation per voice in a word (clean / fair / poor, from attack bleed and
  envelope correlation between stems). **WARNING X separated badly**: its stem carries another instrument; its
  cues have low confidence and muting it on a miss may take part of something else with it.
- `focus voice a-b, ...`: who has the focus, in bars from the first bar line (8 bars is about 11 s at 174 BPM;
  `(none)` = nothing to play). **WARNING N bars with nothing to play**: a gap of 16 bars or more with no voice
  loud enough with a playable part (an ambient intro, a long breakdown on a held pad): check it is really empty.
  **WARNING X has the focus 80% of the playable time**: little variety; maybe force a section to another voice.
- `nothing to play N/M bars (P%) from bar 16 to the last 8`: the part of the track that matters for a scene
  (from a phrase in to the last bars) with no focus. Under 10% is the aim; more means a quiet or empty stretch.
- `cues easy:N normal:N hard:N`.
- **WARNING validator: N violation(s)**: the pack breaks the format; the game will refuse it. See report.txt.
- **ERROR**: the track failed (the traceback is printed above the summary); the batch went on.

### Overriding the focus

The focus is automatic. When a result is not liked, rerun that one track with an override; it reruns from the
focus stage (seconds plus the previews and checks, about 3 minutes; the separation is cached):

    import_track.py "<file>" --focus-at drop1=bass               # a section id (see report.txt) to one voice
    import_track.py "<file>" --focus-at 77.2-132.4=drums          # a time range in seconds
    import_track.py "<file>" --focus-at breakdown1=none          # nothing to play there
    import_track.py "<file>" --focus drums                       # one voice wherever it plays, all track
    import_track.py "<file>" --min-bars 16                       # longer stretches, fewer changes
    import_track.py "<file>" --focus-auto                        # forget the overrides, automatic again

`--focus-at` can be repeated; a forced phrase is given to the voice only if that voice has at least 4 playable
events there (else nothing to play). Overrides are remembered per track in
`cache/<id>/focus_options.json`, so a later batch over the same folder keeps them until `--focus-auto`.
`report.txt` and `source.focus_detail` in track.json say for every stretch why it went to its voice ("most
prominent", "handed over from drums (2.3 dB behind)", "only voice with a part", "forced on the command line").

Check a pack (only numpy and ffmpeg needed, so plain `python3` works):

    python3 tools/audio_import/validate_track.py /home/joe/rw-audio-work/packs/<id>

Unit tests (synthetic audio made in the test; no recordings, no Demucs; about 40 s):

    /home/joe/.venvs/rw-audio/bin/python -m unittest discover -s tools/audio_import -p 'test_*.py' -v

## Stages and caches

All under `--out` (default `/home/joe/rw-audio-work`), never in a repository. Times for 5 minutes of audio on
the 4-core laptop, 3 threads.

| stage | what | output | time |
|---|---|---|---|
| separate | Demucs on the whole file through its Python API; raw float output, the mix mean restored once, no clamping, so the stems sum to the recording | `cache/<id>/sep_<model>/{mix,drums,bass,other,vocals}.npy` + `meta.json` | 430 s |
| analyse | drum onsets; tempo by a comb over 60-200 BPM, read in 110-200; a weighted least-squares constant grid; drift from local fits; downbeat; sections by novelty on per-bar stem levels, snapped to 8-bar phrases, roles from rhythm-stem intensity; the separation report | `analysis.json` | 65 s |
| voices | the voices and the backing (recording minus voices) | `voices.json`, `voices/<key>.npy` | 1 s |
| events | per voice: what it plays (onsets, bass notes by pitch, note changes, lengths), how high each event is, and its loudness as heard per bar | `events.json` | 170 s |
| focus | the focus timeline (below) | `focus.json` | < 1 s |
| chart | pads by height and the three charts (below) | `charts.json` | 3 s |
| pack | stems (only re-encoded when the voices changed), track.json | `packs/<id>/track.json`, `stems/*.ogg` | 70 s (2 s when the stems are kept) |
| preview | listening files | `packs/<id>/preview/*.ogg` | 60 s |
| validate | `validate_track.py`, then the evidence report | `packs/<id>/report.{txt,json}` | 70 s |

## How the focus is decided (focus.py)

- Loudness as heard: each voice weighted by half the A-weighting curve in dB, roughly the ear at loud listening
  levels (ISO 226 near 80 phon: -15 dB at 50 Hz, -10 dB at 100 Hz), so a sub-bass does not win by power alone.
  Per 8-bar phrase (cut from each section's first bar) each voice gets its share of the voices' weighted power.
- Prominence = 10 log10(share) + up to 3 dB for activity (playable events per beat) + up to 2 dB for movement
  (consecutive events changing pitch or drum sound) + 2 dB if the voice has just come in. A voice is eligible
  only with a share of at least 10% and at least half a playable event per bar, sounding in half the bars.
- Stretches by dynamic programming: cost = how far below the phrase's leader the chosen voice is; a change of
  voice costs 1 dB (hysteresis); a stretch is at least `--min-bars` long (8); a phrase with an eligible voice
  left empty costs 12 dB; and every further phrase a voice keeps while another is within 6 dB costs 8 dB, so
  two close voices hand the focus over phrase by phrase and a clear leader keeps it.
- Always something to play: a phrase where no voice is eligible is judged again with relaxed rules (a voice
  with at least 20% of the perceived power and no more than 30 dB under the loudest phrase of the recording,
  counting every event audible by level and strong for that phrase). The chart uses the same relaxed test
  there (report: "relaxed rules"). Only phrases with no such voice are gaps.
- A voice whose stem separated badly (sep_quality under 0.85) loses up to 4 dB of prominence.
- A stretch longer than 24 bars costs 12 dB a phrase while another voice is eligible, so one voice does not
  hold a whole drop; in a breakdown a drums voice loses 6 dB when a pitched voice is eligible.
- A voice that never gets the focus and has no cue is not written as a voice: it goes into the backing
  (`source.folded_into_backing` in track.json), e.g. the `kick` half of a split drum stem.

## How the part is laid on the pads (layout.py)

One rule for every voice, no names: lower sounds left, higher right. Per stretch: sounds are semitones (bass by
tracked pitch, other parts by the predominant pitch of a harmonic-summed constant-Q spectrum just after the
attack) or, for drums, clusters of hits by brightness (spectral centroid) and band balance, which separates
kick-, snare- and hat-like hits without naming them. Sounds are split between the thumbs (pads 1-2 left, 3-4
right) so that presses closer than half a beat, presses during a held note, and sounds that go back and forth
(kick and snare in a two-step, a trill) are on different thumbs, against a cost for breaking height order;
within each thumb the height order is kept. A sound alone on its thumb takes the outer pad if it is the lowest
or highest. A part on one note with a rhythm (two or more events a bar) is split by metric position (on / off
the beat, or beats 1 and 3 / 2 and 4) so it still moves between two pads. The same sound in a stretch is always
the same pad; the layout is decided once from the hard selection, so easy, normal and hard agree.

## How cues are chosen (chart.py)

Each event is scored (strength, audibility, metric position, how regularly the part plays that position in the
stretch). Per stretch a budget of cues per beat (drums: hard 1.75, normal 1.0, easy 0.5; pitched parts 1.25,
0.75, 0.4; times 0.75-1.0 by section role) is spent on whole positions of the repeating cycle first (1 bar for
drums, 2 for bass, 4 for melodic and vocal parts), so the same pattern comes back where the music repeats; the
minimum spacing is a 16th on hard (alternating thumbs), an 8th on normal, a beat on easy. Hard is chosen from
all events, normal from hard, easy from normal. Held notes of at least a beat become holds, ending inside the
stretch. The whole chart is then made playable with the validator's own rule function. Cue times are the
detected attack in the voice's stem, or the 16th line when the attack is within 6 ms of it.

Ceilings in cues per beat of focus time, judged on the playable chart (Go Back, the reference, is under all):
per stretch drums 1.45 / 1.0 / 0.5 and pitched parts 1.0 / 0.75 / 0.45 (hard / normal / easy); per chart
0.84 / 0.67 / 0.41. A stretch over its ceiling, or the densest stretches of a chart over its ceiling, are
picked again with a smaller budget (whole positions of the cycle go first, so the pattern still repeats).

A stretch whose cues (4 or more) all land on one pad in a chart is spread over two by position in the bar
(off-beat, else beats 2 and 4, else the second half of the bar, on the other thumb's inner pad), so a repeated
phrase still gets the same pads. This is per chart: easy may then differ from hard there.

Last, every cue is checked with the validator's own audibility test (`validate_track.SoundLevels`, 1.5 dB
stricter for the Vorbis coding): a hold that fails becomes a tap, a tap that fails is removed, and the number
removed is in `cache/<id>/charts.json` (`stats`) and printed. The chart stage never writes a cue the
validator rejects as silent.

## Reading the report (`packs/<id>/report.txt`)

- tempo, sections and separation as before.
- focus: the timeline with, per stretch, the voice's perceived share and the runner-up's, why it got the
  focus, the sounds (height : presses -> pad), and per chart: cues and cues per beat, holds, pads used, the
  share of the voice's strong events (top quarter by strength) that became cues, the rank correlation between
  height and pad, how often the next press is on the other thumb / the same thumb / the same pad, and the
  distance from each cue to the nearest onset found by an independent detector on the encoded stem.
- per chart and voice: counts, attack distances, share on the 16th grid, confidence, event kinds.
- drops compared: the share of the first drop's cues found again in the second at the same offset with the
  same pad and voice (and the other way round), and the focus timelines of both.
- The bass's distance to independent onsets is large by design: its cues are pitch changes in a legato line.

## Listening

`packs/<id>/preview/`:
- `mix_clicks_normal.ogg`: the whole recording with a click on every `normal` cue, pitch rising from pad 1 to
  pad 4 (1000, 1500, 2250, 3375 Hz), a softer click where a hold ends, and three quick bell notes at every
  change of focus (rising into a stretch, falling into a gap).
- `focus_forward_normal.ogg`: the same with every voice that is not the focus (and the backing) 9 dB down, so
  you hear what you would be playing.
- `miss_<voice>.ogg`: 30 s of the loudest drop with its focus voice silent from a cue until its first cue four
  bars later, as missed presses make it in the game; everything else keeps playing.

Play with `ffplay -nodisp -autoexit <file>` or any player.

## What is committed

Only the code in `tools/audio_import/` (and this README). Never audio, stems, previews, caches, reports or
packs: they live under `/home/joe/rw-audio-work/`, which is outside every repository.

## Known limits

- Demucs separates drums, bass, vocals and "everything else". "other" holds pads, stabs and leads together, so
  its pitch is the predominant pitch of a chord, which can jump between the chord's bass note and its top.
- Prominence is measured, not heard: the weighting, bonuses and the 6 dB handover margin were set on one track
  (Go Back). A track whose drops are carried by a mid-range bass will give the bass more focus than this one.
- Drum sounds are clustered per stretch, so the same kit can get a slightly different layout in two stretches
  when a hat is mixed with a kick tail.
- Tempo changes: detected and reported, cues placed from detected beats, not exercised on a real track yet.
- Vorbis q10 makes packs about 80 MB for 5 minutes (lower quality makes the stems sum to the record less
  exactly: q6 -24 dB, q8 -29 dB, q10 -38 dB).
