# From the in-flight branches to a new `main`: the plan (7 November 2026)

Written after the weekly usage limit cut off seven agents on the evening of 6 November. It says what is
where, what it takes to finish and merge it, what to clean up, and when `main` can carry it all. Times are
wall-clock with the lead and subagents working in parallel; each full test suite is about 18 minutes.

## Where things stand

- `feature/one-pc` (tip `a0676e55`, pushed) is the integration branch. It is 138 commits ahead of
  `origin/main` and contains it (fast-forward possible). Last full suite on it: 149,148 checks, 0 failures,
  0 script errors (after the UI and blend merges); the later merges (Bassment art, camera clearance,
  Hospital art) were checked with their filtered groups only.
- Merged into it so far: music M1 and M2 (track scenes, DJ transitions), narrative N2.1 to N2.3 (selection,
  router, generator split), heralds and entrance visibility, art A1, A3, A4, A5, W1, W4, W9.
- `main` locally is 28 commits behind `origin/main` (no divergence). Nothing has been pushed to `main`
  since 6 November, as ruled.

### Branches still open (all pushed except where noted)

| Branch | State when cut off | Uncommitted in its worktree | Left to do |
|---|---|---|---|
| `wip/narr-n2-4-underworld` | finished, reported, shots reviewed | none | merge |
| `wip/narr-n2-4-mothership` | entrances built, re-shooting the hub | graph exports + a test edit (4 files) | finish shots, report, merge (not pushed) |
| `wip/narr-n2-4-ward` | sent back: hub gates hidden by the crowd, two side gates behind walls | a late placement tweak (3 files) | the visibility fixes, re-shoot, report, merge |
| `wip/narr-n2-4-hospital` | mid-work, no commit yet | hospital table, hotspots, view test, shoot list (6 files) | finish, shoot, report, merge (not pushed) |
| `wip/narr-n2-5` (returns) | mid-work, no commit yet | 22 files changed, 5 new (8,000 lines: return rows in all path hotspots, `return_spots.gd`, `test_returns.gd`) | finish, test, report, merge (not pushed) |
| `wip/art-a6` (wall decals) | engine done, Hospital converted, shots committed | none | report, review, merge (not pushed) |
| `wip/art-w6` (Gospel) | sent back: daylight dimmed to dusk; re-work in progress | 60 files (textures, maps, two generators) | finish daylight, 20:9 check, report, merge |
| `wip/art-w7` (Squadron) | finished the art, was waiting on its full suite | none | report, review, merge (not pushed) |

Shared work no location agent could do, to be done once after the four N2.4 branches are in:
hub-to-hub links and "way back to the hub" routes (`tools/run/make_scenes.py` S table, a `RunData` rule
letting a hub reach another hub, `max_hotspots` 10 on hubs), the pinned tests (`tests/test_heralds.gd`
`ENTRANCES`, `tests/test_narrative_run.gd` `fixture_rows()`, the graph exports and their count tests), and a
wall test in `tests/test_heralds_view.gd` (it projects points but does not see walls or the crowd). Then the
Warehouse hub's own four entrances (the Floor: an ungated Dungeon hatch and the three copies).

## Phase 0: keep what was cut off (about 1 hour)

1. In each dirty worktree, commit the uncommitted work as a `WIP:` checkpoint on its branch and push the
   branch (five worktrees; `tests/test_zz_scan.gd` in the Hospital worktree looks like scratch: keep it out).
2. Resume each cut-off agent with a message (their transcripts are kept) rather than starting fresh.

## Phase 1: finish and merge the in-flight branches (about 1 working day)

In parallel, each in its own worktree:

| Package | Agent time | Lead time (review, merge, filtered tests, push) |
|---|---|---|
| N2.4 Hell | done | 0.5 h |
| N2.4 Alien Spaceship | 1 to 2 h | 0.5 h |
| N2.4 Mental Hospital (visibility) | 2 to 3 h | 0.5 h |
| N2.4 Hospital | 2 to 3 h | 0.5 h |
| N2.5 Returns | 2 to 4 h | 1 h |
| A6 Wall decals | report only | 1 h (engine change: read the diff, full suite) |
| W6 Gospel daylight | 2 to 3 h | 0.5 h |
| W7 Squadron | report only | 0.5 h |

Then, one after the other on the merged head:

