using System;
using System.Collections.Generic;
using System.Linq;
using Bedsit.Rooms;
using Bedsit.Sims2;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Builds a room from a <see cref="RoomDef"/> on top of the BedsitWorld: hides the legacy (Sims 2) furniture / shell / windows,
    /// builds a new shell with the def's openings, places furniture, decor and cleanable tasks from the prop catalog, adds lights,
    /// the exterior views and ground. All content is data; no object in this file is specific to a particular room.
    /// </summary>
    public class RoomBuilder : MonoBehaviour
    {
        public static RoomBuilder Current { get; private set; }

        public RoomDef Def { get; private set; }
        public BedsitWorld World { get; private set; }
        public Transform Root { get; private set; }
        public readonly Dictionary<string, Transform> Tags = new Dictionary<string, Transform>();
        public readonly List<Cleanable> Cleanables = new List<Cleanable>();
        public readonly List<Light> Lights = new List<Light>();
        public readonly List<string> Missing = new List<string>();
        public readonly List<string> Report = new List<string>();
        public int PropCount { get; private set; }
        public int TriangleCount { get; private set; }

        Transform _furniture, _decor, _clutter, _shell, _exterior, _lightsRoot;

        public static bool Enabled => !RoomLibrary.LegacyRequested;

        /// <summary>Build the selected room onto the world. Returns null if the room def is missing or the legacy room was requested.</summary>
        public static RoomBuilder Build(BedsitWorld world, RoomDef def)
        {
            if (world == null || def == null) return null;
            var go = new GameObject("Room_" + def.id);
            go.transform.SetParent(world.transform, false);
            var rb = go.AddComponent<RoomBuilder>();
            rb.Def = def; rb.World = world; rb.Root = go.transform;
            Current = rb;
            rb.BuildAll();
            return rb;
        }

        void OnDestroy() { if (Current == this) Current = null; }

        // ================================================================================================================ build

        void BuildAll()
        {
            _shell = Group("Shell"); _furniture = Group("Furniture"); _decor = Group("Decor"); _clutter = Group("Cleanables");
            _exterior = Group("Exterior"); _lightsRoot = Group("Lights");

            HideLegacy();
            BuildShell();
            foreach (var p in Def.furniture) Place(p, _furniture);
            foreach (var p in Def.decor) Place(p, _decor);
            foreach (var c in Def.cleanables) BuildCleanable(c);
            BuildExteriors();
            BuildLights();
            ApplyWorldHandles();
            ApplyEnvironment();

            foreach (var r in Root.GetComponentsInChildren<Renderer>(true))
            {
                var mf = r.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null)
                    for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) TriangleCount += (int)(mf.sharedMesh.GetIndexCount(s) / 3);
            }
            Report.Add($"room '{Def.id}': {PropCount} props, {Cleanables.Count} cleanables, {Lights.Count} lights, {TriangleCount} triangles, {Missing.Count} missing props");
            if (Missing.Count > 0) Debug.LogWarning("[RoomBuilder] missing props: " + string.Join(", ", Missing.Distinct()));
        }

        Transform Group(string name)
        {
            var g = new GameObject(name).transform;
            g.SetParent(Root, false);
            return g;
        }

        void HideLegacy()
        {
            // entries: "name", "prefix*", or with a position filter "name@x<0" / "name@z>-3" (world position of the object)
            int hidden = 0;
            foreach (Transform t in World.transform)
            {
                if (t == Root) continue;
                foreach (var entry in Def.hideLegacy)
                {
                    string n = entry, filter = null;
                    int at = entry.IndexOf('@');
                    if (at > 0) { n = entry.Substring(0, at); filter = entry.Substring(at + 1); }
                    bool match = n.EndsWith("*") ? t.name.StartsWith(n.Substring(0, n.Length - 1)) : t.name == n;
                    if (!match) continue;
                    if (filter != null && !PassesFilter(t.position, filter)) continue;
                    t.gameObject.SetActive(false); hidden++;
                    break;
                }
            }
            Report.Add($"legacy objects hidden: {hidden}");
        }

        static bool PassesFilter(Vector3 p, string f)
        {
            // axis letter, comparison, number: x<0, z>-3
            if (f.Length < 3) return true;
            float v = f[0] == 'x' ? p.x : f[0] == 'y' ? p.y : p.z;
            bool less = f[1] == '<';
            if (!float.TryParse(f.Substring(2), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var lim)) return true;
            return less ? v < lim : v > lim;
        }

        // ================================================================================================================ shell

        static readonly Dictionary<string, Material> MatCache = new Dictionary<string, Material>();
        static Material Mat(string name)
        {
            if (MatCache.TryGetValue(name, out var m) && m != null) return m;
            m = Resources.Load<Material>("Art/Materials/" + name);
            if (m == null) { Debug.LogWarning("[RoomBuilder] missing material " + name); m = new Material(Shader.Find("Standard")) { color = Color.magenta }; }
            MatCache[name] = m;
            return m;
        }

        GameObject Slab(string name, Vector3 min, Vector3 max, Material mat, float uv, bool shadows = true)
        {
            var go = new GameObject(name);
            go.transform.SetParent(_shell, false);
            go.AddComponent<MeshFilter>().sharedMesh = BedsitWorldBuilder.BoxMesh(min, max, uv);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = mat;
            if (!shadows) mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return go;
        }

        void BuildShell()
        {
            float hw = Def.halfWidth, hd = Def.halfDepth, h = Def.height, t = 0.12f;
            var wall = Mat(Def.shell.wallMaterial); var floor = Mat(Def.shell.floorMaterial); var ceil = Mat(Def.shell.ceilingMaterial);
            Slab("Floor", new Vector3(-hw - t, -0.12f, -hd - t), new Vector3(hw + t, 0f, hd + t), floor, 0.55f);
            Slab("Ceiling", new Vector3(-hw - t, h, -hd - t), new Vector3(hw + t, h + 0.12f, hd + t), ceil, 0.5f);

            // four walls; each cut by the openings that belong to it
            BuildWall("S", new Vector3(-hw - t, 0, -hd - t), new Vector3(hw + t, h, -hd), wall);
            BuildWall("N", new Vector3(-hw - t, 0, hd), new Vector3(hw + t, h, hd + t), wall);
            BuildWall("E", new Vector3(hw, 0, -hd), new Vector3(hw + t, h, hd), wall);
            BuildWall("W", new Vector3(-hw - t, 0, -hd), new Vector3(-hw, h, hd), wall);

            // skirting boards (not across doorways) and a picture-rail style cornice
            var skirt = Mat(Def.shell.skirtingMaterial); float sh = Def.shell.skirtingHeight, st = Def.shell.skirtingThickness;
            foreach (var side in new[] { "S", "N", "E", "W" })
            {
                bool alongX = side == "S" || side == "N";
                float a0 = alongX ? -hw : -hd, a1 = alongX ? hw : hd;
                var doors = Def.openings.Where(o => o.wall == side && o.kind == "door").OrderBy(o => o.along).ToList();
                float cur = a0;
                var segs = new List<(float, float)>();
                foreach (var d in doors) { segs.Add((cur, d.along - d.width * 0.5f - 0.05f)); cur = d.along + d.width * 0.5f + 0.05f; }
                segs.Add((cur, a1));
                foreach (var (s0, s1) in segs)
                {
                    if (s1 - s0 < 0.05f) continue;
                    Vector3 mn, mx;
                    switch (side)
                    {
                        case "S": mn = new Vector3(s0, 0, -hd); mx = new Vector3(s1, sh, -hd + st); break;
                        case "N": mn = new Vector3(s0, 0, hd - st); mx = new Vector3(s1, sh, hd); break;
                        case "E": mn = new Vector3(hw - st, 0, s0); mx = new Vector3(hw, sh, s1); break;
                        default: mn = new Vector3(-hw, 0, s0); mx = new Vector3(-hw + st, sh, s1); break;
                    }
                    Slab("Skirting_" + side, mn, mx, skirt, 1f);
                }
                if (Def.shell.cornice)
                {
                    Vector3 mn, mx; float ch = 0.07f, ct = 0.05f;
                    switch (side)
                    {
                        case "S": mn = new Vector3(-hw, h - ch, -hd); mx = new Vector3(hw, h, -hd + ct); break;
                        case "N": mn = new Vector3(-hw, h - ch, hd - ct); mx = new Vector3(hw, h, hd); break;
                        case "E": mn = new Vector3(hw - ct, h - ch, -hd); mx = new Vector3(hw, h, hd); break;
                        default: mn = new Vector3(-hw, h - ch, -hd); mx = new Vector3(-hw + ct, h, hd); break;
                    }
                    Slab("Cornice_" + side, mn, mx, skirt, 1f);
                }
            }
            if (!string.IsNullOrEmpty(Def.shell.rugProp))
            {
                var rug = PropCatalog.Instantiate(Def.shell.rugProp, _decor);
                if (rug != null) { rug.transform.position = Def.shell.rugPos + Vector3.up * 0.004f; rug.transform.rotation = Quaternion.Euler(0, Def.shell.rugYaw, 0); PropCount++; }
                else Missing.Add(Def.shell.rugProp);
            }
        }

        /// <summary>A wall slab cut by all the openings on that side (boxes between and around the openings).</summary>
        void BuildWall(string side, Vector3 min, Vector3 max, Material mat)
        {
            bool alongX = side == "S" || side == "N";
            float a0 = alongX ? min.x : min.z, a1 = alongX ? max.x : max.z;
            var ops = Def.openings.Where(o => o.wall == side).OrderBy(o => o.along).ToList();
            Vector3 Mn(float a, float y) => alongX ? new Vector3(a, y, min.z) : new Vector3(min.x, y, a);
            Vector3 Mx(float a, float y) => alongX ? new Vector3(a, y, max.z) : new Vector3(max.x, y, a);
            float cur = a0;
            int i = 0;
            foreach (var o in ops)
            {
                float o0 = o.along - o.width * 0.5f, o1 = o.along + o.width * 0.5f;
                if (o0 > cur) Slab($"Wall{side}_{i++}", Mn(cur, min.y), Mx(o0, max.y), mat, 0.7f);
                if (o.sill > min.y + 0.001f) Slab($"Wall{side}_sill{i++}", Mn(o0, min.y), Mx(o1, o.sill), mat, 0.7f);
                if (o.sill + o.height < max.y) Slab($"Wall{side}_head{i++}", Mn(o0, o.sill + o.height), Mx(o1, max.y), mat, 0.7f);
                cur = o1;
            }
            if (a1 > cur) Slab($"Wall{side}_{i++}", Mn(cur, min.y), Mx(a1, max.y), mat, 0.7f);
        }

        // ================================================================================================================ props

        public GameObject Place(PlacementDef p, Transform group)
        {
            if (p == null || string.IsNullOrEmpty(p.prop)) return null;
            var go = PropCatalog.Instantiate(p.prop, group);
            if (go == null) { Missing.Add(p.prop); return null; }
            PropCount++;
            if (!string.IsNullOrEmpty(p.parent) && Tags.TryGetValue(p.parent, out var par))
            {
                go.transform.SetParent(par, false);
                go.transform.localPosition = p.pos;
                go.transform.localRotation = Quaternion.Euler(p.euler);
            }
            else
            {
                go.transform.position = p.pos;
                go.transform.rotation = Quaternion.Euler(p.euler);
            }
            go.transform.localScale = Vector3.one * (Mathf.Approximately(p.scale, 0f) ? 1f : p.scale);
            if (!p.castShadows) foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            if (!string.IsNullOrEmpty(p.tag)) { go.name = p.tag; Tags[p.tag] = go.transform; }
            return go;
        }

        void BuildCleanable(CleanableDef c)
        {
            var root = new GameObject("Cleanable_" + c.id);
            root.transform.SetParent(_clutter, false);
            var cl = root.AddComponent<Cleanable>();
            cl.Def = c;
            cl.Height = c.height; cl.PickRadius = c.radius;
            cl.PrimaryView = ParseView(c.view);

            void Part(PlacementDef pd, bool messy, int index)
            {
                var go = Place(pd, root.transform);
                if (go == null) return;
                go.name = (messy ? "messy_" : "tidy_") + index + "_" + pd.prop;
                go.transform.SetParent(root.transform, true);
                (messy ? cl.MessyParts : cl.TidyParts).Add(go.transform);
                if (!messy) cl.RememberScale(go.transform, go.transform.localScale.x);
            }
            Part(c.messy, true, 0);
            for (int i = 0; i < c.messyExtra.Count; i++) Part(c.messyExtra[i], true, i + 1);
            if (c.tidy != null && !string.IsNullOrEmpty(c.tidy.prop) && (c.tidy.prop != c.messy.prop || c.action != "slide"))
            {
                Part(c.tidy, false, 0);
                for (int i = 0; i < c.tidyExtra.Count; i++) Part(c.tidyExtra[i], false, i + 1);
            }
            else if (c.tidy != null)
            {
                // slide: the same object moves to the tidy pose (world pos, or relative to its parent tag)
                Vector3 pos = c.tidy.pos; Quaternion rot = Quaternion.Euler(c.tidy.euler);
                if (!string.IsNullOrEmpty(c.tidy.parent) && Tags.TryGetValue(c.tidy.parent, out var par)) { pos = par.TransformPoint(c.tidy.pos); rot = par.rotation * rot; }
                cl.SlideTargetPos = pos; cl.SlideTargetRot = rot;
            }
            if (!string.IsNullOrEmpty(c.target) && Tags.TryGetValue(c.target, out var bin)) cl.BinTarget = bin;
            if (cl.MessyParts.Count == 0) { Missing.Add("cleanable:" + c.id); Destroy(root); return; }
            root.transform.position = cl.MessyParts[0].position;
            foreach (var t in cl.MessyParts.Concat(cl.TidyParts)) t.SetParent(root.transform, true);
            cl.Init();
            cl.AttachGlow(BedsitLayers.MirrorGlass);
            Cleanables.Add(cl);
        }

        public static CompassDirection ParseView(string v)
        {
            switch ((v ?? "N").ToUpperInvariant()) { case "E": return CompassDirection.East; case "S": return CompassDirection.South; case "W": return CompassDirection.West; default: return CompassDirection.North; }
        }

        // ================================================================================================================ exterior

        void BuildExteriors()
        {
            foreach (var e in Def.exteriors)
            {
                var go = PropCatalog.Instantiate(e.prop, _exterior);
                if (go == null) { Missing.Add(e.prop); continue; }
                go.name = string.IsNullOrEmpty(e.id) ? e.prop : e.id;
                go.transform.position = e.pos; go.transform.rotation = Quaternion.Euler(e.euler);
                go.transform.localScale = Vector3.one * (Mathf.Approximately(e.scale, 0f) ? 1f : e.scale);
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                PropCount++;
            }
            // frames/windows for openings
            foreach (var o in Def.openings)
            {
                if (string.IsNullOrEmpty(o.frameProp)) continue;
                float hw = Def.halfWidth, hd = Def.halfDepth, t = 0.12f;
                Vector3 pos, euler;
                switch (o.wall)
                {
                    case "N": pos = new Vector3(o.along, o.sill, hd + t * 0.5f); euler = new Vector3(0, 180f, 0); break;   // front faces south (into the room)
                    case "S": pos = new Vector3(o.along, o.sill, -hd - t * 0.5f); euler = Vector3.zero; break;           // front faces north
                    case "E": pos = new Vector3(hw + t * 0.5f, o.sill, o.along); euler = new Vector3(0, -90f, 0); break;  // front faces west
                    default: pos = new Vector3(-hw - t * 0.5f, o.sill, o.along); euler = new Vector3(0, 90f, 0); break;   // front faces east
                }
                var go = PropCatalog.Instantiate(o.frameProp, _furniture);
                if (go == null) { Missing.Add(o.frameProp); continue; }
                go.name = "Frame_" + o.id;
                go.transform.position = pos; go.transform.rotation = Quaternion.Euler(euler);
                PropCount++;
            }
            foreach (var g in Def.ground)
            {
                var go = new GameObject("Ground_" + g.material);
                go.transform.SetParent(_exterior, false);
                go.AddComponent<MeshFilter>().sharedMesh = BedsitWorldBuilder.BoxMesh(g.min, g.max, g.uvPerMetre);
                go.AddComponent<MeshRenderer>().sharedMaterial = Mat(g.material);
            }
        }

        // ================================================================================================================ lights

        void BuildLights()
        {
            foreach (var l in Def.lights)
            {
                var go = new GameObject(l.name);
                go.transform.SetParent(_lightsRoot, false);
                var li = go.AddComponent<Light>();
                li.type = l.type == "spot" ? LightType.Spot : l.type == "directional" ? LightType.Directional : LightType.Point;
                go.transform.position = l.pos; go.transform.rotation = Quaternion.Euler(l.euler);
                li.color = l.color; li.intensity = l.intensity; li.range = l.range; li.spotAngle = l.spotAngle;
                li.shadows = l.shadows == "soft" ? LightShadows.Soft : l.shadows == "hard" ? LightShadows.Hard : LightShadows.None;
                if (l.pulseHz > 0f) { var p = go.AddComponent<LightPulse>(); p.Hz = l.pulseHz; p.Depth = l.pulseDepth; p.Light = li; p.Base = l.intensity; }
                Lights.Add(li);
                if (l.role == "sun") World.Sun = li;
                if (l.role == "room" && World.RoomLight == null || l.name == "RoomPendant") World.RoomLight = li;
            }
            // the legacy sun/room lights are replaced by the room's own set
            if (World.Sun != null && !Lights.Contains(World.Sun)) World.Sun.gameObject.SetActive(false);
        }

        void ApplyWorldHandles()
        {
            World.BedPillowEye = Def.bedPillowEye;
            World.WakeYaw = Def.wakeYaw;
            foreach (var o in Def.openings)
            {
                if (o.view == "club" || (o.wall == "W" && o.kind == "window")) { World.WestNpcSpot = new Vector3(-Def.halfWidth - 0.12f - 1.55f, 0f, o.along); World.WestNpcLookAt = new Vector3(0f, 0f, o.along); }
                if (o.wall == "E" && o.kind == "window") { World.EastNpcSpot = new Vector3(Def.halfWidth + 0.12f + 1.55f, 0f, o.along); World.EastNpcLookAt = new Vector3(0f, 0f, o.along); }
            }
        }

        void ApplyEnvironment()
        {
            var e = Def.environment;
            if (e == null) return;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = e.ambientSky; RenderSettings.ambientEquatorColor = e.ambientEquator; RenderSettings.ambientGroundColor = e.ambientGround;
            if (e.fog) { RenderSettings.fog = true; RenderSettings.fogColor = e.fogColor; RenderSettings.fogMode = FogMode.Exponential; RenderSettings.fogDensity = e.fogDensity; }
            if (!string.IsNullOrEmpty(e.skybox))
            {
                var m = Resources.Load<Material>("Art/Materials/" + e.skybox);
                if (m != null) { RenderSettings.skybox = m; Skybox = m; }
            }
            var cam = Camera.main;
            if (cam != null)
            {
                if (Skybox != null) cam.clearFlags = CameraClearFlags.Skybox; else cam.backgroundColor = e.sky;
            }
        }

        public static Material Skybox { get; private set; }

        // ================================================================================================================ queries

        public Cleanable Find(string id) { return Cleanables.FirstOrDefault(c => c.Id == id); }
        public int TidiedCount => Cleanables.Count(c => c.Tidied);
    }

    /// <summary>Gentle pulse for club/venue lights, locked to a rate (e.g. 174 bpm / 60 x 0.5).</summary>
    public class LightPulse : MonoBehaviour
    {
        public Light Light; public float Hz = 1f, Depth = 0.4f, Base = 1f;
        float _ph;
        void Update()
        {
            if (Light == null) return;
            _ph += Time.deltaTime * Hz * Mathf.PI * 2f;
            Light.intensity = Base * (1f - Depth + Depth * (0.5f + 0.5f * Mathf.Sin(_ph)));
        }
    }
}
