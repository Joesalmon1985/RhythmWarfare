"""Check a recording of the continuous run (tools/story/record_music.gd on res://src/run/run_play.tscn) in which a scene plays an ARRANGEMENT: a section switch
inside a phase must be one voice group per section, no restart, the new pack on the grid within one mix chunk, and the mix the phase mix times the section's recipe.

    RW_RUN_MUSIC=<music.json> RW_RUN_BOT=perfect godot --headless --path . -s tools/story/record_music.gd -- <out base> <song seconds> res://src/run/run_play.tscn
    python tools/content/check_section_audio.py <out base> <music.json>

For every phase of a scene with sections it reads the voice log (one drums voice per section, the pack and start time of each), fits each 16-beat block of the recording as
the section's drum loop (from the section's downbeat), its bass and synth loops (from the reveal beat, or the section's start when the reveal came earlier) and the riser or fall,
and compares the fitted gains with stage gain x recipe gain. It reports the delay of every section's drums against the phase's: within one mix chunk (6 ms) they are on the grid.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "story"))
sys.path.insert(0, str(ROOT / "tools" / "content"))

import check_run_audio as cra  # noqa: E402
from arrange import load_recipes, recipe_gains  # noqa: E402

BEAT = cra.BEAT
CHUNK_MS = 6.0


def sections_of(entry: dict, arrangements: dict, phase_bars: int = 16) -> list[dict]:
    """The sections of a scene's phase, as RunData slices them (slot k = bars 16k+1..16k+16)."""
    arr = arrangements[entry["arrangement"]]
    total = int(arr["bars"])
    first = (int(entry.get("slot", 0)) * phase_bars) % total
    out, bar = [], 0
    for s in arr["sections"]:
        if first <= bar < first + phase_bars:
            out.append({"start_beat": (bar - first) * 4, "beats": int(s["bars"]) * 4, "pack": s["pack"], "mix": s["mix"]})
        bar += int(s["bars"])
    return out


