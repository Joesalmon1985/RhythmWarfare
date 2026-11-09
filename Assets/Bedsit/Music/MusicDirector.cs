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

        bool TryScheduleBuild(string songId, string anchor, double now)
        {
            var song = _songs.Find(songId);
            double bs = BeatSeconds, D;
            if (_rec != null && _recSong.id == songId)
            {
                D = RecTimeOfAnchor(anchor);
                if (D <= now) { L($"build {songId}:{anchor} rejected: anchor already reached ({D:0.000} <= {now:0.000})"); return false; }
            }
            else if (_rec == null) D = now + S.startDelaySeconds + S.buildBeats * bs;
            else { L($"build {songId}:{anchor} rejected: a different recording is playing"); return false; }

            double start = D - S.buildBeats * bs;
            if (start < now + S.prepMarginBeats * bs) { L($"build {songId}:{anchor} rejected: not enough time (start {start:0.000} < now+margin)"); return false; }
            ScheduleBuild(song, anchor, D, start);
            return true;
        }

        void ScheduleBuild(SongDef song, string anchor, double D, double start)
        {
            double bs = BeatSeconds;
            BuildsStarted++;
            PendingPlan = $"build {song.id}:{anchor} start {start:0.000} drop {D:0.000}";
            L($"BUILD {song.id}:{anchor} scheduled: start {start:0.000}, drop {D:0.000} ({S.buildBeats} beats)");

            At(start - 8 * bs, "rhythm lead-in", () => { Mode = MusicMode.Rhythm; });

            // recording hands the floor to the custom arrangement (simultaneous cross-fade)
            if (_rec != null)
            {
                double fade = S.recordedFadeBeatsAtBuild * bs;
                Mixer.RampTo(_rec, start, start + fade, 0f);
                Mixer.StopAt(_rec, start + fade);
                var old = _rec;
                At(start + fade, "recording cleared", () => { if (_rec == old) _rec = null; });
            }

            CreateStemVoices(start, S.buildBeats / (double)_loops.loopBeats);
            ScheduleLayout(start, 0, Math.Max(_plan.buildLoops.Length, 1), true);
            var notes = new List<Note>();
            for (int k = 0; k < _plan.buildLoops.Length; k++) notes.AddRange(NotesForLoop(start, k, _plan.buildLoops[k].charted));
            var win = Judge.AddWindow($"build {song.id}:{anchor}", start, D - bs, S.threshold, notes);
            At(start, "window open", () => { CurrentWindow = win; });
            At(D - S.evalLeadSeconds, "evaluate build", () => EvaluateBuild(win, song, anchor, D, 0));
        }

        void CreateStemVoices(double start, double loopsCount)
        {
            _stemVoices.Clear(); _muted.Clear(); _hitsSinceMute.Clear();
            foreach (var st in _loops.stems)
            {
                if (!_stemPcm.TryGetValue(st.id, out var clip)) continue;
                var v = Mixer.Play("stem:" + st.id, clip, start, 0, 0f, loop: true, role: "custom");
                _stemVoices[st.id] = v; _muted[st.id] = false; _hitsSinceMute[st.id] = 0;
            }
        }

        /// <summary>Arrangement ramps: which stems are audible in each 8-bar loop of the build.</summary>
        void ScheduleLayout(double start, int firstLoop, int loopCount, bool fadeIn)
        {
            double bs = BeatSeconds;
            for (int k = firstLoop; k < firstLoop + loopCount; k++)
            {
                var def = _plan.buildLoops[Math.Min(k, _plan.buildLoops.Length - 1)];
                double t = start + k * _loops.loopBeats * bs;
                foreach (var kv in _stemVoices)
                {
                    float target = def.audible.Contains(kv.Key) ? S.customGain : 0f;
                    if (k == firstLoop && fadeIn) Mixer.RampTo(kv.Value, t, t + S.customFadeInBeats * bs, target);
                    else Mixer.RampTo(kv.Value, t - 0.01, t + 0.04, target);
                }
            }
        }

        List<Note> NotesForLoop(double start, int k, string[] charted)
        {
            var list = new List<Note>(); double bs = BeatSeconds;
            foreach (var stemId in charted)
            {
                var st = _loops.Find(stemId); if (st == null) continue;
                foreach (var c in st.cues)
                {
                    double beat = c.tick / (double)_loops.ticksPerBeat;
                    if (beat > _loops.loopBeats - 1 + 1e-6) continue;             // keep the last beat before the drop free
                    list.Add(new Note { Time = start + (k * _loops.loopBeats + beat) * bs, Pad = c.pad, Stem = stemId });
                }
            }
            return list;
        }

        void EvaluateBuild(JudgeWindow win, SongDef song, string anchor, double D, int recoveryAttempt)
        {
            Judge.Update(Mixer.Time);
            Judge.Close(win);
            double acc = win.Accuracy;
            bool pass = acc >= win.Threshold;
            L($"EVAL {win.Label}: {win.Hits}/{win.Total} = {acc * 100:0.0}% (threshold {win.Threshold * 100:0}%) -> {(pass ? "PASS" : "FAIL")}");
            if (pass || recoveryAttempt >= S.maxRecoveryAttempts)
            {
                if (!pass) L("recovery attempts exhausted: continuing to the drop anyway (no soft-lock)");
                if (recoveryAttempt == 0) { if (pass) BuildsPassed++; else BuildsFailed++; }
                LastBuildPassed = pass;
                EnterRecordedDrop(song, anchor, D);
            }
            else
            {
                if (recoveryAttempt == 0) BuildsFailed++;
                RecoveryAttempts++;
                ScheduleRecovery(song, anchor, D, recoveryAttempt + 1);
            }
        }

        void EnterRecordedDrop(SongDef song, string anchor, double D)
        {
            double bs = BeatSeconds;
            _rec = Mixer.Play(song.id, _songPcm[song.id], D, song.Anchor(anchor), S.recordedGain, role: "recorded");
            _recSong = song;
            foreach (var kv in _stemVoices)
            {
                Mixer.RampTo(kv.Value, D, D + S.customFadeBeats * bs, 0f);
                Mixer.StopAt(kv.Value, D + S.customFadeBeats * bs + 0.01);
            }
            PendingPlan = $"mixing {song.id} from {anchor}";
            L($"DROP {song.id}:{anchor} at {D:0.000}");
            At(D, "mixing mode", () => { Mode = MusicMode.Mixing; CurrentWindow = null; Judge.Enabled = true; AdvanceAfterDrop(D); });
        }

        void ScheduleRecovery(SongDef song, string anchor, double start, int attempt)
        {
            double bs = BeatSeconds;
            double end = start + S.recoveryBeats * bs;
            L($"RECOVERY #{attempt}: custom phrase {start:0.000} -> {end:0.000}, then drop {song.id}:{anchor}");
            PendingPlan = $"recovery #{attempt} until {end:0.000}, then {song.id}:{anchor}";
            // custom stems keep looping (never silent); arrangement = loop 2 of the build layout
            foreach (var kv in _stemVoices)
            {
                var def = _plan.buildLoops[Math.Min(2, _plan.buildLoops.Length - 1)];
                Mixer.RampTo(kv.Value, start - 0.01, start + 0.04, def.audible.Contains(kv.Key) ? S.customGain : 0f);
            }
            var notes = NotesForLoop(start, 0, _plan.buildLoops[Math.Min(2, _plan.buildLoops.Length - 1)].charted);
            var win = Judge.AddWindow($"recovery#{attempt} {song.id}:{anchor}", start, end - bs, S.recoveryThreshold, notes);
            At(start, "recovery window open", () => { CurrentWindow = win; });
            At(end - S.evalLeadSeconds, "evaluate recovery", () => EvaluateBuild(win, song, anchor, end, attempt));
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
            double bs = BeatSeconds, lead = S.buildBeats * bs;
            if (D <= now) { L($"handover rejected: outgoing anchor already reached ({D:0.000} <= {now:0.000})"); return false; }
            double entry = D - lead;
            double clipPos = inSong.Anchor(inAnchor) - S.buildBeats * inSong.BeatSeconds;
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
                    if (c.D - S.buildBeats * bs >= now + S.prepMarginBeats * bs && ScheduleHandover(to, string.IsNullOrEmpty(leg.toAnchor) ? "firstDrop" : leg.toAnchor, c.D, now, c.a)) return true;
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
            double start = endT + 4 * bs, D = start + S.buildBeats * bs;
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
            if (CurrentWindow != null && !CurrentWindow.Closed) return ("drop (" + CurrentWindow.Label + ")", CurrentWindow.End + BeatSeconds);
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
