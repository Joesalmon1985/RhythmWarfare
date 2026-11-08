# The Android APK with the 61 tracks (Stage E, 8 November 2026)

Branch `wip/apk`. The recordings are other artists' music: the bundle and the APK are never committed
(`/track_packs/` and `build/` are in `.gitignore`).

## What the packs hold (measured)

`C:\Users\joesa\rw-audio-work\packs`: 61 folders, 4.6 GB on disk.

| Part | Size | Needed at runtime? |
|---|---|---|
| `stems/*.ogg` (256 referenced by the `track.json` files; one more on disk, unreferenced) | 3.93 GB (about 500 kbps, `-q:a 10`-like, 48 kHz stereo Vorbis) | yes: `AudioStreamOggVorbis.load_from_file` in `run_track_audio.gd` |
| `track.json` (61) | about 10 MB | yes: read by `RunTrackScenes` / `TrackPack` |
| `preview/*.ogg` | 684 MB | no (listening files, "never read by the game") |
| `report.json`, `report.txt`, `stems/.made_from` | small | no (build intermediates) |

So the need is the stems plus `track.json`. Everything else stays out.

## The re-encode

The pack contract (`docs/TRACK_PACK_FORMAT.md`, `TrackPack._check_stems`) requires 48 kHz stereo Ogg Vorbis and equal stem
lengths to 5 ms, so the phone build keeps the format and lowers the quality only: `ffmpeg -c:a libvorbis -q:a 4 -ar 48000 -ac 2`.
(The previews the importer writes use `-q:a 5`; the project's own mono loops are 96 kbps.) Measured on one track
(4 stems, 65.9 MB): `-q:a 3` 14.7 MB, `-q:a 4` 16.3 MB, `-q:a 5` 20.6 MB; length unchanged to the sample (268.611438 s before and after).
Quality 4 was chosen for size; it was not auditioned by ear (ONE_PC_PLAN X4 says the bitrate is chosen by ear on three tracks: still to do).

| | Size |
|---|---|
| Stems as imported (referenced ones) | about 4.1 GB (the script printed 25 % for 1,027 MB out) |
| Bundle after re-encode, `-q:a 4`, with `track.json` and `.import` stubs | **1,027 MB** (25 % of the input) |
| Debug APK with all 61 packs | **1,225,141,764 bytes (1.23 GB, 1.14 GiB)**: about 198 MB of game plus 1.03 GB of tracks |
| Target | well under 1.5 GB: met (at `-q:a 5` it would be about 1.25 GB of tracks, 1.45 GB APK: too close, so not used) |

## The bundling route

1. `python tools/audio_import/build_android_packs.py` (options `--src`, `--dest`, `--quality`, `--ids`, `--limit`, `--jobs`, `--dry-run`)
   reads `$RW_AUDIO_WORK/packs` (else `C:/Users/joesa/rw-audio-work/packs`), re-encodes the stems `track.json` names, copies `track.json`,
   and writes the bundle to `<repo>/track_packs/<id>/{track.json,stems/*.ogg}`. It also writes a `<stem>.ogg.import` file containing
   `importer="keep"`: Godot then neither imports the file (no 1 GB second copy in `.godot/imported`) nor swaps it for an `.oggvorbisstr`;
   the exporter ships the original bytes, which `load_from_file` needs. (Without that, the APK would hold only the converted resource.)
2. Run `--import` once so Godot sees the folder, then export. The Android preset carries `include_filter="track_packs/*/track.json"` (the
   JSON is not a resource, so it needs naming; the stems ship through `keep`). In the APK the files sit under `assets/track_packs/<id>/`.
3. Loader (`RunTrackScenes.packs_root`): `packs_dir_override`, else `RW_TRACKS_DIR`, else `user://track_packs` **if that folder exists**,
   else the bundled `res://track_packs` **if it exists**, else `user://track_packs` as before. Nothing changes on a machine with neither
   a user folder nor a bundle. On the phone nothing is pushed by hand: `user://track_packs` does not exist, so the bundle is used.
   `TrackPack.load_pack` (`DirAccess.dir_exists_absolute`, `FileAccess`) and the stem loader work with `res://` paths; that is by reading
   the code and by the export check below, not run on a device.

Export command (Git Bash, from the worktree root, after `--import`):
`"C:/Users/joesa/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe" --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk`

## Proved

- 3 tracks (13 stems): APK 251,493,729 bytes; `unzip -l` lists all 13 stems and 3 `track.json` as `assets/track_packs/...` `.ogg` (no `.oggvorbisstr`).
- All 61: export exit code 0 (`[ DONE ] export`, signed, verified); `unzip -l` lists 256 stems (`.ogg`) and 61 `track.json`, 16,658 files in all.

## Not done

- Nothing was installed or run on a phone (none plugged in): latency, worst frame time, memory and load time per scene are **not measured**,
  and that the stems load and play from the APK's `assets` is **not proved on a device** (only that they are in the file).
- The `-q:a 4` quality was not auditioned.
- Decoding an Ogg out of the APK while the UI runs (`run_track_audio.gd` worker threads) and the 1.2 GB install size on the phone's storage are unmeasured.
- A release build and keystore, and a split APK / `.pck` fallback (not needed at this size).

## Desktop suites on this branch (loader change, with the 61-pack bundle present in the worktree)

`--filter run_`: 16,705 checks, 0 failures, 0 SCRIPT ERROR lines. `--filter playtest`: 2,982 checks, 0 failures, 0 SCRIPT ERROR lines (both exit 0). The tests set packs_dir_override or run with track scenes off, so they do not exercise the res:// fallback itself.
