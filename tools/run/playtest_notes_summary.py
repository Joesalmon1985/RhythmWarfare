#!/usr/bin/env python3
"""Which songs and visuals were disliked most, from a Debug / Playtest notes file (docs/DEBUG_MODE.md).

    python tools/run/playtest_notes_summary.py playtest_notes.jsonl [--top 10] [--json]

The game appends one JSON object per line to user://playtest_notes.jsonl each time a verdict button is pressed
(music_dislike, visual_dislike, like, note). This reads that file (or the .md beside it) and prints:

  * the totals,
  * the songs (packs) ranked by "Don't like the MUSIC", each with where it comes from (OWNER'S LOOP or a PLACEHOLDER),
    its stem files named as the owner's exports are, and the scenes it was heard in, with the likes it also got,
  * the same per owner's set (the stem file name without its Drums / Bass / Synth part, e.g. "Beat Shaper - C07"),
  * the visuals (map / view) ranked by "Don't like the VISUALS" with the scenes,
  * the scenes ranked by dislikes of either kind,
  * every typed note.

Only the standard library is used."""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

SOURCE_LABELS = {"owner": "OWNER'S LOOP", "owner_standin": "OWNER'S LOOP (stand-in, temporary)", "placeholder": "PLACEHOLDER (temporary)"}


def load(path):
    """The entries of a .jsonl notes file; a .md path reads the .jsonl beside it. A line that does not parse is skipped."""
    p = Path(path)
    if p.suffix == ".md":
        p = p.with_suffix(".jsonl")
    if p.is_dir():
        p = p / "playtest_notes.jsonl"
    entries = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            entries.append(v)
    return entries


def set_name(stems):
    """The owner's set name of a pack's stems: 'Beat Shaper - C07-Bass.wav' -> 'Beat Shaper - C07' (a placeholder has none)."""
    for key in ("bass", "drums", "other"):
        f = str(stems.get(key, ""))
        m = re.match(r"^(.*?)-(Drums|Bass|Synth)(?: \(\d+\))?\.\w+$", f)
        if m:
            tail = re.search(r"(\(\d+\))\.\w+$", f)
            return m.group(1) + (" " + tail.group(1) if tail else "")
    return ""


def summarise(entries):
    """Counters for the report (a plain dict, so --json and the tests can read it)."""
    out = {"total": len(entries), "verdicts": collections.Counter(e.get("verdict", "?") for e in entries),
           "songs": {}, "sets": {}, "visuals": {}, "scenes": {}, "notes": []}
    for e in entries:
        verdict = e.get("verdict", "")
        pack = e.get("pack_playing", "") or "(none)"
        scene = "%s/%s" % (e.get("run", "?"), e.get("scene", "?"))
        vis = e.get("visual", {}) or {}
        vkey = "%s / %s" % (vis.get("map", "?"), vis.get("view", "?"))
        if verdict in ("music_dislike", "like"):
            s = out["songs"].setdefault(pack, {"dislike": 0, "like": 0, "source": e.get("source", ""), "temporary": bool(e.get("temporary", False)), "stems": e.get("stems", {}), "scenes": collections.Counter()})
            s["dislike" if verdict == "music_dislike" else "like"] += 1
            if verdict == "music_dislike":
                s["scenes"][scene] += 1
            name = set_name(e.get("stems", {}) or {})
            if name:
                t = out["sets"].setdefault(name, {"dislike": 0, "like": 0, "packs": set()})
                t["dislike" if verdict == "music_dislike" else "like"] += 1
                t["packs"].add(pack)
        if verdict in ("visual_dislike", "like"):
            v = out["visuals"].setdefault(vkey, {"dislike": 0, "like": 0, "scenes": collections.Counter()})
            v["dislike" if verdict == "visual_dislike" else "like"] += 1
            if verdict == "visual_dislike":
                v["scenes"][scene] += 1
        if verdict in ("music_dislike", "visual_dislike", "like"):
            sc = out["scenes"].setdefault(scene, {"music": 0, "visual": 0, "like": 0})
            sc[{"music_dislike": "music", "visual_dislike": "visual", "like": "like"}[verdict]] += 1
        if verdict == "note" or e.get("text"):
            out["notes"].append({"ts": e.get("ts", ""), "scene": scene, "pack": pack, "text": e.get("text", "")})
    return out


