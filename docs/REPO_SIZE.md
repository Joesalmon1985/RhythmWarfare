# Repository size and build size

Measured on 5 November 2026 at `710a96a5` (the starting point of this work) and after the changes of this document (branch `paths-size`).
Part 1 covers everything except the audio packs under `songs/packs/` (Part 2, below). No history was rewritten and no file that the game or the tests read was deleted.

## 1. Numbers

| What | Before | After | Saved |
| --- | --- | --- | --- |
| Tracked files at `HEAD`, raw | 17 456 files, 933.7 MiB | 16 985 files, 894.2 MiB | 39.5 MiB, 471 files |
| The same, unique blobs packed | 531.5 MiB | 509.8 MiB | 21.7 MiB |
| Exported pack (`--export-pack "Windows Desktop"`) | **611 MB (581 MiB), and broken** | **240 MB (227 MiB), starts and loads every run** | 371 MB, 61 % |
| `.git` on this machine (`git count-objects -vH`, all branches of all worktrees) | 852 MiB | see section 5 | grows, see 5 |

"After" counts only Part 1. The packs (443 MB raw in the tree, 87 MiB of the 227 MiB pack) are Part 2.

### What was in the repository (HEAD `710a96a5`)

| Folder | Raw MiB | Note |
| --- | --- | --- |
| `songs/packs` | 442.9 | 74 packs: Gospel 17, Ember 15, Squadron 14, `stub` 2, the owner's Ableton packs 26 (Part 2) |
| `docs/shots` | 228.5 | 656 proof screenshots; 5 are linked from a document |
| `content/library` | 79.6 | the owner's loop renders (`.wav`), the source of `songs/library` and the packs |
| `assets/story` | 64.6 | art: baked people sheets (`people/`, about 44 MiB), textures, SVG rig parts (`source/`) |
| `ToAddTry1` | 31.1 | the owner's first Ableton drop (the source of mission 1) |
| everything else | about 50 | `songs/story_*` Ogg, `songs/library`, `assets/openra`, `pixelexample` 7.3 |

By type: `.wav` 561 MiB (302 files), `.jpg` 203 MiB (562), `.png` 88 MiB (5 938), `.ogg` 53 MiB, `.import` 7 MiB (7 893 files), the rest small.

Largest tracked blobs (raw): `docs/shots/faces/mothership_after.jpg` 8.3 MiB, then seven more face sheets of 6 to 7.5 MiB, `docs/shots/dance/flair_moves.jpg` 4.7, three `content/library` WAVs of 4 MiB, `ToAddTry1/Other1.wav` 3.3, then the placeholder stems at 2.84 MiB each. Nothing is near 100 MB.

Identical files: 134 files over 5 KB share a hash with another (154.8 MiB raw, 42 groups), but git stores each blob once, so the packed size already does not pay for them. 138 MiB of the 154.8 are pack stems (the Gospel and Ember placeholders repeat `bass.wav` and `other.wav` across scenes; Part 2); 17 MiB are other WAV and library copies; the non-audio duplicates (room textures, two shots) are under 3 MiB in all. Nothing to remove.

### Where history carries the weight (all branches, packed 860 MiB, 21 907 blobs; 531 MiB are blobs of `HEAD`, 328 MiB are history only)

| Path | Packed in history | of which still at `HEAD` |
| --- | --- | --- |
| `docs/shots/**` | 263 MiB | 189 MiB |
| `assets/story/*/people/**` (the baked sheets, rebuilt many times) | 237 MiB | 49 MiB |
| `songs/packs/` placeholders (`gospel_`, `ember_`, `stub_`) | 87.5 MiB | 87.5 MiB |
| `songs/*/audio/**` (old mission Ogg, long gone from `HEAD`) | 52 MiB | 1 MiB |
| `songs/packs/` the owner's Ableton packs (cold, dd, lv, meta, squadron) | 86 MiB | 86 MiB |
| `content/library/**` | 37 MiB | 37 MiB |
| `ToAddTry*`, `pixelexample`, `assets/trial` | 32 MiB | 27 MiB |

