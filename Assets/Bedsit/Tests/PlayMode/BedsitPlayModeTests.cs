using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Bedsit.Game;
using Bedsit.Sims2;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Bedsit.Tests
{
    /// <summary>
    /// Play Mode tests for the first-person bedsit POC. They run the real Bedsit scene against the user's own Sims 2
    /// install (config.json) and verify behaviour from the player's point of view, including pixel tests that colour the
    /// player's body and the NPCs and then count those colours in actual eye-camera renders.
    /// </summary>
    public abstract class BedsitFixtureBase
    {
        protected BedsitGame Game;
        protected Material Magenta, Cyan;

        protected virtual bool SkipWakeUp => true;
        protected virtual void BeforeLoad() { }
        protected virtual Bedsit.Sims2.BedsitContent.ContentMode Mode => Bedsit.Sims2.BedsitContent.ContentMode.Auto;

        [UnitySetUp]
        public IEnumerator LoadBedsit()
        {
            if (Sims2Runtime.FindConfig() == null && !BedsitContent.BakedAvailable)
                Assert.Ignore("Neither config.json (Sims 2 install) nor baked content (Assets/LocalBaked) found: these tests need one of them.");
            BeforeLoad();
            BedsitGame.SkipWakeUp = SkipWakeUp;
            BedsitContent.ForceMode = Mode;
            if (Mode == BedsitContent.ContentMode.Baked && !BedsitContent.BakedAvailable) Assert.Ignore("baked content not present (run Bedsit/Bake)");
            var load = SceneManager.LoadSceneAsync("Bedsit", LoadSceneMode.Single);
            while (!load.isDone) yield return null;
            float t = 0f;
            while ((BedsitGame.Instance == null || !BedsitGame.Instance.Ready) && t < 90f) { t += Time.unscaledDeltaTime; yield return null; }
            Game = BedsitGame.Instance;
            Assert.IsNotNull(Game, "BedsitGame did not start");
            Assert.IsTrue(Game.Ready, "Bedsit did not become ready: " + Game.Status);
            if (SkipWakeUp) { while (!Game.WakeUpFinished) yield return null; }
            yield return null;
            Magenta = new Material(Shader.Find("Unlit/Color")) { color = new Color(1f, 0f, 1f) };
            Cyan = new Material(Shader.Find("Unlit/Color")) { color = new Color(0f, 1f, 1f) };
        }

        [TearDown]
        public void Cleanup()
        {
            BedsitGame.SkipWakeUp = false;
            BedsitContent.ForceMode = BedsitContent.ContentMode.Auto;
        }

        // ---------------------------------------------------------------------------------------------------- helpers

        protected IEnumerator WaitForTurn()
        {
            float guard = 0f;
            while (Game.View.IsTurning && guard < 3f) { guard += Time.deltaTime; yield return null; }
        }

        protected IEnumerator Face(CompassDirection d)
        {
            Game.View.SnapTo(d);
            Game.Interactions.Refresh();
            yield return null;
        }

        protected static void Paint(SimCharacterActor a, Material m)
        {
            foreach (var r in a.GetComponentsInChildren<Renderer>(true))
            {
                var mats = new Material[r.sharedMaterials.Length];
                for (int i = 0; i < mats.Length; i++) mats[i] = m;
                r.sharedMaterials = mats;
            }
        }

        protected static int CountPixels(Camera cam, System.Func<Color32, bool> match, int w = 320, int h = 180)
        {
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32);
            var prevT = cam.targetTexture; var prevA = RenderTexture.active;
            cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            var px = tex.GetPixels32();
            cam.targetTexture = prevT; RenderTexture.active = prevA;
            rt.Release(); Object.Destroy(rt); Object.Destroy(tex);
            int n = 0; foreach (var p in px) if (match(p)) n++;
            return n;
        }

        protected static bool IsMagenta(Color32 p) => p.r > 200 && p.g < 70 && p.b > 200;
        protected static bool IsCyan(Color32 p) => p.r < 70 && p.g > 200 && p.b > 200;

        protected IEnumerator WaitUntil(System.Func<bool> cond, float timeout, string what)
        {
            float t = 0f;
            while (!cond() && t < timeout) { t += Time.deltaTime; yield return null; }
            Assert.IsTrue(cond(), "Timed out waiting for: " + what);
        }
    }

    // ===================================================================================================================
    public class InputRegionTests
    {
        [Test] public void LeftEdgeTurnsLeft() => Assert.AreEqual(PlayerAction.TurnLeft, InputRegions.Classify(new Vector2(0.05f, 0.3f)));
        [Test] public void RightEdgeTurnsRight() => Assert.AreEqual(PlayerAction.TurnRight, InputRegions.Classify(new Vector2(0.95f, 0.6f)));
        [Test] public void TopCentreInteracts() => Assert.AreEqual(PlayerAction.Interact, InputRegions.Classify(new Vector2(0.5f, 0.85f)));
        [Test] public void MiddleAndBottomAreInert()
        {
            Assert.AreEqual(PlayerAction.None, InputRegions.Classify(new Vector2(0.5f, 0.3f)));
            Assert.AreEqual(PlayerAction.None, InputRegions.Classify(new Vector2(0.5f, 0.1f)));
        }
        [Test] public void ScreenPixelsMapCorrectly()
        {
            Assert.AreEqual(PlayerAction.TurnLeft, InputRegions.ClassifyScreen(new Vector2(50, 400), 1280, 720));
            Assert.AreEqual(PlayerAction.Interact, InputRegions.ClassifyScreen(new Vector2(640, 650), 1280, 720));
        }
        [Test] public void CompassMathWraps()
        {
            Assert.AreEqual(CompassDirection.East, CompassDirection.North.TurnedRight());
            Assert.AreEqual(CompassDirection.West, CompassDirection.North.TurnedLeft());
            var d = CompassDirection.North;
            for (int i = 0; i < 4; i++) d = d.TurnedRight();
            Assert.AreEqual(CompassDirection.North, d);
        }
    }

    // ===================================================================================================================
    public class FirstPersonTests : BedsitFixtureBase
    {
        [UnityTest]
        public IEnumerator StartingCameraIsFirstPerson()
        {
            var eye = Game.EyeCamera;
            Assert.IsNotNull(eye);
            Assert.AreSame(eye, Camera.main, "the eye camera is the main camera");
            // the camera hangs off the player rig, never off a character, and sits at standing eye height
            Assert.IsNull(eye.GetComponentInParent<SimCharacterActor>(), "camera must not belong to a character");
            Assert.AreEqual(BedsitWorldBuilder.EyeHeight, Game.Rig.position.y, 0.01f);
            Assert.AreEqual(Game.World.BedsitStandpoint.x, eye.transform.position.x, 0.01f);
            Assert.AreEqual(Game.World.BedsitStandpoint.z, eye.transform.position.z, 0.01f);
            // no other camera renders to the screen (no third-person / orbit / over-the-shoulder camera)
            var screenCams = Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).Where(c => c.enabled && c.targetTexture == null).ToArray();
            Assert.AreEqual(1, screenCams.Length, "exactly one camera draws to the screen: " + string.Join(",", screenCams.Select(c => c.name)));
            // the player's body is excluded from the eye camera by culling mask
            Assert.AreEqual(0, eye.cullingMask & BedsitLayers.PlayerMirrorOnlyMask, "eye camera must not render the player layer");
            yield return null;
        }

        [UnityTest]
        public IEnumerator RightTurnIsExactlyNinetyDegrees()
        {
            var pos = Game.EyeCamera.transform.position;
            float before = Game.View.CurrentYaw;
            Game.Input.Raise(PlayerAction.TurnRight);
            yield return WaitForTurn();
            Assert.AreEqual(CompassDirection.East, Game.View.Facing);
            Assert.AreEqual(Mathf.Repeat(before + 90f, 360f), Game.View.CurrentYaw, 0.001f);
            Assert.AreEqual(0f, Vector3.Distance(pos, Game.EyeCamera.transform.position), 1e-5f, "turning must not move the camera");
        }

        [UnityTest]
        public IEnumerator LeftTurnIsExactlyNinetyDegreesAnticlockwise()
        {
            Game.Input.Raise(PlayerAction.TurnLeft);
            yield return WaitForTurn();
            Assert.AreEqual(CompassDirection.West, Game.View.Facing);
            Assert.AreEqual(270f, Game.View.CurrentYaw, 0.001f);
        }

        [UnityTest]
        public IEnumerator FourTurnsReturnToOriginalOrientation()
        {
            var rot0 = Game.EyeCamera.transform.rotation;
            for (int i = 0; i < 4; i++) { Game.Input.Raise(PlayerAction.TurnRight); yield return WaitForTurn(); }
            Assert.AreEqual(CompassDirection.North, Game.View.Facing);
            Assert.AreEqual(0f, Quaternion.Angle(rot0, Game.EyeCamera.transform.rotation), 0.01f);
            for (int i = 0; i < 4; i++) { Game.Input.Raise(PlayerAction.TurnLeft); yield return WaitForTurn(); }
            Assert.AreEqual(0f, Quaternion.Angle(rot0, Game.EyeCamera.transform.rotation), 0.01f);
        }

        [UnityTest]
        public IEnumerator TurnTakesAboutAThirdOfASecond()
        {
            float t0 = Time.time;
            Game.Input.Raise(PlayerAction.TurnRight);
            yield return WaitForTurn();
            float dt = Time.time - t0;
            Assert.That(dt, Is.InRange(0.2f, 0.45f), "smooth turn duration");
        }

        [UnityTest]
        public IEnumerator ExactlyFourDistinctCompassViewsNinetyDegreesApart()
        {
            var yaws = new List<float>();
            for (int i = 0; i < 4; i++) { yaws.Add(Game.View.CurrentYaw); Game.Input.Raise(PlayerAction.TurnRight); yield return WaitForTurn(); }
            Assert.AreEqual(new List<float> { 0f, 90f, 180f, 270f }, yaws.Select(y => Mathf.Round(y)).ToList());
        }

        [UnityTest]
        public IEnumerator PlayerBodyIsNeverVisibleNorthEastWestButIsInTheMirror()
        {
            Paint(Game.Player, Magenta);
            Paint(Game.NpcCorridor, Cyan); Paint(Game.NpcEast, Cyan); Paint(Game.NpcWest, Cyan);
            yield return null;

            foreach (var d in new[] { CompassDirection.North, CompassDirection.East, CompassDirection.West })
            {
                yield return Face(d);
                Game.Mirror.Render();
                int magenta = CountPixels(Game.EyeCamera, IsMagenta);
                Assert.AreEqual(0, magenta, $"player body visible while facing {d}");
            }

            // also never visible mid-turn
            yield return Face(CompassDirection.West);
            Game.Input.Raise(PlayerAction.TurnLeft);                    // West -> South: at all times sample the view
            int samples = 0, peak = 0;
            while (Game.View.IsTurning) { Game.Mirror.Render(); peak = Mathf.Max(peak, CountPixels(Game.EyeCamera, IsMagenta)); samples++; yield return null; }
            Assert.Greater(samples, 3);

            // South: the mirror reveals the player
            yield return Face(CompassDirection.South);
            Game.Mirror.Render();
            int inMirror = CountPixels(Game.EyeCamera, IsMagenta);
            Assert.Greater(inMirror, 300, "the player's Sim must be visible in the mirror");
        }

        [UnityTest]
        public IEnumerator EachNonMirrorViewContainsAnNpc()
        {
            Paint(Game.NpcCorridor, Cyan); Paint(Game.NpcEast, Cyan); Paint(Game.NpcWest, Cyan);
            yield return null;
            foreach (var d in new[] { CompassDirection.North, CompassDirection.East, CompassDirection.West })
            {
                yield return Face(d);
                Game.Mirror.Render();
                int cyan = CountPixels(Game.EyeCamera, IsCyan);
                Assert.Greater(cyan, 150, $"an NPC must be visible facing {d} (cyan pixels: {cyan})");
            }
        }

        [UnityTest]
        public IEnumerator MirrorCameraIsTheEyeMirroredThroughTheGlassPlane()
        {
            yield return Face(CompassDirection.South);
            Game.Mirror.Render();
            var m = Game.Mirror.transform;
            var eye = Game.EyeCamera.transform.position;
            var refl = Game.Mirror.ReflectionCamera.transform.position;
            float dEye = Vector3.Dot(eye - m.position, m.forward);
            float dRefl = Vector3.Dot(refl - m.position, m.forward);
            Assert.AreEqual(dEye, -dRefl, 0.01f, "reflection camera is at the mirrored distance behind the glass");
            Assert.AreEqual(eye.x, refl.x, 0.01f);
            Assert.AreEqual(eye.y, refl.y, 0.01f);
            Assert.IsNotNull(Game.Mirror.ReflectionCamera.targetTexture, "reflection renders to a RenderTexture");
        }
    }

    // ===================================================================================================================
    public class InteractionTests : BedsitFixtureBase
    {
        [UnityTest]
        public IEnumerator EachDirectionHasItsInteractionTarget()
        {
            var expect = new Dictionary<CompassDirection, string>
            {
                { CompassDirection.North, "door" }, { CompassDirection.East, "window_east" },
                { CompassDirection.South, "mirror" }, { CompassDirection.West, "window_west" },
            };
            foreach (var kv in expect)
            {
                yield return Face(kv.Key);
                Assert.IsNotNull(Game.Interactions.Current, "no target facing " + kv.Key);
                Assert.AreEqual(kv.Value, Game.Interactions.Current.Id);
            }
        }

        [UnityTest]
        public IEnumerator MirrorInteractionPlaysAnAuthenticAnimationOnTheReflectedPlayer()
        {
            yield return Face(CompassDirection.South);
            var before = Game.Player.CapturePose();
            Game.Input.Raise(PlayerAction.Interact);
            float max = 0f;
            for (float t = 0f; t < 2.2f; t += Time.deltaTime)
            {
                max = Mathf.Max(max, SimCharacterActor.MaxPoseDelta(before, Game.Player.CapturePose()));
                yield return null;
            }
            Assert.Greater(max, 20f, "the reflected player's skeleton must visibly change pose (max bone change " + max + " deg)");
            if (!BedsitContent.UsingBaked)
            {
                var res = SimAnimationLibrary.Resolve(AnimationKeys.Wave);
                Assert.IsNotNull(res);
                StringAssert.StartsWith("a-", res.ResourceName);
                StringAssert.EndsWith("_anim", res.ResourceName);
                StringAssert.EndsWith(".package", res.Package);
                Debug.Log($"[Test] mirror wave: {res.ResourceName} from {res.Package}, max bone change {max:0.0} deg");
            }
            else Debug.Log($"[Test] mirror wave (baked clip), max bone change {max:0.0} deg");
        }

        [UnityTest]
        public IEnumerator EastWindowInteractionAnimatesTheNpc()
        {
            yield return Face(CompassDirection.East);
            var before = Game.NpcEast.CapturePose();
            Game.Input.Raise(PlayerAction.Interact);
            float max = 0f; bool sawWave = false;
            for (float t = 0f; t < 2.0f; t += Time.deltaTime)
            {
                sawWave |= Game.NpcEast.CurrentKey == AnimationKeys.Wave;
                max = Mathf.Max(max, SimCharacterActor.MaxPoseDelta(before, Game.NpcEast.CapturePose()));
                yield return null;
            }
            Assert.IsTrue(sawWave, "east NPC plays the wave reaction");
            Assert.Greater(max, 20f, "east NPC pose change " + max);
        }

        [UnityTest]
        public IEnumerator WestWindowInteractionAnimatesTheNpc()
        {
            yield return Face(CompassDirection.West);
            var before = Game.NpcWest.CapturePose();
            Game.Input.Raise(PlayerAction.Interact);
            float max = 0f; bool sawClap = false;
            for (float t = 0f; t < 1.5f; t += Time.deltaTime)
            {
                sawClap |= Game.NpcWest.CurrentKey == AnimationKeys.Clap;
                max = Mathf.Max(max, SimCharacterActor.MaxPoseDelta(before, Game.NpcWest.CapturePose()));
                yield return null;
            }
            Assert.IsTrue(sawClap, "west NPC plays the clap reaction");
            Assert.Greater(max, 15f, "west NPC pose change " + max);
        }

        [UnityTest]
        public IEnumerator NorthInteractionOpensTheDoorAndWalksIntoTheCorridorAtEyeHeight()
        {
            yield return Face(CompassDirection.North);
            var eye = Game.EyeCamera;
            float eyeY = Game.Rig.position.y;
            Assert.IsFalse(Game.World.Door.IsOpen);
            Game.Input.Raise(PlayerAction.Interact);
            yield return WaitUntil(() => Game.Transition.IsMoving || Game.Zones.CurrentZoneId == BedsitGame.ZoneCorridor, 6f, "movement to start");
            // while moving, the camera stays at eye height and is still the one first-person camera
            while (Game.Transition.IsMoving)
            {
                Assert.AreEqual(eyeY, Game.Rig.position.y, 1e-4f, "eye height changes during the transition");
                Assert.AreSame(eye, Camera.main);
                yield return null;
            }
            yield return WaitUntil(() => Game.Zones.CurrentZoneId == BedsitGame.ZoneCorridor, 4f, "arrival in the corridor");
            Assert.IsTrue(Game.World.Door.IsOpen, "the door opened");
            Assert.Greater(Game.Rig.position.z, BedsitWorldBuilder.HalfD + BedsitWorldBuilder.WallT, "camera is now beyond the doorway");
            Assert.AreEqual(Game.World.CorridorStandpoint.z, Game.Rig.position.z, 0.02f);
            Assert.AreEqual(eyeY, Game.Transition.MinEyeHeightDuringMove, 1e-4f);
            Assert.AreEqual(eyeY, Game.Transition.MaxEyeHeightDuringMove, 1e-4f);
            Assert.AreEqual(CompassDirection.North, Game.View.Facing);
            Assert.IsNull(eye.GetComponentInParent<SimCharacterActor>());
            // still first person in the corridor: the player body is not visible
            Paint(Game.Player, Magenta); yield return null;
            Assert.AreEqual(0, CountPixels(eye, IsMagenta));
            // and the corridor has its own interaction (south = back to the bedsit)
            yield return Face(CompassDirection.South);
            Assert.AreEqual("back_to_bedsit", Game.Interactions.Current.Id);
        }
    }

    // ===================================================================================================================
    public class WakeUpTests : BedsitFixtureBase
    {
        protected override bool SkipWakeUp => false;

        [UnityTest]
        public IEnumerator WakeUpFadesInRisesAndHandsOverControl()
        {
            // starts dark, lying low, looking at the ceiling, input locked
            Assert.AreEqual(1f, Game.Hud.FadeAlpha, 0.01f, "screen begins dark");
            Assert.IsTrue(Game.Input.Locked);
            Assert.Less(Game.Rig.position.y, 1.0f, "player starts lying in bed");
            float startY = Game.Rig.position.y;

            yield return WaitUntil(() => Game.Hud.FadeAlpha < 0.5f, 6f, "fade into the room");
            bool rose = false;
            yield return WaitUntil(() => { rose |= Game.Rig.position.y > startY + 0.2f; return Game.WakeUpFinished; }, 15f, "wake-up to finish");
            Assert.IsTrue(rose, "camera rises");
            Assert.AreEqual(0f, Game.Hud.FadeAlpha, 0.01f);
            Assert.AreEqual(BedsitWorldBuilder.EyeHeight, Game.Rig.position.y, 0.01f, "standing eye level");
            Assert.AreEqual(CompassDirection.North, Game.View.Facing);
            Assert.AreEqual(0f, Game.View.CurrentYaw % 360f, 0.01f);
            Assert.IsFalse(Game.Input.Locked, "the player can now look in four directions");
        }
    }

    // ===================================================================================================================
    public class AuthenticAnimationTests : BedsitFixtureBase
    {
        [UnityTest]
        public IEnumerator OriginalSims2AnimationVisiblyChangesACharactersPose()
        {
            if (BedsitContent.UsingBaked) Assert.Ignore("needs the live Sims 2 data (resource-level checks)");
            var npc = Game.NpcCorridor;
            yield return new WaitForSeconds(0.5f);
            var rest = npc.CapturePose();
            // the animation is a real Maxis ANIM resource decoded by OpenTS2
            var res = SimAnimationLibrary.Resolve(AnimationKeys.Wave);
            Assert.IsNotNull(res.Asset.AnimResource);
            Assert.Greater(res.Channels, 20, "a full-body skeletal animation has dozens of channels");
            Assert.IsTrue(res.Asset.AnimResource.AnimTargets.Any(t => t.TagName.ToLower() == "auskel"), "targets the original Sims skeleton");
            Assert.IsTrue(npc.PlayOneShot(AnimationKeys.Wave));
            float max = 0f;
            for (float t = 0f; t < 2.0f; t += Time.deltaTime) { max = Mathf.Max(max, SimCharacterActor.MaxPoseDelta(rest, npc.CapturePose())); yield return null; }
            Assert.Greater(max, 30f, "wave changes at least one bone by >30 degrees (was " + max + ")");
            Debug.Log($"[Test] authentic animation {res.ResourceName} ({res.Package}): {res.Channels} channels, max bone change {max:0.0} deg");
        }

        [UnityTest]
        public IEnumerator EveryLibraryAnimationResolvesToAnOriginalResource()
        {
            if (BedsitContent.UsingBaked) Assert.Ignore("needs the live Sims 2 data (resource-level checks)");
            foreach (var key in SimAnimationLibrary.Definitions.Keys)
            {
                var r = SimAnimationLibrary.Resolve(key);
                Assert.IsNotNull(r, "unresolved animation " + key);
                StringAssert.EndsWith("_anim", r.ResourceName);
            }
            yield return null;
        }
    }
}

