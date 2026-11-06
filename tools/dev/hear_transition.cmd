@echo off
rem Hear one scene change between two tracks, with sound (see hear_transition.sh, which this runs). From PowerShell, cmd, or a double-click:
rem     tools\dev\hear_transition.cmd --list
rem     tools\dev\hear_transition.cmd --pair 1            (add --cut to hear the same change as a plain cut)
rem     tools\dev\hear_transition.cmd chase_status_no_problem_original_mix stimpy_party_last_sounds
rem It uses Git's bash by its full path: plain "bash" on Windows is WSL's, which cannot run this.
setlocal
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo Git for Windows was not found. Install it, or run tools/dev/hear_transition.sh from Git Bash.
  pause
  exit /b 2
)
"%GITBASH%" "%~dp0hear_transition.sh" %*
if errorlevel 1 pause
