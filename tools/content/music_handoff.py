"""Writes docs/MUSIC_HANDOFF.md: what every level (and the dungeon) plays now, what is still a placeholder and what to export next.

    python tools/content/music_handoff.py

The sheet is generated from content/run/run.json, content/story/music.json, content/trial/passages.json (its music entry, read only) and
songs/packs/*/pack.json + timing_report.json, so it cannot disagree with the game. The hand-written parts (the dungeon's suggested packs, the
sets still to export) live in the constants below.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_json  # noqa: E402
from beatshaper import resolve_music_node, scene_window  # noqa: E402

OUT = ROOT / "docs" / "MUSIC_HANDOFF.md"

# The dungeon plays one pack for every passage (content/trial/passages.json "music"). Ambient for the walk, the fight set for the fights.
DUNGEON = {"ambient": "dd_part1", "fight": "dd_part2",
           "ambient_alternates": ["dd_part1_v1", "dd_part1_v2", "dd_part1_v3"]}
# What a world still waits for (world id -> sentence). Anything not listed has its own final recording.
WAITING = {"underworld": "Lv3 Hell: the three WAVs are in `ToAddTry2/` but its three MIDI files are missing, so the importer cannot chart it. "
                         "Until then every scene of the Underworld plays arrangements of the Cold Fusion Interface family (dark, aggressive, 174 BPM; with Metaverse Ready Fusion "
                         "as a contrasting section) as the nearest match the catalogue offers."}
NOT_YET = [
    "**The paths:** the 17 Gospel scenes (124 BPM) and the 15 Ember scenes (145 BPM) still play synthesised placeholders; the prompts to give your music tool are in the section \"The three paths\" above (one per scene, 8-bar seamless loop, separate MIDI tracks). "
    "The 14 Squadron scenes already play your loops; if you re-export, C05 and C06 (thin bass) are the ones to look at first.",
    "`Lv3 Hell`: export `Beat Shaper - Lv3 Hell-Drums.mid` and `-Bass.mid` (the Synth MIDI is not needed). The WAVs are already there. "
    "Then: `python tools/content/beatshaper.py import NewMusic --set \"Lv3 Hell\" --id lv3_hell`, add `lv3_*` families to the Underworld palette's first position (`content/music/palettes.json` already lists `lv3_*`) and run `arrange.py generate underworld --seed N --bars 80 --id underworld_N --write` (docs/MUSIC_REPORT.md, \"Importing a new folder\").",
    "Optional: more `Lv1 Warehouse (n)`, `Lv2`, `Lv4`, `Lv5` takes: every pack of a family is one more loop for its arrangements (a new take only needs `beatshaper.py import` and a new `arrange.py generate`). "
    "The `DD Part1` variants are spare (the dungeon plays `dd_part1` and does not read arrangements).",
    "A dungeon fight set and ambient set are imported (`dd_part2`, `dd_part1`); if you want a different feel per zone, export more `DD ...` projects.",
]

PATH_ORDER = ["gospel", "squadron", "ember"]


def pack_status(pid: str) -> str:
    """One line: how the pack was measured at import (from timing_report.json), '' when the report predates the loosened importer."""
    rp = ROOT / "songs/packs" / pid / "timing_report.json"
    if not rp.exists():
        return "tempo strict (older import)"
    r = read_json(rp)
    t = r.get("timing", {})
    parts = [f"tempo {t.get('tempo_verified', 'strict')}"]
    bt = t.get("bass_timing")
    parts.append("bass " + (bt["mode"].replace("_", " ") if bt else "audio checked"))
    ir = r.get("import_report", {})
    dn = ir.get("drum_notes", {})
    if dn.get("mode") == "auto":
        parts.append(f"drum notes auto (kick {dn['kick']}, snare {dn['snare']})")
    return ", ".join(parts)


def paths_section(packs: dict) -> list[str]:
    """The three paths' shopping lists (content/paths/<id>/): placeholder scenes with the owner's prompt, imported scenes with their gains."""
    L = ["## The three paths (sister runs at their own tempo)", "",
         "Each path (`content/paths/<id>/run.json`, `docs/CONTINUOUS_RUN.md` \"Paths\") has its own tempo and its own packs (`songs/packs/<id>_*`, tagged `\"path\"`, never loaded by the 174 BPM run). "
         "A scene marked **placeholder** plays a synthesised stand-in (`tools/content/make_path_placeholders.py`, WAV not Ogg, bass-forward by measurement, never auditioned); drop the owner's export "
         "into `content/imports/<id>/<scene>/` and import it with `python tools/content/beatshaper.py --path <id> apply ...` (`docs/MUSIC_IMPORT.md` section 7), which replaces the pack and clears the flag. "
         "A loop at another tempo than the path's is refused, never stretched.", ""]
    for pd in sorted((ROOT / "content" / "paths").iterdir(), key=lambda d: (PATH_ORDER.index(d.name) if d.name in PATH_ORDER else 99, d.name)):
        rj, mj = pd / "run.json", pd / "music.json"
        if not (rj.exists() and mj.exists()):
            continue
        run = read_json(rj)
        info = run.get("path", {})
        if info.get("dev"):
            continue
        pid, bpm = info.get("id", pd.name), run["timing"]["bpm"]
        music = {n["id"]: n for n in read_json(mj)["nodes"]}
        report = {}
        rp = ROOT / "docs" / "paths" / f"{pid}_music_report.json"
        if rp.exists():
            report = read_json(rp).get("scenes", {})
        nodes = run["nodes"]
        temp = [n for n in nodes if music[n["id"]].get("temporary")]
        L += [f"### {info.get('title', pid)} (`{pid}`, {bpm} BPM, {len(nodes)} scenes, entered from `{info.get('entry_from')}`)", "",
              f"{len(temp)} of {len(nodes)} scenes are placeholders; {len(nodes) - len(temp)} play the owner's loops.", ""]
        if temp:
            L += ["| Scene id | Scene | Pack now | Status | The owner's prompt (verbatim) |", "| --- | --- | --- | --- | --- |"]
            for n in nodes:
                m = music[n["id"]]
                if m.get("temporary"):
                    L.append(f"| `{n['id']}` | {n['title']} | `{m['chart']}` | placeholder | {m.get('prompt', '(none recorded)')} |")
            L.append("")
        if len(temp) < len(nodes):
            L += ["| Scene id | Scene | Pack | Status | Gains drums / bass / synth (dB) | Import notes |", "| --- | --- | --- | --- | --- | --- |"]
            for n in nodes:
                m = music[n["id"]]
                if m.get("temporary"):
                    continue
                pk = packs.get(m["chart"], {})
                lp = pk.get("loops", {})
                g = " / ".join(f"{lp[k]['gain_db']:+g}" if k in lp and "gain_db" in lp[k] else "?" for k in ("drums", "bass", "other"))
                rep = report.get(str(pk.get("label", "")), {})
                note = pack_status(m["chart"])
                if rep.get("max_error_ms_required"):
                    note += f", needed --max-error-ms {read_json(rp).get('max_error_ms', 40)} (worst hit {rep.get('worst_error_ms', '?')} ms)"
                L.append(f"| `{n['id']}` | {n['title']} | `{m['chart']}` | owner's loops imported | {g} | {note} |")
            L.append("")
        if pid == "squadron":
            L += ["The Squadron loops are 16-beat (4-bar) phrases, not the 8 bars the prompts asked for; a 64-beat phase plays four laps, each with a new layer (`docs/CONTINUOUS_RUN.md` \"Paths\"). "
                  "`docs/paths/squadron_music_report.json` has the full measurements; the bass is thin in C05 and C06 (see `docs/HANDOVER.md`).", ""]
    return L


def main() -> None:
    run = read_json(ROOT / "content/run/run.json")
    music = {n["id"]: resolve_music_node(n) for n in read_json(ROOT / "content/story/music.json")["nodes"]}
    packs = {}
    for pj in sorted((ROOT / "songs/packs").glob("*/pack.json")):
        p = read_json(pj)
        packs[p["id"]] = p
    path_packs = {k: v for k, v in packs.items() if v.get("path")}
    packs = {k: v for k, v in packs.items() if not v.get("path")}  # the paths' packs are listed by `paths_section`
    trial_music = {}
    tj = ROOT / "content/trial/passages.json"
    if tj.exists():
        trial_music = read_json(tj).get("music", {})
    label = lambda pid: packs[pid]["label"] if pid in packs else pid  # noqa: E731
    worlds = {w["id"]: w for w in run["worlds"]}
    L = ["# Music handoff sheet", "",
         "Generated by `python tools/content/music_handoff.py` from the route map, `content/story/music.json` and the packs; regenerate after changing any of them. "
         "What every scene of every world plays today, what is still a placeholder, and what to export next. How to import: `docs/MUSIC_IMPORT.md`.", "",
         "## What each scene plays now", "",
         "A **world** is a small graph of **scenes**; each scene is one 64-beat phase at a place in the world and names an arrangement and a slot of it (`content/story/music.json`, one entry per scene; `content/music/arrangements/`). "
         "The arrangement's 16-bar window `slot` is what the scene plays: one 16-bar section or two 8-bar ones, each a pack of the arrangement's family with a mix recipe. The entry scene opens on the world's base pack, the exit scene ends on a drop and an ending. "
         "The pack named in the table is the first section's (the chart of block 0, what the route lock compares); the sections column lists the window, and `alternates` are the other arrangements the per-run seed may pick instead (same family, same slots). "
         "A scene plays tier min(depth, 4) of its chart pack (depth is per world). Sibling scenes offered "
         "in one route window that chart different packs fall under the route lock (the chart is fixed 3.5 beats before the phase ends and the other routes grey out). "
         "`bass` says how the bass cues were timed at import: *audio checked* (the audio agrees with the bass MIDI) or *midi fallback* (charted from the MIDI timing).", ""]
    for wid, w in worlds.items():
        sc = [n for n in run["nodes"] if n["world"] == wid]
        L += [f"### {w['title']} (`{wid}`, depth {w['depth']}, tier {min(int(w['depth']), 4)}, art world `{w['map']}`)", "",
              "| Scene id | Scene | Role | Routes to | Arrangement (slot) | Window (sections) | Alternates | Final? | Import notes |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for n in sc:
            m = music[n["id"]]
            same = m["audio"] == m["chart"]
            plays = f"`{m['arrangement']}` ({m['slot']})" if "arrangement" in m else (f"`{m['audio']}` ({label(m['audio'])})" if m["audio"] == m["chart"] else f"`{m['audio']}` / `{m['chart']}`")
            window = ", ".join(f"{x['role']} {x['bars']}: `{x['pack']}`" for x in scene_window(m)) if "arrangement" in m else f"`{m['audio']}`"
            alts = ", ".join(f"`{a}`" for a in m.get("alternates", [])) or "none"
            treat = f", treatment `{m['treatment']}`" if m["treatment"] != "none" else ""
            role = "entry" if n.get("entry") else "exit" if n.get("exit_scene") else "middle"
            routes = ", ".join(f"`{r['to']}`" + (" (loop)" if r.get("loop") else "") for r in n["next"])
            L.append(f"| `{n['id']}` | {n['title']} | {role} | {routes} | {plays}{treat} | {window} | {alts} | "
                     f"{'**nearest match**' if m['temporary'] else 'own music'} | {pack_status(m['chart'])} |")
        L.append("")
    waiting = [(i, WAITING[i]) for i in worlds if i in WAITING and any(music[n["id"]]["temporary"] for n in run["nodes"] if n["world"] == i)]
    if waiting:
        L += ["### Still a nearest match", ""] + [f"- `{i}`: {why}" for i, why in waiting] + [""]
    L += paths_section(path_packs)
    L += ["## What to export next", ""] + [f"- {s}" for s in NOT_YET] + [""]
    L += ["## The Deathtrap Dungeon", "",
          "The dungeon (`content/trial/passages.json`, `music` block) plays: "
          f"audio `{trial_music.get('audio')}`, chart `{trial_music.get('chart')}`"
          + (", treatment `%s`" % trial_music.get("treatment") if trial_music.get("treatment") not in (None, "none") else "")
          + (", temporary." if trial_music.get("temporary") else ".") + "", "",
          f"Imported and ready: **`{DUNGEON['ambient']}`** (`DD Part1`, the ambient set; variants {', '.join('`%s`' % v for v in DUNGEON['ambient_alternates'])}) and "
          f"**`{DUNGEON['fight']}`** (`DD Part2`, the fight set). Suggested assignment, to be wired by whoever owns `content/trial/`:", "",
          "```json",
          '"music": {"audio": "%s", "chart": "%s", "treatment": "none", "temporary": false}' % (DUNGEON["ambient"], DUNGEON["ambient"]),
          "```", "",
          f"The dungeon engine plays one pack at a time; if it is taught to switch for fights, use `{DUNGEON['fight']}` for the fight phrases "
          f"(it is a 174 BPM, 16-beat-phrase set; `{DUNGEON['ambient']}` is 87 BPM x2, 32 beats). Both validate "
          "(`python tools/content/beatshaper.py validate` also checks that the pack named in `passages.json` exists).", ""]
    L += ["## Packs in the repository", "",
          "| Pack id | Source | Profile | Phrase | Import | Used by |", "| --- | --- | --- | --- | --- | --- |"]
    in_use = {p["source"]["project"] for pid, p in packs.items() if any(pid in m["packs"] for m in music.values())
              or pid in (trial_music.get("audio"), trial_music.get("chart"), DUNGEON["ambient"], DUNGEON["fight"])}
    for pid, p in packs.items():
        used = [f"`{i}`" for i, m in music.items() if pid in m["packs"]]
        used = [", ".join(used[:6]) + (f" and {len(used) - 6} more" if len(used) > 6 else "")] if used else []
        if trial_music.get("audio") == pid or trial_music.get("chart") == pid:
            used.append("dungeon (now)")
        if pid in (DUNGEON["ambient"], DUNGEON["fight"]) and "dungeon (now)" not in used:
            used.append("dungeon (suggested)")
        src = p["source"]
        L.append(f"| `{pid}` | {src['project']}{' (%d)' % src['variant'] if src['variant'] else ''} | {p['profile']} | {p['phrase_beats']} beats | {pack_status(pid)} | "
                 f"{', '.join(used) or ('spare (an alternate take)' if src['project'] in in_use else 'imported, not in any scene yet')} |")
    L += ["", "`cold_fusion` (+ `_v1` to `_v3`, `Cold Fusion Interface`, 174 BPM, 16-beat phrase) and `meta_fusion` (+ `_v1`, `Metaverse Ready Fusion`, 174 BPM, 32-beat phrase) come from "
          "`ToAddTry3/Cold` and `ToAddTry3/Meta`; the Underworld's arrangements play them (docs/MUSIC_REPORT.md; `docs/MUSIC_CATALOGUE.md` has their measured facts). "
          "The Ableton renders of the same folders are loop-library clips (`content/imports/cold_meta.json`), not packs.", ""]
    L += ["Not imported from `ToAddTry2/`: `Default Project` (an unedited template of the Warehouse groove) and `Lv3 Hell` (audio only, no MIDI: see above).", ""]
    L += ["## Format reminder", "",
          "- One **set** per level: `Beat Shaper - <project>-Drums`, `-Bass` and `-Synth`, each as **.wav and .mid**. Variants keep the ` (1)`, ` (2)` suffix on all three files.",
          "- **Needed:** Drums.wav/.mid and Bass.wav/.mid. A missing Synth is imported as a silent backing; the Synth MIDI is never read.",
          "- **Length:** 16 quarter notes; rendered at 87 BPM (32-beat phrase) or 174 BPM (16-beat phrase); the importer measures which. A MIDI that ends a quarter short or long is fine.",
          "- **Drum MIDI:** kick 36, snare 38/40; when none of those are present the most common low and mid notes (hats skipped) are used and the choice is reported. `--kick`/`--snare` override.",
          "- **Bass MIDI:** every note is a hold on a pad chosen by pitch; if the audio and the MIDI disagree on timing the MIDI wins, with a warning (`--trust-midi` forces it).",
          "- Check a folder before importing: `python tools/content/beatshaper.py survey NewMusic`.", ""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
