using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Bedsit.Editor
{
    /// <summary>
    /// Blender FBX -> Unity prop prefabs.
    ///  * every FBX under Assets/Bedsit/Art/Models is imported with fixed settings (metres, no cameras/lights, normals/tangents);
    ///  * Blender material names are ROLE names (cotton_red, wood_dark, screen_on ...): each is mapped to a shared Standard-shader
    ///    material in Assets/Bedsit/Resources/Art/Materials (rules below), so a prop never keeps a per-file material;
    ///  * a prefab per model is written to Assets/Bedsit/Resources/Art/Props/&lt;name&gt;.prefab (what PropCatalog loads at run time).
    /// Run via the menu Bedsit/Art/Build Props (also invoked from the command line: -executeMethod / editor.invoke_menu).
    /// </summary>
    public static class ArtPipeline
    {
        public const string ModelsRoot = "Assets/Bedsit/Art/Models";
        public const string TexturesRoot = "Assets/Bedsit/Art/Textures";
        public const string MaterialsRoot = "Assets/Bedsit/Resources/Art/Materials";
        public const string PropsRoot = "Assets/Bedsit/Resources/Art/Props";

        /// <summary>Blender front (-Y) already arrives facing +Z in Unity (FBX Y-up/-Z-forward export; verified with the smoke mug:
        /// its +X handle lands at Unity -X, which is the viewer's right when looking at the front from +Z). No extra spin.</summary>
        public const float ModelYaw = 0f;

        // role (exact or prefix) -> surface description
        sealed class Rule
        {
            public string Albedo;            // texture short name (Textures/<name>_albedo.jpg) or null: keep imported colour
            public string Normal;            // texture short name or null
            public float Tile = 1f;          // texture repeats per metre-of-UV (props use 1 UV unit = 1 m)
            public float NormalScale = 1f;
            public float Smooth = 0.35f, Metal = 0f;
            public bool TintAlbedo;          // multiply the albedo texture by the imported colour
            public Color? Emission;          // HDR emission colour
            public float Alpha = 1f;
            public float ColorGain = 1f;
        }

        static readonly List<(string prefix, Rule rule)> Rules = new List<(string, Rule)>
        {
            ("wall_plaster", new Rule { Albedo = "wall_plaster", Normal = "wall_plaster", Tile = 1f, Smooth = 0.05f, NormalScale = 0.8f }),
            ("floor_boards", new Rule { Albedo = "floor_boards", Normal = "floor_boards", Tile = 1f, Smooth = 0.32f }),
            ("floor_parquet", new Rule { Albedo = "floor_parquet", Normal = "floor_parquet", Tile = 1f, Smooth = 0.35f }),
            ("ceiling", new Rule { Normal = "wall_plaster", Tile = 1f, NormalScale = 0.4f, Smooth = 0.03f }),
            ("paint_white", new Rule { Normal = "wall_plaster", Tile = 2f, NormalScale = 0.25f, Smooth = 0.55f }),
            ("plaster", new Rule { Albedo = "wall_plaster", Normal = "wall_plaster", Tile = 0.8f, Smooth = 0.08f }),
            ("wood_dark", new Rule { Albedo = "wood_dark", Normal = "wood_dark", Tile = 1.4f, Smooth = 0.45f }),
            ("wood_light", new Rule { Albedo = "floor_laminate", Normal = "floor_laminate", Tile = 1.2f, Smooth = 0.4f }),
            ("wood_painted", new Rule { Normal = "wall_plaster", Tile = 2f, NormalScale = 0.3f, Smooth = 0.55f }),
            ("denim", new Rule { Albedo = "denim", Normal = "denim", Tile = 6f, TintAlbedo = true, ColorGain = 2.2f, Smooth = 0.08f, NormalScale = 0.8f }),
            ("fabric_pattern", new Rule { Albedo = "fabric_pattern", Normal = "fabric_pattern", Tile = 3f, Smooth = 0.08f }),
            ("cotton", new Rule { Normal = "cotton", Tile = 7f, NormalScale = 0.7f, Smooth = 0.08f }),
            ("carpet", new Rule { Albedo = "carpet_dirty", Normal = "carpet_dirty", Tile = 2.5f, TintAlbedo = true, ColorGain = 1.8f, Smooth = 0.05f }),
            ("rug", new Rule { Normal = "carpet_dirty", Tile = 3f, Smooth = 0.05f }),
            ("leather", new Rule { Normal = "wall_plaster", Tile = 6f, NormalScale = 0.5f, Smooth = 0.5f }),
            ("rubber", new Rule { Smooth = 0.2f }),
            ("plastic", new Rule { Smooth = 0.55f }),
            ("metal_rust", new Rule { Albedo = "metal_rust", Normal = "metal_rust", Tile = 1.5f, Metal = 0.7f, Smooth = 0.3f }),
            ("metal", new Rule { Normal = "metal_worn", Tile = 2f, NormalScale = 0.5f, Metal = 0.9f, Smooth = 0.6f }),
            ("foil", new Rule { Metal = 0.85f, Smooth = 0.7f }),
            ("ceramic", new Rule { Smooth = 0.82f }),
            ("glass", new Rule { Smooth = 0.95f, Alpha = 0.1f }),
            ("paper", new Rule { Smooth = 0.1f }),
            ("cardboard", new Rule { Smooth = 0.04f, Normal = "cotton", Tile = 4f, NormalScale = 0.4f }),
            ("liquid", new Rule { Smooth = 0.92f }),
            ("food", new Rule { Smooth = 0.45f }),
            ("screen_off", new Rule { Smooth = 0.9f, Metal = 0.1f }),
            ("screen_on", new Rule { Smooth = 0.9f, Emission = new Color(0.9f, 1.5f, 2.2f) }),
            ("led_green", new Rule { Emission = new Color(0.2f, 3f, 0.4f), Smooth = 0.4f }),
            ("led_red", new Rule { Emission = new Color(3f, 0.2f, 0.1f), Smooth = 0.4f }),
            ("neon_pink", new Rule { Emission = new Color(4f, 0.3f, 2.2f) }),
            ("neon_cyan", new Rule { Emission = new Color(0.2f, 2.6f, 4f) }),
            ("neon", new Rule { Emission = new Color(3.5f, 2f, 1f) }),
            ("window_lit", new Rule { Emission = new Color(1.6f, 1.25f, 0.7f) }),
            ("bulb_warm", new Rule { Emission = new Color(3f, 2f, 1f), Smooth = 0.9f }),
            ("lamp_shade", new Rule { Emission = new Color(1.2f, 0.85f, 0.45f), Smooth = 0.1f }),
            ("light_beam_emitter", new Rule { Emission = new Color(3f, 3f, 3f) }),
            ("brick", new Rule { Albedo = "brick_red", Normal = "brick_red", Tile = 0.5f, Smooth = 0.1f }),
            ("asphalt", new Rule { Albedo = "asphalt", Normal = "asphalt", Tile = 0.3f, Smooth = 0.15f }),
            ("paving", new Rule { Albedo = "paving", Normal = "paving", Tile = 0.5f, Smooth = 0.2f }),
            ("concrete", new Rule { Albedo = "concrete", Normal = "concrete", Tile = 0.3f, Smooth = 0.1f }),
            ("mirror_glass", new Rule { Smooth = 1f, Metal = 0.95f }),
            ("poster", new Rule { Smooth = 0.3f }),
            ("flyer", new Rule { Smooth = 0.3f }),
            ("print", new Rule { Smooth = 0.3f }),
            ("skin", new Rule { Smooth = 0.5f }),
        };

        // thin soft goods are modelled as open surfaces: render them double-sided (Bedsit/Cloth)
        static readonly string[] TwoSidedPrefixes = { "cotton", "denim", "fabric", "terry", "knit", "nylon", "paper", "flyer", "foil", "cardboard", "tissue", "poster", "stitch", "sticker", "scuff" };
        static bool IsTwoSided(string role) { foreach (var p in TwoSidedPrefixes) if (role.StartsWith(p, StringComparison.OrdinalIgnoreCase)) return true; return false; }

        static Rule RuleFor(string role)
        {
            // longest matching prefix wins
            Rule best = null; int bl = -1;
            foreach (var (p, r) in Rules) if (role.StartsWith(p, StringComparison.OrdinalIgnoreCase) && p.Length > bl) { best = r; bl = p.Length; }
            return best ?? new Rule();
        }

        [MenuItem("Bedsit/Art/Build Props")]
        public static void BuildProps()
        {
            ImportTextures();
            Directory.CreateDirectory(MaterialsRoot);
            Directory.CreateDirectory(PropsRoot);
            EnsureSceneMaterials();
            var guids = AssetDatabase.FindAssets("t:Model", new[] { ModelsRoot });
            int built = 0, skipped = 0;
            var report = new List<string>();
            foreach (var g in guids)
            {
                var path = AssetDatabase.GUIDToAssetPath(g);
                if (path.Contains("/_smoke/")) { skipped++; continue; }
                try { if (BuildOne(path, report)) built++; else skipped++; }
                catch (Exception e) { Debug.LogError("[ArtPipeline] " + path + ": " + e); }
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            File.WriteAllText("Docs/art/prop_build_report.txt", string.Join("\n", report));
            Debug.Log($"[ArtPipeline] props built: {built}, skipped: {skipped}, materials: {Directory.GetFiles(MaterialsRoot, "*.mat").Length}");
        }

        /// <summary>Materials the shell/ground/sky need that no FBX carries.</summary>
        static void EnsureSceneMaterials()
        {
            MaterialFor("wall_plaster", new Color(0.93f, 0.9f, 0.84f));
            MaterialFor("floor_boards", Color.white);
            MaterialFor("floor_parquet", Color.white);
            MaterialFor("ceiling_white", new Color(0.93f, 0.92f, 0.9f));
            MaterialFor("paint_white_gloss", new Color(0.9f, 0.89f, 0.85f));
            MaterialFor("asphalt", Color.white);
            MaterialFor("paving", Color.white);
            MaterialFor("concrete", Color.white);
            MaterialFor("brick_red", Color.white);
        }

        static void ImportTextures()
        {
            if (!Directory.Exists(TexturesRoot)) return;
            foreach (var f in Directory.GetFiles(TexturesRoot, "*.*"))
            {
                if (f.EndsWith(".meta")) continue;
                var p = f.Replace('\\', '/');
                var ti = AssetImporter.GetAtPath(p) as TextureImporter;
                if (ti == null) continue;
                bool normal = Path.GetFileNameWithoutExtension(p).EndsWith("_normal");
                if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; }
                ti.sRGBTexture = !normal;
                ti.mipmapEnabled = true;
                ti.anisoLevel = 4;
                ti.textureCompression = TextureImporterCompression.Compressed;
                ti.maxTextureSize = 1024;
                ti.SaveAndReimport();
            }
        }

        static bool BuildOne(string modelPath, List<string> report)
        {
            var imp = AssetImporter.GetAtPath(modelPath) as ModelImporter;
            if (imp != null)
            {
                bool dirty = false;
                if (imp.globalScale != 1f) { imp.globalScale = 1f; dirty = true; }
                if (!imp.useFileScale) { imp.useFileScale = true; dirty = true; }
                if (imp.importCameras || imp.importLights) { imp.importCameras = false; imp.importLights = false; dirty = true; }
                if (imp.importBlendShapes) { imp.importBlendShapes = false; dirty = true; }
                if (imp.animationType != ModelImporterAnimationType.None) { imp.animationType = ModelImporterAnimationType.None; dirty = true; }
                if (imp.meshCompression != ModelImporterMeshCompression.Off) { imp.meshCompression = ModelImporterMeshCompression.Off; dirty = true; }
                if (imp.importTangents != ModelImporterTangents.CalculateMikk) { imp.importTangents = ModelImporterTangents.CalculateMikk; dirty = true; }
                if (imp.importNormals != ModelImporterNormals.Import) { imp.importNormals = ModelImporterNormals.Import; dirty = true; }
                if (imp.isReadable) { imp.isReadable = false; dirty = true; }
                if (dirty) imp.SaveAndReimport();
            }
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
            if (model == null) return false;
            string name = Path.GetFileNameWithoutExtension(modelPath);

            var root = new GameObject(name);
            var inst = (GameObject)UnityEngine.Object.Instantiate(model, root.transform, false);
            inst.name = "Model";
            inst.transform.localRotation = Quaternion.Euler(0f, ModelYaw, 0f);
            int tris = 0;
            foreach (var r in inst.GetComponentsInChildren<Renderer>(true))
            {
                var src = r.sharedMaterials;
                var dst = new Material[src.Length];
                for (int i = 0; i < src.Length; i++) dst[i] = MaterialFor(src[i]);
                r.sharedMaterials = dst;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                r.receiveShadows = true;
                var mf = r.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null) tris += mf.sharedMesh.triangles.Length / 3;
                string rn = r.name.ToLowerInvariant();
                if (rn.StartsWith("glass") || rn == "glass") r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            var b = Bounds(root);
            var path = PropsRoot + "/" + name + ".prefab";
            PrefabUtility.SaveAsPrefabAsset(root, path);
            UnityEngine.Object.DestroyImmediate(root);
            report.Add($"{name}\t{tris}\t{b.size.x:0.000}x{b.size.y:0.000}x{b.size.z:0.000}\tcentre {b.center.x:0.00},{b.center.y:0.00},{b.center.z:0.00}");
            return true;
        }

        static Bounds Bounds(GameObject go)
        {
            var rs = go.GetComponentsInChildren<Renderer>(true);
            if (rs.Length == 0) return new Bounds(go.transform.position, Vector3.zero);
            var b = rs[0].bounds;
            foreach (var r in rs) b.Encapsulate(r.bounds);
            return b;
        }

        // ---------------------------------------------------------------------------------------------- materials

        public static Material MaterialFor(Material imported)
        {
            string role = imported != null ? imported.name : "default";
            role = role.Replace(" (Instance)", "");
            int dot = role.IndexOf('.');
            if (dot > 0 && dot < role.Length - 1 && char.IsDigit(role[dot + 1])) role = role.Substring(0, dot);     // Blender "cotton_red.001"
            Color c = imported != null && imported.HasProperty("_Color") ? imported.color : new Color(0.6f, 0.6f, 0.6f);
            return MaterialFor(role, c);
        }

        public static Material MaterialFor(string role, Color imported)
        {
            string path = MaterialsRoot + "/" + role + ".mat";
            var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (existing != null) return existing;
            Directory.CreateDirectory(MaterialsRoot);

            var rule = RuleFor(role);
            Color col = imported;
            col.a = 1f;
            var clothShader = IsTwoSided(role) && rule.Alpha >= 1f ? Shader.Find("Bedsit/Cloth") : null;
            var m = new Material(clothShader != null ? clothShader : Shader.Find("Standard")) { name = role };
            if (rule.TintAlbedo) { col.r = Mathf.Clamp01(col.r * rule.ColorGain); col.g = Mathf.Clamp01(col.g * rule.ColorGain); col.b = Mathf.Clamp01(col.b * rule.ColorGain); }
            m.SetColor("_Color", rule.Albedo != null && !rule.TintAlbedo ? Color.white : col);
            if (rule.Albedo != null)
            {
                var t = Tex(rule.Albedo + "_albedo");
                if (t != null) { m.SetTexture("_MainTex", t); m.SetTextureScale("_MainTex", new Vector2(rule.Tile, rule.Tile)); }
            }
            if (rule.Normal != null)
            {
                var n = Tex(rule.Normal + "_normal");
                if (n != null)
                {
                    m.SetTexture("_BumpMap", n); m.SetTextureScale("_BumpMap", new Vector2(rule.Tile, rule.Tile));
                    m.SetFloat("_BumpScale", rule.NormalScale); m.EnableKeyword("_NORMALMAP");
                }
            }
            m.SetFloat("_Glossiness", rule.Smooth);
            m.SetFloat("_Metallic", rule.Metal);
            if (rule.Emission.HasValue)
            {
                var e = rule.Emission.Value;
                // emission takes the role colour (neon_pink etc. already carry theirs in the rule; screen/led use the rule)
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", e);
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                if (role.StartsWith("screen_on") || role.StartsWith("led_") || role.StartsWith("neon") || role.StartsWith("window_lit"))
                    m.SetColor("_Color", Color.Lerp(Color.black, Color.white, 0.1f) * 1f + new Color(col.r, col.g, col.b) * 0.1f);
            }
            if (rule.Alpha < 1f)
            {
                col.a = rule.Alpha;
                m.SetColor("_Color", col);
                m.SetFloat("_Mode", 3f);
                m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.One);
                m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                m.SetInt("_ZWrite", 0);
                m.DisableKeyword("_ALPHATEST_ON"); m.DisableKeyword("_ALPHABLEND_ON"); m.EnableKeyword("_ALPHAPREMULTIPLY_ON");
                m.renderQueue = 3000;
            }
            AssetDatabase.CreateAsset(m, path);
            return m;
        }

        static Texture2D Tex(string name)
        {
            var p = TexturesRoot + "/" + name + ".jpg";
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
            if (t == null) t = AssetDatabase.LoadAssetAtPath<Texture2D>(TexturesRoot + "/" + name + ".png");
            return t;
        }

        [MenuItem("Bedsit/Art/Reset Materials")]
        public static void ResetMaterials()
        {
            if (!Directory.Exists(MaterialsRoot)) return;
            foreach (var f in Directory.GetFiles(MaterialsRoot, "*.mat")) AssetDatabase.DeleteAsset(f.Replace('\\', '/'));
            AssetDatabase.Refresh();
        }
    }
}
