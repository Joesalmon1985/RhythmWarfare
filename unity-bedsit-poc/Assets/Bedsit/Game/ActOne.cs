using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Bedsit.Sims2;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// "Act One" of the bedroom game (enabled together with the music POC: <c>-music</c> / BEDSIT_MUSIC=1):
    ///  * the player wakes, puts on headphones and the music starts (the music POC waits for <see cref="HeadphonesStarted"/>);
    ///  * only the player is visible (in the mirror) - no other Sims anywhere yet;
    ///  * the room is messy: look round and tap the clutter to tidy it away (a second, optional minigame running alongside the rhythm game);
    ///  * on the recorded drop there are three knocks at the door; only then can the door be opened;
    ///  * opening it shows a woman if the room is clean enough, a man if it is not.
    /// </summary>
    public class ActOne : MonoBehaviour
    {
        public static ActOne Instance { get; private set; }
        public static bool Requested => MusicPoc.Requested;

        /// <summary>Fraction of the clutter that must be tidied for the room to count as clean.</summary>
        public float CleanThreshold = 0.8f;

        public BedsitGame Game { get; private set; }
        public readonly List<ClutterItem> Items = new List<ClutterItem>();
        public int TotalItems { get; private set; }
        public int TidiedCount { get; private set; }
        public float TidyFraction => TotalItems == 0 ? 1f : TidiedCount / (float)TotalItems;
        public bool IsClean => TidyFraction >= CleanThreshold - 1e-6f;

        public bool SetupDone { get; private set; }
        public bool HeadphonesStarted { get; private set; }
        public bool HeadphonesOn { get; private set; }
        public float HeadphonesProgress { get; private set; }
        public bool Knocked { get; private set; }
        public bool DoorOpened { get; private set; }
        public string VisitorKind { get; private set; }              // "woman" | "man" | null
        public SimCharacterActor Visitor { get; private set; }
        public bool KnockPending => Knocked && !DoorOpened;
        public readonly List<string> Log = new List<string>();

        public event Action<ClutterItem> Tidied;

        ActOneHud _hud;
        GameObject _playerHeadphones;

        // scripted tidier for automated runs: -tidybot=all|most|none (tidies one item every few seconds, then answers the knock)
        string _bot; int _botQuota; float _botNext; float _botKnockAt = -1f, _botOpenedAt = -1f; bool _botShot;
        static string Arg(string name) { foreach (var a in Environment.GetCommandLineArgs()) if (a.StartsWith(name + "=")) return a.Substring(name.Length + 1); return null; }
        Transform _clutterRoot;
        ClutterItem _hover;
        float _baseRoomLight = -1f;

        void Awake() { Instance = this; }
        void OnDestroy() { if (Instance == this) Instance = null; if (Game != null && Game.Input != null) Game.Input.ClickHandler = null; }

        void Update()
        {
            if (!SetupDone)
            {
                var g = BedsitGame.Instance;
                if (g == null || !g.Ready) return;
                Game = g;
                Setup();
            }
            if (!HeadphonesStarted && Game.WakeUpFinished) StartCoroutine(HeadphonesRoutine());

            // the room brightens a little as it is tidied
            if (Game.World != null && Game.World.RoomLight != null)
            {
                if (_baseRoomLight < 0f) _baseRoomLight = Game.World.RoomLight.intensity;
                float target = _baseRoomLight * (1f + 0.28f * TidyFraction);
                Game.World.RoomLight.intensity = Mathf.MoveTowards(Game.World.RoomLight.intensity, target, Time.deltaTime * 0.6f);
            }

            // desktop hover highlight
            var picked = Game.View != null && !Game.View.IsTurning && !Game.Input.Locked ? PickAt(UnityEngine.Input.mousePosition) : null;
            if (picked != _hover) { if (_hover != null) _hover.SetHover(false); _hover = picked; if (_hover != null) _hover.SetHover(true); }

            if (UnityEngine.Input.GetKeyDown(KeyCode.F2) && !Knocked) ForceKnock();     // developer shortcut
            if (_bot != null) StepBot();
        }

        // ------------------------------------------------------------------------------------------------ setup

        void Setup()
        {
            SetupDone = true;
            // nobody but the player is in the world yet
            foreach (var a in new[] { Game.NpcCorridor, Game.NpcEast, Game.NpcWest }) if (a != null) a.gameObject.SetActive(false);
            Game.EastTarget.Interactable = false; Game.WestTarget.Interactable = false;       // windows have nobody to react
            Game.DoorTarget.Interactable = false;                                              // locked until someone knocks
            Game.DoorOverride = OnDoorInteract;
            if (Game.World.Door != null) { Game.World.Door.AjarNormalizedTime = 0f; Game.World.Door.SetFraction(0f); }   // shut until somebody knocks
            Game.Interactions.Refresh();

            _clutterRoot = new GameObject("Clutter").transform;
            _clutterRoot.SetParent(Game.World.transform, false);
            var room = Game.Room;
            if (room != null && room.Cleanables.Count > 0)
            {
                // the data-driven room: real prop models with messy/tidy states (see RoomBuilder / Cleanable)
                foreach (var c in room.Cleanables) Items.Add(c);
                if (RoomSave.LoadRequested) { int n = RoomSave.Apply(room, RoomSave.Read(room.Def.id)); Log.Add($"room save loaded: {n} tasks restored"); }
                foreach (var c in room.Cleanables) c.Gone += _ => { RoomSave.Save(room); };
                TidiedCount = room.Cleanables.Count(c => c.Tidied);
            }
            else
            {
                foreach (var spot in ClutterFactory.Layout)
                {
                    var item = ClutterFactory.Create(spot, _clutterRoot, BedsitLayers.MirrorGlass);
                    Items.Add(item);
                }
            }
            TotalItems = Items.Count;

            _hud = new GameObject("ActOneHud").AddComponent<ActOneHud>();
            _hud.transform.SetParent(transform, false);
            _hud.Act = this;

            Game.Input.ClickHandler = px => TryTidyAtScreen(px);
            BuildPlayerHeadphones();
            _bot = Arg("-tidybot");
            if (_bot != null) { _botQuota = _bot == "all" ? TotalItems : _bot == "most" ? Mathf.CeilToInt(TotalItems * 0.87f) : 0; _botNext = Time.time + 12f; }
            Log.Add($"act one ready: {TotalItems} pieces of clutter, clean at {CleanThreshold * 100:0}%");
        }

        // ------------------------------------------------------------------------------------------------ headphones

        /// <summary>The player's reflection wears the same headphones (mirror-only layer, so the first-person camera never sees them).</summary>
        void BuildPlayerHeadphones()
        {
            if (Game.Player == null) return;
            Transform head = null;
            foreach (var t in Game.Player.GetComponentsInChildren<Transform>(true)) if (t.name == "head") { head = t; break; }
            if (head == null) { Log.Add("headphones: no head bone found, mirror headphones skipped"); return; }
            var go = new GameObject("PlayerHeadphones");
            go.transform.position = head.position; go.transform.rotation = Quaternion.identity;
            go.AddComponent<MeshFilter>().sharedMesh = ClutterFactory.HeadphonesMesh();
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = ClutterFactory.PropMaterial;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            go.layer = BedsitLayers.PlayerMirrorOnly;
            go.transform.SetParent(head, true);                       // follows the head through every animation
            go.SetActive(false);
            _playerHeadphones = go;
        }

        IEnumerator HeadphonesRoutine()
        {
            HeadphonesStarted = true;
            Log.Add("headphones: putting them on");
            const float dur = 1.5f;
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                HeadphonesProgress = Mathf.SmoothStep(0f, 1f, t / dur);
                if (_playerHeadphones != null && !_playerHeadphones.activeSelf && t > dur * 0.55f) _playerHeadphones.SetActive(true);   // appears in the mirror
                yield return null;
            }
            if (_playerHeadphones != null) _playerHeadphones.SetActive(true);
            HeadphonesProgress = 1f; HeadphonesOn = true;
            Log.Add("headphones: on");
        }

        // ------------------------------------------------------------------------------------------------ tidying

        public int Remaining(CompassDirection d)
        {
            int n = 0;
            foreach (var i in Items) if (!i.Tidied && !i.Tidying && i.PrimaryView == d) n++;
            return n;
        }

        /// <summary>The clutter item under a screen position (pixels), or null. Only items in front of the camera can be picked.</summary>
        public ClutterItem PickAt(Vector2 px)
        {
            var cam = Game != null ? Game.EyeCamera : null;
            if (cam == null) return null;
            float scale = Screen.height / 720f;
            ClutterItem best = null; float bestK = 1f;
            foreach (var it in Items)
            {
                if (it == null || it.Tidied || it.Tidying || !it.gameObject.activeSelf) continue;
                var sp = cam.WorldToScreenPoint(it.PickCentre);
                if (sp.z < 0.2f) continue;
                var edge = cam.WorldToScreenPoint(it.PickCentre + cam.transform.right * it.PickRadius);
                float r = Mathf.Max(Vector2.Distance(sp, edge) * 1.15f, 46f * scale);
                float k = Vector2.Distance(px, sp) / r;
                if (k <= 1f && k < bestK) { best = it; bestK = k; }
            }
            return best;
        }

        public bool TryTidyAtScreen(Vector2 px)
        {
            if (Game == null || Game.View == null || Game.View.IsTurning) return false;
            var it = PickAt(px);
            return it != null && Tidy(it, px);
        }

        public bool Tidy(ClutterItem it, Vector2? screenPos = null)
        {
            if (it == null || !it.Tidy()) return false;
            TidiedCount++;
            Log.Add($"tidied {it.Kind} ({TidiedCount}/{TotalItems})");
            if (_hud != null && screenPos.HasValue) _hud.PulseAt(screenPos.Value);
            Tidied?.Invoke(it);
            return true;
        }

        void StepBot()
        {
            if (HeadphonesOn && TidiedCount < _botQuota && Time.time >= _botNext)
            {
                foreach (var it in Items) if (!it.Tidied && !it.Tidying) { Tidy(it); break; }
                _botNext = Time.time + 3.2f;
            }
            if (Knocked && !DoorOpened)
            {
                if (_botKnockAt < 0f) _botKnockAt = Time.time;
                if (Time.time - _botKnockAt > 2.5f)
                {
                    Game.View.SnapTo(CompassDirection.North); Game.Interactions.Refresh();
                    Game.Input.Raise(PlayerAction.Interact);
                }
            }
            if (DoorOpened)
            {
                if (_botOpenedAt < 0f) _botOpenedAt = Time.time;
                if (!_botShot && Time.time - _botOpenedAt > 2.2f)
                {
                    _botShot = true;
                    var path = ScreenshotUtil.Capture(Game.EyeCamera, "actone_exe_" + VisitorKind + ".png", 1280, 720);
                    Log.Add("screenshot " + path);
                }
            }
        }

        // ------------------------------------------------------------------------------------------------ knock + door

        /// <summary>Called when the music reaches the recorded drop (three knocks sound on beats 0, 1, 2 of it).</summary>
        public void OnKnock(double timeline)
        {
            if (Knocked) return;
            Knocked = true;
            Log.Add($"knock at the door (timeline {timeline:0.000})");
            if (Game != null && Game.DoorTarget != null) { Game.DoorTarget.Interactable = true; Game.Interactions.Refresh(); }
            StartCoroutine(KnockShake());
        }

        public void ForceKnock() { OnKnock(-1); }

        IEnumerator KnockShake()
        {
            var door = Game.World.Door != null ? Game.World.Door.transform : null;
            if (door == null) yield break;
            Vector3 home = door.position;
            float bs = 60f / 174f;
            for (int k = 0; k < 3; k++)
            {
                for (float t = 0f; t < 0.14f; t += Time.deltaTime)
                {
                    float a = 0.014f * (1f - t / 0.14f) * Mathf.Sin(t * 95f);
                    if (door != null) door.position = home + new Vector3(0f, 0f, a);
                    yield return null;
                }
                if (door != null) door.position = home;
                yield return new WaitForSeconds(Mathf.Max(0f, bs - 0.14f));
            }
        }

        void OnDoorInteract()
        {
            if (!Knocked || DoorOpened) return;
            DoorOpened = true;
            Game.DoorTarget.Interactable = false;
            Game.Interactions.Refresh();
            bool clean = IsClean;
            VisitorKind = clean ? "woman" : "man";
            Visitor = clean ? Game.NpcEast : Game.NpcCorridor;           // Pleasantview Sim 13 (female) / Sim 11 (male)
            Log.Add($"door opened: room {(clean ? "clean" : "messy")} ({TidiedCount}/{TotalItems}) -> a {VisitorKind} is at the door");
            StartCoroutine(OpenDoorRoutine(clean));
        }

        IEnumerator OpenDoorRoutine(bool clean)
        {
            var w = Game.World;
            if (Visitor != null)
            {
                var pos = new Vector3(0f, 0f, w.DoorwayPoint.z + 1.1f);
                Visitor.transform.position = pos;
                Visitor.FaceTowards(new Vector3(0f, 0f, 0f));
                Visitor.gameObject.SetActive(true);
                Visitor.PlayIdle();
            }
            if (w.Door != null && !w.Door.IsOpen) { w.Door.Open(); while (w.Door.IsOpening) yield return null; }
            yield return new WaitForSeconds(0.3f);
            if (Visitor != null) Visitor.PlayOneShot(clean ? AnimationKeys.Wave : AnimationKeys.Surprise);
        }
    }
}
