#!/usr/bin/env bash
# Plays one wizard duel between two separate game processes over the real network stack (loopback), with no windows and no audio
# (song time follows the wall clock), then checks that both processes agree on who won and on every wizard's health.
#   bash tools/duel/two_players.sh [host_bot] [join_bot] [seed]      bots: apprentice | adept | archmage | perfect
# A window pair with sound instead: run the game twice, host on one ("Host a duel"), the other joins (or types 127.0.0.1).
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$(command -v godot || echo "$HOME/godot/Godot_v4.5.1-stable_linux.x86_64")}"
HOST_BOT="${1:-adept}"
JOIN_BOT="${2:-apprentice}"
SEED="${3:-11}"
OUT="${TMPDIR:-/tmp}/rw_duel_$$"
mkdir -p "$OUT"
export RW_DUEL_VIRTUAL=1 RW_DUEL_QUIT=1
RW_DUEL_AUTO=host RW_DUEL_NAME=Merlin RW_DUEL_BOT="$HOST_BOT" RW_DUEL_SEED="$SEED" timeout 240 "$GODOT" --headless --path "$ROOT" res://src/duel/duel_lobby.tscn > "$OUT/host.log" 2>&1 &
HOST_PID=$!
sleep 4
RW_DUEL_AUTO=join RW_DUEL_NAME=Morgana RW_DUEL_ADDR=127.0.0.1 RW_DUEL_BOT="$JOIN_BOT" RW_DUEL_SEED="$((SEED + 1))" timeout 240 "$GODOT" --headless --path "$ROOT" res://src/duel/duel_lobby.tscn > "$OUT/join.log" 2>&1 &
JOIN_PID=$!
wait "$HOST_PID" "$JOIN_PID"
H="$(grep -h '^DUEL_RESULT' "$OUT/host.log" | tail -1)"
J="$(grep -h '^DUEL_RESULT' "$OUT/join.log" | tail -1)"
echo "host: $H"
echo "join: $J"
PY="$(command -v python3 || command -v python)"
"$PY" - "$H" "$J" <<'PYEOF'
import json, sys
if not sys.argv[1] or not sys.argv[2]:
    print("FAIL: a process printed no DUEL_RESULT"); sys.exit(1)
h = json.loads(sys.argv[1].split(" ", 1)[1]); j = json.loads(sys.argv[2].split(" ", 1)[1])
ok = (h["hp10"][0] == j["hp10"][1] and h["hp10"][1] == j["hp10"][0]
      and h["phrases"] == j["phrases"] and h["reason"] == j["reason"]
      and (h["winner"] == -1 and j["winner"] == -1 or h["winner"] == 1 - j["winner"]))
print("PASS: both phones agree" if ok else "FAIL: the phones disagree")
sys.exit(0 if ok else 1)
PYEOF
