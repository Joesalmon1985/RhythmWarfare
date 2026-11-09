using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Bedsit.Music
{
    public enum MusicMode { Rhythm, Mixing }

    /// <summary>
    /// Executes the plan (plan.json) on one authoritative timeline. It schedules recordings and custom stems on the Mixer at
    /// absolute timeline times, creates judged windows for the playable builds, evaluates them at the drop and branches
    /// (success -> recorded drop, failure -> recovery phrase), and handles handovers between recordings.
    /// It never moves a recording backwards and never schedules an incoming build from an anchor that has already passed.
    /// </summary>
    public sealed class MusicDirector
    {
        public readonly Mixer Mixer;
        public readonly RhythmJudge Judge;
        readonly SongManifest _songs;
        readonly PlanDef _plan;
        readonly LoopManifest _loops;
        readonly Dictionary<string, PcmClip> _songPcm;
        readonly Dictionary<string, PcmClip> _stemPcm;
        PlanSettings S => _plan.settings;

        public MusicMode Mode { get; private set; } = MusicMode.Mixing;
        public readonly List<string> Log = new List<string>();
        public bool Started { get; private set; }

        // recorded deck
        Mixer.Voice _rec; SongDef _recSong;
        // custom layer
        readonly Dictionary<string, Mixer.Voice> _stemVoices = new Dictionary<string, Mixer.Voice>();
        readonly Dictionary<string, bool> _muted = new Dictionary<string, bool>();
        readonly Dictionary<string, int> _hitsSinceMute = new Dictionary<string, int>();
        public IReadOnlyDictionary<string, bool> StemMuted => _muted;

        // plan state
        int _leg;
        readonly List<(double t, string label, Action a)> _events = new List<(double, string, Action)>();
        public JudgeWindow CurrentWindow { get; private set; }
        public string IncomingSong { get; private set; }
        public double IncomingEntryTime { get; private set; }
        public string PendingPlan { get; private set; } = "none";
        public int RecoveryAttempts { get; private set; }
        public int BuildsStarted, BuildsPassed, BuildsFailed, HandoversDone;
        public bool LastBuildPassed;
        public string CurrentSongId => _recSong?.id;
        public double BeatSeconds { get; private set; } = 60.0 / 174.0;

        public MusicDirector(Mixer mixer, RhythmJudge judge, SongManifest songs, PlanDef plan, LoopManifest loops,
                             Dictionary<string, PcmClip> songPcm, Dictionary<string, PcmClip> stemPcm)
        {
            Mixer = mixer; Judge = judge; _songs = songs; _plan = plan; _loops = loops; _songPcm = songPcm; _stemPcm = stemPcm;
            Judge.PerfectWindow = S.judgePerfectSeconds; Judge.GoodWindow = S.judgeGoodSeconds;
            Judge.NoteMissed += OnMiss; Judge.NoteHit += OnHit;
        }

        bool Avail(string id) { var s = _songs.Find(id); return s != null && s.available && _songPcm.ContainsKey(id); }
        void L(string msg) { Log.Add($"[{Mixer.Time:0.000}] {msg}"); }

        // ------------------------------------------------------------------------------------------------ driving

        public void Start()
        {
            Started = true;
            _leg = 0;
            BeginLeg(Mixer.Time);
        }

        /// <summary>Call regularly (every audio block / frame) with the current timeline time.</summary>
        public void Update(double now)
        {
            if (!Started) return;
            Judge.Update(now);
            for (int guard = 0; guard < 64; guard++)
            {
                int idx = -1; double best = double.MaxValue;
                for (int i = 0; i < _events.Count; i++) if (_events[i].t <= now && _events[i].t < best) { best = _events[i].t; idx = i; }
                if (idx < 0) break;
                var e = _events[idx]; _events.RemoveAt(idx);
                e.a();
            }
        }

        void At(double t, string label, Action a) { _events.Add((t, label, a)); }

        // ------------------------------------------------------------------------------------------------ legs

        void BeginLeg(double now)
        {
            while (true)
            {
                if (_plan.legs == null || _plan.legs.Length == 0) { PendingPlan = "no legs"; return; }
                if (_leg >= _plan.legs.Length) _leg = 1;               // cycle (legs[0] is the opening build)
                var leg = _plan.legs[_leg];
                bool ok = false;
                switch (leg.type)
                {
                    case "build": ok = Avail(leg.song) && TryScheduleBuild(leg.song, leg.anchor, now); break;
                    case "handover":
                        ok = Avail(leg.from) && Avail(leg.to) && TryScheduleHandover(leg.from, leg.fromAnchor, leg.to, leg.toAnchor, now);
                        if (!ok && leg.fallbackType == "build")
                        {
                            ok = Avail(leg.fallbackSong) && TryScheduleBuild(leg.fallbackSong, leg.fallbackAnchor, now);
                            if (ok) L($"{leg.id}: handover to '{leg.to}' unavailable -> fallback build {leg.fallbackSong}:{leg.fallbackAnchor}");
                        }
                        break;
                    case "repeat": ok = TryScheduleRepeat(leg, now); break;
                }
                if (ok) return;
                L($"{leg.id} ({leg.type}) skipped: unavailable or no valid future anchor");
                _leg++;
                if (_leg > _plan.legs.Length + 2) { PendingPlan = "nothing schedulable"; return; }
            }
        }

        void AdvanceAfterDrop(double dropTime)
        {
            var leg = _plan.legs[Math.Min(_leg, _plan.legs.Length - 1)];
            _leg = leg.type == "repeat" ? 1 : _leg + 1;
            BeginLeg(dropTime);
        }

        // ------------------------------------------------------------------------------------------------ timeline helpers

        double RecTimeOfAnchor(string anchor) => Mixer.TimelineOfClipTime(_rec, _recSong.Anchor(anchor));

        // ------------------------------------------------------------------------------------------------ builds
        //
        // A playable build is a short run of 32-beat phases (plan.json "buildLoops"): e.g. drums (warm-up) -> bass (gate) ->
        // drums with the recording's own buildup fading in underneath (gate) -> the recorded drop. A failed gate repeats that
        // phase as a recovery attempt: the custom loops never stop and the recording is never rewound mid-track (a failed
        // buildup is faded out and re-entered fresh), so there is no silence. After maxRecoveryAttempts the build moves on anyway.

        sealed class Build
        {
            public SongDef Song; public string Anchor;
            public int Recoveries;
            public Mixer.Voice Rec;            // the recording voice of the current buildup attempt
            public double PlannedDrop;         // drop time if every remaining phase passes first time
        }
        Build _build;

        double BuildTotalSeconds => _plan.buildLoops.Length * (double)_loops.loopBeats * BeatSeconds;
        double BuildupClipStart(SongDef song, string anchor) => song.Anchor(anchor) - _loops.loopBeats * song.BeatSeconds;

        bool TryScheduleBuild(string songId, string anchor, double now)
        {
            var song = _songs.Find(songId);
            double bs = BeatSeconds, total = BuildTotalSeconds, D;
            if (_rec != null && _recSong.id == songId)
            {
                D = RecTimeOfAnchor(anchor);
                if (D <= now) { L($"build {songId}:{anchor} rejected: anchor already reached ({D:0.000} <= {now:0.000})"); return false; }
            }
            else if (_rec == null) D = now + S.startDelaySeconds + total;
            else { L($"build {songId}:{anchor} rejected: a different recording is playing"); return false; }

            double start = D - total;
            if (start < now + S.prepMarginBeats * bs) { L($"build {songId}:{anchor} rejected: not enough time (start {start:0.000} < now+margin)"); return false; }
            if (BuildupClipStart(song, anchor) < 0) { L($"build {songId}:{anchor} rejected: buildup entry cue {BuildupClipStart(song, anchor):0.000}s is before the start of the file"); return false; }
            ScheduleBuild(song, anchor, D, start);
            return true;
        }

        void ScheduleBuild(SongDef song, string anchor, double D, double start)
        {
            double bs = BeatSeconds;
            BuildsStarted++;
            var b = _build = new Build { Song = song, Anchor = anchor, PlannedDrop = D };
            PendingPlan = $"build {song.id}:{anchor} start {start:0.000} drop {D:0.000}";
            L($"BUILD {song.id}:{anchor} scheduled: start {start:0.000}, drop {D:0.000} ({_plan.buildLoops.Length} phases: {string.Join(" / ", _plan.buildLoops.Select(l => l.id))})");

            At(start - 8 * bs, "rhythm lead-in", () => { Mode = MusicMode.Rhythm; });

            // a recording that was playing hands the floor to the custom arrangement (simultaneous cross-fade)
            if (_rec != null)
            {
                double fade = S.recordedFadeBeatsAtBuild * bs;
                Mixer.RampTo(_rec, start, start + fade, 0f);
                Mixer.StopAt(_rec, start + fade);
                var old = _rec;
                At(start + fade, "recording cleared", () => { if (_rec == old) _rec = null; });
            }

            CreateStemVoices(start);
            RunPhase(b, 0, start, 0);
        }

        void CreateStemVoices(double start)
        {
            _stemVoices.Clear(); _muted.Clear(); _hitsSinceMute.Clear();
            foreach (var st in _loops.stems)
            {
                if (!_stemPcm.TryGetValue(st.id, out var clip)) continue;
                var v = Mixer.Play("stem:" + st.id, clip, start, 0, 0f, loop: true, role: "custom");
                _stemVoices[st.id] = v; _muted[st.id] = false; _hitsSinceMute[st.id] = 0;
            }
        }

        /// <summary>Schedule phase <paramref name="k"/> of the build to start at timeline time <paramref name="t"/> (attempt 0 = first try).</summary>
        void RunPhase(Build b, int k, double t, int attempt)
        {
            double bs = BeatSeconds;
            int n = _plan.buildLoops.Length;
            var def = _plan.buildLoops[k];
            double loop = _loops.loopBeats * bs, end = t + loop;
            bool buildup = def.recording;
            double freeBeats = buildup ? S.buildupFreeBeats : 1;
            string name = string.IsNullOrEmpty(def.id) ? "phase" + k : def.id;
            string label = attempt == 0 ? $"{b.Song.id}:{b.Anchor} {name}" : $"recovery#{attempt} {b.Song.id}:{b.Anchor} {name}";
            double threshold = !def.gate ? 0.0 : (attempt == 0 ? S.threshold : S.recoveryThreshold);
            double plannedDrop = t + (n - k) * loop;

            // arrangement: which custom stems are audible in this phase (eased in/out around the recording's buildup)
            foreach (var kv in _stemVoices)
            {
                bool audible = def.audible.Contains(kv.Key);
                float target = !audible ? 0f : (buildup ? S.customGainUnderRecording : S.customGain);
                if (k == 0 && attempt == 0) Mixer.RampTo(kv.Value, t, t + S.customFadeInBeats * bs, target);
                else if (buildup) Mixer.RampTo(kv.Value, t, t + S.buildupCrossfadeBeats * bs, target);
                else Mixer.RampTo(kv.Value, t - 0.01, t + 0.04, target);
            }

            // the recording's own buildup (its last loop before the drop) enters gradually
            if (buildup)
            {
                double clip = BuildupClipStart(b.Song, b.Anchor);
                var v = Mixer.Play(b.Song.id, _songPcm[b.Song.id], t, clip, 0f, role: "recorded");
                Mixer.RampTo(v, t, t + S.buildupFadeInBeats * bs, S.recordedGain);
                b.Rec = v;
                L($"buildup: {b.Song.id} enters at {t:0.000} (clip {clip:0.000}s), eases in over {S.buildupFadeInBeats:0} beats; drop {plannedDrop:0.000}");
            }

            // judged notes (a note on the very last beat(s) before the drop is never charted)
            double lastBeat = _loops.loopBeats - freeBeats - (buildup ? 1 : 0);
            var notes = NotesForPhase(t, def.charted, lastBeat);
            double winEnd = buildup ? end - S.buildupFreeBeats * bs : end - bs;
            var win = Judge.AddWindow(label, t, winEnd, threshold, notes);
            At(t, "phase start", () => { CurrentWindow = win; b.PlannedDrop = plannedDrop; RestoreAllStems(); PendingPlan = $"build {b.Song.id}:{b.Anchor} - {name}{(attempt > 0 ? " (recovery " + attempt + ")" : "")}, drop planned {plannedDrop:0.000}"; });
            double evalAt = (buildup ? winEnd : end) - S.evalLeadSeconds;
            At(evalAt, "phase end", () => OnPhaseEnd(b, k, win, end, attempt));
        }

        List<Note> NotesForPhase(double t, string[] charted, double lastBeat)
        {
            var list = new List<Note>(); double bs = BeatSeconds;
            foreach (var stemId in charted)
            {
                var st = _loops.Find(stemId); if (st == null) continue;
                foreach (var c in st.cues)
                {
                    double beat = c.tick / (double)_loops.ticksPerBeat;
                    if (beat > lastBeat + 1e-6) continue;
                    list.Add(new Note { Time = t + beat * bs, Pad = c.pad, Stem = stemId });
                }
            }
            return list;
        }

        void OnPhaseEnd(Build b, int k, JudgeWindow win, double end, int attempt)
        {
            Judge.Update(Mixer.Time);
            Judge.Close(win);
            var def = _plan.buildLoops[k];
            bool last = k == _plan.buildLoops.Length - 1;
            double acc = win.Accuracy;
            if (!def.gate)
            {
                L($"{win.Label}: {win.Hits}/{win.Total} = {acc * 100:0.0}% (warm-up loop, not gated)");
                RunPhase(b, k + 1, end, 0);
                return;
            }
            bool pass = acc >= win.Threshold;
            L($"EVAL {win.Label}: {win.Hits}/{win.Total} = {acc * 100:0.0}% (threshold {win.Threshold * 100:0}%) -> {(pass ? "PASS" : "FAIL")}");
            if (pass || attempt >= S.maxRecoveryAttempts)
            {
                if (!pass) L("recovery attempts exhausted: moving on anyway (no soft-lock)");
                if (!last) RunPhase(b, k + 1, end, 0);
                else FinishBuild(b, pass, end);
                return;
            }
            b.Recoveries++; RecoveryAttempts++;
            if (last && b.Rec != null)
            {
                // the drop is withheld: the buildup eases out before it arrives, the drums go round again, and the buildup re-enters
                Mixer.RampTo(b.Rec, Mixer.Time, end, 0f);
                Mixer.StopAt(b.Rec, end);
                b.Rec = null;
            }
            L($"RECOVERY #{attempt + 1}: {def.id} again {end:0.000} -> {end + _loops.loopBeats * BeatSeconds:0.000}{(last ? " (buildup re-enters, drop held)" : "")}");
            RunPhase(b, k, end, attempt + 1);
        }

        void FinishBuild(Build b, bool pass, double D)
        {
            double bs = BeatSeconds;
            if (b.Recoveries == 0) BuildsPassed++; else BuildsFailed++;
            LastBuildPassed = pass;
            _rec = b.Rec; _recSong = b.Song;
            foreach (var kv in _stemVoices)
            {
                Mixer.RampTo(kv.Value, D, D + S.customFadeBeats * bs, 0f);
                Mixer.StopAt(kv.Value, D + S.customFadeBeats * bs + 0.01);
            }
            PendingPlan = $"mixing {b.Song.id} from {b.Anchor}";
            L($"DROP {b.Song.id}:{b.Anchor} at {D:0.000}");
            At(D, "mixing mode", () => { Mode = MusicMode.Mixing; CurrentWindow = null; _build = null; Judge.Enabled = true; AdvanceAfterDrop(D); });
        }

        void RestoreAllStems()
        {
            foreach (var id in _stemVoices.Keys)
            {
                if (!_muted[id]) continue;
                _muted[id] = false; _hitsSinceMute[id] = 0;
                double t = Mixer.Time + 0.005;
                Mixer.TrimTo(_stemVoices[id], t, t + S.stemRestoreRampSeconds, 1f);
            }
        }

        // ------------------------------------------------------------------------------------------------ handovers

        bool TryScheduleHandover(string from, string fromAnchor, string to, string toAnchor, double now)
        {
            if (_rec == null || _recSong.id != from) { L($"handover {from}->{to} rejected: {from} is not the playing recording"); return false; }
            double D = RecTimeOfAnchor(fromAnchor);
            return ScheduleHandover(_songs.Find(to), toAnchor, D, now, fromAnchor);
        }

        bool ScheduleHandover(SongDef inSong, string inAnchor, double D, double now, string outAnchorName)
        {
            double bs = BeatSeconds, lead = S.handoverLeadBeats * bs;
            if (D <= now) { L($"handover rejected: outgoing anchor already reached ({D:0.000} <= {now:0.000})"); return false; }
            double entry = D - lead;
            double clipPos = inSong.Anchor(inAnchor) - S.handoverLeadBeats * inSong.BeatSeconds;
            if (clipPos < 0) { L($"handover into {inSong.id}:{inAnchor} rejected: entry cue {clipPos:0.000}s is before the start of the file"); return false; }
            if (entry < now + S.prepMarginBeats * bs) { L($"handover rejected: incoming entry {entry:0.000} too soon (now {now:0.000})"); return false; }

            var outgoing = _rec; var outSong = _recSong;
            var inV = Mixer.Play(inSong.id, _songPcm[inSong.id], entry, clipPos, 0f, role: "recorded");
            Mixer.RampTo(inV, entry, entry + 8 * bs, S.recordedGain);
            // fade the outgoing track over the final fadeOutBeats before the shared drop; silence at D (no double drop)
            Mixer.RampTo(outgoing, D - S.fadeOutBeats * bs, D, 0f);
            Mixer.StopAt(outgoing, D);
            IncomingSong = inSong.id; IncomingEntryTime = entry;
            PendingPlan = $"handover {outSong.id}:{outAnchorName} -> {inSong.id}:{inAnchor} entry {entry:0.000} drop {D:0.000}";
            L($"HANDOVER scheduled: {outSong.id} fades {D - S.fadeOutBeats * bs:0.000}->{D:0.000}; {inSong.id} enters {entry:0.000} (clip {clipPos:0.000}s) -> drop {D:0.000}");
            At(D, "handover complete", () =>
            {
                _rec = inV; _recSong = inSong; IncomingSong = null; HandoversDone++;
                L($"HANDOVER done: {inSong.id}:{inAnchor} drop at {D:0.000}");
                AdvanceAfterDrop(D);
            });
            return true;
        }

        bool TryScheduleRepeat(LegDef leg, double now)
        {
            if (!Avail(leg.to)) return false;
            var to = _songs.Find(leg.to);
            double bs = BeatSeconds;
            if (_rec != null && _recSong.id != to.id)
            {
                // earliest outgoing anchor that is still ahead AND leaves enough time for the incoming introduction
                var cands = new List<(double D, string a)>();
                foreach (var a in leg.outgoingCandidates) cands.Add((RecTimeOfAnchor(a), a));
                cands.Sort((x, y) => x.D.CompareTo(y.D));
                foreach (var c in cands)
                    if (c.D - S.handoverLeadBeats * bs >= now + S.prepMarginBeats * bs && ScheduleHandover(to, string.IsNullOrEmpty(leg.toAnchor) ? "firstDrop" : leg.toAnchor, c.D, now, c.a)) return true;
                L("repeat: no outgoing anchor leaves enough time");
                return false;
            }
            // same song (or nothing playing): restart a fresh cycle after the current recording reaches its ending
            double endT = now;
            if (_rec != null)
            {
                endT = RecTimeOfAnchor("ending");
                if (endT <= now) endT = now;
                Mixer.RampTo(_rec, endT - 8 * bs, endT, 0f);
                Mixer.StopAt(_rec, endT);
                var old = _rec;
                At(endT, "recording ended", () => { if (_rec == old) _rec = null; });
            }
            double start = endT + 4 * bs, D = start + BuildTotalSeconds;
            L($"REPEAT: restarting {to.id} after the ending at {endT:0.000}");
            ScheduleBuild(to, "firstDrop", D, start);
            return true;
        }

        // ------------------------------------------------------------------------------------------------ mistakes

        void OnMiss(Note n)
        {
            if (!_stemVoices.TryGetValue(n.Stem, out var v)) return;
            if (_muted[n.Stem]) return;
            _muted[n.Stem] = true; _hitsSinceMute[n.Stem] = 0;
            double t = Mixer.Time + 0.005;
            Mixer.TrimTo(v, t, t + S.stemMuteRampSeconds, S.stemMuteLevel);
            L($"MISS {n.Stem} pad {n.Pad}: stem muted (timeline keeps running)");
        }

        void OnHit(Note n)
        {
            if (!_stemVoices.TryGetValue(n.Stem, out var v) || !_muted[n.Stem]) return;
            if (++_hitsSinceMute[n.Stem] >= S.restoreAfterHits)
            {
                _muted[n.Stem] = false;
                double t = Mixer.Time + 0.005;
                Mixer.TrimTo(v, t, t + S.stemRestoreRampSeconds, 1f);
                L($"RECOVERED {n.Stem}: stem restored at its current musical position");
            }
        }

        // ------------------------------------------------------------------------------------------------ status

        public double RecordedPosition(double now) => _rec != null ? Mixer.ClipTimeAt(_rec, now) : -1;

        public (string anchor, double time) NextAnchor(double now)
        {
            if (_rec != null)
            {
                string best = null; double bt = double.MaxValue;
                foreach (var a in new[] { "firstDrop", "secondDrop", "ending" })
                {
                    double t = RecTimeOfAnchor(a);
                    if (t > now && t < bt) { bt = t; best = _recSong.id + ":" + a; }
                }
                if (best != null) return (best, bt);
            }
            if (_build != null) return ("drop (" + _build.Song.id + ":" + _build.Anchor + ", if the gates pass)", _build.PlannedDrop);
            return ("-", 0);
        }

        public string StatusText(double now)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"mode {Mode.ToString().ToUpper()}   t={now:0.00}s   song {(CurrentSongId ?? "-")}  pos {(RecordedPosition(now) >= 0 ? RecordedPosition(now).ToString("0.00") + "s" : "-")}");
            var (a, t) = NextAnchor(now);
            sb.AppendLine($"beat {(now / BeatSeconds):0.0}   next anchor {a} {(t > 0 ? "in " + (t - now).ToString("0.0") + "s" : "")}");
            sb.AppendLine($"incoming {(IncomingSong ?? "-")} {(IncomingSong != null ? "enters " + IncomingEntryTime.ToString("0.00") : "")}");
            if (CurrentWindow != null) sb.AppendLine($"window {CurrentWindow.Label}: {CurrentWindow.Hits}/{CurrentWindow.Total} = {CurrentWindow.Accuracy * 100:0}% (need {CurrentWindow.Threshold * 100:0}%)  missed {CurrentWindow.Misses}");
            else sb.AppendLine("window -");
            sb.AppendLine("stems muted: " + (string.Join(",", _muted.Where(k => k.Value).Select(k => k.Key)).Length == 0 ? "none" : string.Join(",", _muted.Where(k => k.Value).Select(k => k.Key))));
            sb.AppendLine("plan: " + PendingPlan);
            sb.AppendLine($"builds {BuildsPassed}/{BuildsStarted} passed, recoveries {RecoveryAttempts}, handovers {HandoversDone}, stray taps {Judge.StrayTaps}, energy {Judge.Energy * 100:0}%");
            return sb.ToString();
        }
    }
}