(Each blob is counted under the first path git lists for it; the rows overlap a little through the shots.) Two paths account for 500 MiB of the 860: the proof shots and the people sheets' history.

## 2. The export

### Before: a 611 MB pack that could not start a run

`export_filter="all_resources"` with no filter packed everything Godot imports, **and nothing it ignores**. Measured with `--export-pack` and `tools/pck_list.py` / `tools/pck_origin.py` (the pack by source folder):

* **346 MiB were `docs/shots`**, every proof screenshot imported as a lossless texture (476 tracked `.import` files were what made Godot import them), `pixelexample` 6 MiB, `songs/packs/stub_*` 3 MiB, the tests' compiled scripts.
* **`content/` was missing.** `content/.gdignore` kept it out of the exporter's scan, and with it `content/run/run.json`, `content/story/*`, `content/music/*`, `content/paths/*`, `content/trial/*`, `content/duel/*`. Run from the exported pack, `RunData.load_default()` fails with "res://content/run/run.json not found", there are no path folders and no story chapters (`tools/export_smoke.gd` prints exactly that for the old pack). Any build made from these presets since the run and the story were added could not have started them.

### After

`export_presets.cfg` (both presets, same filter) and three `.gdignore` moves:

| Change | Why |
| --- | --- |
| `content/.gdignore` moved to `content/library/` and `content/fixtures/` | the run data must be exported; only the WAV sources (`library`, 80 MB) and the replacement-test fixtures need hiding from the importer |
| `docs/.gdignore`, `pixelexample/.gdignore`; their 479 `.import` files removed | nothing loads them (`grep res://docs` in `src`, `tests`, `tools`: no hit). The shots tools write with absolute paths and never read back. Godot no longer imports 350 MiB of screenshots and leaves no `.import` clutter beside new shots |
| `exclude_filter`: `docs/*, tests/*`, `tools/*` except `tools/autoplay.gd` (loaded by `StoryRun.autoplay`, `RW_`-driven play), `campaign/*, midi_export/*, pixelexample/*, ToAddTry1/*` | not runtime |
| `content/library/*, content/fixtures/*, content/imports/*, content/missions_legacy/*, content/build_state.json` | build inputs of `tools/content`, not read by `src` |
| `content/paths/stub/*, songs/packs/stub_*, songs/test_16/*` | the stub path and the test pack exist for `tests/test_run_paths.gd` and `test_run_matrix.gd`; no player reaches them |
| `*.md, *.mid, *.zip, *.py, *.sh` | MIDI is written by the content tools and never read by `src` (`grep -i midi src`: only variable names); the zip is the owner's hand-off |

Verified by `tools/export_smoke.gd`, run against the pack alone from a folder that is not a project:
`GODOT --headless --main-pack <pack.pck> -s <repo>/tools/export_smoke.gd`. It loads the main run and the three paths with `RunData` (0 errors; 26, 15, 17, 14 packs; every stem resolves as an imported resource: 78 + 45 + 51 + 42), the five story chapters, the duel rules, the loop library, the campaign data, the main scene and `tools/autoplay.gd`. Old pack: 3 failures. New pack: 0.

Result (`--export-pack "Windows Desktop"`, throwaway folder outside the repo):

| | Before | After |
| --- | --- | --- |
| Pack | 611 023 444 bytes (581.1 MiB), 16 439 files | 239 535 164 bytes (226.9 MiB), 15 434 files |
| `docs/shots` | 346.0 MiB | 0 |
| `content/` | **absent** | about 2 MiB |

What the 227 MiB is: `songs/packs` 86.9 (Part 2), `assets/story` 74.4 (lossless textures, see below), the story and mission Ogg about 56, `songs/library` 9.8, `assets/openra` 3.4, the rest (scripts, data, `.import`, `uid_cache`) under 10.

ANDROID_LINE

### Import options (checked, left as they are)

