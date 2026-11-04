#!/usr/bin/env bash
# Frame time of the run in every world (RW_RUN_UNTIL_PHASE=n plays n phases = n scenes from the world's entry scene; the default 2 includes one door walk) (the budget the chapters keep: 12 ms mean, 20 ms p95 on the reference laptop). Real-time windowed runs on the dummy audio driver with
# perfect play, two phases (about 45 s) per world, vsync off. Needs a display; run it on an idle machine (other jobs inflate every number).
#   bash tools/run/frames.sh [node ...]      the RW_STORY_LINES / RW_STORY_HIDE / RW_STORY_NOSTAGE switches of the chapters apply (the run reuses StoryStage)
# Prints one line per node: the frames played, mean, p95, max, how many ran over 50 ms (a stage build or a stall), then each stage build's time.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
NODES=("$@"); [ ${#NODES[@]} -eq 0 ] && NODES=(warehouse mothership underworld hospital ward hospital_late ward_late)  # worlds: their entry scenes (any scene id works too)
for n in "${NODES[@]}"; do
  out=$(env RW_RUN_START="$n" RW_RUN_BOT=perfect RW_RUN_ROUTES="${RW_RUN_ROUTES:-left}" RW_RUN_UNTIL_PHASE="${RW_RUN_UNTIL_PHASE:-2}" RW_STORY_QUIT=1 \
        timeout 300 "$GODOT" --path "$ROOT" --disable-vsync --audio-driver Dummy --resolution 1280x720 res://src/run/run_play.tscn 2>&1 | grep -E "^RUN (FRAMES|stage builds)|SCRIPT ERROR")
  echo "$n: $(echo "$out" | grep -o 'FRAMES.*')"
  echo "$out" | grep -o '"ms":[0-9.]*,"parts_ms":{[^}]*},"world":"[a-z_]*"' | sed 's/^/    build /'
done
