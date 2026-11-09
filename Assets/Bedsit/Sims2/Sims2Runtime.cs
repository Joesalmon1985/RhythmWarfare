using System;
using System.Collections.Generic;
using System.IO;
using OpenTS2.Common;
using OpenTS2.Content;
using OpenTS2.Content.DBPF;
using OpenTS2.Content.DBPF.Scenegraph;
using OpenTS2.Engine;
using OpenTS2.Files;
using OpenTS2.Files.Formats.DBPF;
using UnityEngine;

namespace Bedsit.Sims2
{
    /// <summary>
    /// Owns OpenTS2 initialisation for the POC. Locates the user's own Sims 2 install through a local config.json
    /// (never committed), initialises the OpenTS2 core and loads the packages the bedsit needs. All Sims 2 content is
    /// read at runtime from the player's installation: nothing extracted from the game is shipped with the project.
    /// </summary>
    public static class Sims2Runtime
    {
        public static bool Initialised { get; private set; }
        public static string ConfigPath { get; private set; }
        public static string LastError { get; private set; }

        /// <summary>Search order: BEDSIT_CONFIG env var, next to the exe / project root, current directory.</summary>
        public static string FindConfig()
        {
            var env = Environment.GetEnvironmentVariable("BEDSIT_CONFIG");
            if (!string.IsNullOrEmpty(env) && File.Exists(env)) return env;
            var candidates = new List<string>
            {
                Path.GetFullPath(Path.Combine(Application.dataPath, "..", "config.json")),
                Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "config.json")),
                Path.Combine(Environment.CurrentDirectory, "config.json"),
            };
            foreach (var c in candidates) if (File.Exists(c)) return c;
            return null;
        }

        /// <summary>Initialise OpenTS2 and mount the base game's Sims3D packages. Safe to call repeatedly.</summary>
        public static bool Initialise()
        {
            if (Initialised) return true;
            try
            {
                ConfigPath = FindConfig();
                if (ConfigPath == null)
                {
                    LastError = "config.json not found (copy config.example.json and point it at your Sims 2 install)";
                    return false;
                }
                // OpenTS2 reads "config.json" relative to the working directory.
                Directory.SetCurrentDirectory(Path.GetDirectoryName(ConfigPath));
                Core.InitializeCore();
                MountPackages();
                Initialised = true;
                return true;
            }
            catch (Exception e)
            {
                LastError = e.ToString();
                Debug.LogError("[Sims2Runtime] initialisation failed: " + e);
                return false;
            }
        }

        static void MountPackages()
        {
            var content = ContentManager.Instance;
            var packages = new List<string>();
            // Base game geometry, materials, textures, animations, CAS parts...
            packages.AddRange(Filesystem.GetPackagesInDirectory(
                Path.Combine(Filesystem.GetPathForProduct(ProductFlags.BaseGame), "TSData/Res/Sims3D")));
            // Skin tones + clothing catalogue entries used by Sim appearances.
            packages.AddRange(Filesystem.GetPackagesInDirectory(
                Path.Combine(Filesystem.GetPathForProduct(ProductFlags.BaseGame), "TSData/Res/Catalog/Skins")));
            // Wall / floor patterns + base materials.
            packages.AddRange(Filesystem.GetPackagesInDirectory(
                Path.Combine(Filesystem.GetPathForProduct(ProductFlags.BaseGame), "TSData/Res/Materials")));
            packages.AddRange(Filesystem.GetPackagesInDirectory(
                Path.Combine(Filesystem.GetPathForProduct(ProductFlags.BaseGame), "TSData/Res/Catalog/Patterns")));
            content.AddPackages(packages);
        }

        /// <summary>Mount further packages (e.g. an expansion's Sims3D folder) on demand.</summary>
        public static void MountDirectory(ProductFlags product, string relativeDir)
        {
            var dir = Path.Combine(Filesystem.GetPathForProduct(product), relativeDir);
            ContentManager.Instance.AddPackages(Filesystem.GetPackagesInDirectory(dir));
        }

        public static ScenegraphResourceAsset GetCres(string name)
        {
            return ContentManager.Instance.GetAsset<ScenegraphResourceAsset>(
                new ResourceKey(name, GroupIDs.Scenegraph, TypeIDs.SCENEGRAPH_CRES));
        }

        public static ScenegraphAnimationAsset GetAnimation(string name)
        {
            return ContentManager.Instance.GetAsset<ScenegraphAnimationAsset>(
                new ResourceKey(name, GroupIDs.Scenegraph, TypeIDs.SCENEGRAPH_ANIM));
        }

        /// <summary>Package file name that holds a resource, for provenance records ("Sims00.package").</summary>
        public static string PackageOf(ResourceKey key)
        {
            var entry = ContentManager.Instance.GetEntry(key);
            return entry?.Package?.FilePath != null ? Path.GetFileName(entry.Package.FilePath) : "(unknown)";
        }
    }
}
