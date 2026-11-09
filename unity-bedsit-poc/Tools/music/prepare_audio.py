"""Prepare local audio for the bedroom music POC (reproducible; outputs are git-ignored).

  python -I Tools/music/prepare_audio.py --gatekeeper "<path to Gatekeeper mp3>" --rw "<path to RhythmWarfare checkout>"

* Converts the Gatekeeper mp3 to LocalAudio/songs/gatekeeper.wav: 48 kHz, stereo, 16-bit PCM, NO trimming and no
  silence removal, so file time == original timestamp reference (ffmpeg removes the standard LAME encoder delay).
* Converts the RhythmWarfare 174 BPM loop stems used as the custom playable layer to LocalAudio/loops/*.wav (48 kHz stereo).
* Checks the loop MIDI cues (tick/960 beats) against the actual stem audio: median onset offset per stem.
* Writes LocalAudio/prepare_report.json and Docs/music/loop_stem_check.json.
"""
import argparse, glob, json, os, subprocess, sys
import numpy as np

SR = 48000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def ffmpeg():
    c = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe'))
    return c[0] if c else 'ffmpeg'


def to_wav(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run([ffmpeg(), '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', dst], check=True)


def read_pcm(path):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def onsets_near(mono, t_expected, window=0.06):
    """Time of the largest energy rise within +-window of the expected time (1 ms resolution)."""
    s0 = max(0, int((t_expected - window) * SR)); s1 = min(len(mono), int((t_expected + window) * SR))
    w = SR // 1000
    n = (s1 - s0) // w
    e = (mono[s0:s0 + n * w].reshape(n, w) ** 2).sum(axis=1)
    rise = np.diff(e, prepend=e[0])
    return (s0 + int(np.argmax(rise)) * w) / SR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gatekeeper', required=True)
    ap.add_argument('--rw', required=True)
    a = ap.parse_args()

    out_songs = os.path.join(ROOT, 'LocalAudio', 'songs')
    out_loops = os.path.join(ROOT, 'LocalAudio', 'loops')
    to_wav(a.gatekeeper, os.path.join(out_songs, 'gatekeeper.wav'))

    lib = json.load(open(os.path.join(a.rw, 'songs', 'library', 'index.json'), encoding='utf-8'))
    bpm = lib['bpm']; tpb = lib['ticks_per_beat']
    report = {'library_bpm': bpm, 'ticks_per_beat': tpb, 'stems': []}
    wanted = [('groove_half_time', 'kick'), ('groove_half_time', 'snare'), ('bass_sub_line', 'bass'), ('acc_hats_driving', 'other')]
    for clip, part in wanted:
        c = lib['clips'][clip]
        sound = list(c['sounds'][part])[0]
        rel = c['loops'][part][sound]
        src = os.path.join(a.rw, 'songs', 'library', rel)
        name = f'{clip}__{part}__{sound}'
        dst = os.path.join(out_loops, name + '.wav')
        to_wav(src, dst)
        pcm = read_pcm(dst)
        mono = pcm.mean(axis=1)
        entry = {'clip': clip, 'part': part, 'sound': sound, 'wav': f'LocalAudio/loops/{name}.wav', 'frames': int(len(pcm)),
                 'seconds': round(len(pcm) / SR, 5), 'bars': c['bars'], 'key': c.get('key', ''), 'peak': round(float(np.abs(pcm).max()), 3)}
        # MIDI vs audio: cue ticks -> expected time -> actual onset
        cues = c.get('cues', {}).get(part, [])
        offs = []
        for tick, _lane, pad in cues:
            t = tick / tpb * 60.0 / bpm
            offs.append((onsets_near(mono, t) - t) * 1000.0)
        entry['cue_count'] = len(cues)
        entry['pads'] = sorted({int(p) for _, _, p in cues})
        if offs:
            entry['median_onset_minus_midi_ms'] = round(float(np.median(offs)), 1)
            entry['max_abs_offset_ms'] = round(float(np.max(np.abs(offs))), 1)
            entry['midi_matches_audio'] = bool(np.max(np.abs(np.array(offs) - np.median(offs))) < 15.0)
        # exact loop length vs 8 bars at library BPM
        entry['expected_seconds_8bars'] = round(32 * 60.0 / bpm, 5)
        report['stems'].append(entry)
        print(entry)

    os.makedirs(os.path.join(ROOT, 'Docs', 'music'), exist_ok=True)
    json.dump(report, open(os.path.join(ROOT, 'Docs', 'music', 'loop_stem_check.json'), 'w'), indent=2)
    json.dump(report, open(os.path.join(ROOT, 'LocalAudio', 'prepare_report.json'), 'w'), indent=2)


if __name__ == '__main__':
    main()