Counted over the 7 414 tracked `.import` files: 6 975 textures are `compress/mode=0` (lossless) with `mipmaps/generate=false`; 227 WAVs are `compress/mode=2` (QOA, about 4:1; the loop length in frames is kept, and it is the mode the loop packs were tested with); 212 Ogg files are imported as `oggvorbisstr` (no re-encode). Pixel art stays lossless: VRAM compression (ETC2/ASTC, `import_etc2_astc=true` is already set for any texture that asks for it) would smear single-pixel detail and the people sheets are R8 index images, which VRAM formats cannot store. Mipmaps are already off everywhere. Nothing to tighten; the remaining export bulk is audio (Part 2) and the baked people sheets (about 40 MiB in the pack).

Not done: 24 SVG pieces in `assets/story/*/source/views/` (the removed 2D rooms; their names appear in no manifest) are rasterised into the pack, about 3 MiB. Left because the art is under polish by another agent; a later `exclude_filter` entry `assets/story/*/source/views/*` after a check against the manifests would take them out.

## 3. Repository changes of Part 1

| Change | Saves (HEAD, raw) |
| --- | --- |
| 479 `.import` sidecars of `docs/` and `pixelexample/` removed | 0.5 MiB, and no import of 350 MiB |
| 12 face, figure and flair sheets in `docs/shots` halved (4x pixel zoom instead of 8x; `tools/shrink_shots.py`) | 39.1 MiB (65.9 to 26.8) |

`tools/shrink_shots.py` is idempotent and conservative: PNG screenshots were tried as 256-colour palettes (25 MiB to 7.5 MiB) but none of the 77 screenshot PNGs over 60 KB kept a 38 dB match against the original at 256 colours (smooth light and glow gradients band), so they stay; JPEGs that are already near their size stay. PNGs under runtime art were not touched: a byte-identical pixel re-encode with Pillow (`optimize=True`, level 9) saves 1.3 % on a 150-file sample (the generators already optimise), not worth 5 938 changed blobs.

Left, with reasons:

