#!/usr/bin/env bash
# Screenshots of the Debug / Playtest mode (docs/DEBUG_MODE.md) into docs/shots/debug/ (needs a display; virtual clock):
#   picker_*           the scene list (top, then scrolled to the Gospel and the Squadron headings) at a phone held sideways and held upright
#   detail_*           a scene's identity (audio files, mix, visual, hotspots): an arrangement scene of the 174 run, an owner's loop of Squadron, a Gospel placeholder
#   play_overlay_*     the in-play overlay (the panel, the three feedback buttons, the toast after a press)
#   notes              the notes screen with the notes the overlay shot wrote
#   bash tools/run/shoot_debug.sh [out_dir]     GODOT=<console binary>
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-}"
if [ -z "$GODOT" ]; then
  if [ -n "${USERPROFILE:-}" ]; then GODOT="$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"; else GODOT="$HOME/godot/Godot_v4.5.1-stable_linux.x86_64"; fi
fi
OUT="${1:-$ROOT/docs/shots/debug}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
py() { python3 "$@" 2>/dev/null || python "$@"; }

# (1600x720 is a phone held sideways: the game lays out in 720-unit-high space, so this is a 1:1 view; 720x1600 is a phone held upright)
# shot <name> <resolution WxH> <scene> <steps...>   (the steps are shoot.gd's: <frame>:shot:<name>, <frame>:keydown:M ...), then the png becomes a jpg
shot() {
  local name="$1" res="$2" scene="$3"; shift 3
  env APPDATA="$TMP/appdata" XDG_DATA_HOME="$TMP/data" "${EXTRA[@]}" \
    "$GODOT" --path "$ROOT" --resolution "$res" -s tools/shoot.gd -- "$scene" "$TMP" "$@" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" || true
  for png in "$TMP"/*.png; do
    [ -f "$png" ] || continue
    ffmpeg -nostdin -y -loglevel error -i "$png" -q:v 3 "$OUT/$(basename "${png%.png}").jpg" && rm -f "$png"
    echo "shot $OUT/$(basename "${png%.png}").jpg"
  done
}

LIST=res://src/debug/playtest_list.tscn
EXTRA=()
shot picker_landscape 1600x720 $LIST 8:shot:picker_landscape
shot picker_portrait 720x1600 $LIST 8:shot:picker_portrait
EXTRA=(RW_DEBUG_SCROLL=gospel)
shot picker_gospel_landscape 1600x720 $LIST 10:shot:picker_gospel_landscape
EXTRA=(RW_DEBUG_SCROLL=squadron)
shot picker_squadron_portrait 720x1600 $LIST 10:shot:picker_squadron_portrait
EXTRA=(RW_DEBUG_DETAIL=main/warehouse.bar)
shot detail_warehouse_bar 1600x720 $LIST 8:shot:detail_warehouse_bar
EXTRA=(RW_DEBUG_DETAIL=squadron/city)
shot detail_squadron_city 1600x720 $LIST 8:shot:detail_squadron_city
shot detail_squadron_city_portrait 720x1600 $LIST 8:shot:detail_squadron_city_portrait
EXTRA=(RW_DEBUG_DETAIL=gospel/jordan.baptism)
shot detail_gospel_baptism 1600x720 $LIST 8:shot:detail_gospel_baptism

# in play (RW_DEBUG=1 makes the mode on for the launch): Squadron city on the owner's C07 loop, then the Gospel's placeholder; M, V and L are pressed, the toast is on screen in the shot
RUN=res://src/run/run_play.tscn
EXTRA=(RW_DEBUG=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=0.5 RW_RUN_PATH=squadron RW_RUN_START=city RW_RUN_BOT=perfect)
shot play_overlay_squadron_city 1600x720 $RUN 30:shot:play_overlay_squadron_city 31:keydown:M 32:keyup:M 33:shot:play_overlay_toast_music 34:keydown:V 35:keyup:V 36:keydown:L 37:keyup:L 38:shot:play_overlay_toast_like
EXTRA=(RW_DEBUG=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=0.5 RW_RUN_START=warehouse.bar RW_RUN_BOT=perfect RW_RUN_SEED=3)
shot play_overlay_warehouse_bar 1600x720 $RUN 30:shot:play_overlay_warehouse_bar 31:keydown:V 32:keyup:V 34:shot:play_overlay_toast_visual
EXTRA=(RW_DEBUG=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=0.5 RW_RUN_PATH=gospel RW_RUN_START=jordan.baptism RW_RUN_BOT=perfect)
shot play_overlay_gospel_baptism 1600x720 $RUN 30:shot:play_overlay_gospel_baptism 31:keydown:M 32:keyup:M

EXTRA=(RW_DEBUG=1)
shot notes 1600x720 res://src/debug/playtest_notes_screen.tscn 8:shot:notes
shot notes_portrait 720x1600 res://src/debug/playtest_notes_screen.tscn 8:shot:notes_portrait
cp "$TMP/appdata/Godot/app_userdata/Rhythm Warfare/playtest_notes.md" "$OUT/playtest_notes_example.md" 2>/dev/null || true
cp "$TMP/appdata/Godot/app_userdata/Rhythm Warfare/playtest_notes.jsonl" "$OUT/playtest_notes_example.jsonl" 2>/dev/null || true

# the pause panel of a debug run (a real-time run on the real clock, no scripted taps): Back to scene list and the note field
EXTRA=(RW_DEBUG=1 RW_RUN_START=warehouse.bar RW_RUN_SEED=3)
shot play_pause_panel 1600x720 $RUN 240:keydown:Escape 241:keyup:Escape 270:shot:play_pause_panel
