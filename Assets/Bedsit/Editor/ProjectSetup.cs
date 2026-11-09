using System.IO;
using Bedsit.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Bedsit.EditorTools
{
    /// <summary>One-click, repeatable project setup: layers and the scenes under Assets/Scenes.</summary>
    public static class ProjectSetup
    {
        public const string AnimationProofScene = "Assets/Scenes/AnimationProof.unity";
        public const string BedsitScene = "Assets/Scenes/Bedsit.unity";

        [MenuItem("Bedsit/Setup/Configure Layers")]
        public static void ConfigureLayers()
        {
            var tagManager = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var layers = tagManager.FindProperty("layers");
            SetLayer(layers, BedsitLayers.PlayerMirrorOnly, "PlayerMirrorOnly");
            tagManager.ApplyModifiedProperties();
            AssetDatabase.SaveAssets();
        }

        static void SetLayer(SerializedProperty layers, int index, string name)
        {
            var p = layers.GetArrayElementAtIndex(index);
            if (p.stringValue != name) p.stringValue = name;
        }

        [MenuItem("Bedsit/Setup/Create Animation Proof Scene")]
        public static void CreateAnimationProofScene()
        {
            Directory.CreateDirectory("Assets/Scenes");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            new GameObject("AnimationProofRunner").AddComponent<AnimationProofRunner>();
            EditorSceneManager.SaveScene(scene, AnimationProofScene);
            AddToBuild(AnimationProofScene);
        }

        [MenuItem("Bedsit/Setup/Create Bedsit Scene")]
        public static void CreateBedsitScene()
        {
            Directory.CreateDirectory("Assets/Scenes");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            new GameObject("BedsitGame").AddComponent<BedsitGame>();
            EditorSceneManager.SaveScene(scene, BedsitScene);
            AddToBuild(BedsitScene);
        }

        static void AddToBuild(string path)
        {
            var list = new System.Collections.Generic.List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            if (!list.Exists(s => s.path == path)) list.Add(new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = list.ToArray();
        }

        [MenuItem("Bedsit/Run Animation Proof")]
        public static void RunAnimationProof()
        {
            EditorSceneManager.OpenScene(AnimationProofScene);
            EditorApplication.EnterPlaymode();
        }
    }
}