| Step | Agent time | Lead time |
|---|---|---|
| Shared wiring (hub links, ways back, pinned tests, wall test in the view test) | 3 to 4 h | 1 h incl. full suite |
| Warehouse hub entrances (Floor) | 2 to 3 h | 0.5 h |
| Full suite, walks, `check_hotspots`, graph validator, coverage audit on the final head | | 1 h |

Expected merge conflicts, all small: `tests/test_heralds_view.gd` `ROUTES` blocks, `tools/story/shoot_heralds.sh`
(each agent added a comment-skip line), the identical `check_hotspots.py` fix on four branches, the graph
export files, `content/run/run.json` (regenerate, never hand-merge).

## Phase 2: housekeeping (about 2 to 3 hours)

- Delete the 40 local branches already merged into `feature/one-pc` (survey list A) and the eight stale
  worktrees that hold them (`MusicGame-bj`, `-face`, `-look`, `-merge`, `-paths`, `-paths2`, `-pretest`,
  `-size`). Keep `MusicGame` (the owner's checkout), `MusicGame-onepc` and the six agent worktrees.
- Fast-forward local `main` to `origin/main`.
- Propose to the owner which merged remote branches to delete on GitHub (13 `origin/feature/*` and
  `origin/wip/*` already in `main` or `feature/one-pc`); the two unmerged `origin/wip/blackjack-polish-a/-c`
  are unverified WIP from a crashed session: keep or drop on the owner's word.
- Repo weight: `.git` is 1.3 GB; `docs/shots/` on the branch is 1,073 files, 270 MB. No history rewrite.
  Going forward: one shrunk contact sheet per package, old per-frame shots of superseded audits removed in a
  commit. The three 4 MB `content/library/*.wav` backing loops and `ToAddTry1/*.wav` are old audio already on
  `origin/main`; the 61 new recordings' packs are not in Git and stay out (they ship inside the APK).
- Docs: rulings 34 onward (A3, A5, W4, W9, N2.2, M2.4 merged; the daylight rule; the decal rule; the
  view-test limit), `docs/HANDOVER.md` and the game guide brought up to the merged state (M1.8).
- Dev hygiene: commit the generated `.uid` files of the tools that lack them, so worktrees stay clean.
- The owner's checkout shows `Rhythm_Warfare_Level_01_MIDI.zip` deleted in the working tree: restore it or
  commit the deletion, the owner's call.

## Phase 3: `main` (half a day, plus the owner's play and listen)

1. Final head of `feature/one-pc`: full suite green, 0 script errors; walks OK; `check_hotspots` 0 errors;
   graph validator 20 of 20 cells; coverage audit figures recorded (reactive objects, N2.6, are not in this
   round, so touch coverage will still be under the 50% target: written down as the known gap).
2. The owner plays a run with `tools\dev\play_tracks.cmd` and listens to the transitions with
   `tools\dev\hear_transition.cmd` (M2.6). Anything that sounds or looks wrong is fixed on `feature/one-pc`.
3. On the owner's word: `main` fast-forwards to `feature/one-pc` (or a `--no-ff` merge commit, one line
   naming the features), tagged, pushed. Not before.

## Phase 4: ready for new work (1 hour)

- Fresh `wip/` branches from `main` for the next packages, the plan's remaining rows re-listed in
  `ONE_PC_PLAN.md`: N2.6 reactive objects (coverage), N2.7 people re-bake, art W2 Mothership, W3 Underworld,
  W5 Ward, W8 Ember, A2 people, the final `audit_capture.sh all` pass against the audit, M1.8 docs, and
  stage X: the Android APK with the re-encoded tracks bundled, phone measurements.

## Total

About two working days of wall-clock if the usage limit holds: day 1 finishes and merges everything above;
day 2 is housekeeping, the final checks and the owner's play; `main` moves when the owner says so.
Three days if the limit cuts in again or the Gospel/returns agents need a second round.

## Risks

- The weekly usage limit: the lead keeps at most four agents running at once in this round, Sonnet for
  content and docs, Opus only for the shared wiring and the decal review.
- Windows audio: Godot's WASAPI output stopped opening on this PC during the blend work; the owner's listen
  will show whether it is back. Two transition measurements were made on the silent driver only.
- No phone has run any of this yet; multi-touch and 20:9 are proven in headless shots only.
