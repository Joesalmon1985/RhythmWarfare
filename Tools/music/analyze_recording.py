"""Independent check of recorded sessions (Evidence/audio/runtime_*.wav): clipping, silences > 250 ms, whether the recorded drop lands where the
director scheduled it, and how gradually the recording's buildup comes in. Drop/entry times are read from the session log (runtime_*.txt).
Run: python -I Tools/music/analyze_recording.py [perfect partial fail]"""
import os, re, sys, wave
import numpy as np

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
audio = os.path.join(root, 'Evidence', 'audio')


def load(path):
    w = wave.open(path)
    a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32).reshape(-1, w.getnchannels()) / 32768
    return a, w.getframerate()


def rms(m, sr, t0, t1):
    return float(np.sqrt((m[int(t0 * sr):int(t1 * sr)] ** 2).mean()))


for name in (sys.argv[1:] or ['perfect', 'partial', 'fail']):
    a, sr = load(os.path.join(audio, f'runtime_{name}.wav'))
    m = a.mean(1)
    log = open(os.path.join(audio, f'runtime_{name}.txt'), encoding='utf-8').read()
    drops = [float(x) for x in re.findall(r'DROP gatekeeper:\w+ at ([\d.]+)', log)]
    entries = [float(x) for x in re.findall(r'buildup: gatekeeper enters at ([\d.]+)', log)]
    print(f'{name}: {len(a) / sr:.1f}s peak {np.abs(a).max():.3f} clipped(>=0.999) {int((np.abs(a) >= 0.999).sum())}')
    win = int(sr * 0.05)
    r = np.sqrt(np.convolve(m ** 2, np.ones(win) / win, 'same'))[::win // 5]
    t = np.arange(len(r)) * (win // 5) / sr
    low = r < 10 ** (-60 / 20)
    runs, s = [], None
    for i, v in enumerate(low):
        if v and s is None: s = i
        if not v and s is not None: runs.append((t[s], t[i])); s = None
    print('  silent runs > 0.25 s (-60 dB):', [(round(float(x), 2), round(float(y), 2)) for x, y in runs if y - x > 0.25])
    for e in entries[-1:]:
        print('  last buildup entry %.3f: rms per second after entry: %s' % (e, [round(rms(m, sr, e + k, e + k + 1), 3) for k in range(0, 10)]))
    for d in drops:
        if d + 3.0 > len(a) / sr: continue
        i = int(d * sr)
        b = rms(m, sr, d - 1.5, d - 0.05); f = rms(m, sr, d + 0.1, d + 3.0)
        seg = m[i - int(0.3 * sr):i + int(0.6 * sr)]; w = int(sr * 0.005)
        e = np.sqrt(np.convolve(seg ** 2, np.ones(w) / w, 'same')); k = int(np.argmax(e > 2.0 * b))
        print('  drop at %.3f: rms 1.5 s before %.3f, 3 s after %.3f (x%.1f); first onset >2x the pre-drop level at %+.0f ms' % (d, b, f, f / b, (k / sr - 0.3) * 1000))
