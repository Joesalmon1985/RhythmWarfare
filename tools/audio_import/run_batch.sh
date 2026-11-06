#!/usr/bin/env bash
# Imports every recording in <work>/ToAddTry4 that has no valid pack yet. Safe to run twice: finished packs are skipped.
#   tools/audio_import/run_batch.sh [WORK_FOLDER]        (default $RW_AUDIO_WORK, else ~/rw-audio-work)
# Needs the audio venv at <work>/venv (Windows: venv/Scripts/python.exe, Linux: venv/bin/python) or $RW_AUDIO_PYTHON.
# Writes <work>/batch/{validate.txt,batch.log,summary.txt}. Packs that fail validation (or have no track.json) are
# MOVED, never deleted, to <work>/packs_failed_on_laptop/ and imported again. Demucs runs on the GPU when torch sees one.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="${1:-${RW_AUDIO_WORK:-$HOME/rw-audio-work}}"
[ -d "$work" ] || { echo "no work folder $work" >&2; exit 2; }
work="$(cd "$work" && pwd)"
export RW_AUDIO_WORK="$work" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
py="${RW_AUDIO_PYTHON:-}"
if [ -z "$py" ]; then
    for c in "$work/venv/Scripts/python.exe" "$work/venv/bin/python"; do [ -x "$c" ] && { py="$c"; break; }; done
fi
[ -n "$py" ] && [ -x "$py" ] || { echo "no audio venv python under $work/venv (set RW_AUDIO_PYTHON)" >&2; exit 2; }
[ -d "$work/ToAddTry4" ] || { echo "no recordings folder $work/ToAddTry4" >&2; exit 2; }
mkdir -p "$work/batch" "$work/packs" "$work/packs_failed_on_laptop"
log="$work/batch/batch.log"
say() { echo "[$(date '+%F %T')] $*" | tee -a "$log"; }
t_start=$(date +%s)
say "batch start: work=$work python=$py"
"$py" -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())" 2>&1 | tee -a "$log"

# (a) validate every existing pack (against its recording when that is in ToAddTry4)
: > "$work/batch/validate.txt"
for d in "$work"/packs/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"; id="$(basename "$d")"
    if [ ! -f "$d/track.json" ]; then echo "$id no track.json" >> "$work/batch/validate.txt"; continue; fi
    src="$("$py" -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8')).get('source',{}).get('input_path',''))" "$d/track.json" 2>/dev/null)"
    src="${src//\//}"; rec="$work/ToAddTry4/${src##*/}"
    args=(); [ -n "$src" ] && [ -f "$rec" ] && args=(--recording "$rec")
    out="$("$py" "$here/validate_track.py" "$d" "${args[@]}" 2>&1)"
    n="$(echo "$out" | grep -o '^\(OK\|FAIL\): [0-9]* violation' | grep -o '[0-9]*' | tail -1)"
    echo "$id ${n:-error}" >> "$work/batch/validate.txt"
    # the validator passes this pack now but its report.json (an earlier run) says otherwise: record the new result, so
    # --skip-imported keeps the pack instead of importing it again
    [ "${n:-x}" = "0" ] && [ -f "$d/report.json" ] && "$py" "$here/batch_summary.py" --revalidated "$d/report.json" | tee -a "$log"
done
say "validated $(wc -l < "$work/batch/validate.txt") pack folder(s): $work/batch/validate.txt"

# RW_BATCH_VALIDATE_ONLY=1 stops here (a dry look at the packs)
[ -n "${RW_BATCH_VALIDATE_ONLY:-}" ] && exit 0

# (b) move aside what is broken
stamp="$(date +%Y%m%d_%H%M%S)"
while read -r id n rest; do
    if [ "$n" != "0" ]; then
        dest="$work/packs_failed_on_laptop/$id"; [ -e "$dest" ] && dest="${dest}_$stamp"
        mv "$work/packs/$id" "$dest" && say "moved aside $id (${n:-?} ${rest:-violations}) -> $dest"
    fi
done < "$work/batch/validate.txt"

# (c) import everything that is not done
rm -f "$work/batch_summary.txt"
say "importing from $work/ToAddTry4"
OMP_NUM_THREADS="${OMP_NUM_THREADS:-3}" "$py" "$here/import_track.py" "$work/ToAddTry4" --skip-imported --prune-cache \
    --out "$work" --device auto 2>&1 | tr '\r' '\n' | grep --line-buffered -v '^ *[0-9]*%|' >> "$log"
say "import_track.py finished"

# (d) summary
{ echo "# batch of $(date '+%F %T'), $(( $(date +%s) - t_start )) s this run"
  "$py" "$here/batch_summary.py" "$work" "$work/batch_summary.txt"; } > "$work/batch/summary.txt"
cat "$work/batch/summary.txt" | tee -a "$log"
