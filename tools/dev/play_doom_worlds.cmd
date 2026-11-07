@echo off
rem Plays the Doom worlds pilot from this checkout (docs/doom/LAUNCH.md): the run with RW_DOOM_WORLDS=1, starting in a Doom scene, with the imported track packs.
rem From PowerShell:   & "C:\...\tools\dev\play_doom_worlds.cmd" --scene doom_warehouse        (the scene defaults to doom_warehouse)
rem Without --scene or the flag the game is the legacy campaign, untouched.
setlocal
set "SCENE=doom_warehouse"
if /i "%~1"=="--scene" set "SCENE=%~2"
set "RW_DOOM_WORLDS=1"
set "RW_RUN_START=%SCENE%"
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo Git for Windows was not found. Install it, or run: RW_DOOM_WORLDS=1 RW_RUN_START=%SCENE% bash tools/dev/play_tracks.sh --run
  pause
  exit /b 2
)
echo Doom worlds: scene %SCENE% (RW_DOOM_WORLDS=1)
"%GITBASH%" "%~dp0play_tracks.sh" --run
if errorlevel 1 pause