* **Regenerable artefacts git-ignored: none.** The candidates are the baked people sheets (`assets/story/*/people`, about 44 MiB) and the Gospel/Ember placeholder packs (87 MiB). Both are rebuilt by a documented, deterministic command (`python3 tools/story/build_assets.py <chapter> people`; `python3 tools/content/make_path_placeholders.py <path> --force`), but the game, `tools/test.sh` and the walks fail on a fresh clone until those have run, there is no CI to run them, and another agent is regenerating both right now. Adding a pre-step to `tools/test.sh` and the ignore entries is a decision for after Part 2 (it also needs the placeholders' tracked `.import` files to be generated: Godot writes them on `--import`, which `tools/test.sh` already runs).
* **Duplicates:** none worth dropping (see above).
* **Source art next to processed art:** `assets/story/*/source` is not source-only: the manifests load it (rig parts, props, pieces) and it is imported as a texture, so it stays. `content/library` WAVs (80 MB) and `ToAddTry1` (31 MB) are the owner's renders and cannot be regenerated; they are already outside the export.
* **Proof shots:** the remaining 640 images (about 160 MiB) are mostly at the size their tools write them. Only 5 are linked from a document. See the recommendation.

## 4. History does not shrink: the rewrite option (reported, not run)

Shrinking files at `HEAD` adds the new, smaller blobs to history **without removing the old ones**. A clone made today still downloads every old version; the 12 halved sheets add about 11 MiB to `.git` (new blobs) while the checkout shrinks by 39 MiB. Only a history rewrite takes bytes out of `.git`.

What it would save (packed, from the table above; each row is independent of the others):

| Rewrite | Removes from history | Notes |
| --- | --- | --- |
| Drop `docs/shots/**` from all history, keep a small curated set (the 5 linked images and a few contact sheets) re-added in one new commit | about 255 MiB | shots are regenerable by the capture scripts (they need a display); keep them out of git or in a release asset |
| Drop `assets/story/*/people/**` from history and re-add the current sheets | about 188 MiB (237 less the 49 at `HEAD`) | the sheets are rebuilt by `tools/story/build_assets.py`; each rebuild added a new 10 MiB blob per chapter |
| Drop `songs/*/audio/**` (old missions' Ogg, long deleted) | about 51 MiB | |
| All three | about 490 MiB of 860 | leaves about 370 MiB |

Commands (not run; do it on a fresh mirror clone, never in a working checkout):

```
pip install git-filter-repo                   # or put git-filter-repo on PATH
git clone --mirror https://github.com/<owner>/<repo>.git rw-mirror.git
cd rw-mirror.git
# measure first
git filter-repo --analyze && sort -k2 -n -r filter-repo/analysis/path-all-sizes.txt | head -40
# the rewrite (paths removed from every commit on every ref)
git filter-repo --invert-paths \
    --path docs/shots/ \
    --path-glob 'assets/story/*/people/*' \
    --path-glob 'songs/*/audio/*'
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git count-objects -vH                          # the new size-pack
# then, in a normal clone of the rewritten repo: rebuild what was removed and commit it as new history
python3 tools/story/build_assets.py && python3 tools/shrink_shots.py
git add assets/story docs/shots && git commit -m "Re-add the baked sheets"
git push --force --mirror origin               # only after every collaborator has agreed (below)
```

BFG equivalent for the shots only: `java -jar bfg.jar --delete-folders shots --no-blob-protection rw-mirror.git`, then the same `reflog expire` and `gc` (BFG deletes by name everywhere, including `HEAD` unless protected, which is why the filter-repo form with a re-add commit is clearer).

Risks:

* Every commit hash changes. All clones (the owner's `MusicGame`, the Android checkout `DuelMasterBattle`, every worktree: `MusicGame-face`, `-merge`, `-paths`, `-paths2`, `-pretest`, `-size`) must be re-cloned or hard-reset onto the new history; any uncommitted or unpushed branch work has to be rebased onto it by hand (`git rebase --onto`), and the open branches `feature/*` (face-polish, wizard-duel-lan, story-warehouse-music-test, continuous-story-run, deathtrap-opening, visual-adventure, look-pass, run-on-25d, music-library, story-25d) would all be rewritten too (`filter-repo` rewrites every ref; each must be force-pushed).
* Anything that cites a commit hash (docs, `HANDOVER.md`, `docs/*_PLAN.md`, the commit hashes in progress logs such as `56adc157`, `5efcfd2`) will point at nothing; a `.git/filter-repo/commit-map` file records old to new.
* GitHub keeps the old objects reachable by the old hashes (pull-request refs, caches) until GitHub Support runs a gc; the size on the server does not fall at once.
* It is not needed to stay under GitHub's limits today (the largest file is 8.3 MiB, the repository about 0.85 GiB). It is a convenience (clone time) and the first step of Git LFS if the owner's real loops arrive.

## 5. Recommendation

1. **Keep what Part 1 did:** it fixes a build that could not run and cuts the pack by 61 %; the repository changes are small and safe.
2. **Do not rewrite history yet.** Wait until the audio packs are final (Part 2) and the visual work has stopped producing new shots and sheets; one rewrite, once, then.
3. **Stop adding proof shots to git.** The shots are 30 % of the repository and 5 of 656 are linked. Keep them in `docs/shots` locally (they are produced by the capture scripts), commit only the few a document links to, and run `python3 tools/shrink_shots.py` before committing any. If the owner agrees, `docs/shots/` can go into `.gitignore` (not done: other agents commit their shots there).
4. **Rebuilding the people sheets** adds about 10 MiB of history per chapter each time; commit them once per art milestone, not per tweak.
5. **Before the next real build,** run `tools/export_smoke.gd` against the pack (command in section 2); it is the only check that the exported data matches what the game loads.

## 6. How to reproduce the measurements

```
GODOT="C:/Users/joesa/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"
"$GODOT" --headless --path . --import
"$GODOT" --headless --path . --export-pack "Windows Desktop" /tmp/rw.pck      # a folder outside the repo; about 2 minutes
python3 tools/pck_list.py /tmp/rw.pck --top 40                                 # by folder and by type
python3 tools/pck_origin.py /tmp/rw.pck --depth 3                              # the imported payload by the source folder it came from
cd /tmp && "$GODOT" --headless --main-pack /tmp/rw.pck -s <repo>/tools/export_smoke.gd
```

## Part 2 (audio packs)

Not started in this document; added when the packs are final.
