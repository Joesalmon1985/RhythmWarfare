using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>Persisted cleaning progress of a room: which cleanables are tidy. JSON in the persistent data folder
    /// (bedsit_room_&lt;id&gt;.json). Saving happens whenever a task finishes; loading (-loadroom / BEDSIT_LOADROOM=1, or an explicit
    /// call) snaps those tasks to their tidy state without animation.</summary>
    [Serializable]
    public class RoomSaveData
    {
        public int version = 1;
        public string roomId;
        public List<string> tidied = new List<string>();
        public string savedUtc;
    }

    public static class RoomSave
    {
        public static string PathFor(string roomId) { return System.IO.Path.Combine(Application.persistentDataPath, "bedsit_room_" + roomId + ".json"); }
        /// <summary>Tests redirect this to a temp file.</summary>
        public static string OverridePath;

        static string Path_(string roomId) { return OverridePath ?? PathFor(roomId); }

        public static bool LoadRequested
        {
            get
            {
                foreach (var a in Environment.GetCommandLineArgs()) if (a == "-loadroom") return true;
                return Environment.GetEnvironmentVariable("BEDSIT_LOADROOM") == "1";
            }
        }

        public static RoomSaveData Capture(RoomBuilder rb)
        {
            var d = new RoomSaveData { roomId = rb.Def.id, savedUtc = DateTime.UtcNow.ToString("o") };
            foreach (var c in rb.Cleanables) if (c.Tidied) d.tidied.Add(c.Id);
            return d;
        }

        public static void Save(RoomBuilder rb)
        {
            try { File.WriteAllText(Path_(rb.Def.id), JsonUtility.ToJson(Capture(rb), true)); }
            catch (Exception e) { Debug.LogWarning("[RoomSave] save failed: " + e.Message); }
        }

        public static RoomSaveData Read(string roomId)
        {
            try { var p = Path_(roomId); return File.Exists(p) ? JsonUtility.FromJson<RoomSaveData>(File.ReadAllText(p)) : null; }
            catch (Exception e) { Debug.LogWarning("[RoomSave] load failed: " + e.Message); return null; }
        }

        /// <summary>Apply saved progress. Returns how many tasks were restored.</summary>
        public static int Apply(RoomBuilder rb, RoomSaveData d)
        {
            if (d == null || d.roomId != rb.Def.id) return 0;
            int n = 0;
            foreach (var id in d.tidied) { var c = rb.Find(id); if (c != null && !c.Tidied) { c.SnapToTidy(); n++; } }
            return n;
        }

        public static void Delete(string roomId) { try { var p = Path_(roomId); if (File.Exists(p)) File.Delete(p); } catch { } }
    }
}
