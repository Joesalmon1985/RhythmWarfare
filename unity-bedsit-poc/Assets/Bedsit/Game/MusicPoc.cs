using System;
using System.Collections.Generic;
using System.IO;
using Bedsit.Music;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Development entry point for the bedroom music POC (feature flag: BEDSIT_MUSIC=1 or the "-music" argument).
    /// One MusicSession (mixer + judge + director) lives for the whole play session; turning in the bedsit never touches it.
    /// Audio leaves through a single AudioSource whose OnAudioFilterRead pulls the Mixer, so the timeline IS the audio clock.
    /// If no audio device is available the mixer is pumped from Update instead (same samples, same timeline).
    /// Command line: -music  -musicbot=perfect|partial|fail  -musicrecord=SECONDS  -musicspeed=N (pump mode only)  -overlay
    /// </summary>
    public class MusicPoc : MonoBehaviour
    {
        public static MusicPoc Instance { get; private set; }

        public static bool ForceRequest;                 // tests / editor tools
        public static bool Requested
        {
            get
            {
                if (ForceRequest) return true;
                if (Environment.GetEnvironmentVariable("BEDSIT_MUSIC") == "1") return true;
                return Array.IndexOf(Environment.GetCommandLineArgs(), "-music") >= 0;
            }
        }

        static string Arg(string name)
        {
            foreach (var a in Environment.GetCommandLineArgs()) if (a.StartsWith(name + "=")) return a.Substring(name.Length + 1);
            return null;
        }

        public MusicSession Session { get; private set; }
        public string Status { get; private set; } = "starting";
        public bool DeviceActive { get; private set; }
        public bool Paused { get { return Session != null && Session.Mixer.Paused; } }
        public float InputLatencySeconds = 0.0f;          // calibration: subtract from tap times (audio buffer + display lag)
        public MusicBot Bot;
        public int Taps;

        AudioSource _source;
        int _rate;
        double _lastCallback = -1;
        float _startedAt;
        float[] _scratch = new float[4096];
        bool _started;
        double _speed = 1.0;

        // recording of what the mixer actually produced
        readonly object _capLock = new object();
        List<float> _capture;
        double _recordSeconds;
        string _recordName;
        bool _recorded;

        BedsitGame _game;

        void Awake() { Instance = this; }
        void OnDestroy() { if (Instance == this) Instance = null; }

        void Start()
        {
            _game = BedsitGame.Instance;
            _rate = AudioSettings.outputSampleRate > 0 ? AudioSettings.outputSampleRate : 48000;
            var root = MusicSession.FindAudioRoot();
            if (root == null) { Status = "FAILED: LocalAudio folder not found (run Tools/music/prepare_audio.py)"; Debug.LogError("[MusicPoc] " + Status); return; }
            try { Session = MusicSession.Create(root, _rate); }
            catch (Exception e) { Status = "FAILED: " + e.Message; Debug.LogException(e); return; }
            foreach (var p in Session.Problems) Debug.LogWarning("[MusicPoc] " + p);

            var botName = Arg("-musicbot");
            if (botName == "perfect") Bot = MusicBot.Perfect();
            else if (botName == "partial") Bot = MusicBot.Partial();
            else if (botName == "fail") Bot = MusicBot.Failing();
            if (double.TryParse(Arg("-musicspeed"), out var sp)) _speed = Math.Max(1.0, sp);
            if (double.TryParse(Arg("-musicrecord"), out var rec)) { _recordSeconds = rec; _recordName = "runtime_" + (botName ?? "manual"); _capture = new List<float>(); }

            // one AudioSource drives the DSP callback
            _source = gameObject.AddComponent<AudioSource>();
            _source.clip = AudioClip.Create("music-dsp", 2048, 2, _rate, false);
            _source.loop = true; _source.spatialBlend = 0f; _source.playOnAwake = false;
            var ones = new float[2048 * 2]; for (int i = 0; i < ones.Length; i++) ones[i] = 1f;
            _source.clip.SetData(ones, 0);
            _source.Play();
            _startedAt = Time.realtimeSinceStartup;
            Status = "waiting for wake-up";

            var hud = gameObject.AddComponent<MusicHud>(); hud.Poc = this;
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "-overlay") >= 0 || Bot != null) { var ov = gameObject.AddComponent<MusicOverlay>(); ov.Poc = this; ov.Visible = true; }
            else { var ov = gameObject.AddComponent<MusicOverlay>(); ov.Poc = this; ov.Visible = false; }
        }

        // ------------------------------------------------------------------------------------------------ audio thread

        void OnAudioFilterRead(float[] data, int channels)
        {
            if (Session == null) return;
            _lastCallback = AudioSettings.dspTime;
            int frames = data.Length / channels;
            if (channels == 2) { Session.Mixer.Render(data, frames); Tap(data, frames); return; }
            if (_scratch.Length < frames * 2) _scratch = new float[frames * 2];
            Session.Mixer.Render(_scratch, frames);
            Tap(_scratch, frames);
            for (int f = 0; f < frames; f++)
                for (int c = 0; c < channels; c++) data[f * channels + c] = c == 0 ? _scratch[f * 2] : c == 1 ? _scratch[f * 2 + 1] : 0f;
        }

        void Tap(float[] stereo, int frames)
        {
            if (_capture == null) return;
            lock (_capLock) { for (int i = 0; i < frames * 2; i++) _capture.Add(stereo[i]); }
        }

        // ------------------------------------------------------------------------------------------------ main thread

        void Update()
        {
            if (Session == null) return;
            if (!_started)
            {
                // Act One: the music starts as the player puts the headphones on (after the wake-up)
                bool go = _game != null && _game.WakeUpFinished && (ActOne.Instance == null || ActOne.Instance.HeadphonesStarted);
                if (go) StartMusic(); else return;
            }

            // no audio device? pump the mixer ourselves so the game still runs (and can be recorded)
            bool callbacksArrive = _lastCallback >= 0 && AudioSettings.dspTime - _lastCallback < 0.5;
            DeviceActive = callbacksArrive;
            if (!callbacksArrive && Time.realtimeSinceStartup - _startedAt > 1.0 && !Session.Mixer.Paused)
            {
                double seconds = Time.unscaledDeltaTime * _speed;
                int frames = (int)(seconds * _rate);
                int done = 0;
                while (done < frames)
                {
                    int n = Math.Min(2048, frames - done);
                    if (_scratch.Length < n * 2) _scratch = new float[n * 2];
                    Session.Mixer.Render(_scratch, n);
                    Tap(_scratch, n);
                    done += n;
                    // keep scheduling in step with the faster clock
                    var t = Session.Mixer.Time;
                    Bot?.Step(Session.Judge, t);
                    Session.Director.Update(t);
                }
            }

            double now = Session.Mixer.Time;
            Bot?.Step(Session.Judge, now);
            Session.Director.Update(now);

            if (_game != null && _game.Input != null) _game.Input.PadsEnabled = Session.Director.Mode == MusicMode.Rhythm && !Paused;

            if (Input.GetKeyDown(KeyCode.P)) SetPaused(!Paused);
            if (Input.GetKeyDown(KeyCode.F1)) { var ov = GetComponent<MusicOverlay>(); if (ov != null) ov.Visible = !ov.Visible; }

            if (_capture != null && !_recorded && now >= _recordSeconds) FinishRecording();
            Status = Session.Director.Mode + " " + (Session.Director.CurrentSongId ?? "-");
        }

        void StartMusic()
        {
            _started = true;
            if (_game != null && _game.Input != null) _game.Input.PadTriggered += OnPad;
            Session.Director.DropReached += t => { if (ActOne.Instance != null) ActOne.Instance.OnKnock(t); };
            Session.Director.Start();
            Status = "running";
            Debug.Log("[MusicPoc] music started. audio device callbacks: " + (DeviceActive ? "yes" : "pending/no"));
        }

        void OnPad(int pad)
        {
            if (Session == null || Paused) return;
            Taps++;
            Session.Judge.Tap(pad + 1, Session.Mixer.Time - InputLatencySeconds);
        }

        public void SetPaused(bool p) { if (Session != null) Session.Mixer.Paused = p; }

        void OnApplicationFocus(bool focus) { if (!focus && Application.isMobilePlatform && Session != null) SetPaused(true); }
        void OnApplicationPause(bool pause) { if (pause && Session != null) SetPaused(true); }

        void FinishRecording()
        {
            _recorded = true;
            float[] data;
            lock (_capLock) data = _capture.ToArray();
            var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Evidence", "audio"));
            var path = Path.Combine(dir, _recordName + ".wav");
            PcmClip.SaveWav16(path, data, _rate);
            var rep = AudioStats.Analyze(data, _rate, -60, 3.2);
            var log = string.Join("\n", Session.Director.Log) + (ActOne.Instance != null ? "\n--- act one ---\n" + string.Join("\n", ActOne.Instance.Log) : "");
            File.WriteAllText(Path.Combine(dir, _recordName + ".txt"), rep + "\n" + Session.Director.StatusText(Session.Mixer.Time) + "\n" + log);
            Debug.Log("[MusicPoc] recorded " + path + " : " + rep);
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "-quit") >= 0) Application.Quit();
        }
    }
}
