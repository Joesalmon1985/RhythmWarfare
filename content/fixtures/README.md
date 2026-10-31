    python tools/content/make_fixtures.py

- replacement/groove_watch/kick__kick_march.wav: a stand-in for an owner render of the groove_watch kick part with the
  March Kick sound: a long 808-style kick, 48 kHz stereo 16-bit, the clip's two bars plus a half-bar release tail.
- replacement/groove_watch/kick.mid: an edited structure MIDI for the same part: the original two kicks plus one on
  beat 4 of bar 1, as an Ableton type 1 export at 96 PPQ with no tempo event (the build rescales the PPQ exactly and
  uses the recorded 174 BPM).
- example_groove/: an example asset folder to copy into content/library/ (clip.json, kick.mid, snare.mid).
- waves_fixture.json and mission_fixture.json: a short mission the tests build into a temporary folder.
`tools/content/test_content.py` uses all of them; nothing here is part of the shipped campaign.
