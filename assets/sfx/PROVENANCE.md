# Sound effects provenance

These Ogg Vorbis files were extracted by `tools/extract_openra_sounds.py` from the owner's own Red Alert content as installed for OpenRA (`%APPDATA%\OpenRA\Content\ra\v2`: `sounds.mix`, `speech.mix`, `allies.mix`); Red Alert has been freeware since 2008 and the OpenRA engine used to read the packages is GPL. Each `.aud` file is pulled out of its package with `OpenRA.Utility.exe ra --extract <file>` (pinned checkout `C:\Users\joesa\Documents\Cursor\DuelMaster\DuelMasterBattle\WizardRTSHybrid\external\openra`), decoded to 16-bit PCM by the script's pure-Python port of OpenRA's `AudReader` (Westwood compressed and IMA ADPCM), and encoded with ffmpeg (`-c:a libvorbis -q:a 4`) at the native sample rate. Nothing was edited by hand; `sfx.json` lists the source package, AUD format, sample rate and duration of each sound.

Weapon reports come from `mods/ra/weapons/*.yaml`: M1Carbine `gun11`, M60mg `pillbox1`, Vulcan `gun13` (inherited from `^HeavyMG`), Grenade `grenade1`; the sniper rifle is `gun5`; FireballLauncher defines no report.

Commands:

```
python tools/extract_openra_sounds.py --check
python tools/extract_openra_sounds.py
python -m unittest discover -s tools -p "test_extract_openra_sounds.py"
```
