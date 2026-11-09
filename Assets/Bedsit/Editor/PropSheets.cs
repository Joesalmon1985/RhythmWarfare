using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Bedsit.Editor
{
    /// <summary>Renders every prop prefab as it appears in Unity (real materials, real lighting) onto contact sheets under
    /// Evidence/props/ so the imported look - not just the Blender preview - can be inspected (pink/missing materials,
    /// scale, orientation). Menu: Bedsit/Art/Render Prop Sheets. <see cref="Filter"/> limits it to a name prefix.</summary>
    public static class PropSheets
    {
        public static string Filter = "";
        public static int Cell = 360, Columns = 4, Rows = 3;

        [MenuItem("Bedsit/Art/Render Prop Sheets")]
        public static void RenderAll() { Render(Filter); }

        public static string Render(string prefix)
        {
            var guids = AssetDatabase.FindAssets("t:Prefab", new[] { ArtPipeline.PropsRoot });
            var paths = guids.Select(AssetDatabase.GUIDToAssetPath).Where(p => Path.GetFileNameWithoutExtension(p).StartsWith(prefix ?? "")).OrderBy(p => p).ToList();
            Directory.CreateDirectory("Evidence/props");

            var oldAmbientMode = RenderSettings.ambientMode; var oldSky = RenderSettings.ambientSkyColor; var oldEq = RenderSettings.ambientEquatorColor; var oldGr = RenderSettings.ambientGroundColor;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.66f, 0.74f); RenderSettings.ambientEquatorColor = new Color(0.5f, 0.48f, 0.46f); RenderSettings.ambientGroundColor = new Color(0.3f, 0.27f, 0.24f);

            var stage = new GameObject("PropSheetStage");
            var key = new GameObject("key").AddComponent<Light>(); key.transform.SetParent(stage.transform); key.type = LightType.Directional; key.intensity = 0.95f; key.color = new Color(1f, 0.95f, 0.86f); key.shadows = LightShadows.Soft;
            key.transform.rotation = Quaternion.Euler(42f, -35f, 0f);
            var fill = new GameObject("fill").AddComponent<Light>(); fill.transform.SetParent(stage.transform); fill.type = LightType.Directional; fill.intensity = 0.35f; fill.color = new Color(0.8f, 0.88f, 1f);
            fill.transform.rotation = Quaternion.Euler(20f, 140f, 0f);
            var camGo = new GameObject("cam"); camGo.transform.SetParent(stage.transform);
            var cam = camGo.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0.30f, 0.32f, 0.36f); cam.fieldOfView = 30f;
            cam.enabled = false;
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); floor.transform.SetParent(stage.transform);
            floor.GetComponent<Renderer>().sharedMaterial = new Material(Shader.Find("Standard")) { color = new Color(0.42f, 0.42f, 0.44f) };
            floor.GetComponent<Renderer>().sharedMaterial.SetFloat("_Glossiness", 0.1f);
            floor.transform.localScale = Vector3.one * 2f;

            var rt = new RenderTexture(Cell, Cell, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            var tex = new Texture2D(Cell, Cell, TextureFormat.RGB24, false);
            int perSheet = Columns * Rows, sheetIndex = 0, n = 0;
            Texture2D sheet = null;
            var written = new List<string>();
            foreach (var p in paths)
            {
                if (n % perSheet == 0) { if (sheet != null) { Save(sheet, prefix, sheetIndex++, written); } sheet = new Texture2D(Cell * Columns, Cell * Rows, TextureFormat.RGB24, false); FillGrey(sheet); }
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(p);
                var go = (GameObject)Object.Instantiate(prefab);
                go.transform.position = Vector3.zero;
                var rs = go.GetComponentsInChildren<Renderer>();
                if (rs.Length > 0)
                {
                    var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                    floor.transform.position = new Vector3(b.center.x, 0f, b.center.z);
                    float radius = Mathf.Max(b.extents.magnitude, 0.05f);
                    Vector3 dir = new Vector3(-0.55f, 0.45f, -1f).normalized;       // front of the prop faces +Z: view from the front, a little left and above
                    dir = new Vector3(0.55f, 0.45f, 1f).normalized;
                    cam.transform.position = b.center + dir * radius * 3.1f;
                    cam.transform.LookAt(b.center);
                    cam.nearClipPlane = 0.02f; cam.farClipPlane = 100f;
                    cam.Render();
                    RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, Cell, Cell), 0, 0); tex.Apply(); RenderTexture.active = null;
                    int cx = n % perSheet % Columns, cy = Rows - 1 - (n % perSheet) / Columns;
                    sheet.SetPixels(cx * Cell, cy * Cell, Cell, Cell, tex.GetPixels());
                }
                Object.DestroyImmediate(go);
                n++;
            }
            if (sheet != null) Save(sheet, prefix, sheetIndex, written);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release();
            Object.DestroyImmediate(stage);
            RenderSettings.ambientMode = oldAmbientMode; RenderSettings.ambientSkyColor = oldSky; RenderSettings.ambientEquatorColor = oldEq; RenderSettings.ambientGroundColor = oldGr;
            var names = string.Join("\n", paths.Select(Path.GetFileNameWithoutExtension));
            File.WriteAllText($"Evidence/props/sheet_{(string.IsNullOrEmpty(prefix) ? "all" : prefix)}_order.txt", names);
            Debug.Log($"[PropSheets] {paths.Count} props -> {string.Join(", ", written)}");
            return string.Join(";", written);
        }

        static void FillGrey(Texture2D t) { var px = new Color[t.width * t.height]; for (int i = 0; i < px.Length; i++) px[i] = new Color(0.3f, 0.32f, 0.36f); t.SetPixels(px); }

        static void Save(Texture2D sheet, string prefix, int index, List<string> written)
        {
            sheet.Apply();
            var f = $"Evidence/props/sheet_{(string.IsNullOrEmpty(prefix) ? "all" : prefix)}_{index}.png";
            File.WriteAllBytes(f, sheet.EncodeToPNG());
            written.Add(f);
        }
    }
}