def report(entries, top=10):
    s = summarise(entries)
    lines = []
    v = s["verdicts"]
    lines.append("Playtest notes: %d entries  (MUSIC -: %d, VISUAL -: %d, LIKE: %d, notes: %d)" % (s["total"], v.get("music_dislike", 0), v.get("visual_dislike", 0), v.get("like", 0), v.get("note", 0)))
    lines.append("")
    lines.append("SONGS disliked most (pack, dislikes / likes, where it comes from)")
    ranked = sorted((k for k in s["songs"] if s["songs"][k]["dislike"] > 0), key=lambda k: (-s["songs"][k]["dislike"], s["songs"][k]["like"], k))
    if not ranked:
        lines.append("  none")
    for k in ranked[:top]:
        d = s["songs"][k]
        stems = d["stems"] or {}
        lines.append("  %-28s %2d disliked / %d liked   %s" % (k, d["dislike"], d["like"], SOURCE_LABELS.get(d["source"], d["source"]) + ("" if not d["temporary"] or d["source"] == "placeholder" else " [temporary]")))
        if stems:
            lines.append("      files: %s | %s | %s" % (stems.get("drums", "?"), stems.get("bass", "?"), stems.get("other", "?")))
        lines.append("      heard in: %s" % ", ".join("%s (%d)" % (sc, n) for sc, n in d["scenes"].most_common()))
    if s["sets"]:
        lines.append("")
        lines.append("OWNER'S SETS (the file name without Drums / Bass / Synth: find them in the DAW)")
        for k in sorted(s["sets"], key=lambda k: (-s["sets"][k]["dislike"], s["sets"][k]["like"], k))[:top]:
            d = s["sets"][k]
            lines.append("  %-44s %2d disliked / %d liked   packs: %s" % (k, d["dislike"], d["like"], ", ".join(sorted(d["packs"]))))
    lines.append("")
    lines.append("VISUALS disliked most (map / view)")
    vr = sorted((k for k in s["visuals"] if s["visuals"][k]["dislike"] > 0), key=lambda k: (-s["visuals"][k]["dislike"], s["visuals"][k]["like"], k))
    if not vr:
        lines.append("  none")
    for k in vr[:top]:
        d = s["visuals"][k]
        lines.append("  %-34s %2d disliked / %d liked   scenes: %s" % (k, d["dislike"], d["like"], ", ".join("%s (%d)" % (sc, n) for sc, n in d["scenes"].most_common())))
    lines.append("")
    lines.append("SCENES by dislikes (music, visual) and likes")
    sr = sorted(s["scenes"], key=lambda k: (-(s["scenes"][k]["music"] + s["scenes"][k]["visual"]), -s["scenes"][k]["like"], k))
    for k in sr[:top]:
        d = s["scenes"][k]
        lines.append("  %-34s music -%d  visual -%d  like +%d" % (k, d["music"], d["visual"], d["like"]))
    if s["notes"]:
        lines.append("")
        lines.append("NOTES")
        for n in s["notes"]:
            lines.append("  %s  %s  %s: %s" % (n["ts"], n["scene"], n["pack"], n["text"]))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("notes", help="playtest_notes.jsonl (or the .md beside it, or the folder that holds them)")
    ap.add_argument("--top", type=int, default=10, help="rows per ranking (default 10)")
    ap.add_argument("--json", action="store_true", help="print the counters as JSON instead")
    a = ap.parse_args(argv)
    try:
        entries = load(a.notes)
    except OSError as e:
        print("cannot read %s: %s" % (a.notes, e), file=sys.stderr)
        return 2
    if a.json:
        s = summarise(entries)
        print(json.dumps(s, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else dict(o)))
    else:
        print(report(entries, a.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
