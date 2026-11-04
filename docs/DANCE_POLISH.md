# Dance polish: break-dance flair for a few dancers

Branch `feature/face-polish` (on top of the face polish, `docs/FACE_POLISH.md`). Most of the room dances exactly as before; about one dancer in eleven
carries one break-dance-inspired move and performs it now and then, for a bar or two, on the bar, then goes back to their own dance. The ordinary dance
also gained soft knees that give on the kick.

## The moves

Each move is one baked cycle of `StoryCharacter.sample()` (keyframes in `StoryCharacter.FLAIR_KEYS`), locked to the bar (no personal phase), starting and
ending near the standing dance stance so a burst cuts in and out cleanly.

| state | cycle | burst | what it is |
| --- | --- | --- | --- |
| `flair_toprock` | 1 bar, 16 frames | 2 bars | Top-rock / Indian step: the right foot crosses in front on 1 with the arms flung open, steps back into a fists-up guard on 2, the left crosses on 3, a kick out to the side on 4; the body rides over the crossing foot. |
| `flair_drop` | 2 bars, 32 frames | 2 bars | Knee drop on 2 into a low crouch with a hand down, a low shuffle (a leg swept out to one side, then the other, a hand on the floor: a six-step reduced to what reads from the front) on 3 to 5, the freeze on the snare of 6 (leaning over the planted hand, the other arm up, a straight leg flung out) held to 7, up again for the next bar. |
| `flair_robot` | 1 bar, 16 frames | 1 bar | Robot / pop: a new hard pose on every beat (goalpost arms, one forearm dropped, a box in front of the chest, a straight point), snapped into in the last sixth of the beat so it lands on the kick, the head ticking against the arms, a chest pop on every hit. |
| `flair_spin` | 1 bar, 16 frames | 1 bar | A spin on one foot: wind-up on 1, the free foot tucked at the knee and the arms pulled in for a full turn through beat 2 (the sheet's front, three-quarter, back and mirrored three-quarter facings, the same turn machinery as the hero's solo), land on 3 with the arms flung up, settle on 4. |

No headspins or windmills: they do not read at 112 px and the rig has no floor contact for the torso.

### Rig extension

Three new pose keys, baked into the sheets (`tools/story/art/people.py`, `Body`): `crouch` (the hips sink by this share of the height), `lift_l`,
`lift_r` (a foot raised by this share). With any of them the legs are two-bone legs: the foot stays where the straight leg would put it (minus the lift,
never below the floor line), the knee bends outwards seen from the front (foreshortened, as a thigh coming towards the eye) and forwards in the
three-quarter view. Dress, skirt and long-coat hems and capes keep their length over a crouch (never below the floor), and a crouched cape hangs level.
All three keys are zero in every other state, so those frames are drawn exactly as before (the hem and canvas changes are no-ops at zero). Flair frames get
a wider canvas (an even margin, so the pixel grid of the other states is untouched). The live rig fallback (no sheet) ignores the keys, so the crowd only
gives a move to people whose sheet carries it.

### Ordinary dance

`dance` now has `crouch = 0.012 + 0.018 * amp * kick`: the knees give on the kick (about 2 px at full size) instead of the figure only squashing.
`footwork` is danced low (`crouch` 0.035 plus 0.02 on the kick). Nothing else in the existing states changed.

## Who flairs and when (deterministic)

- **Who**: `StoryCrowd.flair_of(id)` (mirrored by `tools/story/art/people_sheets.flair_of`): from the actor id hash (`_id_seed`), a person carries a move
  when `(seed * 31 + 7) % 10007 % 11 == 0`, the move `FLAIR_MOVES[(seed * 70 + 3) % 997 % 4]`. Only free dancers: not a person with a fixed `activity`,
  not the hero, and only if their sheet has the move (the baker gives it only to actors who get the dance set).
- **When**: `StoryCrowd.flair_scheduled(seed, move, bar)`: in every four-bar phrase a dancer takes one slot (a whole multiple of the move's length, so a
  two-bar move starts on bar 1 or 3 of the phrase and its cycle lines up) on six phrases in ten; never in the first two bars of the song.
- **Gate** (every frame): the dancer would otherwise be in `dance` or `cheer` (their mood or a non-synchronised directive), is not walking, the room is not
  in an ending tableau, they stand on a dancing sector (`dance_floor`, `stage`, `stage_steps`, `booth`), and their own energy (room energy plus their
  threshold) is at least 50. A clap, look, wave, group (sync) move or anything else always wins.
- **Cap**: `flair_bursts(beats)` takes the scheduled, present flair dancers of the room in actor order, at most `FLAIR_CAP = 3` at once.
- Frames are bar-locked (`sheet_frame` uses no personal offset for flair), so a burst starts on the move's first frame on the downbeat.

### How sparse

| chapter | dancers with a move (sheets) | moves present |
| --- | --- | --- |
| night_one | 3 of 33 free dancers | drop, robot, spin |
| mothership | 10 of 100 | all four |
| underworld | 9 of 100 | all four |
| hospital | 10 of 99 | all four |
| mental_hospital | 11 of 98 | all four |