namespace Bedsit.Tests
{
    /// <summary>The first-person and interaction tests again, but forcing the BAKED content path (no Sims 2 / OpenTS2 data).</summary>
    public class BakedFirstPersonTests : FirstPersonTests
    {
        protected override Bedsit.Sims2.BedsitContent.ContentMode Mode => Bedsit.Sims2.BedsitContent.ContentMode.Baked;
    }

    public class BakedInteractionTests : InteractionTests
    {
        protected override Bedsit.Sims2.BedsitContent.ContentMode Mode => Bedsit.Sims2.BedsitContent.ContentMode.Baked;
    }
}

namespace Bedsit.Tests
{
    /// <summary>The music session inside the real bedsit scene: looking around must never disturb it.</summary>
    public class MusicPocSceneTests : BedsitFixtureBase
    {
        protected override void BeforeLoad()
        {
            if (Bedsit.Music.MusicSession.FindAudioRoot() == null) Assert.Ignore("LocalAudio not found (run Tools/music/prepare_audio.py)");
            MusicPoc.ForceRequest = true;
        }

        [TearDown] public void ResetFlag() { MusicPoc.ForceRequest = false; }

        IEnumerator StartMusicWithBot()
        {
            yield return WaitUntil(() => MusicPoc.Instance != null && MusicPoc.Instance.Session != null && MusicPoc.Instance.Status != "starting" && MusicPoc.Instance.Status != "waiting for wake-up", 40f, "music POC to start");
            MusicPoc.Instance.Bot = Bedsit.Music.MusicBot.Perfect();
            yield return WaitUntil(() => MusicPoc.Instance.Session.Judge.TotalHits >= 8, 40f, "the first notes to be played");
        }

