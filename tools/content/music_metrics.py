"""Before/after music metrics for docs/MUSIC_REPORT.md.

    python tools/content/music_metrics.py [--before <git rev>]   (default: the commit before the populate step, 41016a9b)

Prints: playable variations per scene and per chapter, source WAV files used of the files available (the catalogue's `used_by`), and asset size on disk
(songs/ in the working tree, and the part under git at the `--before` revision). "Playable variation" = a distinct sequence of packs a scene's 16-bar window can play
(the arrangement and its alternates; a plain scene has one), "variations of a chapter" = the music_packs it lists.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beatshaper import resolve_music_node, scene_window  # noqa: E402
from common import ROOT, read_json  # noqa: E402

CHAPTERS = ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def old_nodes(rev: str) -> list[dict]:
    return json.loads(git("show", f"{rev}:content/story/music.json"))["nodes"]


def variations(node: dict) -> list[tuple]:
    if "arrangement" not in node:
        return [(node["audio"],)]
    out = []
    for a in [node["arrangement"], *node.get("alternates", [])]:
        seq = tuple(f"{s['pack']}:{s['role']}" for s in scene_window(node, a))
        if seq not in out:
            out.append(seq)
    return out


def used_files(packs: set[str], cat: dict) -> set[str]:
    return {f["id"] for f in cat["files"] if f["kind"] == "wav" and any(u["type"] == "pack" and u["id"] in packs for u in f.get("used_by", []))}


def tree_size(rev: str | None) -> int:
    if rev is None:
        return sum(p.stat().st_size for p in (ROOT / "songs").rglob("*") if p.is_file())
    total = 0
    for line in git("ls-tree", "-r", "-l", rev, "songs").splitlines():
        total += int(line.split()[3])
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default="41016a9b")
    args = ap.parse_args()
    cat = read_json(ROOT / "content" / "music" / "catalogue.json")
    new = [resolve_music_node(n) for n in read_json(ROOT / "content" / "story" / "music.json")["nodes"]]
    old = [dict(n, packs=[n["audio"]]) for n in old_nodes(args.before)]
    trial = read_json(ROOT / "content" / "trial" / "passages.json").get("music", {})
    trial_packs = {trial.get("audio"), trial.get("chart"), trial.get("fight_audio"), trial.get("fight_chart")} - {None}
    print("scene | before (packs, variations) | after (packs, variations)")
    tb = ta = 0
    for o, n in zip(old, new):
        vo, vn = variations(o), variations(n)
        tb += len(vo)
        ta += len(vn)
        print(f"{n['id']:22s} | {len(o['packs'])} pack, {len(vo)} | {len(n['packs'])} packs, {len(vn)} ({n.get('arrangement')} slot {n.get('slot')})")
    print(f"scenes: {len(new)}; variations summed over scenes: before {tb}, after {ta}")
    for ch in CHAPTERS:
        raw = read_json(ROOT / "content" / "story" / f"{ch}.json")
        listed = raw.get("music_packs", [raw["music_pack"]])
        before = 2 if ch == "mothership" else 1
        print(f"chapter {ch}: before {before} version(s), after {len(listed)}")
    pb = {p for n in old for p in n["packs"]} | trial_packs
    chapter_packs = {sec["pack"] for f in (ROOT / "content" / "music" / "arrangements").glob("ch_*.json") for sec in read_json(f)["sections"] if "pack" in sec}
    pa = {p for n in new for p in n["packs"]} | trial_packs | chapter_packs
    fa = len([f for f in cat["files"] if f["kind"] == "wav"])
    ub, ua = used_files(pb, cat), used_files(pa, cat)
    print(f"packs played by scenes, the rendered chapters and the dungeon: before {len(pb)}, after {len(pa)} of {len(list((ROOT / 'songs' / 'packs').glob('*/pack.json')))}")
    print(f"source WAVs behind those packs: before {len(ub)}, after {len(ua)} of {fa} available in the catalogue")
    spare = sorted(p.parent.name for p in (ROOT / 'songs' / 'packs').glob('*/pack.json') if p.parent.name not in pa)
    print("packs no scene plays:", ", ".join(spare))
    print(f"songs/ on disk: before {tree_size(args.before) / 1e6:.1f} MB (git {args.before}), after {tree_size(None) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