A room holds 1 to 4 flair dancers; each is in a burst in about one bar in seven (one-bar moves) or one in three (two-bar moves) while dancing,
so a room of 30-40 shows none or one flair at most moments and never more than three (the test simulates Night One with everyone present at high energy).

## Files

- `src/story/story_character.gd`: the four states (`STATES`, `FACE_OF`, `SHEET_CYCLES`, `FLAIR_MOVES`, `FLAIR_BARS`, `FLAIR_KEYS`), the new pose keys in
  `POSE_KEYS`, the sample, the spin's facings in `sheet_pick` (shared helper `spin_facing`, used by the solo too), bar-locked `sheet_frame`; the dance knees.
- `src/story/story_crowd.gd`: `flair_of`, `flair_scheduled`, `flair_bursts`, the gate in `update`.
- `tools/story/dump_poses.gd`: the new keys in the dump. `assets/story/people_poses.json` regenerated.
- `tools/story/art/people.py`: crouch, lifts, two-bone legs, hems, wider flair canvas.
- `tools/story/art/people_sheets.py`: `flair_of`, the move's frames for flair actors (the spin in all three facings).
- `tools/story/check_assets.py`: the four flair states added to the list of known sheet states (one line; it is the asset validator and rejected the new
  states otherwise).
- `tests/test_story_flair.gd`: new tests (pure poses, bar-locked frames, sparse and deterministic assignment, flair frames for exactly the flair dancers,
  at most three bursts at once in a live crowd, starting on the bar, none in a quiet room).

## How to rebuild

```
godot --headless --path . -s tools/story/dump_poses.gd     # after changing sample() / FLAIR_KEYS
python3 tools/story/build_assets.py night_one people
python3 tools/story/build_assets.py mothership people
python3 tools/story/build_assets.py underworld people
python3 tools/story/build_assets.py hospital people
python3 tools/story/build_assets.py mental_hospital people
python3 tools/story/figure_sheets.py
godot --headless --path . --import
```

**Merging**: the sheets (`assets/story/<chapter>/people/*`, and `people.pages` in a chapter's `manifest.json` when the page count changes) and
`people_poses.json` are generated. On a conflict do not merge them by hand: take either side, rerun the dump and the five `build_assets.py <chapter>
people` commands on the merged code and commit the result. Code and regenerated assets are separate commits for this reason.

## Sizes (page PNGs, bytes)

| chapter | before | after | pages |
| --- | --- | --- | --- |
| night_one | 3,148,136 | 3,288,010 | 6 (6) |
| mothership | 8,988,941 | 9,441,871 | 18 (18) |
| underworld | 8,595,585 | 9,071,134 | 19 (19) |
| hospital | 8,228,798 | 8,666,621 | 16 (15) |
| mental_hospital | 9,192,245 | 9,692,138 | 17 (17) |
| total | 38,153,705 | 40,159,774 | 76 (75) |

+2.0 MB (+5.3%), from the flair frames (Night One 7538 -> 7741 unique frames) and the dance knee frames. The hospital gains `people/page_15.png` again
(its manifest's `people.pages` lists it).

## Proof

- `docs/shots/dance/flair_moves.jpg`: every move across its cycle at 3x, front for three actors (a raver, a raver in a cap, the horned queen with a long
  cape), the three-quarter view (the doctor in a long lab coat), LOD 2 and LOD 4, the alien grey for the spin, and the ordinary dance's five styles below.
- `docs/shots/dance/flair_contact.jpg`: 12 consecutive beats (2 samples a beat) of four flair dancers from the built sheets, picked like the runtime: a
  bar of their dance, the burst on the bar (shaded), back to the dance.
- `docs/shots/dance/ingame_crowd_before_after.jpg`, `ingame_bar102_{before,after}.jpg`: Night One in-game (virtual clock, perfect play), before (old
  sheets) and after, a dancer spinning among the normal crowd, zoomed, and the spin through five moments of the bar.

## Checks

- `python3 tools/story/check_assets.py --determinism` (with `GODOT` set, after a `--import`): every chapter OK, determinism OK, manifest check OK; the
  people sheets it rebuilt were byte-identical in size to the committed build. As before, its full rebuild also rewrote 229 unrelated `processed/` and
  `textures/` PNGs; those were restored with `git checkout`, not committed.
- Story tests (`-s tests/run_tests.gd -- --filter story`): 32248 checks, 0 failures (the new `test_story_flair.gd`: 5 tests, 3068 checks).
- Full suite (`-s tests/run_tests.gd`): 44856 checks, 0 failures.
- No existing test was changed.

## Left undone / doubtful

- Dancers face the front (the crowd gives them no heading), so the moves are designed for the front view; only the spin uses the other facings. The
  three-quarter frames of the other moves are not baked.
- The six-step is reduced to legs swept out to either side: the real circular footwork does not read from the front at this size.
- The hero's solo is unchanged (it does not use the flair moves).
- Night One carries no top-rock dancer (the hash gives its three flair dancers the drop, the robot and the spin); the other chapters have all four.
- Flair needs the baked sheet: the live rig fallback cannot crouch, so a person drawn without a sheet never flairs.
- The in-game proof is a crowd at the camera's distance; at the back of the room (LOD 4) the moves are a few pixels and read as silhouettes only.
