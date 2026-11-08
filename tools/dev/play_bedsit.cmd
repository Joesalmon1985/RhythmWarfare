@echo off
rem Launches the game at the bedsit (the new opening, docs/bedsit/LAUNCH.md) from this checkout, with the flag on and the imported track packs (this runs play_tracks.sh --run).
rem Works from PowerShell, cmd, or a double-click:
rem     tools\dev\play_bedsit.cmd            the bedsit, facing north
rem     tools\dev\play_bedsit.cmd E          start facing east (N, E, S or W: RW_BEDSIT_FACING), a development aid; tap left/right to turn, top to leave, or use the arrow keys
rem     tools\dev\play_bedsit.cmd --dev-keys keys 1 to 8 pick any choice on show in the bedsit too (RW_DEV_KEYS=1; off by default there: the arrows are the regions)
rem     tools\dev\play_bedsit.cmd --rave space   start inside a rave (space, magic, dinos or transport: RW_RUN_START=<prefix>_rave); add --fixed to start with the bass already fixed (RW_SPACE_BASS_FIXED=1)
rem     tools\dev\play_bedsit.cmd --race space|magic|dinos|transport  start in that rave's hangar (RW_RUN_START=<prefix>_race): touch the racer for the street race (docs/bedsit/RACE.md)
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
if /i "%~1"=="--rave" if /i "%~2"=="space" set "RW_RUN_START=space_rave"
if /i "%~1"=="--rave" if /i "%~2"=="magic" set "RW_RUN_START=magic_rave"
if /i "%~1"=="--rave" if /i "%~2"=="dinos" set "RW_RUN_START=dino_rave"
if /i "%~1"=="--rave" if /i "%~2"=="transport" set "RW_RUN_START=transport_rave"
if /i "%~1"=="--race" if /i "%~2"=="space" set "RW_RUN_START=space_race"
if /i "%~1"=="--race" if /i "%~2"=="magic" set "RW_RUN_START=magic_race"
if /i "%~1"=="--race" if /i "%~2"=="dinos" set "RW_RUN_START=dino_race"
if /i "%~1"=="--race" if /i "%~2"=="transport" set "RW_RUN_START=transport_race"
if /i "%~3"=="--fixed" set "RW_SPACE_BASS_FIXED=1"
if /i "%~1"=="--fixed" set "RW_SPACE_BASS_FIXED=1"
if /i "%~1"=="--dev-keys" set "RW_DEV_KEYS=1"
if /i "%~2"=="--dev-keys" set "RW_DEV_KEYS=1"
if /i "%~1"=="N" set "RW_BEDSIT_FACING=N"
if /i "%~1"=="E" set "RW_BEDSIT_FACING=E"
if /i "%~1"=="S" set "RW_BEDSIT_FACING=S"
if /i "%~1"=="W" set "RW_BEDSIT_FACING=W"
"%GITBASH%" "%~dp0play_tracks.sh" --run
if errorlevel 1 pause
