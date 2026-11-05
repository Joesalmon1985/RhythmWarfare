#!/usr/bin/env python3
"""Builds the synthetic track pack used by the track mode tests: 12 s at 120 BPM, four voices (one per pad), one
backing stem, a chart with taps, a hold, a two-pad chord and a long rest on one voice. Run from anywhere; it writes
track.json and stems/*.ogg next to this file, plus three deliberately wrong stems in extra/ (short, mono, 44.1 kHz)
that the loader tests copy into temporary packs. Needs numpy and /usr/bin/ffmpeg (libvorbis).

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
DUR = 12.0
BPM = 120.0

# (t, pad, dur)  B = 0.5 s. Pad 1 drums, 2 lead, 3 pads, 4 bass. Pads 1+2 are the left thumb, 3+4 the right.
NORMAL = (
    [(t, 1, 0.0) for t in (1.0, 2.0, 3.0, 4.0, 6.0, 7.0, 8.0, 9.0, 10.0)]
    + [(t, 2, 0.0) for t in (1.5, 2.5, 3.5, 6.5, 7.5, 8.5, 9.5)] + [(4.5, 2, 1.0)]  # a hold on the lead
    + [(1.0, 3, 0.0), (2.0, 3, 0.0), (3.0, 3, 1.0), (10.0, 3, 0.0)]  # chord with the drums at 1.0 and 10.0; rests 4.0 to 10.0
    + [(t, 4, 0.0) for t in (1.5, 2.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5)]
)
EASY = [(t, 1, 0.0) for t in (2.0, 4.0, 6.0, 8.0)] + [(3.0, 4, 0.0), (7.0, 4, 0.0)]

VOICES = [
    ("drums", "Drums", 1, 1.0),
    ("lead", "Lead", 2, 1.0),
    ("pads", "Pads", 3, 0.8),
    ("bass", "Bass", 4, 1.0),
]
FREQ = {1: 110.0, 2: 660.0, 3: 330.0, 4: 55.0}


def tone(n, freq, amp, decay):
    t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)


def voice_audio(pad, cues):
    out = np.zeros(int(DUR * SR))
    for (t, p, d) in cues:
        if p != pad:
            continue
        i = int(round(t * SR))
        if pad == 1:  # pitched click, falling pitch
            n = int(0.12 * SR)
            tt = np.arange(n) / SR
            seg = 0.8 * np.sin(2 * np.pi * (180 * tt - 600 * tt * tt)) * np.exp(-tt * 35)
        elif d > 0:  # a held note: sustained tone with a short attack and release
            n = int(d * SR)
            seg = tone(n, FREQ[pad], 0.5, 0.0)
            ramp = int(0.02 * SR)
            seg[:ramp] *= np.linspace(0, 1, ramp)
            seg[-ramp:] *= np.linspace(1, 0, ramp)
        else:
            n = int(0.3 * SR)
            seg = tone(n, FREQ[pad], 0.6, 9.0)
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
    for key, _label, pad, _gain in VOICES:
        write_ogg(os.path.join(stems, key + ".ogg"), voice_audio(pad, NORMAL))
    write_ogg(os.path.join(stems, "backing.ogg"), backing_audio())
    # wrong stems for the loader tests
    extra = os.path.join(HERE, "extra")
    write_ogg(os.path.join(extra, "short.ogg"), voice_audio(2, NORMAL)[:int(8.0 * SR)])
    write_ogg(os.path.join(extra, "mono.ogg"), voice_audio(2, NORMAL), channels=1)
    write_ogg(os.path.join(extra, "rate44.ogg"), voice_audio(2, NORMAL)[:int(DUR * 44100)], rate=44100)

    def chart(cues):
        return [{"t": t, "pad": p, "dur": d, "conf": 0.9} for (t, p, d) in sorted(cues, key=lambda c: (c[0], c[1]))]

    pack = {
        "format": "rhythm_warfare.track.v1",
        "id": "track_fixture",
        "title": "Track Fixture",
        "artist": "synthetic",
        "duration_s": DUR,
        "tempo": {"bpm": BPM, "first_downbeat_s": 0.0, "beats_per_bar": 4, "confidence": 0.9},
        "voices": [{"key": k, "label": l, "pad": p, "stem": "stems/%s.ogg" % k, "gain": g} for k, l, p, g in VOICES],
        "backing": [{"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}],
        "sections": [
            {"id": "intro", "role": "intro", "start_s": 0.0, "end_s": 4.0},
            {"id": "main", "role": "drop", "start_s": 4.0, "end_s": 10.0},
            {"id": "end", "role": "outro", "start_s": 10.0, "end_s": 12.0},
        ],
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
