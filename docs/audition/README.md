# Arrangement audition previews

One WAV per arrangement in `content/music/arrangements/`: the first sections summed at the run's last mix stage (drums 0.45, bass 1.0, synth 0.6), limited,
16-bit stereo, 48 kHz, 30 to 60 s. Written by `tools/content/arrange.py audition`.

The WAVs are in audition/ (gitignored) (44.5 MB in all).
They are over the 30 MiB budget, so they are not committed. Regenerate them with:

    python tools/content/arrange.py audition


| Arrangement | Palette | Family | Bars | Preview | Sections |
| --- | --- | --- | --- | --- | --- |
| hospital_1 | hospital | lv4_hospital | 64 | 33 s | intro 8 (lv4_hospital), breakdown 8 (lv4_hospital_v2), breakdown 8 (lv4_hospital), variation 8 (lv4_hospital_v2), drop 8 (lv4_hospital_v1), build 8 (lv4_hospital), drop 8 (lv4_hospital_v1), ending 8 (lv4_hospital) |
| mothership_1 | mothership | lv2_alien_spaceship | 64 | 33 s | intro 8 (lv2_alien_spaceship), build 8 (lv2_alien_spaceship_v3), build 8 (lv2_alien_spaceship_v2), variation 8 (lv2_alien_spaceship_v3), drop 8 (lv2_alien_spaceship_v2), breakdown 8 (lv2_alien_spaceship), variation 8 (lv2_alien_spaceship_v2), ending 8 (lv2_alien_spaceship) |
| mothership_2 | mothership | lv2_alien_spaceship | 64 | 33 s | intro 8 (lv2_alien_spaceship), build 8 (lv2_alien_spaceship_v3), breakdown 8 (lv2_alien_spaceship), drop 8 (lv2_alien_spaceship_v3), breakdown 8 (lv2_alien_spaceship), variation 8 (lv2_alien_spaceship_v3), variation 8 (lv2_alien_spaceship_v2), ending 8 (lv2_alien_spaceship) |
| mothership_ch1 | mothership | lv2_alien_spaceship | 80 | 33 s | intro 8 (lv2_alien_spaceship), build 8 (lv2_alien_spaceship_v3), variation 8 (lv2_alien_spaceship), drop 8 (lv2_alien_spaceship_v3), breakdown 8 (lv2_alien_spaceship), drop 8 (lv2_alien_spaceship_v2), breakdown 8 (lv2_alien_spaceship_v3), variation 8 (lv2_alien_spaceship), variation 8 (lv2_alien_spaceship_v2), ending 8 (lv2_alien_spaceship) |
| underworld_1 | underworld | lv2_alien_spaceship | 64 | 33 s | intro 8 (lv2_alien_spaceship), build 8 (lv2_alien_spaceship_v2), build 8 (lv2_alien_spaceship), variation 8 (lv2_alien_spaceship_v2), drop 8 (lv2_alien_spaceship_v3), breakdown 8 (lv2_alien_spaceship), drop 8 (lv2_alien_spaceship_v2), ending 8 (lv2_alien_spaceship) |
| ward_1 | ward | lv5_asylum | 64 | 33 s | intro 8 (lv5_asylum), build 8 (lv5_asylum_v2), drop 8 (lv5_asylum), build 8 (lv5_asylum_v3), variation 16 (lv5_asylum), variation 8 (lv5_asylum_v1), ending 8 (lv5_asylum) |
| warehouse_1 | warehouse | lv1_warehouse | 64 | 33 s | intro 8 (lv1_warehouse), build 8 (lv1_warehouse_v1), build 8 (lv1_warehouse_v2), variation 8 (lv1_warehouse), drop 8 (lv1_warehouse_v2), breakdown 8 (lv1_warehouse_v1), drop 8 (lv1_warehouse), ending 8 (lv1_warehouse) |
