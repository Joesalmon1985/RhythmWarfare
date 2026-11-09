# UnityBedsitPOC

A first-person, Doom-style 2.5D bedsit built from **genuine Sims 2 characters, models, textures and animations**,
using [OpenTS2](https://github.com/LazyDuchess/OpenTS2) technology inside Unity 6. It is a proof of concept for the
visual and interaction architecture of RhythmWarfare and DuelMasterBattle. It does **not** port any gameplay from them.

> You wake up in bed, sit up, and look north / east / south / west. You see the world and other Sims, never your own
> avatar: except in the mirror. Three controls only: turn left, turn right, interact (or walk through the door).

## Status at a glance

| Item | State | Evidence |
|---|---|---|
| Unity 6000.3.28f1 LTS + Unity Hub + Unity Claude Code plugin | installed, working | `Docs/ENVIRONMENT.md` |
| OpenTS2 compiles and runs on Unity 6 (was 2020.3.32f1) | yes, with documented patches | `Docs/OPENTS2_PATCHES.md` |
| Authentic Sims 2 animation on the original skeleton | yes (dressed + base Sims) | `Docs/ANIMATION_PROVENANCE.md`, `Evidence/animation_proof.txt` |
| Furnished first-person bedsit, four compass views, one coherent 3D world | yes | `Evidence/screenshots/` (local) |
| Real planar mirror; player body visible **only** there | yes, test-verified at pixel level | `Docs/TEST_RESULTS.md` |
| Door opens with the original Sims 2 door animation; first-person walk to the corridor at constant eye height | yes | tests + evidence log |
| 37 Play Mode tests (23 live content + 14 baked-content parity) | **37 / 37 pass** | `Docs/TEST_RESULTS.md` |
| Windows executable | built, **self-contained** (baked content, no Sims 2 install needed), run standalone, full flow verified | `Builds/Windows/` (local), `Evidence/evidence_log_windows_exe.txt` |
| Android APK | **built** (35.9 MB, arm64, baked 3D content inside); **not run on a phone** (none connected) | `Docs/ANDROID.md` |
| Characters / room | real 3D (decision: no sprites); converted locally to ordinary Unity assets for phones | `Docs/BAKING.md` |
| Played on a phone / by a person with a real mouse | **NOT verified** (machine-verified only) | |

## Music / rhythm layer

A rhythm-and-mixing layer over the bedsit (Gatekeeper-only first pass) and "Act One" (headphones, a messy room to tidy, a knock at the drop, a visitor at the door) live behind `-music` / `BEDSIT_MUSIC=1`: see [Docs/music/README.md](Docs/music/README.md) and [Docs/music/ACT_ONE.md](Docs/music/ACT_ONE.md).

## Controls (exactly three)

| Action | Mouse / touch | Keyboard (convenience) |
|---|---|---|
| Rotate 90 degrees anticlockwise | click/tap the **left** 22% of the screen | A / Left |
| Rotate 90 degrees clockwise | click/tap the **right** 22% of the screen | D / Right |
| Interact / move forward through a doorway | click/tap the **top-centre** (x 25-75%, top 42%) | W / Up / Space |

The turn is an eased 0.3 s rotation about the fixed eye position. Hints are three faint chevrons plus a small green
diamond marking what the top control will do: visual cues only, no text, no menus, no joystick, no inventory.

## The four views (one room, one camera position)

| View | What you see | Top control does |
|---|---|---|
| **North** | the door (ajar) and the corridor beyond it, a Sim standing in the corridor | plays the rest of the original door animation, then walks you into the corridor in first person |
| **East** | window onto a garden, a Sim outside, bed headboard, painting | the Sim outside waves (`a-react-wave-fullBody_anim`) |
| **South** | freestanding mirror: your own Sim, the room behind you | your reflection waves |
| **West** | second window, different garden view, another Sim outside | that Sim applauds (`a-clapSmall-loop-standing_anim`) |

In the corridor: north = the Sim who greeted you (waves back), south = the doorway (walk back into the bedsit).

## Running it

Two ways to run, same game:

* **Baked (no Sims 2 needed at run time)**: Windows exe / Android APK built from `Assets/LocalBaked` (see `Docs/BAKING.md`).
  Those assets are created on a machine that owns Sims 2 and are EA-derived: keep them private, never commit them.
* **Live (desktop, reads your own Sims 2 install)**: steps below. This is also how the baker gets its data.

Prerequisite for live/baking: your own copy of **The Sims 2** (developed against the Legacy Collection, `game/Base`, `EP1..EP9`, `SP1..SP8`).
No EA content is in this repository.

1. `copy config.example.json config.json` and set `game_dir` (the `game` folder containing `Base/`, `EP1/`...) and
   `user_dir` (any writable folder; see step 2).
2. Premade Sims are read from `<user_dir>/Neighborhoods/N001/Characters/`. Copy the game's own
   `game/Base/TSData/Res/UserData/Neighborhoods/N001/Characters` folder there (that is what `LocalData/` is: git-ignored).
3. Editor: open the project with Unity **6000.3.28f1**, open `Assets/Scenes/Bedsit.unity`, press Play (live content).
   To create the phone/standalone assets: with the game playing, menu `Bedsit/Bake/Bake live content to local assets (Play mode)`;
   then `Bedsit/Build/Windows Player` or `Bedsit/Build/Android APK`.
   Windows build: run `Builds/Windows/UnityBedsitPOC.exe`; it uses baked content unless a `config.json` sits beside it.
4. Evidence mode (records screenshots of the whole flow through the real input path):
   `UnityBedsitPOC.exe -evidence -quit` (or `BEDSIT_EVIDENCE=1`). Output in `Evidence/` next to the exe.

## Architecture

```
Assets/Bedsit/Core     (engine-agnostic gameplay + view logic; no Sims 2 / OpenTS2 dependency)
  FirstPersonViewController  camera rig: yaw / pitch pivots, four compass facings, eased 90 degree turns
  InputRegions / InputRouter pure screen-region logic + mouse/touch/keyboard -> 3 PlayerActions
  InteractionTarget          "in zone Z facing D the top control does X" (data + events)
  InteractionController      picks the current target for (zone, facing); cue + interact routing
  PlayerTransitionController first-person walk through doorways; eye height constant, turns locked
  WorldSceneController       named zones with fixed standpoints
  MirrorReflectionController secondary camera + RenderTexture, off-axis frustum through the glass,
                             player layer rendered only by the mirror camera
  ICharacterActor            logical-key animation interface ("idle", "wave", "clap"...)
  InteractionCue / HudOverlay visual-only cues, fade
Assets/Bedsit/Sims2    (Sims 2 / OpenTS2 binding + baked-content loader)
  BedsitContent              live (OpenTS2) or baked (Unity assets) source for the world and the Sims
  Sims2Runtime               config.json, OpenTS2 init, package mounting, material/texture/shape helpers
  SimAnimationLibrary        logical key -> ORIGINAL ANIM resource (with fallback candidates + provenance)
  SimCharacterActor          dressed premade Sim (CAS outfit + original skeleton + layered original animations)
  SimDoor                    original door model + original door-open animation
  BedsitWorldBuilder         walls/floors (genuine materials), furniture, windows, mirror frame, garden, lights
Assets/Bedsit/Game     BedsitGame (wiring + wake-up), EvidenceRunner, BedsitLayers
Assets/Bedsit/Editor   scene setup, ContentBaker (live -> Unity assets), build scripts
Assets/Bedsit/Tests    Play Mode tests
Assets/ThirdParty/OpenTS2  vendored OpenTS2 source (MPL-2.0), patched for Unity 6, see Docs/OPENTS2_PATCHES.md
```

Gameplay (Core) never touches rendering or Sims 2 types; the Sims 2 layer implements the interfaces. The Core assembly,
`ICharacterActor` and the controller pattern are what would be reused in the Godot games (see `Docs/RECOMMENDATIONS.md`).

### First-person guarantee

* The camera is a child of the player rig only, never of a character. It is the only camera that draws to the screen.
* The player's Sim lives on layer 8 (`PlayerMirrorOnly`). The eye camera's culling mask excludes it; only the mirror
  camera renders it. The player's renderers also cast no shadows.
* The mirror frame itself is on layer 9 so the reflection never contains its own frame; the glass quad is excluded too.
* Tests colour the player magenta and the NPCs cyan, render the eye camera and count pixels: 0 magenta facing N/E/W and during
  turns, hundreds facing the mirror; NPC pixels in every non-mirror view.

## Tests

`Docs/TEST_RESULTS.md`: 23 Play Mode tests, all passing (Unity Test Runner: `Window > General > Test Runner > PlayMode`).
They cover: first-person camera, exact 90 degree turns, four turns = identity, turn time 0.2-0.45 s, no avatar in
N/E/W/mid-turn, mirror reveals the player, NPC in each non-mirror view, mirror camera geometry, interactions per view,
east/west NPC reactions, mirror animation, north interaction opens the door and walks into the corridor at constant eye
height, the wake-up sequence, and that the animation is a genuine OpenTS2-decoded Maxis resource that changes bone poses.
The tests need the local Sims 2 install and skip themselves (Ignore) if `config.json` is absent.

## Assets and licensing

* **Nothing from The Sims 2 is committed.** `.gitignore` excludes `config.json`, `LocalData/`, `*.package`, `Evidence/screenshots/`
  (screenshots contain EA assets) and `Builds/`. All Sims 2 content is read from your own installation at run time.
* Cursor/UI marker (green diamond) and the HUD chevrons are procedurally drawn UI helpers; no characters or environment art are generated.
* OpenTS2 is MPL-2.0 (`Assets/ThirdParty/OpenTS2/LICENSE-OpenTS2-MPL2.md`); our patches to its files are listed and remain MPL-2.0.
  Our own code is yours to license.

## Known limitations (honest list)

* Phone: the APK builds and contains the baked 3D content, but it has **not been run on a device**; performance and the OpenTS2
  surface shaders on a real GPU are unverified (`Docs/ANDROID.md` lists the first things to check).
* Baked animation clips are 30 fps samples of the original animations (the live path uses the exact keyframes).
* Baked output derives from EA assets: private use only.
* Mirror and doors/windows are the originals' geometry; the mirror's glass is our reflection (the game's own mirror node type
  `cViewerRefNodeRecursive` is not implemented by OpenTS2). Window glass alpha is thinned for readability.
* Some OpenTS2 face resources print a warning (`Bone or blend for animation channel ... not found`: blend shapes for eyes/hair
  not present on the rig); expression blends are therefore limited.
* Not verified on a phone, with real touch, or by a human tester other than via the automated and screenshot evidence.

## Bedroom art overhaul
See [Docs/art/ROOM_PIPELINE.md](Docs/art/ROOM_PIPELINE.md), [ASSET_INVENTORY](Docs/art/ASSET_INVENTORY.md) and [LIMITATIONS](Docs/art/LIMITATIONS.md). Room 01 is a data-driven room (`Resources/Rooms/room01.json`) built from original Blender props; `-legacyroom` restores the old Sims 2 furniture.
