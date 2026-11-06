@echo off
rem Plays the game from this checkout with the imported track packs (see play_tracks.sh, which this runs).
rem Works from PowerShell, cmd, or a double-click:   tools\dev\play_tracks.cmd        or        tools\dev\play_tracks.cmd --run
rem It uses Git's bash by its full path: plain "bash" on Windows is WSL's, which cannot run this.
setlocal
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo Git for Windows was not found. Install it, or run tools/dev/play_tracks.sh from Git Bash.
  pause
  exit /b 2
)
"%GITBASH%" "%~dp0play_tracks.sh" %*
if errorlevel 1 pause