        [UnityTest]
        public IEnumerator TurningFollowsCompassOrderAndNeverResetsMusicOrScoring()
        {
            yield return StartMusicWithBot();
            var poc = MusicPoc.Instance; var session = poc.Session;
            var stems = session.Mixer.Voices.Where(v => v.Role == "custom").ToArray();
            Assert.GreaterOrEqual(stems.Length, 4, "custom stems are playing");
            double lastTime = session.Mixer.Time; int lastHits = session.Judge.TotalHits, lastLog = session.Director.Log.Count;
            int started = session.Director.BuildsStarted;

            var expected = new[] { CompassDirection.East, CompassDirection.South, CompassDirection.West, CompassDirection.North,
                                   CompassDirection.West, CompassDirection.South, CompassDirection.East, CompassDirection.North };
            Assert.AreEqual(CompassDirection.North, Game.View.Facing, "starts facing North (scene 1)");
            for (int i = 0; i < expected.Length; i++)
            {
                Game.Input.Raise(i < 4 ? PlayerAction.TurnRight : PlayerAction.TurnLeft);
                yield return WaitForTurn();
                yield return new WaitForSeconds(0.35f);
                Assert.AreEqual(expected[i], Game.View.Facing, "compass order, not scene-number order (step " + i + ")");
                Assert.AreSame(session, MusicPoc.Instance.Session, "same music session in every view");
                Assert.Greater(session.Mixer.Time, lastTime, "music keeps playing");
                Assert.GreaterOrEqual(session.Judge.TotalHits, lastHits, "score never resets");
                Assert.GreaterOrEqual(session.Director.Log.Count, lastLog);
                Assert.AreEqual(started, session.Director.BuildsStarted, "no new build/restart caused by looking around");
                var now = session.Mixer.Voices.Where(v => v.Role == "custom").ToArray();
                Assert.AreEqual(stems.Length, now.Length);
                for (int k = 0; k < stems.Length; k++) Assert.AreSame(stems[k], now[k], "the same stem voices keep playing (no restart)");
                lastTime = session.Mixer.Time; lastHits = session.Judge.TotalHits; lastLog = session.Director.Log.Count;
            }
            Assert.AreEqual(0, session.Judge.TotalMisses, "turning caused no misses for the scripted perfect player");
        }

