"""Audio in and out through ffmpeg, numpy only (so the validator runs under a plain python3 with numpy).

Every decode returns float32 arrays shaped (frames, channels). Resampling is always ffmpeg's soxr at one fixed
setting, so the recording and every stem are resampled by the same linear filter: the stems still sum to the
recording after resampling.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np



def _find_tool(name: str) -> str:
    """ffmpeg / ffprobe from PATH (Linux /usr/bin, Windows the full build on PATH); a clear error if missing."""
    found = shutil.which(name)
    if not found:
        raise FileNotFoundError(f"{name} not found on PATH: install ffmpeg (a build with libvorbis and soxr) and put "
                                f"its bin folder on PATH")
    return found


FFMPEG = _find_tool("ffmpeg")
FFPROBE = _find_tool("ffprobe")
PACK_RATE = 48000
VORBIS_QUALITY = 10  # about 440 kbit/s stereo: separated stems partly cancel, so each stem's coding noise must be low for the sum to match the record (q6 -24 dB, q8 -29 dB, q10 -38 dB on this music)


def resample_filter(rate: int) -> str:
    return f"aresample={rate}:resampler=soxr:precision=28"


def probe(path: str | Path) -> dict:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                          "format=duration,format_name:stream=codec_name,sample_rate,channels:stream_tags:format_tags",
                          "-of", "json", str(path)], capture_output=True, check=True, text=True).stdout
    info = json.loads(out)
    st = next((s for s in info.get("streams", []) if s.get("sample_rate")), {})
    fmt = info.get("format", {})
    tags = {k.lower(): v for k, v in {**fmt.get("tags", {}), **st.get("tags", {})}.items()}
    return {"codec": st.get("codec_name"), "rate": int(st.get("sample_rate", 0) or 0),
            "channels": int(st.get("channels", 0) or 0), "duration": float(fmt.get("duration", 0) or 0),
            "format": fmt.get("format_name"), "tags": tags}


def decode(path: str | Path, rate: int | None = None, channels: int = 2) -> tuple[np.ndarray, int]:
    """Decode any file ffmpeg reads to float32 (frames, channels). rate None keeps the file's own rate."""
    if rate is None:
        rate = probe(path)["rate"]
    cmd = [FFMPEG, "-v", "error", "-nostdin", "-i", str(path), "-map", "0:a:0",
           "-af", resample_filter(rate), "-ac", str(channels), "-f", "f32le", "-acodec", "pcm_f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, channels).copy(), rate


def _pipe_out(x: np.ndarray, rate: int, args: list[str], path: Path) -> None:
    x = np.ascontiguousarray(x, dtype="<f4")
    cmd = [FFMPEG, "-v", "error", "-nostdin", "-y", "-f", "f32le", "-ar", str(rate), "-ac", str(x.shape[1]),
           "-i", "-", *args, str(path)]
    subprocess.run(cmd, input=x.tobytes(), check=True)


def encode_ogg(x: np.ndarray, rate: int, path: str | Path, out_rate: int = PACK_RATE,
               quality: int = VORBIS_QUALITY) -> None:
    """Float (frames, 2) at `rate` to Ogg Vorbis at `out_rate`, resampled by the shared soxr filter."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    af = [] if out_rate == rate else ["-af", resample_filter(out_rate)]
    _pipe_out(x, rate, [*af, "-ar", str(out_rate), "-c:a", "libvorbis", "-q:a", str(quality), "-f", "ogg"], path)


def write_wav(x: np.ndarray, rate: int, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _pipe_out(x, rate, ["-c:a", "pcm_f32le", "-f", "wav"], path)


def mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def frame_rms(x: np.ndarray, rate: int, hop_s: float, win_s: float | None = None) -> np.ndarray:
    """RMS of mono x in frames of win_s every hop_s (centred on frame k*hop_s)."""
    m = mono(x).astype(np.float64)
    # frame k is centred on sample round(k * hop_s * rate) exactly: a whole-sample hop would drift (0.005 s at
    # 44.1 kHz is 220.5 samples; rounding it put frames 0.2 s off by 90 s into a track)
    win = max(1, int(round((win_s or hop_s) * rate)))
    c = np.concatenate([[0.0], np.cumsum(m * m)])
    n = int(len(m) / (hop_s * rate)) + 1
    centres = np.round(np.arange(n) * hop_s * rate).astype(np.int64)
    a = np.clip(centres - win // 2, 0, len(m))
    b = np.clip(centres + win // 2, 0, len(m))
    return np.sqrt((c[b] - c[a]) / np.maximum(b - a, 1))


def db(x, floor: float = 1e-10):
    return 20.0 * np.log10(np.maximum(x, floor))
