# Audio import: a finished recording to a track pack

Pilot (branch `feature/ai-mp3-import-pilot`). Turns one finished recording (FLAC, MP3, WAV: anything ffmpeg
reads) into a track pack as defined in `docs/TRACK_PACK_FORMAT.md`: four voices the player keeps alive by
pressing their pads, a backing stem that always plays, and `easy` / `normal` / `hard` charts worked out from
the audio. There is no MIDI; everything is measured from the recording. Nothing is time-stretched and no tempo
is forced.

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
`HF_HUB_OFFLINE=1`). Versions used for the pilot: Python 3.12.3, torch 2.15.0+cpu, torchaudio 2.11.1+cpu,
demucs 4.1.0, librosa 1.0.0, numpy 2.5.4, scipy 1.18.1, soundfile 0.14.0. No other package was added.

## Use

    cd /home/joe/Projects/MusicGame-mp3
    OMP_NUM_THREADS=3 nice -n 10 /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py \
        "/path/to/Artist - Title.flac" [--id artist_title] [--out /home/joe/rw-audio-work] \
        [--model htdemucs|htdemucs_ft|htdemucs_6s] [--from STAGE | --only STAGE]

The id defaults to `artist_title` from the tags or the file name. Every stage caches its result; a rerun skips
what is done. `--from chart` reruns the chart and everything after it; `--only preview` reruns one stage.

Check a pack (only numpy and ffmpeg needed, so plain `python3` works):

    python3 tools/audio_import/validate_track.py /home/joe/rw-audio-work/packs/<id>

Unit tests (synthetic audio made in the test; no recordings, no Demucs; about 20 s):

    /home/joe/.venvs/rw-audio/bin/python -m unittest discover -s tools/audio_import -p 'test_*.py' -v

## Stages and caches

All under `--out` (default `/home/joe/rw-audio-work`), never in a repository.

