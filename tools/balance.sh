#!/usr/bin/env bash
# Run the autoplay harness for several policies and print a compact table.
#   tools/balance.sh [pack] [enemy_fraction] [policies...]
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
PACK="${1:-res://songs/level_01}"
ENEMY="${2:-1.0}"
shift 2 2>/dev/null
POLICIES=("$@")
if [ ${#POLICIES[@]} -eq 0 ]; then POLICIES=(perfect "accuracy:0.85" "accuracy:0.6" none perfect_no_bass); fi
for pol in "${POLICIES[@]}"; do
  "$GODOT" --headless --path "$ROOT" -s tools/autoplay.gd -- "$PACK" "$pol" "$ENEMY" 1 2>&1 | grep -vE "^\s*$|^Godot Engine" | python -I -c "
import sys, json
txt = sys.stdin.read()
try:
    d = json.loads(txt[txt.index('{'):])
except Exception as ex:
    print('$pol: ERROR', txt[:1500]); sys.exit(0)
p = d['produced']; l = d['lost']
print('%-16s %-8s %-22s t=%6.1fs acc=%4.0f%%  built P:%dt/%di/%da  E:%dt/%di/%da  lost P:%s E:%s  peak=%s  mainHP P=%d E=%d  busy=%s blocked=%s' % (
    d['policy'], d['outcome'], d['reason'], d['outcome_time_s'], d['accuracy']*100,
    p[0]['tank'], p[0]['infantry'], p[0]['aircraft'], p[1]['tank'], p[1]['infantry'], p[1]['aircraft'],
    {k: v for k, v in l[0].items() if k in ('factory','barracks','pad','main')}, {k: v for k, v in l[1].items() if k in ('factory','barracks','pad','main')},
    d['peak_live_units'], d['player_main_hp'], d['enemy_main_hp'], d['air_busy'], d['blocked']))
for e in d['timeline']:
    ev = e['event']
    if ev['kind'] in ('producer_lost', 'pad_lost', 'outcome'):
        print('    %6.1fs %s %s' % (e['t'], ev['kind'], {k: v for k, v in ev.items() if k in ('side','role','slot','reason','pads_alive')}))
"
done
