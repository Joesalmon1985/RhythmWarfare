"""Re-imports the owner's 14 Squadron loops (content/imports/squadron/C01..C14, 140 BPM) into songs/packs/squadron_c01..c14 with the settings chosen on 5 November 2026.

    python tools/content/import_squadron.py                  # import all 14 (about a minute), then measure the written loops and rewrite docs/paths/squadron_music_report.json
    python tools/content/import_squadron.py --only C06,C07   # some scenes only
    python tools/content/import_squadron.py --check          # measure only: nothing imported, the report is not rewritten

Idempotent: `beatshaper.py import` rewrites the same files byte for byte (write_wav leaves an identical file alone). The sources are only read; no audio or MIDI is ever
retimed, stretched or edited, only gain-staged (the owner's dB below) and folded onto a 16-beat loop. The packs are not assigned: content/paths/squadron/music.json is not touched.

Settings (SETTINGS below), chosen as follows:
  * `--max-error-ms 40` for all 14: C01, C02, C04, C08, C09, C12 are refused at the default 12 ms (kick or snare 31 to 38 ms from the MIDI note), C03, C05, C10 verify loosely at 12 ms.
  * bass: the strongest 0.5 dB step (no upper cap) that keeps the bass stem peak at or below -0.3 dBFS and the peaks of the four stage sums (STAGES) at or below -0.5 dBFS. When the sums
    bind, drums (not below -6 dB) and synth (kept at least 6 dB under the bass stem RMS) are lowered first, the smallest total cut that works; only then the bass. The importer has no
    limiter: it refuses a stem whose peak after gain is >= 0.999 and writes plain 16-bit PCM, so the headroom is exactly what is left.
  * synth starts from the level that puts its stem RMS near -28 dBFS (a quiet backing, peak under -3 dBFS) and is only lowered.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import beatshaper as bs  # noqa: E402
from common import ROOT, SAMPLE_RATE  # noqa: E402
from import_recorded import envelope, onset_near  # noqa: E402

PATH_ID = "squadron"
BPM = 140
SRC_DIR = ROOT / "content" / "imports" / PATH_ID
REPORT = ROOT / "docs" / "paths" / "squadron_music_report.json"
MAX_ERROR_MS = 40
# stage gains (drums, bass, synth) the run mixes the three stems with (content/paths/squadron/run.json)
STAGES = {"stage0": (1.0, 0.0, 0.0), "stage1": (0.7, 1.0, 0.0), "stage2": (1.0, 0.9, 0.5), "stage3": (0.55, 1.0, 0.7)}
# scene -> (drums_db, bass_db, synth_db)
SETTINGS = {
    "C01": (-4, 11.5, 12),
    "C02": (-3.5, 11, 12),
    "C03": (-3.5, 9.5, 14),
    "C04": (-2.5, 11.5, 10),
    "C05": (0, -2, 9.5),
    "C06": (-1, -1, 9),
    "C07": (-3, 12.5, 11),
    "C08": (-5, 12, 8),
    "C09": (-1, 6.5, 12.5),
    "C10": (-4.5, 12.5, 13.5),
    "C11": (-4, 6.5, 10),
    "C12": (0, 10, 10.5),
    "C13": (-6, 11, 10.5),
    "C14": (0, 11, 14),
}


def db(x: float) -> float:
    return 20.0 * math.log10(max(float(x), 1e-9))


def read_pack_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2 and w.getframerate() == SAMPLE_RATE
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
        return raw.reshape(-1, w.getnchannels())


def rms(x: np.ndarray) -> float:
    return float(np.sqrt((x ** 2).mean()))


def command_for(scene: str, drums_db: float, bass_db: float, synth_db: float) -> list[str]:
    cmd = [sys.executable, "tools/content/beatshaper.py", "--path", PATH_ID]
    if not (ROOT / "content" / "paths" / PATH_ID / "run.json").exists():
        cmd += ["--bpm", str(BPM)]  # the run.json (which carries the tempo) is not written yet
    return cmd + ["import", f"content/imports/{PATH_ID}/{scene}", "--set", scene, "--id", f"{PATH_ID}_{scene.lower()}", "--max-error-ms", str(MAX_ERROR_MS),
                  "--drums-db", f"{drums_db:g}", "--bass-db", f"{bass_db:g}", "--synth-db", f"{synth_db:g}"]


def timing_facts(scene: str) -> dict:
    """Per kick and per snare: the worst distance (ms) between the MIDI note and the drum transient in the recording (raw, and from the fitted line), and what the default 12 ms limit said."""
    src = bs.Source(SRC_DIR / scene)
    facts: dict = {}
    try:
        a12 = bs.analyse(src, scene, 0, {})
        facts["default_12ms"] = a12["report"]["tempo"]["verified"]  # strict or loose
    except bs.ContentError:
        facts["default_12ms"] = "refused"
    a = bs.analyse(src, scene, 0, {"max_error_ms": float(MAX_ERROR_MS)})
    mono = a["audio"]["Drums"].mean(axis=1)
    env, step = envelope(mono, SAMPLE_RATE)
    spb = 60.0 / BPM
    fit = a["fit"]
    for fam, notes in (("kick", a["kick"]), ("snare", a["snare"])):
        hits = sorted({n["beat"] for n in a["midi"]["Drums"]["notes"] if n["pitch"] in notes})
        errs = []
        for b in hits:
            o = onset_near(env, step, b * spb, 0.04)
            if o is not None:
                errs.append((b, (o - b * spb) * 1000.0))
        resid = [e - fit["fitted_offset_ms"] for _b, e in errs]
        facts[fam] = {"hits": len(hits), "matched": len(errs), "worst_error_ms": round(max((abs(e) for _b, e in errs), default=0.0), 1),
                      "worst_error_after_offset_ms": round(max((abs(r) for r in resid), default=0.0), 1)}
    facts["fitted_bpm"] = fit["fitted_bpm"]
    facts["fitted_offset_ms"] = fit["fitted_offset_ms"]
    facts["worst_error_ms"] = fit["max_abs_ms"]
    facts["tempo_verified_at_40ms"] = a["report"]["tempo"]["verified"]
    facts["max_error_ms_required"] = facts["default_12ms"] == "refused"
    facts["bass_timing"] = a["report"]["bass_timing"]
    facts["loop_frames"] = a["loop_frames"]
    facts["phrase_beats"] = a["phrase_beats"]
    facts["warnings"] = list(a["warnings"]) + [d for d in a["report"]["decisions"] if not d.startswith("WARNING")]
    return facts


def measure(scene: str, drums_db: float, bass_db: float, synth_db: float) -> dict:
    pack_dir = ROOT / "songs" / "packs" / f"{PATH_ID}_{scene.lower()}"
    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    stems = {k: read_pack_wav(pack_dir / pack["stems"][k]) for k in ("drums", "bass", "other")}
    d, b, s = stems["drums"], stems["bass"], stems["other"]
    out: dict = {"pack": pack["id"], "loop_frames": pack["loop_frames"], "phrase_beats": pack["phrase_beats"], "profile": pack["profile"],
                 "stem_peaks_dbfs": {k: round(db(np.abs(v).max()), 2) for k, v in stems.items()},
                 "stem_rms_dbfs": {k: round(db(rms(v)), 2) for k, v in stems.items()}}
    unity_bass_peak = pack["loops"]["bass"]["peak_db"] - pack["loops"]["bass"]["gain_db"]
    out["bass_db_max_noclip"] = round(-0.3 - unity_bass_peak, 2)  # the largest gain that keeps the bass stem peak at -0.3 dBFS (before the sum limits)
    sums = {}
    for name, (gd, gb, gs) in STAGES.items():
        mix = gd * d + gb * b + gs * s
        sums[name] = {"peak_dbfs": round(db(np.abs(mix).max()), 2), "rms_dbfs": round(db(rms(mix)), 2)}
    out["stage_sums"] = sums
    mono = b.mean(axis=1)
    spec = np.abs(np.fft.rfft(mono)) ** 2
    freq = np.fft.rfftfreq(len(mono), 1.0 / SAMPLE_RATE)
    out["bass_share_below_90hz"] = round(float(spec[(freq > 0) & (freq < 90)].sum() / spec[freq > 0].sum()), 3)
    out["bass_vs_drums_rms_db"] = {name: round(db(gb * rms(b)) - db(gd * rms(d)), 2) for name, (gd, gb, _gs) in STAGES.items() if gd and gb}
    out["bass_vs_drums_rms_db_stems"] = round(db(rms(b)) - db(rms(d)), 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma separated scenes, e.g. C06,C07")
    ap.add_argument("--check", action="store_true", help="measure the packs on disk only; import nothing and do not rewrite the report")
    args = ap.parse_args()
    scenes = sorted(SETTINGS)
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",")}
        scenes = [s for s in scenes if s in want]
    bs.select_path(PATH_ID, BPM)
    t0 = time.time()
    report: dict = {}
    if REPORT.exists() and (args.only or args.check):
        report = json.loads(REPORT.read_text(encoding="utf-8")).get("scenes", {})
    results = {}
    for scene in scenes:
        dd, bd, sd = SETTINGS[scene]
        cmd = command_for(scene, dd, bd, sd)
        if not args.check:
            t1 = time.time()
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            sys.stdout.write(proc.stdout)
            if proc.returncode:
                sys.stderr.write(proc.stderr)
                print(f"{scene}: IMPORT FAILED")
                return 1
            took = round(time.time() - t1, 1)
        else:
            took = None
        m = measure(scene, dd, bd, sd)
        row = {**m, "scene": scene, "drums_db": dd, "bass_db": bd, "synth_db": sd, **timing_facts(scene),
               "import_seconds": took, "command": " ".join(["python"] + cmd[1:])}
        row["bass_db_headroom_unused"] = round(row["bass_db_max_noclip"] - bd, 2)
        results[scene] = row
        s2, s3 = m["stage_sums"]["stage2"]["peak_dbfs"], m["stage_sums"]["stage3"]["peak_dbfs"]
        print(f"{scene}: drums {dd:+g} bass {bd:+g} synth {sd:+g} dB; stage 2 / 3 sum peaks {s2} / {s3} dBFS; bass < 90 Hz {m['bass_share_below_90hz']:.0%}; bass vs drums (stage 3) {m['bass_vs_drums_rms_db']['stage3']:+.1f} dB")
    report.update(results)
    if not args.check:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        doc = {"path": PATH_ID, "bpm": BPM, "max_error_ms": MAX_ERROR_MS, "stage_gains_drums_bass_synth": {k: list(v) for k, v in STAGES.items()}, "scenes": report,
               "note": "written by tools/content/import_squadron.py; sums are computed from the written 16-bit loops/*.wav, not from the sources"}
        REPORT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        print(f"report written to {REPORT.relative_to(ROOT).as_posix()}; {len(results)} scene(s) in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
