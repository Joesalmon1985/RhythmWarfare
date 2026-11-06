#!/usr/bin/env bash
# One Godot at a time on this machine. Every worktree of the project shares one user:// folder, and the tests
# write there, so two Godot runs at once corrupt each other. This wrapper stands in for the Godot binary:
#
#     GODOT="$PWD/tools/dev/godot.sh" bash tools/test.sh --filter run_tracks
#     bash tools/dev/godot.sh --headless --path . -s tests/run_tests.gd -- --filter port
#
# It waits for the lock, runs the real binary (GODOT_BIN, else the owner's Godot 4.5.1 console exe) with the
# arguments it was given, and releases the lock. The lock is held for one invocation, so a script that starts
# Godot several times (tools/test.sh: the import, then the run) lets other worktrees in between its steps.
# A lock whose owner is gone (a killed run) is cleared. Wait longer than RW_GODOT_WAIT seconds (default 3600)
# and it gives up with exit 75.
set -u
BIN="${GODOT_BIN:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
LOCK_ROOT="${RW_GODOT_LOCK_DIR:-${RW_AUDIO_WORK:-$USERPROFILE/rw-audio-work}}"
mkdir -p "$LOCK_ROOT" 2>/dev/null || LOCK_ROOT="${TMPDIR:-/tmp}"
LOCK="$LOCK_ROOT/godot.lock.d"
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
