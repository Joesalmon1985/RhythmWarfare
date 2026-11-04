# RhythmWarfare merge and continuous story run

Work in [Joesalmon1985/RhythmWarfare](https://github.com/Joesalmon1985/RhythmWarfare). Complete the tested Warehouse music integration and 2.5D story merge into `main` first. Then implement the continuous story run on a new branch from that merged baseline. The owner will supply more music in the same Beat Shaper WAV/MIDI export format. Make every level ready to receive it.

## 1. Merge and verify the existing work

1. Fetch the current refs and inspect the working tree, local branches and worktrees. Read the repo instructions and the story handover. Find the exact local revision or working tree where the owner tested the Warehouse import. Look for `feature/story-warehouse-music-test` or the branch actually used. Preserve unrelated changes. If the tested integration is uncommitted, capture just its relevant code, configuration and assets in a scoped commit following the repo's asset conventions.
2. Confirm the ancestry of `main`, `feature/story-25d` and the tested import. At the time of the review, GitHub showed `main` at `9f5ba0b` and `feature/story-25d` at `f10d468`, with changes on both sides. The Warehouse import was not visible in the published trees. Use the current local evidence to identify it. If you cannot locate the tested import, report which branch or worktree is missing before proceeding to the redesign.
3. Integrate the current 2.5D story work and the tested Warehouse import into the latest `main`. If the import already includes the current story branch, integrate the combined history once. Otherwise bring in both lines of work. Resolve conflicts with the relevant changes from both sides intact. Use the repository's normal merge workflow.
4. Verify the merged baseline through the existing Story Campaign menu. Level 1 should play the actual Warehouse recording with its matching pad cues across repeated loops. Check that the existing story progression and project startup still work. Record the tested import commit, the resulting `main` SHA and its publication status on GitHub.
5. Create `feature/continuous-story-run` from that verified `main` and do the overhaul there. Keep the baseline merge separate from the redesign so the working music test has a clean point to return to.

## 2. Make the story the game

Use the existing five 2.5D worlds, rooms, camera movement, characters, reactive crowds, four pads and calibration. Replace the old chapter-by-chapter endings with one continuous run. Remove the military modes and loadout flow from the player-facing game and remove their runtime dependencies from the story path. Keep the generic audio, input and import code that the new game uses.

Use 174 BPM in 4/4. Every phase lasts 64 beats, with four blocks of 16 beats. Start each phase with drums alone. A fully successful phase follows this mix:

| Beats | Mix | Required cues |
| --- | --- | --- |
| 1–16 | Drums alone | Drums |
| 17–32 | Bass enters. Drums remain audible underneath. | Bass |
| 33–48 | Drums return to the foreground. Bass continues underneath. | Drums |
| 49–64 | Bass reaches its strongest foreground mix. | Bass plus an independent direction choice |

At each block boundary, good play advances the mix one step. A missed block holds the current mix and cue family for another block, giving the player a chance to recover. For example, missing the first drum block and passing the second reveals bass on beat 33. The phase still lasts exactly 64 beats. Reset to drums alone on the next phase downbeat. Use forgiving, tunable thresholds and smooth gains. Leave enough space for hit windows and hold tails to resolve before switching focus. Derive foreground cues from the actual audio position of that part, including when a delayed reveal changes its start time. Keep one required cue family active at a time.

## 3. Routes, difficulty and survival

Show at least two direction arrows throughout beats 49–64, even if the build stalled. Use separate touch targets clear of the pads. The player can select and change their direction until the phase ends. Highlight their choice and use a marked default when they make none. Commit the destination and next sound treatment on the next downbeat.

Use the result of the first 48 beats to pick a riser or falling effect for the choice window. Start with a riser when the final bass stage has been reached by beat 49 and a falling effect otherwise. The last block still counts toward survival. Honour the selected route if the run survives.

Sibling routes may lead to different places and sound different. **At the same progression point, use the same chart, timing, pad assignments and judgement across those choices.** Give the routes compatible alternate renders of the same music where available, or give the same recordings distinct drum and bass treatments. The Warehouse export sets have different notes, so use them as separate authored phrases. Increase rhythm difficulty with level progression through cue density, syncopation and holds. Keep sibling destinations at the same difficulty tier.

Carry music, the beat grid and crowd energy through room and world transitions. Use crowd energy as the survival meter. Good phrases restore it and sustained poor play depletes it. At depletion, end on a musical boundary with a short fade. A rough block should be recoverable. Give the final worlds onward loops so strong play can continue.

Save a level as reached when the player enters it. Offer Play, Start from a reached level and Settings on the home screen. A restart from a reached level uses its authored opening and fresh energy. Offer retry and reached-level selection after a loss. Handle existing story saves and explain the migration behaviour.

Use Night One/Warehouse as the starting world, Mothership and Underworld as next-tier alternatives, and Hospital and Ward as later alternatives. Build playable routes through all five worlds. Preload candidate audio and rooms in time to meet the next downbeat. Keep the song clock, chart, mix and route deadlines synchronized through pause, resume and calibration.

## 4. Make every level accept the working music format

Build on the tested Warehouse import. Use the owner's actual WAVs for Level 1 playback and their paired MIDI for cues. Accept Beat Shaper exports in a ZIP or folder with matching `Drums`, `Bass` and `Synth` WAV/MIDI files. Group by project name and variant suffix so `(1)` and `(2)` files stay with their matching stems. Keep source files intact and write any decoded, trimmed or padded copies to generated assets.

The tested archive contains an unsuffixed Warehouse set, two numbered Warehouse sets, and one Default Project set. The WAVs are stereo 48 kHz float PCM with unequal lengths. The MIDI headers say 120 BPM, but the drum recordings align at an effective 87 BPM per source quarter. Preserve the verified Warehouse mapping of two game beats per source quarter at 174 BPM, with the WAVs at original speed. Treat 16 source quarters as a 32-game-beat phrase. Check bass alignment and preserve the exact musical loop boundary separately from release tails. Keep that tempo override specific to the verified export profile. Validate the timing of later packs before applying it.

Keep the mixed Drum WAV intact. Derive kick and snare cues from the Drum MIDI, with notes 36 and 40 for Warehouse. Leave the hats audible. Derive bass onsets, pad assignments and playable holds from the Bass MIDI. Resolve overlaps and thin early charts in the generated cue data while retaining the source timing for selected notes. Use Synth as backing in Warehouse and bring it in quietly with the bass reveal. Start Bass and Synth from a common phrase origin at that reveal, then keep both running as foreground focus changes. Cue the bass against the offset the player is actually hearing.

Give each world a data-driven music assignment and a playable default. Use existing compatible recordings or labelled temporary assets for levels awaiting new music. Support assigning a new imported set to a level or phase without code changes or loadout registration. Preserve level and route IDs when replacing music. Keep asset IDs and generated outputs stable so repeated imports are safe.

Provide one documented import workflow with a validation step and a worked example that assigns a new pack to a level. Validate pairing, duplicate IDs, WAV/MIDI timing, playable cue ranges and loop coverage. Report the files accepted and any missing or ambiguous pairs. Give the owner a per-level music handoff sheet listing the exact exports and filenames, how many sets are needed to replace each level's defaults, the musical length and tempo expectations, and where to put and import them. Use the format the owner already exports.

## 5. Verify and hand off

Prove the new loop in Warehouse first, including the four-step mix, a delayed reveal, both transition effects, changing direction, the default route and failure/restart. Verify a live transition to another world and that entry unlocks its restart point. Extend the same system through the other four worlds.

Check that matching WAVs and MIDI drive the audible music and visible cues, with no drift across repeated boundaries. Check that alternate routes use identical required cue events for the same phase and that a level change can increase chart difficulty. Confirm that long holds, touch selection, pause/resume and asset loading work in a phone-sized landscape view. Exercise the new music assignment workflow on a later level using existing or temporary content so the owner can replace it when their recordings are ready.

Deliver the baseline `main` merge SHA, the overhaul branch and its launch instructions. Update the README and handover with the route map, per-level music setup, import procedure and verification results. Identify which checks were automated, listened to or played by hand, along with any remaining issues.
