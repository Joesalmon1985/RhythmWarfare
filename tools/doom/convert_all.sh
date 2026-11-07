#!/usr/bin/env bash
# One line for the whole Doom geometry chain: WAD -> eight StoryMap JSONs -> validation -> plan PNGs -> Godot load check.
#   bash tools/doom/convert_all.sh            (RW_DOOM_WAD names the IWAD; default C:\Users\joesa\rw-audio-work\doom\doom2.wad)
# Stops at the first failing step. Needs a WAD whose map lumps hold geometry (python tools/doom/wad.py prints a lump report).
set -e
cd "$(dirname "$0")/../.."
PY="${PYTHON:-python3}"
"$PY" -I tools/doom/test_doom.py
"$PY" -I tools/doom/wad.py
"$PY" -I tools/doom/convert.py --all
"$PY" -I tools/doom/check_world.py --all
"$PY" -I tools/doom/render_plan.py --all
if [ -z "${SKIP_GODOT:-}" ]; then
  out=$(bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_warehouse doom_bar doom_balcony doom_lounge doom_booth doom_dock doom_mothership doom_underworld 2>&1) || { echo "$out"; exit 1; }
  echo "$out"
  n=$(echo "$out" | grep -c "SCRIPT ERROR" || true)
  [ "$n" = "0" ] || { echo "SCRIPT ERROR lines: $n"; exit 1; }
fi
echo "convert_all: OK"