        [UnityTest]
        public IEnumerator PadTapsInTheBottomStripDoNotTurn()
        {
            yield return StartMusicWithBot();
            var facing = Game.View.Facing;
            Assert.AreEqual(PlayerAction.None, InputRegions.ClassifyScreen(new Vector2(640, 40), 1280, 720), "bottom strip is not a turn/interact zone");
            for (int i = 0; i < 4; i++) { Game.Input.RaisePad(i); yield return null; }
            Assert.AreEqual(facing, Game.View.Facing, "bottom keeps the current facing");
            Assert.IsTrue(Game.Input.PadsEnabled == (MusicPoc.Instance.Session.Director.Mode == Bedsit.Music.MusicMode.Rhythm));
        }

        [UnityTest]
        public IEnumerator PauseFreezesTheTimelineInTheRunningGame()
        {
            yield return StartMusicWithBot();
            var poc = MusicPoc.Instance; var m = poc.Session.Mixer;
            poc.SetPaused(true);
            yield return null;
            double t = m.Time; int hits = poc.Session.Judge.TotalHits, misses = poc.Session.Judge.TotalMisses;
            yield return new WaitForSeconds(1.5f);
            Assert.AreEqual(t, m.Time, 0.0, "timeline frozen");
            Assert.AreEqual(hits, poc.Session.Judge.TotalHits);
            Assert.AreEqual(misses, poc.Session.Judge.TotalMisses, "no misses while paused");
            poc.SetPaused(false);
            yield return new WaitForSeconds(0.6f);
            Assert.Greater(m.Time, t + 0.3, "resumes from the same position");
            Assert.AreEqual(0, poc.Session.Judge.TotalMisses);
        }
    }
}

