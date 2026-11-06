#!/usr/bin/env python3
"""Final report of run_batch.sh: one line per source recording (ok / failed with the reason, cue counts, seconds) and
a last line `BATCH DONE ok=<n> failed=<n>`. Reads <work>/batch_summary.txt (written by import_track.py at the end of
its run), the packs and the cache's source.txt files. Numbers only; no audio.

    python batch_summary.py <work> <run_summary_file> > summary.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AUDIO_EXT = {".flac", ".mp3", ".wav", ".ogg", ".m4a", ".aiff", ".aif", ".opus"}


def _name(p: str) -> str:
    return p.replace("\\", "/").rsplit("/", 1)[-1]


def main(work: str, run_file: str) -> int:
    w = Path(work)
    run = {}  # first field of a summary line (pack id, or the file name for a track that failed early) -> fields
    rf = Path(run_file)
    if rf.is_file():
        for ln in rf.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("#") or " | " not in ln:
                continue
            parts = ln.split(" | ")
            key = parts[0].split(": ERROR")[0] if ": ERROR" in parts[0] else parts[0]
            run[key] = parts
    id_of = {}  # source file name -> pack id
    for sf in sorted((w / "cache").glob("*/source.txt")):
        try:
            id_of[_name(sf.read_text(encoding="utf-8").strip())] = sf.parent.name
        except OSError:
            pass
    for tj in sorted((w / "packs").glob("*/track.json")):
        try:
            id_of.setdefault(_name(json.loads(tj.read_text(encoding="utf-8")).get("source", {}).get("input_path", "")),
                             tj.parent.name)
        except (OSError, ValueError):
            pass
    sources = sorted(p for p in (w / "ToAddTry4").iterdir() if p.suffix.lower() in AUDIO_EXT) if (w / "ToAddTry4").is_dir() else []
    lines, n_ok, n_fail = [], 0, 0
    for s in sources:
        pid = id_of.get(s.name)
        parts = run.get(pid) or run.get(s.name) or run.get(s.stem)
        pack = w / "packs" / (pid or "-")
        cues, viol = "", None
        try:
            tj = json.loads((pack / "track.json").read_text(encoding="utf-8"))
            cues = " ".join(f"{k}:{len(v)}" for k, v in tj["charts"].items())
            viol = json.loads((pack / "report.json").read_text(encoding="utf-8")).get("validation", {}).get("violations")
        except (OSError, ValueError, KeyError):
            pass
        secs = parts[-2].strip() if parts and len(parts) >= 3 and parts[-2].strip().endswith(" s") else "-"
        verdict = parts[-1].strip() if parts else ""
        if parts and "already imported" in " ".join(parts):
            secs = "skipped (done earlier)"
        if not parts:
            status, why = "failed", "not processed in this run" + (" and no pack" if not cues else "")
        elif verdict.startswith("ok"):
            status, why = "ok", verdict if verdict != "ok" else ""
        else:
            status = "failed"
            why = next((p for p in parts if "ERROR" in p or "violation" in p.lower()), parts[1] if len(parts) > 1 else "").strip()
        if status == "ok" and (viol or not cues):
            status, why = "failed", f"{viol} validator violation(s)" if viol else "no pack"
        n_ok += status == "ok"
        n_fail += status == "failed"
        lines.append(f"{status.upper():6} | {pid or s.stem} | cues {cues or '-'} | {secs} | {why}".rstrip(" |").rstrip())
    lines.append(f"BATCH DONE ok={n_ok} failed={n_fail}")
    print("\n".join(lines))
    return 0


def revalidated(report_path: str) -> int:
    """The validator found 0 violations just now: if report.json still records some, record 0 (once)."""
    import datetime
    p = Path(report_path)
    r = json.loads(p.read_text(encoding="utf-8"))
    v = r.get("validation", {})
    if v.get("violations") not in (0, None):
        before = v.get("first")
        v.update({"violations": 0, "first": [], "was": before,
                  "revalidated": datetime.date.today().isoformat() + " by run_batch.sh"})
        r["validation"] = v
        p.write_text(json.dumps(r, indent=1), encoding="utf-8")
        print(f"{p.parent.name}: report.json said {before}, the validator now finds 0 violations: report updated")
    return 0


if __name__ == "__main__":
    if sys.argv[1] == "--revalidated":
        sys.exit(revalidated(sys.argv[2]))
    sys.exit(main(sys.argv[1], sys.argv[2]))
