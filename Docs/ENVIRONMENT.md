# Environment inspection and setup (Windows 11, 9 Nov 2026)

## Found at the start
| Tool | State |
|---|---|
| Git | 2.54.0 present |
| Claude Code | 2.1.292 present |
| .NET SDK | 10.0.401 present (not needed) |
| GitHub CLI | present, signed in |
| Unity Hub / Unity Editor | **not installed** |
| Visual Studio | **not installed** (not required: Unity compiles C#; code was edited with Claude Code) |
| The Sims 2 | Legacy Collection under `RhytmDrama/The.Sims.2.Legacy.Collection/.../game` (`Base`, `EP1..EP9`, `SP1..SP8`), plus a `.rar` of it |
| Disk | C: 333 GB free |

## Installed / configured
* **Unity Hub 3.22.6** via `winget install Unity.UnityHub` (MSIX; installed per user).
* **Unity 6000.3.28f1 (Unity 6.3 LTS)** via the Hub CLI (`Unity Hub.exe -- --headless install --version 6000.3.28f1 --module android
  --module android-sdk-ndk-tools --module android-open-jdk`), installed to `C:\Users\joesa\UnityEditors\` (the Hub install path was
  set there because Program Files is not writable without elevation). Modules: Windows (Mono), Android (SDK, NDK, OpenJDK).
* **Sign-in and licence**: you signed in to Unity in the browser (`unity auth login`) and approved the Unity Personal EULA, after which
  `unity license activate --personal --accept-eula` activated the free Personal licence. No credentials were handled by the agent.
* **Official Unity Claude Code plugin** (`Unity-Technologies/unity-agent-plugin`, v0.1.9-beta): `claude plugin marketplace add Unity-Technologies/unity-agent-plugin`
  then `claude plugin install unity@unity-agent-plugin` (user scope; loads at the next Claude Code session start).
  The plugin's `unity` CLI (copied to `C:\Users\joesa\.unity\bin\unity.exe`) and the project's `com.unity.pipeline` package were used
  to drive the editor: play mode, C# eval, console, screenshots, tests, builds.
* Unity audio is **disabled** in `ProjectSettings/AudioManager.asset` (the audio device failed to initialise and FMOD's thread deadlocked the editor).

## Unity version vs OpenTS2's 2020.3.32f1
OpenTS2 is vendored as source under `Assets/ThirdParty/OpenTS2` (commit `bdabb07f4689ed91803a3d86dcbc8870b8832878`) rather than kept as a separate
2020.3 project: the whole code base compiled on 6000.3.28f1 after removing stray IDE-generated `using Codice...`/`log4net`/`Unity.Plastic` lines and
adding `com.unity.nuget.newtonsoft-json` (see `OPENTS2_PATCHES.md`). The original OpenTS2 clone is kept separate at
`C:\Users\joesa\Documents\Cursor\UnityBedsit-refs\OpenTS2`; no 2020.3 editor was needed. Packages: Animation Rigging 1.3.1, Test Framework 1.6.0, Timeline, uGUI, Newtonsoft Json, Pipeline 0.10.0-exp.1.

## Untouched
`RhythmWarfare` and `DuelMasterBattle` were cloned read-only into `UnityBedsit-refs/` (nothing was checked out, modified or committed in them).