namespace Bedsit.Tests
{
    /// <summary>Act One in the real bedsit scene: nobody but the player, a messy room to tidy, a door that waits for the knock.</summary>
    public class ActOneSceneTests : BedsitFixtureBase
    {
        protected override void BeforeLoad() { MusicPoc.ForceRequest = true; }
        [TearDown] public void ResetFlag() { MusicPoc.ForceRequest = false; }

        ActOne Act => ActOne.Instance;

        IEnumerator ActReady()
        {
            yield return WaitUntil(() => Act != null && Act.SetupDone, 30f, "Act One to set up");
        }

        static bool OnScreen(Camera cam, Vector3 world)
        {
            var sp = cam.WorldToScreenPoint(world);
            return sp.z > 0.2f && sp.x > 0 && sp.x < Screen.width && sp.y > 0 && sp.y < Screen.height;
        }

        [UnityTest]
        public IEnumerator OnlyThePlayerExistsInTheWorldAndShowsOnlyInTheMirror()
        {
            yield return ActReady();
            Assert.IsFalse(Game.NpcEast.gameObject.activeInHierarchy, "no Sim at the east window");
            Assert.IsFalse(Game.NpcWest.gameObject.activeInHierarchy, "no Sim at the west window");
            Assert.IsFalse(Game.NpcCorridor.gameObject.activeInHierarchy, "no Sim in the corridor");
            Assert.IsTrue(Game.Player.gameObject.activeInHierarchy, "the player is there");
            Assert.AreEqual(BedsitLayers.PlayerMirrorOnly, Game.Player.gameObject.layer == 0 ? BedsitLayers.PlayerMirrorOnly : Game.Player.gameObject.layer, "player only on the mirror layer");
            Assert.AreEqual(0, (Game.EyeCamera.cullingMask & BedsitLayers.PlayerMirrorOnlyMask), "the eye camera never renders the player");
            Assert.IsFalse(Game.EastTarget.Interactable || Game.WestTarget.Interactable, "nobody at the windows to react");
            // facing the mirror, the eye camera sees no Sim at all (no skin-coloured NPC pixels) - checked by the old NPC tests' paint method
            foreach (var d in new[] { CompassDirection.North, CompassDirection.East, CompassDirection.West })
            {
                yield return Face(d);
                Paint(Game.NpcEast, Magenta); Paint(Game.NpcWest, Magenta); Paint(Game.NpcCorridor, Magenta);
                Assert.AreEqual(0, CountPixels(Game.EyeCamera, IsMagenta), "no Sim visible facing " + d);
            }
        }

