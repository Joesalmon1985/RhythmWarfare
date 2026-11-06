#!/usr/bin/env bash
# The Godot binary for work in a worktree. It stands in for the real binary:
#
#     GODOT="$PWD/tools/dev/godot.sh" bash tools/test.sh --filter run_tracks
#     bash tools/dev/godot.sh --headless --path . -s tests/run_tests.gd -- --filter port
#
# Every worktree of the project would share one user:// folder (%APPDATA%\Godot\app_userdata\Rhythm Warfare), and
# the tests write there, so two Godot runs at once corrupt each other. So:
#   * each worktree gets its OWN user data folder: <work>/userdata/<worktree folder name> is given to Godot as
#     APPDATA, so user:// is private to the worktree and the owner's real save is never touched. Worktrees
#     therefore run at the same time;
#   * inside one worktree, one Godot at a time: a lock, held for one invocation (a script that starts Godot
#     several times lets others in between its steps). A lock whose owner is gone is cleared. Wait longer than
#     RW_GODOT_WAIT seconds (default 3600) and it gives up with exit 75.
# A caller that has already pointed APPDATA somewhere else (tools/run/walk_run.sh uses a throwaway folder) keeps
# its own folder. RW_GODOT_SHARED=1 goes back to the real user folder and one lock for the whole machine (for a
# measurement that must have the machine to itself, or to reach the owner's real save on purpose).
set -u
BIN="${GODOT_BIN:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
LOCK_ROOT="${RW_GODOT_LOCK_DIR:-${RW_AUDIO_WORK:-$USERPROFILE/rw-audio-work}}"
mkdir -p "$LOCK_ROOT" 2>/dev/null || LOCK_ROOT="${TMPDIR:-/tmp}"
LOCK="$LOCK_ROOT/godot.lock.d"
if [ -z "${RW_GODOT_SHARED:-}" ]; then
  tree="$(basename "$(cd "$(dirname "$0")/../.." && pwd)")"
  LOCK="$LOCK_ROOT/godot.lock.$tree.d"
  norm() { printf '%s' "$1" | tr '\\' '/' | tr '[:upper:]' '[:lower:]' | sed 's#/*$##'; }
  if [ "$(norm "${APPDATA:-}")" = "$(norm "$USERPROFILE/AppData/Roaming")" ]; then
    export APPDATA="$LOCK_ROOT/userdata/$tree"
    mkdir -p "$APPDATA"
  fi
fi
WAIT="${RW_GODOT_WAIT:-3600}"
waited=0
while ! mkdir "$LOCK" 2>/dev/null; do
  owner="$(cat "$LOCK/pid" 2>/dev/null || true)"
  if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
    rm -rf "$LOCK"  # the run that held it is gone
    continue
  fi
  if [ -z "$owner" ] && [ "$waited" -ge 10 ]; then
    rm -rf "$LOCK"  # a lock with no owner recorded for ten seconds: its creator died before writing the pid
    continue
  fi
  if [ "$waited" -ge "$WAIT" ]; then
    echo "godot.sh: waited ${WAIT}s for $LOCK (held by pid ${owner:-?}); giving up" >&2
    exit 75
  fi
  sleep 2
  waited=$((waited + 2))
done
echo "$$" > "$LOCK/pid"
echo "$PWD: $*" > "$LOCK/what"
trap 'rm -rf "$LOCK"' EXIT
trap 'exit 130' INT TERM
"$BIN" "$@"
