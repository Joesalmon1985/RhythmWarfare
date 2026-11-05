"""Stage 1: Demucs separation through its Python API, cached as float32 .npy (no clamping, no per-stem rescale).

Demucs's own command line writes WAVs that are clamped to +-1 (float) or rescaled per stem (int), and either breaks
the rule that the stems sum to the recording. Here the raw model output is kept, with the mix it was computed from,
both at the model's rate (44.1 kHz).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from audio_io import decode

MODELS = ("htdemucs", "htdemucs_ft", "htdemucs_6s")


def separate(src: str | Path, out_dir: str | Path, model_name: str = "htdemucs", shifts: int = 1,
             overlap: float = 0.25, start_s: float | None = None, dur_s: float | None = None,
             force: bool = False) -> dict:
    """Separate `src` into out_dir/{mix,<stem>}.npy; returns the meta dict. Skips if out_dir/meta.json exists."""
    out = Path(out_dir)
    meta_path = out / "meta.json"
    if meta_path.exists() and not force:
        return json.loads(meta_path.read_text())
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "3")))
    t0 = time.time()
    model = get_model(model_name)
    model.eval()
    rate = int(model.samplerate)
    mix, _ = decode(src, rate=rate, channels=2)
    if start_s is not None:
        a = int(start_s * rate)
        mix = mix[a:a + int((dur_s or 30.0) * rate)]
    wav = torch.from_numpy(mix.T.copy())
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        est = apply_model(model, ((wav - mean) / std)[None], shifts=shifts, split=True, overlap=overlap,
                          progress=True, device="cpu")[0]
    # the mean goes back once in total, not once per stem, so the stems still sum to the mix
    est = est * std + mean / len(model.sources)
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "mix.npy", mix.astype(np.float32))
    for name, s in zip(model.sources, est):
        np.save(out / f"{name}.npy", s.numpy().T.astype(np.float32))
    meta = {"model": model_name, "sources": list(model.sources), "rate": rate, "frames": int(mix.shape[0]),
            "shifts": shifts, "overlap": overlap, "excerpt": [start_s, dur_s] if start_s is not None else None,
            "seconds": round(time.time() - t0, 1), "threads": torch.get_num_threads()}
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta


def load(out_dir: str | Path) -> tuple[np.ndarray, dict[str, np.ndarray], dict]:
    out = Path(out_dir)
    meta = json.loads((out / "meta.json").read_text())
    mix = np.load(out / "mix.npy")
    stems = {k: np.load(out / f"{k}.npy") for k in meta["sources"]}
    return mix, stems, meta


if __name__ == "__main__":  # model comparison helper: separate.py <src> <out_dir> <model> [start dur]
    import sys
    a = sys.argv
    print(separate(a[1], a[2], a[3], start_s=float(a[4]) if len(a) > 4 else None,
                   dur_s=float(a[5]) if len(a) > 5 else None))