| stage | what | output | time for 5 min of audio on the 4-core laptop, 3 threads |
|---|---|---|---|
| separate | Demucs on the whole file through its Python API; raw float output, the mix mean restored once (not once per stem), no clamping, so the stems sum to the recording (Demucs's own CLI clamps or rescales each stem, which breaks that) | `cache/<id>/sep_<model>/{mix,drums,bass,other,vocals}.npy` + `meta.json` | 430 s (htdemucs) |
| analyse | drum onsets; tempo by a comb over 60-200 BPM, read in the 110-200 range; a weighted least-squares constant grid over every drum onset in the track; drift from local per-window fits; downbeat from phrase-change energy jumps and kick-vs-snare per beat phase; sections by novelty on per-bar stem levels, snapped to 8-bar phrases, roles from rhythm-stem intensity; the separation report | `cache/<id>/analysis.json` | 65 s |
| voices | four voices and the backing (see below) | `cache/<id>/voices.json`, `voices/<key>.npy`, `voices/backing.npy` | 60 s |
| chart | events per voice, ranking, pad choice, nested charts | `cache/<id>/charts.json` (cues with voice, score, event kind, every detected event) | 65 s |
| pack | one common gain if any stem would clip (its inverse is every stem's `gain`), soxr to 48 kHz, Vorbis q10; `duration_s` measured from the decoded Oggs | `packs/<id>/track.json`, `packs/<id>/stems/*.ogg` | 70 s |
| preview | listening files | `packs/<id>/preview/*.ogg` | 40 s |
| validate | `validate_track.py` on the pack, then the evidence report | `packs/<id>/report.{txt,json}` | 60 s |

So about 13 minutes per track, 7 of them Demucs. `htdemucs_ft` would make the separation about 4x slower.

## How voices, pads and cues are chosen

Voices. A Demucs stem that sounds in at least a quarter of the track and carries at least 0.4% of its energy
is a candidate; the four best (active share x sqrt(energy share)) become voices. If fewer than four qualify the
tool splits the strongest stem into two complementary halves (drums into kick below 150 Hz and tops; the
melodic stem into harmonic and percussive halves) or merges two weak stems. The backing is the recording minus
the four voices, so voices + backing are an exact partition of the recording before encoding.

Events. Drums: onsets (log-mel flux), each moved to the steepest rise of a 1 ms energy envelope, and labelled
kick / snare / hat from band levels relative to each band's loudest moment within 5 s. Bass: notes by pitch
(pyin), because a held sub or reese pumps with the sidechain and those swells are not notes; a note starts
where the pitch moves at least 0.9 semitone and holds for 70 ms (glides count once), placed on an attack within
15 ms if there is one, else on the 16th line within 40 ms. Melodic and vocal parts: onsets with a clear attack
(at least 0.4 of the voice's 99th-percentile flux), chroma changes, and note lengths (time within 12 dB of the
note's peak). An event is a candidate only where the voice is within 24 dB of the whole track and 30 dB of its
own loud level, so no cue lands where the voice is silent or buried.

Ranking and selection. Each event scores strength, audibility, metric position, and how regularly the part
plays that position across the section. Per section and voice, a budget (cues per beat by role and difficulty)
is spent on whole positions in the repeating cycle first (1 bar for drums, 2 for bass, 4 for melodic and
vocal parts), so the same pattern comes back every cycle where the music repeats; leftovers go to accents.
Hard is chosen from all events, normal from hard, easy from normal.

Pads. The hard candidates are selected per voice (independent of pads), the number of their presses that
fall within half a beat of another voice's is counted for every pair, and the thumb split with the fewest
clashes wins. Then all four pads are resolved together against the contract's playability rules with the
validator's own rule function (the same EPS as the game loader); drums and bass win conflicts, holds are
shortened to make room or become taps.

## Reading the report (`packs/<id>/report.txt`)

- tempo: BPM and its ratio to 174 and 87, the grid residual (median and rms ms of drum onsets from the grid),
  drift per 8-bar window from local fits (a constant tempo stays within about +-10 ms from start to end), the
  tempo of each half, and the downbeat phase scores.
- sections with times, bars and intensity.
- separation: stem minus recording residual, each stem's energy share, active share, band leakage, envelope
  correlation and drum-attack coincidence, and each stem's share of the recording by section, with a sentence
  per stem.
- per chart and voice: cue counts, holds, rates per minute and per beat, the distance from each cue to the
  nearest onset found by an independent detector (librosa's default, on the encoded stem), the share of the
  voice's strong onsets that became cues, confidence quantiles, event kinds, and the share within 20 ms of a
  16th line; per section cue rates; how often two pads are asked for together; the correlation of cue rate
  with section energy; the validator's stem-sum error, alignment lags and silent-cue counts.
- The bass's distance to independent onsets is large by design: its cues are pitch changes in a legato line,
  which have no attack for an onset detector to find. Its share on the 16th grid is the better check.

## Listening

`packs/<id>/preview/`: `mix_clicks_normal.ogg` (the whole track with a click on every `normal` cue, one pitch
per pad, low to high from pad 1 to 4, and a softer click where a hold ends), `solo_pad<N>_<key>_clicks.ogg`
(one voice alone with its clicks), and `miss_<key>.ogg` (30 s of the loudest drop with that voice dropped from a
cue until its first cue four bars later, as the game does after missed presses). Play with
`ffplay -nodisp -autoexit <file>` or any player.

## What is committed

Only the code in `tools/audio_import/` (and its README). Never audio, stems, previews, caches, reports or
packs: they live under `/home/joe/rw-audio-work/`, which is outside every repository.

## Known limits

- Demucs separates drums, bass, vocals and "everything else". In this genre "other" holds pads, stabs and
  leads together; the pilot keeps it as one voice. Separation artefacts (some sub in "other", drum attacks in
  the vocal stem) are audible when a voice is muted alone.
- Charting is measured, not heard: the drum backbone, bass notes and phrase starts follow the audio and repeat
  where the music repeats, but whether a chart feels like performing the part needs a human ear (use the
  previews).
- Tempo changes: the tool detects and reports drift and would place cues from detected beats, but this path
  has not been exercised on a real track with a tempo change.
- Sections: roles come from intensity of drums and bass; a track whose drop is carried by something else may
  be labelled oddly. Sections only scale chart density and are informational in the game.
- Vorbis q10 makes packs about 80 MB for 5 minutes; lower quality makes the stems sum to the record less
  exactly (q6 measured -24 dB, q8 -29 dB, q10 -38 dB) because separated stems partly cancel each other.
