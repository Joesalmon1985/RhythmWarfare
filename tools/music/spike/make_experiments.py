"""THROWAWAY (M2.1 spike): writes the experiment list the spike scene plays (exit and entry points as RunTrackPlan computes them: entry bar = first drop bar - 16, exit at the end of lap 2)."""
import json, math, sys, os
PACKS = sys.argv[1]; OUT = sys.argv[2]

def pk(tid):
    d = json.load(open(os.path.join(PACKS, tid, 'track.json'), encoding='utf-8'))
    bpm = float(d['tempo']['bpm']); fd = float(d['tempo']['first_downbeat_s']); bar = 240.0 / bpm
    drop = next(s for s in d['sections'] if s['role'] == 'drop')
    dbar = round((float(drop['start_s']) - fd) / bar)
    E = dbar - 16
    stems = [dict(key=v['key'], stem=v['stem'], gain=float(v.get('gain', 1.0))) for v in d['voices']] + \
            [dict(key=b['key'], stem=b['stem'], gain=float(b.get('gain', 1.0))) for b in d.get('backing', [])]
    return dict(id=tid, dir=os.path.join(PACKS, tid).replace(chr(92), '/'), bpm=bpm, fd=fd, bar=bar, drop_bar=dbar, E=E,
                entry_t=fd + E * bar, exit_t=fd + (E + 32) * bar, stems=stems)

def blend(name, o, i, W=12, pauses=0, pitch_shift=False, pre=3.0):
    rho = i['bpm'] / o['bpm']
    return dict(name=name, mode='blend', out=o, inc=i, out_t_at_T=o['exit_t'], in_entry_t=i['entry_t'], rate=rho,
                cents=1200 * math.log2(rho), W=W, bar_in=i['bar'], beat_out=o['bar'] / 4, pre_s=pre, pauses=pauses,
                pitch_shift=pitch_shift, complete_s=W * i['bar'], post_s=W * i['bar'] + 1.0)

def echo(name, o, i, effects=True):
    W = 2
    return dict(name=name, mode='echo_out', out=o, inc=i, out_t_at_T=o['exit_t'], in_entry_t=i['entry_t'], rate=1.0, cents=0.0, W=W,
                bar_in=i['bar'], beat_out=o['bar'] / 4, pre_s=3.0, pauses=0, pitch_shift=False, effects=effects,
                complete_s=W * i['bar'], post_s=W * i['bar'] + 1.5)

chase, stimpy = pk('chase_status_no_problem_original_mix'), pk('stimpy_party_last_sounds')
ung, amp = pk('unglued_telefonik'), pk('amplify_crossy_badman')
tern, acuna = pk('ternion_sound_artifice'), pk('acuna_go_back')
exps = [
    blend('blend_175_172', chase, stimpy),
    blend('blend_172_177', ung, amp),
    blend('blend_175_172_pauses', chase, stimpy, pauses=10),
    blend('blend_175_172_pitchshift', chase, stimpy, pitch_shift=True),
    echo('echo_140_174', tern, acuna, effects=True),
    echo('cut_steps_140_174', tern, acuna, effects=False),
    dict(name='pitchshift_identity', mode='identity', out=chase, out_t_at_T=chase['exit_t'], pre_s=1.0, post_s=6.0, rate=1.0, pitch_shift=True),
    dict(name='cpu', mode='cpu', out=chase, inc=stimpy, out_t_at_T=chase['exit_t'], in_entry_t=stimpy['entry_t'], rate=stimpy['bpm'] / chase['bpm'], seg_s=8.0),
]
json.dump(exps, open(OUT, 'w', encoding='utf-8'), indent=1)
for e in exps:
    print(e['name'], e['mode'], 'out_t_at_T=%.3f' % e['out_t_at_T'], 'entry=%.3f' % e.get('in_entry_t', 0), 'rate=%.6f' % e['rate'], 'cents=%.1f' % e.get('cents', 0))
