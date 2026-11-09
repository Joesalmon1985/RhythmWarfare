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
            if (_plan.stopAfterLegs > 0 && _dropsDone >= _plan.stopAfterLegs)
            {
                PendingPlan = "plan complete: the recording plays on in MIXING mode";
                L("plan complete after " + _dropsDone + " drop(s): no further builds");
                return;
            }
            var leg = _plan.legs[Math.Min(_leg, _plan.legs.Length - 1)];
            _leg = leg.type == "repeat" ? 1 : _leg + 1;
            BeginLeg(dropTime);
        }

        // ------------------------------------------------------------------------------------------------ timeline helpers

        double RecTimeOfAnchor(string anchor) => Mixer.TimelineOfClipTime(_rec, _recSong.Anchor(anchor));

        // ------------------------------------------------------------------------------------------------ builds
        //
        // A playable build (plan.json "buildLoops") is a few 32-beat rhythm loops followed by the recording's own run-in to the drop:
        //   drums -> bass -> drums -> bass (gate: the whole minigame must reach the threshold) -> run-in (the recorded song enters 128 beats
        //   before its drop, the minigame disappears, nothing is judged) -> the recorded drop, a door knock, MIXING mode.
        // A failed gate repeats the last loop as a recovery attempt (custom loops never stop, the recording is never started early or
        // rewound, so there is no silence). After maxRecoveryAttempts the build moves on anyway.

        sealed class Build
        {
            public SongDef Song; public string Anchor;
            public int Recoveries;
            public Mixer.Voice Rec;                                  // the recording voice of the run-in
            public double PlannedDrop;                               // drop time if every remaining gate passes first time
            public readonly List<JudgeWindow> Windows = new List<JudgeWindow>();   // first-attempt rhythm windows (for the aggregate gate)
            public bool GatePassed = true;
            public double IntroSeconds, OffsetBeats;                 // opening builds: length of the intro section, loop phase of the custom drums
        }
        Build _build;

        public PcmClip KnockClip;                                    // optional: three knocks on the drop, on beats 0, 1 and 2
        public event Action<double> DropReached;                     // raised (main thread) when the timeline reaches a recorded drop
        public double LastDropTime { get; private set; } = -1;
        int _dropsDone;

        double PhaseBeats(BuildLoopDef d) => d.beats > 0 ? d.beats : _loops.loopBeats;
        double BuildTotalSeconds { get { double b = 0; foreach (var d in _plan.buildLoops) b += PhaseBeats(d); return b * BeatSeconds; } }
        BuildLoopDef RecordingPhase => _plan.buildLoops.FirstOrDefault(d => d.recording);
        double RunInClipStart(SongDef song, string anchor)
        {
            var d = RecordingPhase; double beats = d != null ? PhaseBeats(d) : 0;
            return song.Anchor(anchor) - beats * song.BeatSeconds;
        }

        bool TryScheduleBuild(string songId, string anchor, double now)
        {
            var song = _songs.Find(songId);
            double bs = BeatSeconds, total = BuildTotalSeconds, D;
            if (_rec != null && _recSong.id == songId)
            {
                D = RecTimeOfAnchor(anchor);
                if (D <= now) { L($"build {songId}:{anchor} rejected: anchor already reached ({D:0.000} <= {now:0.000})"); return false; }
            }
            else if (_rec == null)
            {
                if (UseOpening) return TryScheduleOpening(song, anchor, now + S.startDelaySeconds);
                D = now + S.startDelaySeconds + total;
            }
            else { L($"build {songId}:{anchor} rejected: a different recording is playing"); return false; }

            double start = D - total;
            if (start < now + S.prepMarginBeats * bs) { L($"build {songId}:{anchor} rejected: not enough time (start {start:0.000} < now+margin)"); return false; }
            if (RunInClipStart(song, anchor) < 0) { L($"build {songId}:{anchor} rejected: run-in entry cue {RunInClipStart(song, anchor):0.000}s is before the start of the file"); return false; }
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

        void CreateStemVoices(double start, double clipOffsetSeconds = 0)
        {
            _stemVoices.Clear(); _muted.Clear(); _hitsSinceMute.Clear();
            foreach (var st in _loops.stems)
            {
                if (!_stemPcm.TryGetValue(st.id, out var clip)) continue;
                var v = Mixer.Play("stem:" + st.id, clip, start, clipOffsetSeconds, 0f, loop: true, role: "custom");
                _stemVoices[st.id] = v; _muted[st.id] = false; _hitsSinceMute[st.id] = 0;
            }
        }

        /// <summary>Schedule phase <paramref name="k"/> of the build to start at timeline time <paramref name="t"/> (attempt 0 = first try).</summary>
        void RunPhase(Build b, int k, double t, int attempt)
        {
            double bs = BeatSeconds;
            int n = _plan.buildLoops.Length;
            var def = _plan.buildLoops[k];
            double len = PhaseBeats(def) * bs, end = t + len;
            string name = string.IsNullOrEmpty(def.id) ? "phase" + k : def.id;
            double plannedDrop = t;
            for (int j = k; j < n; j++) plannedDrop += PhaseBeats(_plan.buildLoops[j]) * bs;

            if (def.recording)
            {
                // the minigame disappears: the custom layer eases out while the recording's own run-in eases in, nothing is judged
                double xf = S.buildupCrossfadeBeats * bs;
                foreach (var kv in _stemVoices) { Mixer.RampTo(kv.Value, t, t + xf, 0f); Mixer.StopAt(kv.Value, t + xf + 0.01); }
                double clip = RunInClipStart(b.Song, b.Anchor);
                var v = Mixer.Play(b.Song.id, _songPcm[b.Song.id], t, clip, 0f, role: "recorded");
                Mixer.RampTo(v, t, t + S.buildupFadeInBeats * bs, S.recordedGain);
                b.Rec = v;
                L($"run-in: {b.Song.id} enters at {t:0.000} (clip {clip:0.000}s), eases in over {S.buildupFadeInBeats:0} beats; rhythm game off; drop {plannedDrop:0.000}");
                At(t, "run-in start", () =>
                {
                    _rec = b.Rec; _recSong = b.Song; Mode = MusicMode.Mixing; CurrentWindow = null; b.PlannedDrop = plannedDrop;
                    PendingPlan = $"run-in {b.Song.id}:{b.Anchor}, drop {plannedDrop:0.000}";
                });
                At(end - S.evalLeadSeconds, "drop", () => FinishBuild(b, b.GatePassed, end));
                return;
            }

            string label = attempt == 0 ? $"{b.Song.id}:{b.Anchor} {name}" : $"recovery#{attempt} {b.Song.id}:{b.Anchor} {name}";
            double threshold = !def.gate ? 0.0 : (attempt == 0 ? S.threshold : S.recoveryThreshold);

            // arrangement: which custom stems are audible in this phase
            foreach (var kv in _stemVoices)
            {
                float target = def.audible.Contains(kv.Key) ? S.customGain : 0f;
                if (k == 0 && attempt == 0) Mixer.RampTo(kv.Value, t, t + S.customFadeInBeats * bs, target);
                else Mixer.RampTo(kv.Value, t - 0.01, t + 0.04, target);
            }

            // judged notes (the very last beat of a loop is never charted)
            var notes = NotesForPhase(t, def.charted, _loops.loopBeats - 1);
            var win = Judge.AddWindow(label, t, end - bs, threshold, notes);
            if (attempt == 0) b.Windows.Add(win);
            At(t, "phase start", () =>
            {
                CurrentWindow = win; b.PlannedDrop = plannedDrop; RestoreAllStems();
                PendingPlan = $"build {b.Song.id}:{b.Anchor} - {name}{(attempt > 0 ? " (recovery " + attempt + ")" : "")}, drop planned {plannedDrop:0.000}";
            });
            At(end - S.evalLeadSeconds, "phase end", () => OnPhaseEnd(b, k, win, end, attempt));
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
            if (!def.gate)
            {
                L($"{win.Label}: {win.Hits}/{win.Total} = {win.Accuracy * 100:0.0}% (not gated)");
                RunPhase(b, k + 1, end, 0);
                return;
            }
            int hits = win.Hits, total = win.Total; string scope = "";
            if (def.aggregate && attempt == 0)
            {
                hits = 0; total = 0;
                foreach (var w in b.Windows) { hits += w.Hits; total += w.Total; }
                scope = $" (all {b.Windows.Count} loops)";
            }
            double acc = total == 0 ? 1.0 : hits / (double)total;
            bool pass = acc >= win.Threshold;
            L($"EVAL {win.Label}{scope}: {hits}/{total} = {acc * 100:0.0}% (threshold {win.Threshold * 100:0}%) -> {(pass ? "PASS" : "FAIL")}");
            if (pass || attempt >= S.maxRecoveryAttempts)
            {
                if (!pass) L("recovery attempts exhausted: moving on anyway (no soft-lock)");
                b.GatePassed = pass;
                RunPhase(b, k + 1, end, 0);
                return;
            }
            b.Recoveries++; RecoveryAttempts++;
            L($"RECOVERY #{attempt + 1}: {def.id} again {end:0.000} -> {end + PhaseBeats(def) * BeatSeconds:0.000}");
            RunPhase(b, k, end, attempt + 1);
        }

        void FinishBuild(Build b, bool pass, double D)
        {
            double bs = BeatSeconds;
            if (b.Recoveries == 0) BuildsPassed++; else BuildsFailed++;
            LastBuildPassed = pass;
            PendingPlan = $"mixing {b.Song.id} from {b.Anchor}";
            L($"DROP {b.Song.id}:{b.Anchor} at {D:0.000}");
            if (KnockClip != null)
                for (int i = 0; i < 3; i++) Mixer.Play("knock", KnockClip, D + i * bs, 0, S.knockGain, role: "fx");
            At(D, "mixing mode", () =>
            {
                Mode = MusicMode.Mixing; CurrentWindow = null; _build = null; Judge.Enabled = true;
                LastDropTime = D; _dropsDone++;
                DropReached?.Invoke(D);
                AdvanceAfterDrop(D);
            });
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


        // ------------------------------------------------------------------------------------------------ opening build (song from the start)
        //
        // No recording is playing yet: the recorded song starts from its very first sample. Its first section (clip 0 .. anchor - runInBeats) hosts a
        // drums-only rhythm minigame (the custom kick/snare loops are phase-locked so that a loop boundary falls on the run-in start, exactly as in the
        // 128-beat cue grid). Gate (80 %): pass -> the recording simply carries on into its next section (the run-in), the custom drums ease out, the
        // minigame disappears, and the section ends in the drop (+ door knock). Fail -> the intro section is looped again (recovery, 60 %, at most
        // maxRecoveryAttempts), after which the run-in starts anyway.

        bool UseOpening => _plan.opening != null && _plan.opening.charted != null && _plan.opening.charted.Length > 0;

        bool TryScheduleOpening(SongDef song, string anchor, double start)
        {
            double runIn = _plan.opening.runInBeats > 0 ? _plan.opening.runInBeats : 128;
            double intro = song.Anchor(anchor) - runIn * song.BeatSeconds;
            if (intro < 8 * BeatSeconds) { L($"build {song.id}:{anchor} rejected: no intro section before the run-in cue ({intro:0.000}s)"); return false; }
            ScheduleOpening(song, anchor, start, intro, runIn);
            return true;
        }

        void ScheduleOpening(SongDef song, string anchor, double start, double intro, double runIn)
        {
            double bs = BeatSeconds;
            BuildsStarted++;
            double D = start + song.Anchor(anchor);
            var b = _build = new Build { Song = song, Anchor = anchor, PlannedDrop = D, IntroSeconds = intro };
            double introBeats = intro / bs, L32 = _loops.loopBeats;
            double rem = introBeats % L32;
            b.OffsetBeats = rem < 1e-3 || L32 - rem < 1e-3 ? 0 : L32 - rem;      // custom loop phase at the intro start so a loop boundary lands on the run-in
            PendingPlan = $"opening {song.id}:{anchor} start {start:0.000} drop {D:0.000}";
            L($"BUILD {song.id}:{anchor} scheduled (opening): the song starts at {start:0.000}; intro {intro:0.000}s ({introBeats:0.0} beats) with a drums minigame, then the {runIn:0}-beat run-in, drop {D:0.000}");
            At(Math.Max(Mixer.Time, start - 8 * bs), "rhythm lead-in", () => { Mode = MusicMode.Rhythm; });
            RunIntro(b, 0, start, null);
        }

        void RunIntro(Build b, int attempt, double t, Mixer.Voice previous)
        {
            double bs = BeatSeconds, intro = b.IntroSeconds, end = t + intro;

            // the recording (from its first sample; a recovery loop restarts it, cutting the previous pass exactly at the section end)
            if (previous != null) { Mixer.RampTo(previous, t - 0.03, t, 0f); Mixer.StopAt(previous, t); }
            var rec = Mixer.Play(b.Song.id, _songPcm[b.Song.id], t, 0.0, 0f, role: "recorded");
            double fade = attempt == 0 ? S.introFadeInSeconds : 0.03;
            Mixer.RampTo(rec, t, t + fade, S.recordedGain);
            b.Rec = rec;
            At(t, "intro start", () => { _rec = rec; _recSong = b.Song; });

            // custom drums (kick/snare) over the intro, phase-locked to the run-in
            double offsetSec = b.OffsetBeats * bs;
            if (attempt > 0) foreach (var kv in _stemVoices) { Mixer.RampTo(kv.Value, t - 0.02, t, 0f); Mixer.StopAt(kv.Value, t); }
            CreateStemVoices(t, offsetSec);
            foreach (var kv in _stemVoices)
            {
                float target = _plan.opening.audible.Contains(kv.Key) ? S.customGainOverIntro : 0f;
                Mixer.RampTo(kv.Value, t, t + (attempt == 0 ? S.customFadeInBeats * bs : 0.03), target);
            }

            // judged notes: the loop pattern as it falls over the intro, never in the last beat
            var notes = new List<Note>();
            double L32 = _loops.loopBeats, introBeats = intro / bs;
            foreach (var stemId in _plan.opening.charted)
            {
                var st = _loops.Find(stemId); if (st == null) continue;
                for (int k = 0; k * L32 - b.OffsetBeats < introBeats; k++)
                    foreach (var c in st.cues)
                    {
                        double beat = c.tick / (double)_loops.ticksPerBeat;
                        double tb = k * L32 + beat - b.OffsetBeats;
                        if (tb < 0.0 - 1e-6 || tb > introBeats - 1.0) continue;
                        notes.Add(new Note { Time = t + tb * bs, Pad = c.pad, Stem = stemId });
                    }
            }
            string label = attempt == 0 ? $"{b.Song.id}:{b.Anchor} intro" : $"recovery#{attempt} {b.Song.id}:{b.Anchor} intro";
            double threshold = attempt == 0 ? S.threshold : S.recoveryThreshold;
            var win = Judge.AddWindow(label, t, end - bs, threshold, notes);
            At(t, "intro window", () =>
            {
                CurrentWindow = win; RestoreAllStems(); b.PlannedDrop = t + (b.Song.Anchor(b.Anchor));
                PendingPlan = $"opening {b.Song.id}:{b.Anchor} - intro{(attempt > 0 ? " (recovery " + attempt + ")" : "")}, drop planned {b.PlannedDrop:0.000}";
            });
            At(end - S.evalLeadSeconds, "intro end", () => OnIntroEnd(b, win, rec, end, attempt));
        }

        void OnIntroEnd(Build b, JudgeWindow win, Mixer.Voice rec, double end, int attempt)
        {
            Judge.Update(Mixer.Time);
            Judge.Close(win);
            bool pass = win.Accuracy >= win.Threshold;
            L($"EVAL {win.Label}: {win.Hits}/{win.Total} = {win.Accuracy * 100:0.0}% (threshold {win.Threshold * 100:0}%) -> {(pass ? "PASS" : "FAIL")}");
            if (!pass && attempt < S.maxRecoveryAttempts)
            {
                b.Recoveries++; RecoveryAttempts++;
                L($"RECOVERY #{attempt + 1}: intro loops again {end:0.000} -> {end + b.IntroSeconds:0.000}");
                RunIntro(b, attempt + 1, end, rec);
                return;
            }
            if (!pass) L("recovery attempts exhausted: moving on to the run-in anyway (no soft-lock)");
            b.GatePassed = pass;
            StartRunIn(b, end);
        }

        /// <summary>The next section of the song: the recording carries on, the custom drums ease out and the minigame disappears.</summary>
        void StartRunIn(Build b, double t)
        {
            double bs = BeatSeconds;
            double xf = S.buildupCrossfadeBeats * bs;
            foreach (var kv in _stemVoices) { Mixer.RampTo(kv.Value, t, t + xf, 0f); Mixer.StopAt(kv.Value, t + xf + 0.01); }
            double D = Mixer.TimelineOfClipTime(b.Rec, b.Song.Anchor(b.Anchor));
            L($"run-in: {b.Song.id} carries on into its next section at {t:0.000}; rhythm game off; drop {D:0.000}");
            At(t, "run-in start", () =>
            {
                Mode = MusicMode.Mixing; CurrentWindow = null; b.PlannedDrop = D;
                PendingPlan = $"run-in {b.Song.id}:{b.Anchor}, drop {D:0.000}";
            });
            At(D - S.evalLeadSeconds, "drop", () => FinishBuild(b, b.GatePassed, D));
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
            L($"REPEAT: restarting {to.id} after the ending at {endT:0.000}");
            if (UseOpening) return TryScheduleOpening(to, "firstDrop", endT + 4 * bs);
            double start = endT + 4 * bs, D = start + BuildTotalSeconds;
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
