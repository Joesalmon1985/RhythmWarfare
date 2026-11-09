using System.Collections;
using System.Collections.Generic;
using Bedsit.Sims2;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Entry point of the Bedsit scene. Assembles the first-person rig, the Sims 2 world and its characters, wires the
    /// reusable systems together (input -> view / interaction / transition) and runs the wake-up sequence.
    /// All rendering/asset specifics live in Bedsit.Sims2; the controllers it wires are engine-agnostic.
    /// </summary>
    public class BedsitGame : MonoBehaviour
    {
        public static BedsitGame Instance { get; private set; }
        /// <summary>Tests set this before loading the scene to skip the wake-up animation.</summary>
        public static bool SkipWakeUp;

        public const string ZoneBedsit = "bedsit";
        public const string ZoneCorridor = "corridor";

        // cast (premade Pleasantview Sims, see README)
        public uint PlayerSim = 12, CorridorSim = 11, EastSim = 13, WestSim = 14;

        public bool Ready { get; private set; }
        public bool WakeUpFinished { get; private set; }
        public string Status { get; private set; } = "starting";

        public Camera EyeCamera { get; private set; }
        public Transform Rig { get; private set; }
        public FirstPersonViewController View { get; private set; }
        public InteractionController Interactions { get; private set; }
        public PlayerTransitionController Transition { get; private set; }
        public WorldSceneController Zones { get; private set; }
        public InputRouter Input { get; private set; }
        public HudOverlay Hud { get; private set; }
        public MirrorReflectionController Mirror { get; private set; }
        public BedsitWorld World { get; private set; }

        public SimCharacterActor Player { get; private set; }
        public SimCharacterActor NpcCorridor { get; private set; }
        public SimCharacterActor NpcEast { get; private set; }
        public SimCharacterActor NpcWest { get; private set; }

        public InteractionTarget DoorTarget, EastTarget, MirrorTarget, WestTarget, CorridorNpcTarget, CorridorBackTarget;

        public readonly List<string> Log = new List<string>();

        void Awake() => Instance = this;
        void OnDestroy() { if (Instance == this) Instance = null; }

        IEnumerator Start()
        {
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 0;
            BuildRig();
            Hud = new GameObject("Hud").AddComponent<HudOverlay>();
            Hud.transform.SetParent(transform, false);
            Hud.Input = Input;
            Hud.SetFade(1f);
            yield return null;

            Status = "building world";
            World = BedsitWorldBuilder.Build();
            if (World == null) { Status = "FAILED: " + Sims2Runtime.LastError; Debug.LogError(Status); yield break; }
            yield return null;

            Status = "creating characters";
            CreateCast();
            yield return null;

            BuildControllers();
            WireInteractions();
            Ready = true;
            Status = "ready";

            if (SkipWakeUp) { StartAtStandpoint(); Hud.SetFade(0f); WakeUpFinished = true; Hud.SetHintsVisible(true); }
            else yield return WakeUp();
        }

        // ------------------------------------------------------------------------------------------------------ build

        void BuildRig()
        {
            Rig = new GameObject("PlayerRig").transform;
            Rig.SetParent(transform, false);
            var yaw = new GameObject("YawPivot").transform; yaw.SetParent(Rig, false);
            var pitch = new GameObject("PitchPivot").transform; pitch.SetParent(yaw, false);
            var camGo = new GameObject("EyeCamera") { tag = "MainCamera" };
            camGo.transform.SetParent(pitch, false);
            EyeCamera = camGo.AddComponent<Camera>();
            EyeCamera.fieldOfView = 64f;
            EyeCamera.nearClipPlane = 0.06f;
            EyeCamera.farClipPlane = 120f;
            EyeCamera.clearFlags = CameraClearFlags.SolidColor;
            EyeCamera.backgroundColor = new Color(0.62f, 0.78f, 0.95f);
            EyeCamera.allowMSAA = true;

            View = Rig.gameObject.AddComponent<FirstPersonViewController>();
            View.YawPivot = yaw; View.PitchPivot = pitch; View.EyeCamera = EyeCamera;

            Input = gameObject.AddComponent<InputRouter>();
            Input.Locked = true;
            Input.ActionTriggered += OnAction;
        }

        void CreateCast()
        {
            Player = SimCharacterActor.CreateFromNeighborhood("player", "N001", PlayerSim);
            NpcCorridor = SimCharacterActor.CreateFromNeighborhood("npc_corridor", "N001", CorridorSim);
            NpcEast = SimCharacterActor.CreateFromNeighborhood("npc_east", "N001", EastSim);
            NpcWest = SimCharacterActor.CreateFromNeighborhood("npc_west", "N001", WestSim);

            // The player's own body: invisible to the eye camera (mirror-only layer), casts no shadows.
            if (Player != null)
            {
                Player.transform.SetParent(transform, false);
                Player.transform.position = new Vector3(World.BedsitStandpoint.x, 0f, World.BedsitStandpoint.z);
                Player.transform.rotation = Quaternion.LookRotation(Vector3.back, Vector3.up);   // facing the mirror
                Player.SetLayerRecursive(BedsitLayers.PlayerMirrorOnly);
                foreach (var r in Player.GetComponentsInChildren<Renderer>(true))
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                Player.PlayIdle();
            }
            Stand(NpcCorridor, World.CorridorNpcSpot, World.CorridorNpcLookAt);
            Stand(NpcEast, World.EastNpcSpot, World.EastNpcLookAt);
            Stand(NpcWest, World.WestNpcSpot, World.WestNpcLookAt);
        }

        void Stand(SimCharacterActor a, Vector3 pos, Vector3 look)
        {
            if (a == null) return;
            a.transform.SetParent(transform, false);
            a.transform.position = pos;
            a.FaceTowards(new Vector3(look.x, pos.y, look.z));
            a.PlayIdle();
        }

        void BuildControllers()
        {
            Zones = gameObject.AddComponent<WorldSceneController>();
            Interactions = gameObject.AddComponent<InteractionController>();
            Transition = gameObject.AddComponent<PlayerTransitionController>();
            Interactions.View = View;
            Transition.Rig = Rig; Transition.View = View;
            Zones.Rig = Rig; Zones.View = View; Zones.Interactions = Interactions;
            Zones.DefineZone(ZoneBedsit, World.BedsitStandpoint, CompassDirection.North);
            Zones.DefineZone(ZoneCorridor, World.CorridorStandpoint, CompassDirection.North);

            // mirror
            var mirrorGo = World.MirrorFrame.gameObject;
            Mirror = mirrorGo.AddComponent<MirrorReflectionController>();
            Mirror.GlassLayer = BedsitLayers.MirrorGlass;
            Mirror.Initialize(EyeCamera, World.MirrorGlassSize, BedsitLayers.PlayerMirrorOnly);
            Mirror.ExcludeFromReflection(World.MirrorFrameObject);

            // visual cue
            var cue = new GameObject("InteractionCue").AddComponent<InteractionCue>();
            cue.transform.SetParent(transform, false);
            cue.Controller = Interactions;
            cue.ViewerCamera = EyeCamera;
            cue.Layer = BedsitLayers.MirrorGlass;               // never shown in the mirror

            Interactions.enabled = false; Interactions.enabled = true;     // re-run OnEnable now that View is assigned
        }

        InteractionTarget MakeTarget(string id, string zone, CompassDirection dir, Vector3 cuePos)
        {
            var go = new GameObject("Target_" + id);
            go.transform.SetParent(transform, false);
            go.transform.position = cuePos;
            var t = go.AddComponent<InteractionTarget>();
            t.Id = id; t.ZoneId = zone; t.Direction = dir;
            Interactions.Register(t);
            return t;
        }

        void WireInteractions()
        {
            float h = BedsitWorldBuilder.HalfW, d = BedsitWorldBuilder.HalfD;
            DoorTarget = MakeTarget("door", ZoneBedsit, CompassDirection.North, new Vector3(0f, 2.05f, d - 0.25f));
            EastTarget = MakeTarget("window_east", ZoneBedsit, CompassDirection.East, new Vector3(h - 0.35f, 1.35f, 0.5f));
            MirrorTarget = MakeTarget("mirror", ZoneBedsit, CompassDirection.South, new Vector3(0f, 1.5f, -d + 0.5f));
            WestTarget = MakeTarget("window_west", ZoneBedsit, CompassDirection.West, new Vector3(-h + 0.35f, 1.35f, -0.25f));
            CorridorNpcTarget = MakeTarget("corridor_npc", ZoneCorridor, CompassDirection.North,
                World.CorridorNpcSpot + new Vector3(0f, 2.15f, 0f));
            CorridorBackTarget = MakeTarget("back_to_bedsit", ZoneCorridor, CompassDirection.South,
                new Vector3(0f, 2.05f, BedsitWorldBuilder.CorridorInnerZ0 + 0.3f));

            DoorTarget.Interacted += _ => EnterCorridor();
            EastTarget.Interacted += _ => React(NpcEast, AnimationKeys.Wave, "east window: NPC waves");
            WestTarget.Interacted += _ => React(NpcWest, AnimationKeys.Clap, "west window: NPC claps");
            MirrorTarget.Interacted += _ => React(Player, AnimationKeys.Wave, "mirror: reflected player waves");
            CorridorNpcTarget.Interacted += _ => React(NpcCorridor, AnimationKeys.Wave, "corridor: NPC waves");
            CorridorBackTarget.Interacted += _ => ReturnToBedsit();
            Interactions.SetZone(ZoneBedsit);
        }

        // ------------------------------------------------------------------------------------------------------ actions

        void OnAction(PlayerAction a)
        {
            if (Transition != null && Transition.IsMoving) return;
            switch (a)
            {
                case PlayerAction.TurnLeft: View.TurnLeft(); break;
                case PlayerAction.TurnRight: View.TurnRight(); break;
                case PlayerAction.Interact: Interactions.TryInteract(); break;
            }
        }

        void React(SimCharacterActor actor, string key, string what)
        {
            Log.Add(what);
            if (actor == null) return;
            actor.PlayOneShot(key);
        }

        void EnterCorridor()
        {
            Log.Add("door: entering corridor");
            StartCoroutine(EnterCorridorRoutine());
        }

        IEnumerator EnterCorridorRoutine()
        {
            Input.Locked = true;
            Hud.SetHintsVisible(false);
            if (!World.Door.IsOpen) { World.Door.Open(); while (World.Door.IsOpening) yield return null; }
            var doorway = new Vector3(0f, 0f, World.DoorwayPoint.z);
            bool done = false;
            Transition.MoveAlong(new[] { doorway, World.CorridorStandpoint }, () => done = true);
            while (!done) yield return null;
            Zones.ArriveInZone(ZoneCorridor);
            Input.Locked = false;
            Hud.SetHintsVisible(true);
            // the corridor Sim greets the arrival
            NpcCorridor?.PlayOneShot(AnimationKeys.Wave);
        }

        void ReturnToBedsit()
        {
            Log.Add("corridor: returning to the bedsit");
            StartCoroutine(ReturnRoutine());
        }

        IEnumerator ReturnRoutine()
        {
            Input.Locked = true;
            Hud.SetHintsVisible(false);
            bool done = false;
            Transition.MoveAlong(new[] { new Vector3(0f, 0f, World.DoorwayPoint.z), World.BedsitStandpoint }, () => done = true);
            while (!done) yield return null;
            Zones.ArriveInZone(ZoneBedsit);
            Input.Locked = false;
            Hud.SetHintsVisible(true);
        }

        // ------------------------------------------------------------------------------------------------------ wake-up

        void StartAtStandpoint()
        {
            Zones.EnterZoneImmediate(ZoneBedsit, CompassDirection.North);
            View.SetPitch(0f);
            Interactions.Refresh();
            Input.Locked = false;
        }

        IEnumerator WakeUp()
        {
            Status = "waking up";
            // Lying in bed: eyes at pillow height, looking up at the ceiling, facing west along the bed.
            Zones.EnterZoneImmediate(ZoneBedsit, CompassDirection.West);
            Rig.position = World.BedPillowEye;
            View.YawPivot.rotation = Quaternion.Euler(0f, 270f, 0f);
            View.SetPitch(-72f);
            Hud.SetFade(1f);
            Input.Locked = true;
            yield return new WaitForSeconds(0.8f);                          // 1. screen begins dark
            yield return Hud.FadeTo(0f, 2.0f);                              // 2. fade into the room
            yield return new WaitForSeconds(0.5f);

            // 3. rise to a standing first-person eye level and swing round to face north
            Vector3 from = Rig.position, to = World.BedsitStandpoint;
            const float dur = 3.4f;
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                float k = Mathf.SmoothStep(0f, 1f, t / dur);
                float lift = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t / (dur * 0.6f)));      // sit up first, then move out
                Rig.position = new Vector3(Mathf.Lerp(from.x, to.x, k), Mathf.Lerp(from.y, to.y, lift), Mathf.Lerp(from.z, to.z, k));
                View.SetPitch(Mathf.Lerp(-72f, 0f, Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t / (dur * 0.85f)))));
                View.YawPivot.rotation = Quaternion.Euler(0f, Mathf.Lerp(270f, 360f, k), 0f);
                yield return null;
            }
            StartAtStandpoint();                                            // exact standpoint + North, pitch 0
            WakeUpFinished = true;
            Hud.SetHintsVisible(true);
            Status = "playing";
        }
    }
}
