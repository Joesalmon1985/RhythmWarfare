# Act One - the messy bedsit, headphones, the knock and the visitor

Enabled together with the music POC (`-music` / `BEDSIT_MUSIC=1`); without the flag the original first-person POC is unchanged. Code: `Assets/Bedsit/Game/ActOne*.cs`,
`Clutter*.cs`, `PropMesh.cs`, shader `Resources/Shaders/BedsitProp.shader`. Music side: [README.md](README.md).

## The flow

1. **Wake-up** (existing animation) -> the player **puts on headphones**: an earcup slides in on each side of the view and a band across the top, then they pulse gently with the beat.
   The player's reflection in the mirror gets red over-ear headphones at the same moment. Gatekeeper starts from its first sample about 1 s after they begin to go on.
2. **Only the player exists.** The three NPCs (east window, west window, corridor) are hidden; the window interactions are disabled. The player is visible only in the mirror (as before).
3. **The room is messy** (15 pieces of clutter). While the drums-only rhythm minigame runs (the song's first 25.5 s) and afterwards, the player can look round and **tap items to tidy them away**. Pass the minigame and the song carries on into its next section (44 s, no minigame) which ends in the drop.
4. **The knock** (when that next section finishes, at the drop). There are three knocks (beats 0, 1, 2); the door shakes with each, the north compass wedge flashes, and the door's interact cue appears.
   Before the knock the door is locked (the top-centre control does nothing facing it).
5. **Open the door** (top-centre while facing north): the door opens with its original animation. If at least **80 %** of the mess is tidied a **woman** stands there and waves
   (Pleasantview Sim 13); otherwise a **man** is there and reacts with the "surprise" animation (Sim 11). The threshold is `ActOne.CleanThreshold`.

## Showing the tidying graphically (no text anywhere)

| Element | What it shows |
|---|---|
| **Glint + dust glow** on every untidy item | a twinkling gold star and a soft pulsing halo, so mess can be spotted from across the room (and in desktop, hovering brightens it) |
| **Tidy animation** | tap -> the item pops up, spins, shrinks away with a flash, and a burst of gold/white sparkles; a **ring** pulses out under the finger/pointer |
| **Compass rose** (top-left) | one wedge per view; gold pips = pieces of mess still left in that view; the wedge you are facing is lit; the north wedge **flashes gold** once somebody is knocking |
| **Tidy meter** (under the rose) | fills with gold as the room is cleaned; a tick marks the 80 % "clean enough" point and a **star lights up and glows** when you are past it |
| **The room itself** | the room light brightens by up to 28 % as it is tidied |
| **Headphones** | the earcups/band on screen and in the mirror |

## Clutter

Procedural props (no Sims 2 assets, so they behave identically in live and baked content): bin bag, stack of pizza boxes, books, mugs, bottles, laundry heap, plate with fork,
paper-cup tower, magazines, takeaway cartons, shirts, crumpled paper, trainers. They are drawn a little larger than life and sit on surfaces the camera can actually see - the eye
is at 1.62 m looking level, so **floor-level mess is off-screen**: items are on the bed, dresser, window sills, bookcase, chair, plant, or in tall piles against the north wall.
The layout is the `ClutterFactory.Layout` table (world metres); it was placed by eye from the four standing views, not auto-validated for overlap with furniture.

| View | Items |
|---|---|
| North | bin bag, pizza boxes, books on the bookcase shelf, a shirt over the plant |
| East | mug and bottles on the sill, laundry and a plate on the bed |
| South (mirror) | cups, magazines, takeaway on the dresser (the mirror also reflects the mess) |
| West | paper balls and a mug on the sill, a shirt on the chair, trainers on the dresser |

## Controls

Tap/click an item = tidy it. A click is offered to Act One **before** the three screen-region controls (after the rhythm pads), so an item under a turn zone is tidied instead of
turning the view; the rest of the edge still turns. Hit-testing is a generous screen-space circle around each item (at least 46 px at 720p), items behind the camera are ignored,
and nothing can be tidied during a turn.

## Verification (automated; not a playtest)

`ActOneSceneTests` in the real scene: only the player exists (no Sim pixels in any view, NPCs inactive); at least 3 pieces of mess on screen in each of the four views and compass
pips for each; tapping a mug tidies it, tapping bare wall does nothing, it cannot be tidied twice and the meter rises; a tidy click inside a turn zone does not turn the view; the door
starts shut and locked, does nothing before the knock, opens after it, and a fully tidied room gets the **woman** (Sim 13) while 5/15 gets the **man** (Sim 11); headphones go on after
waking. Exe runs (`-tidybot=all|most|none`, see [README.md](README.md)): tidy all -> woman, tidy 14/15 -> woman, tidy none -> man, each with the knock logged at the drop time.
Screenshots of the visitor (`Evidence/screenshots/actone_exe_*.png`) are git-ignored because they contain Sims 2 content.

## Not done / not judged

* The visitor does not speak or move beyond one animation; nothing happens after the door is open (the player is not walking out; no Act Two).
* No audio when items are tidied (no sound effect assets); the knock is the only new sound.
* Clutter art is blocky programmer art in a different style from the Sims 2 objects. Swapping in real Sims 2 clutter objects would need the baker extended (not done).
* Whether 15 items and an 80 % bar feel right, whether the glints are too loud or too quiet, and whether the headphones look good in the mirror are not judged - I have only looked at screenshots.
