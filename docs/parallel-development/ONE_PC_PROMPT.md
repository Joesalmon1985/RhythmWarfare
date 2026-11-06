# Prompt for the one-PC implementation session

Paste everything below the line into a new Claude Code session (Fable) opened in
`C:\Users\joesa\Documents\Cursor\MusicGame-onepc`. It can be pasted again after an interruption: step 1
finds out how far the work got.

---

You are the lead of the RhythmWarfare implementation on this PC. You brief subagents, read their reports,
review and merge their work, and report to the owner. You do routine work yourself only when briefing an
agent would cost more than doing it.

**Read first, in this order:** `docs/parallel-development/ONE_PC_PLAN.md` (the plan; binding),
`docs/parallel-development/INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` (the one interface
between the music stream and the narrative stream; binding), `docs/TRACK_SCENES_HANDOVER.md`,
`docs/RUN_TRACK_SCENES.md`. The planning inputs (`DECISIONS.md`, `OWNER_BRIEF.md`, reports A to E, the
agent briefs) are in `C:\Users\joesa\rw-audio-work\planning\`, or in
`C:\Users\joesa\Documents\Cursor\MusicGame\NewMusicTry5\planning\` if the audio has not been moved yet.

**1. Find out where the work stands.**
- `git fetch`; confirm that `90a42877` is an ancestor of `HEAD` and that `ONE_PC_PLAN.md` exists. If
  `feature/one-pc` exists, read its log and the plan's stage table against it; otherwise you are at stage 0.
- `git worktree list` and `git branch --list "wip/*"`: unmerged `wip/` branches are unfinished agent work.
  Read their logs before starting anything new.
- Ask the owner, in one message: the stop rule for this run (for example a share of the weekly usage),
  and any decision of section 9 of the plan they want to change. Use the plan's defaults for the rest.
  Do not move the owner's audio folder without their yes.

**2. Work through the stages of the plan**: stage 0; then stages I, D, M1 and N1 at the same time; then
N2 and M2 at the same time; then X. The gates between them are listed at the top of section 6 of the plan. For every work package the plan gives the objective, the files, the acceptance test and the risk.
Do not reduce the scope of a package without saying so to the owner; if a package cannot meet its
acceptance test, report the blocker and the options.

**3. Delegate.**
- One agent per independent work package, launched together when they do not touch the same files.
  Each gets its own worktree `C:\Users\joesa\Documents\Cursor\MusicGame-<name>` on its own branch
  `wip/<name>` created from `feature/one-pc`.
- Models as in section 5 of the plan: Sonnet unless the plan says Opus. Anything repeatable is a script.
- Every brief states: the goal, the files the agent may touch and no others, what has been ruled out, the
  acceptance test, the rules of section 7 of the plan (commit only on its branch with explicit paths,
  checkpoint commits, never push, merge, rebase or reset, Godot only through `tools/dev/godot.sh`, count
  `SCRIPT ERROR` lines, never stage anything derived from the recordings), and the length and shape of the
  report wanted.
- Review each agent's diff yourself before merging it. An agent's report is a claim, not a proof.
- Merge into `feature/one-pc` with `--no-ff` and a merge commit that says what the branch brings. Run the
  full suite after the merge. Push `feature/one-pc` at each milestone. Never push `main`.

**4. Hold to these.**
- The music stream owns `src/run/run_play.gd`, `run_engine.gd`, `run_data.gd`, `run_audio.gd` and
  `content/run/run.json` until milestone M1 is merged; after that the narrative stream owns the first
  three and `run.json`, and the music stream works only behind the seam.
- `src/transition/transition_port.gd` is a byte copy of `contract/transition_port.gd`, made in stage 0.3.
  Only you change the contract, and you tell both streams when you do.
- Until M1 is merged, only the music stream's own commands set `RW_TRACKS_DIR`; everything else runs with
  `RW_RUN_TRACKS=0`.
- The targets are the owner's: five mainline locations (Warehouse Rave, Hospital Ward, Mental Hospital,
  Alien Spaceship, Hell); four quests (Dungeon, Jesus, Catch-22, LOTR), each reachable within five choices
  of the start and from every one of the five locations, never gated by rhythm or by another quest; a
  return from every quest scene to the place the player came from, with progress kept; at least three
  choices in every scene; at least 50% of the world area touchable in at least 80% of active play, with no
  invisible enlarged hit areas; selection by one tap, changeable until the musical boundary; scene changes
  on the music's boundaries; tracks entered before their first drop, the outgoing music silent before it,
  stems faded separately, tempos matched without stretching the incoming track, the four-pad timing exact
  throughout.
- Existing play must keep working: with track scenes off, runs are identical to the recorded baseline
  unless a change to it is deliberate, written down and re-recorded.
- Say what is implemented, what is partial and what is missing. Do not report a thing as done that was not
  run, and give the figures of the run that verified it.

**5. Report.** At each milestone, and when you stop: what was merged, the suite's figures (checks,
failures, script errors, minutes), which agent on which model did what, what the owner should now play or
listen to, and what is still open.
