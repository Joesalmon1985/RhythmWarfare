@echo off
rem Launches the game at the bedsit (the new opening, docs/bedsit/LAUNCH.md) from this checkout, with the flag on and the imported track packs (this runs play_tracks.sh --run).
rem Works from PowerShell, cmd, or a double-click:
rem     tools\dev\play_bedsit.cmd            the bedsit, facing north
rem     tools\dev\play_bedsit.cmd E          look from the east (N, E, S or W): the camera stands at that viewpoint (RW_STORY_CAM), a development aid until the turn hook lands
rem F3 shows the overlay line (compass letter and theme name). The save is the play copy of play_tracks.sh, never the real one.
setlocal
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo Git for Windows was not found. Install it, or run this from Git Bash with RW_BEDSIT=1 RW_RUN_PATH=bedsit tools/dev/play_tracks.sh --run
  pause
  exit /b 2
)
set "RW_BEDSIT=1"
set "RW_RUN_PATH=bedsit"
if /i "%~1"=="N" set "RW_STORY_CAM=bedsit_n"
if /i "%~1"=="E" set "RW_STORY_CAM=bedsit_e"
if /i "%~1"=="S" set "RW_STORY_CAM=bedsit_s"
if /i "%~1"=="W" set "RW_STORY_CAM=bedsit_w"
"%GITBASH%" "%~dp0play_tracks.sh" --run
if errorlevel 1 pause
