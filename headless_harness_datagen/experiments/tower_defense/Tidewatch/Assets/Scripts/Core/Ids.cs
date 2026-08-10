namespace Tidewatch.Core
{
    /// <summary>Tidal phase of a level. Order is the canonical cycle.</summary>
    public enum TidePhase
    {
        Low = 0,
        Rising = 1,
        High = 2,
        Ebbing = 3,
    }

    /// <summary>How an enemy moves across tile-state.</summary>
    public enum MoveClass
    {
        /// <summary>Walks dry land only. Blocked by flooded tiles.</summary>
        Terrestrial = 0,
        /// <summary>Can cross both dry and flooded tiles.</summary>
        Amphibious = 1,
        /// <summary>Requires water (flooded or deep-water tiles). Beached on dry tiles.</summary>
        Pelagic = 2,
    }

    /// <summary>Tower target selection priority.</summary>
    public enum TargetPriority
    {
        First = 0,
        Last = 1,
        Strongest = 2,
        Closest = 3,
    }

    /// <summary>Tower archetype ids. Data references towers by these stable string ids.</summary>
    public static class TowerIds
    {
        public const string BeaconSpire = "beacon_spire";
        public const string FlareMortar = "flare_mortar";
        public const string PrismArray = "prism_array";
        public const string HarpoonBallista = "harpoon_ballista";
        public const string FogBell = "fog_bell";
    }

    /// <summary>Enemy archetype ids.</summary>
    public static class EnemyIds
    {
        public const string Skitterling = "skitterling";
        public const string BrineHulk = "brine_hulk";
        public const string AbyssalLurker = "abyssal_lurker";
        public const string Spitter = "spitter";
        public const string Broodmother = "broodmother";
        public const string DrownedBell = "drowned_bell";
    }

    /// <summary>Difficulty preset ids.</summary>
    public static class DifficultyIds
    {
        public const string CalmSea = "calm_sea";
        public const string RisingGale = "rising_gale";
        public const string AbyssalNight = "abyssal_night";
    }

    /// <summary>Base terrain of a tile, before tide state is applied.</summary>
    public enum TerrainType
    {
        /// <summary>Raised causeway; dry at most tides, floods at High.</summary>
        Causeway = 0,
        /// <summary>Low trench; flooded at most tides, drains at Low.</summary>
        Trench = 1,
        /// <summary>Deep water; always water, never walkable by terrestrial. Pelagic-only.</summary>
        DeepWater = 2,
        /// <summary>Solid rock; never walkable, never buildable.</summary>
        Rock = 3,
        /// <summary>Elevated build plot. Blocks movement, buildable.</summary>
        BuildPlot = 4,
        /// <summary>Spawn gate. Traversable by enemies entering, not otherwise walkable.</summary>
        Gate = 5,
        /// <summary>The Great Lantern base tile. Enemies path toward it; leaks happen here.</summary>
        Base = 6,
    }
}