def main() -> int:
    base = Path(sys.argv[1])
    music_path = Path(sys.argv[2])
    rec, rate = cra.read_pcm(base.with_suffix(".wav"))
    info = json.loads(base.with_suffix(".json").read_text())
    run = json.loads((ROOT / "content/run/run.json").read_text())
    music = {n["id"]: n for n in json.loads(music_path.read_text())["nodes"]}
    arrs = {p.stem: json.loads(p.read_text()) for p in (ROOT / "content/music/arrangements").glob("*.json")}
    recipes = load_recipes()
    stages = run["stages"]
    s0 = float(info["started_wall"])
    events = info.get("events", [])
    voices = info.get("voices", [])
    starts = [e for e in events if e["kind"] == "phase_start"]
    mixes = [e for e in events if e["kind"] == "mix"]
    loops: dict = {}

    def pack_loops(pid: str) -> dict:
        if pid not in loops:
            d = ROOT / "songs/packs" / pid
            pk = json.loads((d / "pack.json").read_text())
            loops[pid] = {k: cra.resampled(d / v, rate) for k, v in pk["stems"].items()}
        return loops[pid]

    fx = {k: cra.resampled(ROOT / "assets/run" / f"{k}.wav", rate) for k in ("riser", "fall")}
    gain_fx = 10 ** (run["effects"]["gain_db"] / 20.0)
    bad = 0
    phase_delays: list = []
    section_delays: list = []
    seen_switch = False
    print(f"recording {len(rec) / rate:.1f} s at {rate} Hz; song started at wall {s0:.3f}; {len(starts)} phases in the log")
    for ph in starts:
        node = music.get(ph["node"], {})
        if "arrangement" not in node:
            print(f"phase {ph['phase']} {ph['node']}: no arrangement, skipped")
            continue
        t0 = float(ph["t"])
        if s0 + t0 + 64 * BEAT > len(rec) / rate:
            break
        secs = sections_of(node, arrs)
        mine = [v for v in voices if v.get("node") == ph["node"] and t0 - 1e-6 <= float(v["target"]) < t0 + 64 * BEAT - 1e-6]
        drums = [v for v in mine if v["voice"] == "drums"]
        ok_voices = len(drums) == len(secs) and [v["pack"] for v in drums] == [s["pack"] for s in secs] and [v["section"] for v in drums] == list(range(len(secs)))
        print(f"phase {ph['phase']} {ph['node']}: {len(secs)} section(s) {[s['pack'] for s in secs]}; voice log: {len(drums)} drums voice(s) "
              f"{[(v['section'], v['pack']) for v in drums]} {'ok' if ok_voices else 'CHECK (one drums voice per section expected)'}")
        if not ok_voices:
            bad += 1
        reveal = None
        for e in events:
            if e["kind"] == "reveal" and t0 - 1e-6 <= float(e["t"]) < t0 + 64 * BEAT:
                reveal = float(e["beat"])
        a0 = int(round((s0 + t0) * rate))
        phase_delay = None
        for si, sec in enumerate(secs):
            lp = pack_loops(sec["pack"])
            sb = float(sec["start_beat"])
            a = int(round((s0 + t0 + sb * BEAT) * rate))
            seg = rec[a - int(0.3 * rate):a + int(8 * BEAT * rate)]
            d = cra.xcorr_delay(seg, cra.tiled(lp["drums"], a - int(0.3 * rate), len(seg), a), rate, 0.4)
            if si == 0:
                phase_delay = d
                phase_delays.append(d * 1000.0)
            else:
                seen_switch = True
                section_delays.append((d - phase_delay) * 1000.0)
            print(f"   section {si + 1} ({sec['pack']}, {sec['mix']}) starts beat {sb:g}: drums delay {d * 1000.0:+7.2f} ms" +
                  ("" if si == 0 else f" ({(d - phase_delay) * 1000.0:+.2f} ms from the phase's)"))
            rg = recipe_gains(sec["mix"], recipes)
            ad = a + int(round(d * rate))
            for b in range(int(sb // 16), int((sb + sec["beats"]) // 16)):
                mix = [m for m in mixes if t0 + b * 16 * BEAT - 1e-6 <= float(m["t"]) < t0 + (b + 1) * 16 * BEAT - 1e-6]
                if not mix:
                    continue
                stage = int(mix[0]["stage"])
                g = stages[stage]["gains"]
                skip = int(0.7 * rate)
                lo = a0 + int(round(phase_delay * rate)) + int(round(b * 16 * BEAT * rate)) + skip
                ln = int(16 * BEAT * rate) - skip - int(0.3 * rate)
                ms = int(round((b * 16 - sb) * BEAT * rate)) + skip  # the same instant counted from the section's start: where the loops are
                comps = {"drums": (lp["drums"], 0)}
                if reveal is not None and b * 16 >= reveal:
                    borigin = int(round((max(reveal, sb) - sb) * BEAT * rate))
                    comps["bass"] = (lp["bass"], borigin)
                    comps["other"] = (lp["other"], borigin)
                if b == 3:
                    eff = "riser" if stage == 3 else "fall"
                    comps[eff] = (fx[eff], int(round((48 - sb) * BEAT * rate)))
                y = rec[lo:lo + ln]
                shift = {k: 0 for k in comps}
                for _ in range(3):
                    m_ = np.stack([cra.tiled(comps[k][0], ms, ln, comps[k][1] + shift[k]) for k in comps], axis=1)
                    coef, *_ = np.linalg.lstsq(m_, y, rcond=None)
                    for ci, k in enumerate(comps):
                        resid = y - m_ @ coef + coef[ci] * m_[:, ci]
                        shift[k] += int(round(cra.xcorr_delay(resid, m_[:, ci], rate, 0.045 if k == "drums" else 0.03) * rate))
                fit = m_ @ coef
                expl = 1.0 - float(((y - fit) ** 2).sum() / ((y ** 2).sum() + 1e-12))
                names = list(comps)
                exp = {k: g[k] * rg[k] for k in names if k in g}
                exp.update({k: gain_fx for k in names if k in ("riser", "fall")})
                got = dict(zip(names, [round(float(c), 2) for c in coef]))
                ok = all(abs(got[k] - exp[k]) < 0.12 for k in exp) and expl > 0.9
                bad += 0 if ok else 1
                print(f"      block {b + 1} stage {stage} fitted {got}  expected {({k: round(v, 2) for k, v in exp.items()})}  explains {expl * 100:5.1f}%  {'ok' if ok else 'CHECK'}")
    worst = max((abs(x) for x in section_delays), default=0.0)
    spread = (max(phase_delays) - min(phase_delays)) if phase_delays else 0.0
    print(f"section drums delay from their phase's: worst {worst:.2f} ms over {len(section_delays)} switch(es) (one mix chunk is {CHUNK_MS:g} ms); phase delay spread {spread:.2f} ms")
    ok = seen_switch and bad == 0 and worst < CHUNK_MS
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