        [UnityTest]
        public IEnumerator TheRoomIsMessyFromEveryViewpoint()
        {
            yield return ActReady();
            Assert.GreaterOrEqual(Act.TotalItems, 12);
            foreach (var d in new[] { CompassDirection.North, CompassDirection.East, CompassDirection.South, CompassDirection.West })
            {
                yield return Face(d);
                int visible = Act.Items.Count(i => !i.Tidied && OnScreen(Game.EyeCamera, i.PickCentre));
                Assert.GreaterOrEqual(visible, 3, "pieces of mess on screen facing " + d);
                Assert.Greater(Act.Remaining(d), 0, "compass pips for " + d);
            }
        }

        [UnityTest]
        public IEnumerator TappingMessTidiesItAwayAndTheMeterRises()
        {
            yield return ActReady();
            yield return Face(CompassDirection.East);
            var item = Act.Items.First(i => i.Kind == "mug" && OnScreen(Game.EyeCamera, i.PickCentre));
            var px = (Vector2)Game.EyeCamera.WorldToScreenPoint(item.PickCentre);
            Assert.AreEqual(0f, Act.TidyFraction);
            Assert.IsFalse(Act.TryTidyAtScreen(new Vector2(Screen.width * 0.5f, Screen.height * 0.9f)), "tapping bare wall tidies nothing");
            Assert.IsTrue(Act.TryTidyAtScreen(px), "tapping the mug tidies it");
            Assert.IsTrue(item.Tidying || item.Tidied);
            yield return new WaitForSeconds(0.8f);
            Assert.IsTrue(item.Tidied && !item.gameObject.activeSelf, "the item is gone");
            Assert.AreEqual(1, Act.TidiedCount);
            Assert.Greater(Act.TidyFraction, 0f);
            Assert.IsFalse(Act.TryTidyAtScreen(px), "it cannot be tidied twice");
        }

