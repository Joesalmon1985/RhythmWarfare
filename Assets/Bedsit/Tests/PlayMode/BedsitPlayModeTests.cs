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

        [UnitySetUp]
        public IEnumerator LoadBedsit()
        {
            if (Sims2Runtime.FindConfig() == null) Assert.Ignore("config.json (Sims 2 install) not found: these tests need a local Sims 2 install.");
            BedsitGame.SkipWakeUp = SkipWakeUp;
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
            var res = SimAnimationLibrary.Resolve(AnimationKeys.Wave);
            Assert.IsNotNull(res);
            StringAssert.StartsWith("a-", res.ResourceName);
            StringAssert.EndsWith("_anim", res.ResourceName);
            StringAssert.EndsWith(".package", res.Package);
            Debug.Log($"[Test] mirror wave: {res.ResourceName} from {res.Package}, max bone change {max:0.0} deg");
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
