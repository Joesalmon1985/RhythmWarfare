#!/usr/bin/env python3
"""Builds the synthetic track pack (format version 2) used by the track mode tests: 16 s at 120 BPM (B = 0.5 s), three
voices (drums, a lead and a bass, the last two pitched), one backing stem, and a focus that moves drums (0 to 4 s),
lead (4 to 8 s), a gap with nothing to play (8 to 9 s), bass (9 to 16 s). The charts `normal` and `easy` hold taps,
holds (the lead's ends 0.1 s before its stretch does), and two-pad chords on different thumbs in the drums stretch.
Writes track.json and stems/*.ogg next to this file, plus three deliberately wrong stems in extra/ (short, mono,
44.1 kHz) that the loader tests copy into temporary packs. Needs numpy and /usr/bin/ffmpeg (libvorbis).

    python3 tests/fixtures/track_fixture/make_fixture.py
"""
import json
import os
import subprocess
import tempfile
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = 16.0
BPM = 120.0

# (t, pad, dur, voice). Pads 1 and 2 are the left thumb, 3 and 4 the right; low sounds left, high sounds right.
NORMAL = (
    # drums, stretch 0 to 4: kick on 1, snare on 2, a hat on 3 together with the kick (a chord on two thumbs)
    [(1.0, 1, 0.0, "drums"), (1.0, 3, 0.0, "drums"), (1.5, 2, 0.0, "drums"), (2.0, 1, 0.0, "drums"), (2.5, 2, 0.0, "drums"),
     (3.0, 1, 0.0, "drums"), (3.0, 3, 0.0, "drums"), (3.5, 2, 0.0, "drums")]
    # lead, stretch 4 to 8: a rising phrase, a held note 6.5 to 7.9 (just inside the stretch), two notes under it
    + [(4.5, 1, 0.0, "lead"), (5.0, 2, 0.0, "lead"), (5.5, 3, 0.0, "lead"), (6.0, 4, 0.0, "lead"), (6.5, 3, 1.4, "lead"),
       (7.0, 1, 0.0, "lead"), (7.5, 2, 0.0, "lead")]
    # bass, stretch 9 to 16: a held note 12.0 to 13.0
    + [(9.5, 1, 0.0, "bass"), (10.0, 2, 0.0, "bass"), (10.5, 1, 0.0, "bass"), (11.0, 2, 0.0, "bass"), (11.5, 1, 0.0, "bass"),
       (12.0, 2, 1.0, "bass"), (13.5, 1, 0.0, "bass"), (14.0, 2, 0.0, "bass"), (14.5, 1, 0.0, "bass"), (15.0, 2, 0.0, "bass")]
)
EASY = [(2.0, 1, 0.0, "drums"), (3.0, 1, 0.0, "drums"), (5.0, 2, 0.0, "lead"), (7.0, 1, 0.0, "lead"),
        (10.0, 2, 0.0, "bass"), (11.5, 1, 0.0, "bass"), (14.0, 2, 0.0, "bass")]

FOCUS = [(0.0, 4.0, "drums"), (4.0, 8.0, "lead"), (9.0, 16.0, "bass")]

# key, label, kind, gain
VOICES = [
    ("drums", "Drums", "drums", 1.0),
    ("lead", "Lead", "pitched", 0.8),
    ("bass", "Bass", "pitched", 1.0),
]
FREQ = {"lead": {1: 330.0, 2: 392.0, 3: 494.0, 4: 660.0}, "bass": {1: 55.0, 2: 73.4}}


def tone(n, freq, amp, decay):
    t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)


def voice_audio(voice, cues):
    out = np.zeros(int(DUR * SR))
    for (t, pad, d, v) in cues:
        if v != voice:
            continue
        i = int(round(t * SR))
        if voice == "drums":  # a click whose pitch rises with the pad, falling within the hit
            n = int(0.12 * SR)
            tt = np.arange(n) / SR
            seg = 0.8 * np.sin(2 * np.pi * ((120 + 120 * pad) * tt - 600 * tt * tt)) * np.exp(-tt * 35)
        elif d > 0:  # a held note: sustained tone with a short attack and release
            n = int(d * SR)
            seg = tone(n, FREQ[voice][pad], 0.5, 0.0)
            ramp = int(0.02 * SR)
            seg[:ramp] *= np.linspace(0, 1, ramp)
            seg[-ramp:] *= np.linspace(1, 0, ramp)
        else:
            n = int(0.3 * SR)
            seg = tone(n, FREQ[voice][pad], 0.6, 9.0)
        out[i:i + n] += seg[:len(out) - i]
    return out


def backing_audio():
    out = np.zeros(int(DUR * SR))
    rng = np.random.default_rng(1)
    beat = 60.0 / BPM
    k = 0
    while k * beat < DUR - 0.1:  # a quiet hat on every beat and a soft low drone
        i = int(k * beat * SR)
        n = int(0.05 * SR)
        out[i:i + n] += 0.15 * rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 80)[:len(out) - i][:n]
        k += 1
    out += tone(len(out), 82.4, 0.08, 0.0)
    return out


def write_ogg(path, samples, channels=2, rate=SR):
    pcm = np.clip(samples, -1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    if channels == 2:
        pcm = np.repeat(pcm[:, None], 2, axis=1)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["/usr/bin/ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-c:a", "libvorbis", "-q:a", "1",
                    "-ar", str(rate), "-ac", str(channels), path], check=True)
    os.unlink(wav_path)


def main():
    stems = os.path.join(HERE, "stems")
    for key, _label, _kind, _gain in VOICES:
        write_ogg(os.path.join(stems, key + ".ogg"), voice_audio(key, NORMAL))
    write_ogg(os.path.join(stems, "backing.ogg"), backing_audio())
    # wrong stems for the loader tests
    extra = os.path.join(HERE, "extra")
    write_ogg(os.path.join(extra, "short.ogg"), voice_audio("lead", NORMAL)[:int(8.0 * SR)])
    write_ogg(os.path.join(extra, "mono.ogg"), voice_audio("lead", NORMAL), channels=1)
    write_ogg(os.path.join(extra, "rate44.ogg"), voice_audio("lead", NORMAL)[:int(DUR * 44100)], rate=44100)

    def chart(cues):
        return [{"t": t, "pad": p, "dur": d, "conf": 0.9, "voice": v} for (t, p, d, v) in sorted(cues, key=lambda c: (c[0], c[1]))]

    pack = {
        "format": "rhythm_warfare.track.v2",
        "id": "track_fixture",
        "title": "Track Fixture",
        "artist": "synthetic",
        "duration_s": DUR,
        "tempo": {"bpm": BPM, "first_downbeat_s": 0.0, "beats_per_bar": 4, "confidence": 0.9},
        "voices": [{"key": k, "label": l, "kind": kind, "stem": "stems/%s.ogg" % k, "gain": g} for k, l, kind, g in VOICES],
        "backing": [{"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}],
        "sections": [
            {"id": "intro", "role": "intro", "start_s": 0.0, "end_s": 4.0},
            {"id": "main", "role": "drop", "start_s": 4.0, "end_s": 13.0},
            {"id": "end", "role": "outro", "start_s": 13.0, "end_s": 16.0},
        ],
        "focus": [{"start_s": a, "end_s": b, "voice": v} for a, b, v in FOCUS],
        "charts": {"normal": chart(NORMAL), "easy": chart(EASY)},
        "default_chart": "normal",
        "rules": {"restore_after_idle_beats": 8},
        "source": {"note": "synthetic fixture made by make_fixture.py"},
    }
    with open(os.path.join(HERE, "track.json"), "w") as f:
        json.dump(pack, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