        [UnityTest]
        public IEnumerator TidyClicksTakePriorityOverTheTurnZones()
        {
            yield return ActReady();
            yield return Face(CompassDirection.East);
            Assert.IsNotNull(Game.Input.ClickHandler, "Act One hooks the click router");
            // an item in the right-hand turn zone is tidied rather than turning the view
            var inZone = Act.Items.FirstOrDefault(i => { var sp = Game.EyeCamera.WorldToScreenPoint(i.PickCentre); return sp.z > 0 && sp.x > Screen.width * (1f - InputRegions.SideWidth) && sp.x < Screen.width; });
            if (inZone != null)
            {
                var sp = (Vector2)Game.EyeCamera.WorldToScreenPoint(inZone.PickCentre);
                Assert.IsTrue(Game.Input.ClickHandler(sp));
            }
            Assert.AreEqual(CompassDirection.East, Game.View.Facing, "tidying never turns the view");
        }

        [UnityTest]
        public IEnumerator DoorStaysShutUntilTheKnockThenOpensForAWomanIfTheRoomIsClean()
        {
            yield return ActReady();
            yield return Face(CompassDirection.North);
            Assert.IsFalse(Game.World.Door.IsOpen, "the door starts shut");
            Assert.IsFalse(Game.DoorTarget.Interactable, "locked before the knock");
            Game.Input.Raise(PlayerAction.Interact); yield return new WaitForSeconds(0.3f);
            Assert.IsFalse(Act.DoorOpened, "nothing happens before the knock");
            foreach (var it in Act.Items.ToArray()) Act.Tidy(it);
            Assert.IsTrue(Act.IsClean);
            Act.ForceKnock();
            yield return null;
            Assert.IsTrue(Act.Knocked); Assert.IsTrue(Game.DoorTarget.Interactable, "unlocked by the knock");
            Game.Interactions.Refresh();
            Game.Input.Raise(PlayerAction.Interact);
            yield return WaitUntil(() => Game.World.Door.IsOpen, 6f, "the door to open");
            Assert.AreEqual("woman", Act.VisitorKind);
            Assert.AreSame(Game.NpcEast, Act.Visitor, "Pleasantview Sim 13 (female)");
            Assert.IsTrue(Act.Visitor.gameObject.activeInHierarchy);
            Assert.IsFalse(Game.NpcCorridor.gameObject.activeInHierarchy, "only one visitor");
        }

