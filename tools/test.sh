#!/usr/bin/env bash
# Refresh the editor's class cache (new class_name scripts) and run the headless tests.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
"$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1
"$GODOT" --headless --path "$ROOT" -s tests/run_tests.gd -- "$@" 2>&1 | grep -vE "^\s*$|^Godot Engine"
exit "${PIPESTATUS[0]}"
