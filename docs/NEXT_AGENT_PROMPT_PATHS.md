> **Status (5 November 2026): all six stages are done and pushed.** This prompt is kept for history. The current state, what was verified and the open decisions are in `docs/HANDOVER.md`.

# Prompt for the local agent: three paths and faces (paste everything below the line into a new session)

Intended for a Claude session started in `C:\Users\joesa\Documents\Cursor\MusicGame` on the owner's PC, on the `main` branch of
https://github.com/Joesalmon1985/RhythmWarfare.

---

You are continuing Rhythm Warfare, a Godot 4.5.1 phone rhythm game in this folder. Your job is to execute `docs/THREE_PATHS_AND_FACES_PLAN.md` on
`main`, stage by stage, keeping the game playable and the tests green at every commit. The plan makes every design decision (its section 1); do not re-ask
them. Where you must diverge, say so in the commit message and in `docs/HANDOVER.md`.

Read, in this order: `docs/THREE_PATHS_AND_FACES_PLAN.md` (all of it), then the files its section 0 lists. The "Working rules" of `docs/NEXT_AGENT_PROMPT.md`
still describe this machine (the Godot console binary, Python, `bash tools/test.sh`); its stage list is obsolete.

Working rules:

- Work on `main`. Commit at the end of every stage (plan section 7) with `bash tools/test.sh` green, then `git push origin main`. Regenerated sprite sheets
  are a separate commit from the code that made them.
- Never write text that shows during play (plan D3). Menus, pause, result screens and the F3 line may keep text; `RW_DEV_TEXT=1` restores play text for debugging.
- Nothing in the art depicts a character, place or emblem from a published book, film or real armed force (plan D2); the Gospel path is the exception for its
  source, not for any painting or film of it.
- Music: never generate or time-stretch audio. Scenes play synthesised placeholders at the path's tempo until the owner drops loops into `content/imports/<path>/<scene>/`.
- Start with stage 1a (faces) and stop at any committed stage when the session must end; leave `docs/HANDOVER.md` saying which stage is done, what was verified and what
  was not (the owner's phone run, the owner's real loops).
- Report outcomes honestly: which checks ran, which passed, which you could not run.
- End every commit message with `Co-Authored-By:` naming the model you are.
