using System.Collections.Generic;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Builds the bedsit's mess: small procedural props (pizza boxes, laundry, mugs, bottles, books, bags ...) placed on the furniture and
    /// sills (the first-person eye is at 1.62 m looking level, so floor-level mess would be off-screen: it sits on surfaces or in tall piles).
    /// No Sims 2 assets are used, so this works identically with live and baked content. Positions are world metres (+Z north, +X east).
    /// </summary>
    public static class ClutterFactory
    {
        public struct Spot
        {
            public string Kind; public Vector3 Pos; public float Yaw, Scale;
            public Spot(string kind, float x, float y, float z, float yaw = 0f, float scale = 1.6f) { Kind = kind; Pos = new Vector3(x, y, z); Yaw = yaw; Scale = scale; }
        }

        /// <summary>The layout (tuned by eye from the four standing views). Props are drawn a little larger than life so they read from across the room.</summary>
        public static readonly Spot[] Layout =
        {
            // NORTH (door wall): tall piles against the wall, a shirt over the plant, books on the bookcase
            new Spot("bag",      -0.80f, 0.00f, 2.15f,   0f, 1.3f),
            new Spot("pizza",     0.85f, 0.00f, 2.18f,  15f, 1.35f),
            new Spot("shirt",    -1.40f, 1.15f, 1.62f, 180f, 1.0f),
            new Spot("books",     1.45f, 1.12f, 1.98f, -10f, 1.25f),
            // EAST (window + bed)
            new Spot("mug",       1.99f, 1.00f, 0.12f,   0f, 1.7f),
            new Spot("bottles",   1.99f, 1.00f, 0.80f,  30f, 1.5f),
            new Spot("laundry",   1.70f, 0.60f,-1.10f,  10f, 1.4f),
            new Spot("plate",     1.35f, 0.60f,-1.55f,  -8f, 1.8f),
            // SOUTH (mirror; dresser at the right)
            new Spot("cups",     -1.25f, 1.42f,-1.90f,   0f, 1.6f),
            new Spot("magazines",-1.70f, 1.42f,-2.10f,  40f, 1.4f),
            new Spot("takeaway", -1.45f, 1.42f,-2.20f,  25f, 1.4f),
            // WEST (window, chair, dresser at the left)
            new Spot("paper",    -1.99f, 1.00f,-0.55f,   0f, 1.9f),
            new Spot("mug",      -1.99f, 1.00f,-0.02f,  60f, 1.7f),
            new Spot("shirt",    -1.55f, 0.47f, 0.95f, 100f, 0.9f),
            new Spot("trainers", -1.50f, 1.42f,-1.20f,  20f, 1.4f),
        };

        static Material _mat;
        static readonly Dictionary<string, Mesh> _meshes = new Dictionary<string, Mesh>();

        static Color C(float r, float g, float b) => new Color(r, g, b);

        public static Material PropMaterial => Mat();

        /// <summary>Over-ear headphones modelled around the head centre (ears along world X, player facing -Z): band arc + two ear cups.
        /// Only ever shown in the mirror (it lives on the player's mirror-only layer).</summary>
        public static Mesh HeadphonesMesh()
        {
            var m = new PropMesh(); var dark = C(0.09f, 0.09f, 0.11f); var accent = C(0.88f, 0.22f, 0.28f);
            const float R = 0.118f;
            for (int i = 0; i <= 10; i++)
            {
                float a = Mathf.PI * i / 10f;                           // 0 = right ear .. pi = left ear, over the top
                m.Box(new Vector3(Mathf.Cos(a) * R, Mathf.Sin(a) * R * 1.02f, 0f), new Vector3(0.024f, 0.024f, 0.034f), new Vector3(0f, 0f, a * Mathf.Rad2Deg + 90f), dark);
            }
            foreach (int sgn in new[] { -1, 1 })
            {
                m.Cyl(new Vector3(sgn * 0.094f, 0f, 0.004f), 0.064f, 0.044f, new Vector3(0f, 0f, -sgn * 90f), accent, 0.064f, 16);
                m.Cyl(new Vector3(sgn * 0.086f, 0f, 0.004f), 0.054f, 0.012f, new Vector3(0f, 0f, -sgn * 90f), dark, 0.054f, 16);
            }
            return m.Build("Headphones");
        }

        static Material Mat()
        {
            if (_mat != null) return _mat;
            var sh = Shader.Find("Bedsit/Prop");
            _mat = new Material(sh != null ? sh : Shader.Find("Diffuse")) { name = "BedsitProp" };
            return _mat;
        }

        /// <summary>(mesh, pick radius, height) for a kind.</summary>
        static Mesh MeshFor(string kind, out float radius, out float height)
        {
            var m = new PropMesh();
            switch (kind)
            {
                case "pizza":     // tower of delivery boxes, top one open with a slice
                    for (int i = 0; i < 5; i++) m.Box(new Vector3(0.012f * (i % 2 == 0 ? 1 : -1), 0.03f + i * 0.058f, 0f), new Vector3(0.38f, 0.05f, 0.38f), new Vector3(0, i * 9f, 0), C(0.80f, 0.64f, 0.42f));
                    m.Box(new Vector3(0, 0.32f, -0.16f), new Vector3(0.38f, 0.02f, 0.30f), new Vector3(-62f, 0, 0), C(0.88f, 0.72f, 0.48f));
                    m.Cyl(new Vector3(0, 0.325f, 0.02f), 0.13f, 0.015f, Vector3.zero, C(0.92f, 0.62f, 0.22f));
                    m.Cyl(new Vector3(0.02f, 0.34f, 0.03f), 0.045f, 0.012f, Vector3.zero, C(0.78f, 0.18f, 0.12f), 0.04f, 8);
                    radius = 0.26f; height = 0.34f; break;
                case "bag":       // bin bag
                    m.Blob(new Vector3(0, 0.27f, 0), new Vector3(0.30f, 0.30f, 0.27f), Vector3.zero, C(0.10f, 0.11f, 0.16f), 7, 12);
                    m.Blob(new Vector3(0.10f, 0.50f, 0.03f), new Vector3(0.10f, 0.12f, 0.09f), new Vector3(0, 0, 25f), C(0.12f, 0.13f, 0.19f));
                    m.Cyl(new Vector3(0.12f, 0.57f, 0.03f), 0.02f, 0.07f, new Vector3(0, 0, 20f), C(0.85f, 0.2f, 0.2f), 0.012f, 6);
                    m.Box(new Vector3(-0.10f, 0.20f, 0.24f), new Vector3(0.14f, 0.12f, 0.12f), new Vector3(0, 20, 0), C(0.88f, 0.86f, 0.80f));   // takeaway box sticking out
                    radius = 0.32f; height = 0.60f; break;
                case "books":     // leaning stack
                    m.Box(new Vector3(0, 0.03f, 0), new Vector3(0.30f, 0.06f, 0.22f), new Vector3(0, 0, 0), C(0.75f, 0.18f, 0.18f));
                    m.Box(new Vector3(0.01f, 0.09f, 0), new Vector3(0.27f, 0.05f, 0.20f), new Vector3(0, 12, 0), C(0.18f, 0.40f, 0.72f));
                    m.Box(new Vector3(-0.01f, 0.145f, 0), new Vector3(0.29f, 0.06f, 0.21f), new Vector3(0, -8, 0), C(0.92f, 0.78f, 0.22f));
                    m.Box(new Vector3(0.0f, 0.205f, 0), new Vector3(0.24f, 0.05f, 0.18f), new Vector3(0, 25, 0), C(0.22f, 0.58f, 0.34f));
                    m.Box(new Vector3(0.22f, 0.15f, 0.06f), new Vector3(0.05f, 0.26f, 0.19f), new Vector3(0, 0, -18f), C(0.55f, 0.30f, 0.65f));   // one leaning against it
                    radius = 0.24f; height = 0.28f; break;
                case "mug":
                    m.Cyl(new Vector3(0, 0, 0), 0.045f, 0.10f, Vector3.zero, C(0.92f, 0.92f, 0.90f), 0.05f, 12);
                    m.Cyl(new Vector3(0, 0.095f, 0), 0.040f, 0.006f, Vector3.zero, C(0.30f, 0.18f, 0.10f), 0.040f, 12);
                    m.Box(new Vector3(0.062f, 0.055f, 0), new Vector3(0.03f, 0.055f, 0.012f), Vector3.zero, C(0.92f, 0.92f, 0.90f));
                    m.Cyl(new Vector3(0.14f, 0, 0.03f), 0.04f, 0.085f, Vector3.zero, C(0.25f, 0.5f, 0.8f), 0.045f, 12);
                    radius = 0.14f; height = 0.11f; break;
                case "bottles":
                    for (int i = 0; i < 3; i++)
                    {
                        var col = i == 1 ? C(0.45f, 0.28f, 0.12f) : C(0.18f, 0.55f, 0.28f);
                        var o = new Vector3(i * 0.075f - 0.07f, 0, (i % 2) * 0.03f);
                        m.Cyl(o, 0.03f, 0.15f, Vector3.zero, col, 0.03f, 10);
                        m.Cyl(o + new Vector3(0, 0.15f, 0), 0.03f, 0.08f, Vector3.zero, col, 0.013f, 10);
                    }
                    m.Cyl(new Vector3(0.10f, 0, -0.07f), 0.03f, 0.15f, new Vector3(0, 0, 80f), C(0.18f, 0.55f, 0.28f), 0.03f, 10);   // one knocked over
                    radius = 0.16f; height = 0.24f; break;
                case "laundry":   // heap of clothes
                    m.Blob(new Vector3(0, 0.08f, 0), new Vector3(0.30f, 0.10f, 0.24f), new Vector3(0, 10, 0), C(0.22f, 0.40f, 0.78f));
                    m.Blob(new Vector3(0.12f, 0.14f, 0.05f), new Vector3(0.22f, 0.09f, 0.17f), new Vector3(0, -25, 8), C(0.82f, 0.25f, 0.30f));
                    m.Blob(new Vector3(-0.10f, 0.17f, -0.04f), new Vector3(0.20f, 0.08f, 0.15f), new Vector3(0, 40, -6), C(0.92f, 0.92f, 0.88f));
                    m.Blob(new Vector3(0.02f, 0.22f, 0.06f), new Vector3(0.15f, 0.07f, 0.12f), new Vector3(0, 70, 5), C(0.30f, 0.68f, 0.40f));
                    m.Blob(new Vector3(0.23f, 0.04f, -0.12f), new Vector3(0.08f, 0.03f, 0.05f), new Vector3(0, 20, 0), C(0.95f, 0.8f, 0.2f));   // a sock
                    radius = 0.32f; height = 0.28f; break;
                case "plate":     // dirty plate with fork
                    m.Cyl(Vector3.zero, 0.13f, 0.02f, Vector3.zero, C(0.94f, 0.94f, 0.92f), 0.14f, 14);
                    m.Blob(new Vector3(0.02f, 0.035f, 0.01f), new Vector3(0.07f, 0.025f, 0.05f), Vector3.zero, C(0.55f, 0.35f, 0.18f));
                    m.Blob(new Vector3(-0.05f, 0.03f, -0.03f), new Vector3(0.035f, 0.02f, 0.03f), Vector3.zero, C(0.72f, 0.22f, 0.15f));
                    m.Box(new Vector3(0.09f, 0.022f, -0.04f), new Vector3(0.16f, 0.006f, 0.014f), new Vector3(0, 35, 0), C(0.78f, 0.78f, 0.80f));
                    radius = 0.16f; height = 0.06f; break;
                case "cups":      // tower of paper cups
                    for (int i = 0; i < 4; i++) m.Cyl(new Vector3(0, i * 0.07f, 0), 0.034f, 0.09f, Vector3.zero, i % 2 == 0 ? C(0.9f, 0.25f, 0.22f) : C(0.96f, 0.96f, 0.96f), 0.044f, 12);
                    m.Cyl(new Vector3(0.12f, 0, 0.02f), 0.034f, 0.09f, new Vector3(0, 0, 75f), C(0.9f, 0.25f, 0.22f), 0.044f, 12);
                    radius = 0.15f; height = 0.34f; break;
                case "takeaway":
                    m.Box(new Vector3(0, 0.05f, 0), new Vector3(0.20f, 0.10f, 0.15f), new Vector3(0, 0, 0), C(0.86f, 0.18f, 0.16f));
                    m.Box(new Vector3(0.01f, 0.115f, 0), new Vector3(0.18f, 0.03f, 0.13f), new Vector3(0, 8, 0), C(0.96f, 0.96f, 0.94f));
                    m.Box(new Vector3(0.18f, 0.04f, 0.04f), new Vector3(0.14f, 0.08f, 0.12f), new Vector3(0, 30, 0), C(0.86f, 0.18f, 0.16f));
                    m.Box(new Vector3(0.0f, 0.15f, 0), new Vector3(0.22f, 0.006f, 0.008f), new Vector3(0, 18, 12), C(0.85f, 0.7f, 0.4f));
                    radius = 0.2f; height = 0.17f; break;
                case "magazines":
                    m.Box(new Vector3(0, 0.01f, 0), new Vector3(0.26f, 0.02f, 0.34f), new Vector3(0, 0, 0), C(0.92f, 0.30f, 0.55f));
                    m.Box(new Vector3(0.02f, 0.03f, 0.01f), new Vector3(0.26f, 0.02f, 0.34f), new Vector3(0, 28, 0), C(0.25f, 0.65f, 0.90f));
                    m.Box(new Vector3(-0.01f, 0.05f, -0.01f), new Vector3(0.26f, 0.02f, 0.34f), new Vector3(0, -22, 0), C(0.95f, 0.85f, 0.25f));
                    m.Box(new Vector3(0.02f, 0.07f, 0.02f), new Vector3(0.20f, 0.02f, 0.26f), new Vector3(0, 55, 0), C(0.95f, 0.95f, 0.95f));
                    radius = 0.22f; height = 0.09f; break;
                case "shirt":     // shirt / jacket slumped over something
                    m.Blob(new Vector3(0, 0.26f, 0), new Vector3(0.24f, 0.28f, 0.07f), new Vector3(-6f, 0, 0), C(0.22f, 0.50f, 0.82f), 6, 10);
                    m.Blob(new Vector3(-0.24f, 0.30f, 0.02f), new Vector3(0.17f, 0.07f, 0.06f), new Vector3(0, 0, -48f), C(0.20f, 0.45f, 0.76f), 5, 8);
                    m.Blob(new Vector3(0.24f, 0.24f, 0.02f), new Vector3(0.17f, 0.07f, 0.06f), new Vector3(0, 0, 40f), C(0.20f, 0.45f, 0.76f), 5, 8);
                    m.Blob(new Vector3(0, 0.50f, 0.03f), new Vector3(0.09f, 0.045f, 0.06f), Vector3.zero, C(0.95f, 0.95f, 0.95f), 5, 8);
                    radius = 0.30f; height = 0.56f; break;
                case "paper":     // crumpled paper balls
                    m.Blob(new Vector3(0, 0.035f, 0), new Vector3(0.04f, 0.04f, 0.04f), Vector3.zero, C(0.96f, 0.96f, 0.94f), 5, 8);
                    m.Blob(new Vector3(0.07f, 0.03f, 0.03f), new Vector3(0.035f, 0.035f, 0.035f), Vector3.zero, C(0.92f, 0.92f, 0.88f), 5, 8);
                    m.Blob(new Vector3(0.02f, 0.03f, -0.07f), new Vector3(0.04f, 0.035f, 0.04f), Vector3.zero, C(0.96f, 0.94f, 0.86f), 5, 8);
                    m.Blob(new Vector3(-0.07f, 0.03f, 0.02f), new Vector3(0.035f, 0.035f, 0.035f), Vector3.zero, C(0.92f, 0.92f, 0.92f), 5, 8);
                    radius = 0.14f; height = 0.08f; break;
                case "trainers":
                    for (int i = 0; i < 2; i++)
                    {
                        var o = new Vector3(i * 0.16f, 0, i * 0.05f); float yaw = i == 0 ? 0f : 35f;
                        m.Box(o + new Vector3(0, 0.025f, 0), new Vector3(0.10f, 0.05f, 0.27f), new Vector3(0, yaw, 0), C(0.95f, 0.95f, 0.92f));
                        m.Box(o + new Vector3(0, 0.075f, -0.02f), new Vector3(0.095f, 0.06f, 0.20f), new Vector3(0, yaw, 0), C(0.85f, 0.22f, 0.20f));
                        m.Box(o + new Vector3(0, 0.12f, 0.0f), new Vector3(0.08f, 0.05f, 0.09f), new Vector3(0, yaw, 0), C(0.80f, 0.20f, 0.18f));
                    }
                    radius = 0.2f; height = 0.15f; break;
                default:
                    m.Box(new Vector3(0, 0.1f, 0), new Vector3(0.2f, 0.2f, 0.2f), Vector3.zero, C(0.7f, 0.6f, 0.5f));
                    radius = 0.2f; height = 0.2f; break;
            }
            return m.Build("Clutter_" + kind);
        }

        public static ClutterItem Create(Spot spot, Transform parent, int glowLayer)
        {
            if (!_meshes.TryGetValue(spot.Kind, out var mesh)) { mesh = MeshFor(spot.Kind, out _, out _); _meshes[spot.Kind] = mesh; }
            MeshFor(spot.Kind, out float radius, out float height);        // cheap: only used for the two numbers
            var go = new GameObject("Clutter_" + spot.Kind);
            go.transform.SetParent(parent, false);
            go.transform.position = spot.Pos;
            go.transform.rotation = Quaternion.Euler(0f, spot.Yaw, 0f);
            go.transform.localScale = Vector3.one * spot.Scale;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = Mat();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            var item = go.AddComponent<ClutterItem>();
            item.Kind = spot.Kind; item.PickRadius = radius * spot.Scale; item.Height = height * spot.Scale;
            float ang = Mathf.Atan2(spot.Pos.x, spot.Pos.z) * Mathf.Rad2Deg;                 // 0 = north, 90 = east
            item.PrimaryView = (CompassDirection)(((Mathf.RoundToInt(ang / 90f) % 4) + 4) % 4);
            item.AttachGlow(glowLayer);
            return item;
        }
    }
}
