# Rhythm Warfare defense campaign starter pack

Research refinement: read `Rhythm_Game_Research_and_Refinements.md` first. The musical MIDI is unchanged; level 3 has safer authored thumb placement, and level 2 now has a reduced practice chart over the same music. The new Claude prompt begins with a rhythm-only playtest milestone.

1. Read `Defense_Campaign_Design_and_Workflow.md` for the ten-level plan and audio workflow.
2. Give Claude `Claude_Defense_Campaign_Prompt.md` and attach this ZIP.
3. Use each `First_Three/level_XX/Music/` folder for Ableton rendering. Its combined master is an alternative view, not extra music.
4. Use that level's `Render_Checklist.csv` for slot/profile WAV names and export range.
5. Keep `song.json`, `chart_rules.json` and `player_chart.json` together. The musical source is complete; the player chart selects the current input focus.

Levels 1–3 contain generated musical MIDI and validated proposed authoring charts. Their enemy waves and production recipes are unbalanced starting points. Levels 4–10 are plans only. No game code, actual WAVs, tested defense maps or playable game build are included.

`Authoring_Tools/` contains a reusable reference MIDI-to-chart converter, the example content generator and structural validator. Install `mido==1.3.3` to run them. The implementation prompt asks Claude to integrate the workflow with the current Godot game and complete playable first-three levels.

The new maximum is three equipped bass instruments, superseding the previous four-bass experimental track. Physical input buttons remain independent of instruments and production recipes.
