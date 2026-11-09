"""Audio analysis for the bedroom music POC (numpy only, no librosa).

Usage:  python -I Tools/music/analyze_audio.py <song.mp3|wav> <out.json> [--bpm 174.0] [--anchors a,b,c]

Decodes with ffmpeg (no trimming) to 48 kHz stereo float, then reports:
  duration, sample rate, channels, low-band onset envelope based BPM (autocorrelation + comb refinement),
  beat-grid origin (phase of beat 0), per-anchor verification (energy before/after, nearest onset, phase),
  and a Krumhansl-Schmuckler key estimate with an uncertainty flag.
"""
import json, subprocess, sys, glob, os
import numpy as np

SR = 48000


def find_ffmpeg():
    c = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe'))
    return c[0] if c else 'ffmpeg'


def decode(path):
    cmd = [find_ffmpeg(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    return a


def lowpass_fft(x, cutoff_hz):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    X[f > cutoff_hz] = 0
    return np.fft.irfft(X, n=len(x))


def onset_envelope(mono, hop=240):
    """Low band (<180 Hz) log-energy flux at 200 Hz frame rate (hop 240 @ 48 kHz = 5 ms)."""
    low = lowpass_fft(mono, 180.0)
    n = len(low) // hop
    e = (low[: n * hop].reshape(n, hop) ** 2).sum(axis=1) + 1e-9
    le = np.log(e)
    flux = np.maximum(0, np.diff(le, prepend=le[0]))
    return flux, SR / hop


def comb_score(env, fps, bpm, phase_s):
    period = fps * 60.0 / bpm
    idx = np.arange(phase_s * fps, len(env) - 1, period)
    return env[np.round(idx).astype(int)].sum() / len(idx)


def best_phase(env, fps, bpm, steps=200):
    period_s = 60.0 / bpm
    best = (-1, 0)
    for k in range(steps):
        p = period_s * k / steps
        s = comb_score(env, fps, bpm, p)
        if s > best[0]:
            best = (s, p)
    return best[1], best[0]


def estimate_bpm(env, fps):
    e = env - env.mean()
    ac = np.correlate(e, e, mode='full')[len(e) - 1:]
    lo, hi = int(fps * 60 / 190), int(fps * 60 / 150)
    lag = lo + int(np.argmax(ac[lo:hi]))
    coarse = 60.0 * fps / lag
    best = (-1, coarse)
    for b in np.arange(coarse - 1.5, coarse + 1.5, 0.01):
        _, s = best_phase(env, fps, b, steps=40)
        if s > best[0]:
            best = (s, b)
    return coarse, best[1]


KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def chroma(mono, start_s=0.0, end_s=None, seg=4.0):
    end_s = end_s or len(mono) / SR
    chroma_sum = np.zeros(12)
    n = int(seg * SR)
    win = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    mask = (freqs > 55) & (freqs < 2000)
    pcs = np.round(12 * np.log2(freqs[mask] / 440.0) + 69).astype(int) % 12
    t = start_s
    while t + seg <= end_s:
        s = int(t * SR)
        spec = np.abs(np.fft.rfft(mono[s:s + n] * win))[mask]
        chroma_sum += np.bincount(pcs, weights=spec, minlength=12)
        t += seg
    return chroma_sum / max(chroma_sum.sum(), 1e-9)


def key_estimate(ch):
    scores = []
    for i in range(12):
        scores.append((np.corrcoef(ch, np.roll(KS_MAJ, i))[0, 1], f'{NOTES[i]} major'))
        scores.append((np.corrcoef(ch, np.roll(KS_MIN, i))[0, 1], f'{NOTES[i]} minor'))
    scores.sort(reverse=True)
    margin = scores[0][0] - scores[1][0]
    return [{'key': k, 'r': round(float(r), 3)} for r, k in scores[:4]], float(margin)


def main():
    path, out = sys.argv[1], sys.argv[2]
    bpm_hint = float(sys.argv[sys.argv.index('--bpm') + 1]) if '--bpm' in sys.argv else 174.0
    anchors = [float(x) for x in sys.argv[sys.argv.index('--anchors') + 1].split(',')] if '--anchors' in sys.argv else []
    a = decode(path)
    mono = a.mean(axis=1)
    dur = len(a) / SR
    env, fps = onset_envelope(mono)
    coarse, bpm_fit = estimate_bpm(env, fps)
    phase, score = best_phase(env, fps, bpm_hint, steps=400)
    beat = 60.0 / bpm_hint
    res = {
        'file': os.path.basename(path), 'duration_s': round(dur, 3), 'sample_rate_decoded': SR, 'channels': 2,
        'bpm_autocorr_coarse': round(coarse, 3), 'bpm_comb_fit': round(bpm_fit, 3), 'bpm_used': bpm_hint,
        'beat_phase_s': round(phase, 4), 'beat_origin_s': round(phase, 4),
        'peak': float(np.abs(a).max()),
    }
    # anchors: verify
    low = lowpass_fft(mono, 180.0)
    rms = lambda s, e: float(np.sqrt(np.mean(low[int(s * SR):int(e * SR)] ** 2)))
    anc = []
    for t in anchors:
        k = (t - phase) / beat
        nearest = round(k)
        off = (t - (phase + nearest * beat)) * 1000.0
        # strongest low-band onset within +-0.6 s
        lo, hi = int((t - 0.6) * fps), int((t + 0.6) * fps)
        j = lo + int(np.argmax(env[lo:hi]))
        anc.append({
            't': t, 'beats_from_origin': round(k, 3), 'offset_from_grid_ms': round(off, 1),
            'strongest_low_onset_s': round(j / fps, 3), 'onset_minus_anchor_ms': round((j / fps - t) * 1000, 1),
            'rms_low_before_4s': round(rms(t - 4, t), 4), 'rms_low_after_4s': round(rms(t, t + 4), 4),
        })
    res['anchors'] = anc
    ch = chroma(mono, 20.0, min(dur, 300.0))
    top, margin = key_estimate(ch)
    res['key_candidates'] = top
    res['key_margin'] = round(margin, 3)
    res['key_certain'] = bool(margin > 0.06)
    res['chroma'] = [round(float(c), 4) for c in ch]
    json.dump(res, open(out, 'w'), indent=2)
    print(json.dumps({k: v for k, v in res.items() if k != 'chroma'}, indent=1)[:2500])


if __name__ == '__main__':
    main()
