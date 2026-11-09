using System.IO;
using Bedsit.Game;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;

namespace Bedsit.EditorTools
{
    /// <summary>Repeatable player builds. The project ships NO Sims 2 content: the player reads the user's own install
    /// through config.json at run time (see README).</summary>
    public static class BuildScripts
    {
        const string WindowsDir = "Builds/Windows";
        const string AndroidDir = "Builds/Android";

        [MenuItem("Bedsit/Build/Windows Player")]
        public static void BuildWindows()
        {
            ApplyCommonSettings();
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.StandaloneWindows64, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.StandaloneWindows64, new[] { GraphicsDeviceType.Direct3D11 });
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.resizableWindow = true;

            Directory.CreateDirectory(WindowsDir);
            var exe = Path.Combine(WindowsDir, "UnityBedsitPOC.exe");
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ProjectSetup.BedsitScene },
                locationPathName = exe,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            });
            Debug.Log($"[Build] Windows: {report.summary.result}, {report.summary.totalSize / (1024 * 1024)} MB, errors {report.summary.totalErrors}, warnings {report.summary.totalWarnings}");
            if (report.summary.result == BuildResult.Succeeded) PostProcess(WindowsDir);
            File.WriteAllText(Path.Combine("Builds", "windows_build_result.txt"), report.summary.result + " " + report.summary.totalSize);
        }

        static void ApplyCommonSettings()
        {
            PlayerSettings.companyName = "Joe Salmon";
            PlayerSettings.productName = "UnityBedsitPOC";
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Standalone, "com.joesalmon.unitybedsitpoc");
            PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Android, "com.joesalmon.unitybedsitpoc");
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
        }

        /// <summary>Copy the user's local config next to the exe so the build runs on this machine.
        /// (config.json holds only paths into the user's own Sims 2 install; it is git-ignored.)</summary>
        static void PostProcess(string dir)
        {
            // The build is self-contained when baked content exists (Assets/LocalBaked): no config.json is copied, so it runs
            // without any Sims 2 install. Without baked content the player needs config.json (see config.example.json).
            File.Copy("config.example.json", Path.Combine(dir, "config.example.json"), true);
            File.WriteAllText(Path.Combine(dir, "README_RUN.txt"),
                "UnityBedsitPOC - first-person Sims 2 bedsit proof of concept\r\n\r\n" +
                "Run UnityBedsitPOC.exe. The game reads your own Sims 2 installation at run time via config.json\r\n" +
                "(copy config.example.json to config.json and set game_dir / user_dir). No Sims 2 content is included.\r\n\r\n" +
                "Controls: click/tap the LEFT edge to turn left, the RIGHT edge to turn right, the TOP-CENTRE to interact / go through the door.\r\n" +
                "(Keyboard: A/Left, D/Right, W/Up/Space.)  Evidence mode: UnityBedsitPOC.exe -evidence -quit\r\n");
        }

        [MenuItem("Bedsit/Build/Android APK")]
        public static void BuildAndroid()
        {
            ApplyCommonSettings();
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel25;
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            EditorUserBuildSettings.buildAppBundle = false;
            Directory.CreateDirectory(AndroidDir);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ProjectSetup.BedsitScene },
                locationPathName = Path.Combine(AndroidDir, "UnityBedsitPOC.apk"),
                target = BuildTarget.Android,
                options = BuildOptions.None,
            });
            Debug.Log($"[Build] Android: {report.summary.result}, {report.summary.totalSize / (1024 * 1024)} MB, errors {report.summary.totalErrors}");
            File.WriteAllText(Path.Combine("Builds", "android_build_result.txt"), report.summary.result + " " + report.summary.totalSize);
        }
    }
}