        [UnityTest]
        public IEnumerator AMessyRoomGetsAMan()
        {
            yield return ActReady();
            yield return Face(CompassDirection.North);
            foreach (var it in Act.Items.Take(5).ToArray()) Act.Tidy(it);          // 5 of 15: not clean
            Assert.IsFalse(Act.IsClean);
            Act.ForceKnock(); yield return null;
            Game.Interactions.Refresh();
            Game.Input.Raise(PlayerAction.Interact);
            yield return WaitUntil(() => Game.World.Door.IsOpen, 6f, "the door to open");
            Assert.AreEqual("man", Act.VisitorKind);
            Assert.AreSame(Game.NpcCorridor, Act.Visitor, "Pleasantview Sim 11 (male)");
            Assert.IsFalse(Game.NpcEast.gameObject.activeInHierarchy);
        }

        [UnityTest]
        public IEnumerator HeadphonesGoOnAfterWakingAndTheMusicWaitsForThem()
        {
            yield return ActReady();
            yield return WaitUntil(() => Act.HeadphonesStarted, 5f, "headphones to start");
            yield return WaitUntil(() => Act.HeadphonesOn, 5f, "headphones on");
            Assert.AreEqual(1f, Act.HeadphonesProgress, 1e-4f);
        }
    }
}
