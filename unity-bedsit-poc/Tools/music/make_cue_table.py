"""Derive the 8 candidate entry cues per song (first/second drop -128/-256/-384 beats, ending -128/-256) from
songs.json - same arithmetic as CueMath.Derive in the game. Writes Docs/music/cue_table.md and cue_table.json.
Invalid cues (negative / beyond the file) are listed and flagged, never clamped."""
import json, os, sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
songs = json.load(open(os.path.join(root, 'Assets/Bedsit/Music/Resources/Music/songs.json'), encoding='utf-8'))['songs']
CANDS = [('firstDrop', [128, 256, 384]), ('secondDrop', [128, 256, 384]), ('ending', [128, 256])]
OWNER = {'firstDrop': 'ownerFirstDrop', 'secondDrop': 'ownerSecondDrop', 'ending': 'ownerEnding'}

out, md = [], []
md.append('# Cue table (derived)\n')
md.append('`cue = anchor - beats * 60/BPM`. A cue is **invalid** if it falls before the start of the file or after its end; invalid cues are '
          'listed, never clamped. "owner" columns use the supplied reference timestamps; "used" columns use the anchors the game aligns to '
          '(measured from the audio where the file exists, otherwise the owner timestamps).\n')
for s in songs:
    beat = 60.0 / s['bpm']
    md.append(f"\n## {s['title']} - {s['artist']}  (`{s['id']}`, {s['bpm']} BPM, "
              f"{'audio on this PC' if s['available'] else '**audio NOT on this PC** - owner timestamps only'})\n")
    md.append('| anchor | beats before | owner cue (s) | used cue (s) | valid | note |')
    md.append('|---|---:|---:|---:|:---:|---|')
    for anchor, beats in CANDS:
        for b in beats:
            row = {}
            for label, a in (('owner', s[OWNER[anchor]]), ('used', s[anchor])):
                t = a - b * beat
                row[label] = t
            dur = s['durationSeconds']
            valid = row['used'] >= 0 and (dur <= 0 or row['used'] < dur)
            note = '' if valid else ('before the start of the file' if row['used'] < 0 else 'after the end of the file')
            out.append({'song': s['id'], 'anchor': anchor, 'beatsBefore': b, 'ownerTime': round(row['owner'], 4),
                        'time': round(row['used'], 4), 'valid': valid, 'reason': note})
            md.append(f"| {anchor} | {b} | {row['owner']:.3f} | {row['used']:.3f} | {'yes' if valid else '**NO**'} | {note} |")
open(os.path.join(root, 'Docs/music/cue_table.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
json.dump(out, open(os.path.join(root, 'Docs/music/cue_table.json'), 'w', encoding='utf-8'), indent=1)
print('cues', len(out), 'invalid', sum(1 for c in out if not c['valid']))
