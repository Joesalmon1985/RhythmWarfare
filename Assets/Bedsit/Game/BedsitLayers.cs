namespace Bedsit.Game
{
    /// <summary>
    /// Layer indices used by the POC. The player's own Sim lives on PlayerMirrorOnly: the first-person eye camera never
    /// renders that layer, only the mirror camera does, so the player's body is visible nowhere except in the mirror.
    /// (OpenTS2 uses layers 0-6; 8 is free.)
    /// </summary>
    public static class BedsitLayers
    {
        public const int PlayerMirrorOnly = 8;
        public const int MirrorGlass = 9;
        public static int PlayerMirrorOnlyMask => 1 << PlayerMirrorOnly;
    }
}
