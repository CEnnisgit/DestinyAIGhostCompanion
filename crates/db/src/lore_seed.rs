//! Curated foundational Destiny lore.
//!
//! The Bungie Manifest (`DestinyLoreDefinition`, loaded by `ManifestSync`) is the
//! canonical, exhaustive lore archive — but it needs a real API key and a sync.
//! This hand-written seed gives the Ghost solid core lore out of the box, even
//! before a manifest sync, so it "always knows" the essentials. Seed hashes live
//! in a high reserved range to avoid colliding with manifest entries.

use sqlx::PgPool;

/// (hash, name, description) for the foundational lore set.
pub const SEED: &[(i64, &str, &str)] = &[
    (4_200_000_001, "The Traveler", "A vast white sphere of paracausal power that arrived in our solar system and ushered in the Golden Age of humanity. When the Darkness came during the Collapse, the Traveler sacrificed itself to shield the Last City, and has hung silent and dormant above it ever since — the source of the Light that animates every Guardian."),
    (4_200_000_002, "The Light", "The paracausal power of the Traveler. Guardians channel it to resurrect, to fight, and to wield the elemental subclasses — Arc, Solar, and Void. The Light is life and creation set against the Darkness."),
    (4_200_000_003, "The Darkness", "An ancient paracausal force opposed to the Light, wielded by the Witness and its followers. Once thought purely malevolent, Guardians have since learned to wield Darkness subclasses — Stasis and Strand — turning the enemy's own power against it."),
    (4_200_000_004, "The Collapse", "The cataclysm that ended humanity's Golden Age, when the forces of the Darkness swept through the solar system. Billions died. The Traveler made its final stand over the Last City, and from its sacrifice the first Ghosts and Guardians arose."),
    (4_200_000_005, "The Golden Age", "Humanity's era of unprecedented prosperity, science, and expansion across the solar system under the Traveler's gifts — extended lifespans, terraformed worlds, and wondrous technology — all of it lost in the Collapse."),
    (4_200_000_006, "Guardians", "The honored dead, raised by Ghosts and the Traveler's Light to defend the Last City and the people within it. So long as their Ghost survives, a Guardian can return from death again and again."),
    (4_200_000_007, "Ghosts", "Small, sapient machines created by the Traveler at the moment of its sacrifice. Each Ghost searches the ruins of the old world for the one Guardian it is destined to raise, then serves as companion, conscience, and lifeline."),
    (4_200_000_008, "The Last City", "Humanity's final bastion, built in the shadow of the Traveler. The last safe city on Earth, it has weathered the Collapse and the Red War, and remains the heart of Guardian civilization."),
    (4_200_000_009, "The Tower", "The Guardians' home and command center at the edge of the Last City, where the Vanguard direct the defense of humanity and Guardians gather between missions."),
    (4_200_000_010, "The Vanguard", "The leadership of the Guardians, one mentor per class: Commander Zavala the Titan, Ikora Rey the Warlock, and — until his death — Cayde-6 the Hunter."),
    (4_200_000_011, "The Three Classes", "Guardians fall into three traditions: Titans, armored defenders who hold the line; Hunters, agile lone scouts and gunslingers; and Warlocks, warrior-scholars who study the Light as a weapon."),
    (4_200_000_012, "The Awoken", "Descendants of humans caught between Light and Darkness during the Collapse, emerging changed. Many dwell in the Reef under Queen Mara Sov, walking a careful path between the powers that made them."),
    (4_200_000_013, "The Hive", "An ancient, parasitic species that worships the Darkness and is bound to the Worm Gods by a pact of endless killing. Their god-kings — Oryx, Crota, Savathûn — have menaced the system for eons."),
    (4_200_000_014, "Oryx, the Taken King", "The Hive god-king who mastered the Taken and crossed the system to avenge his slain son Crota. Guardians boarded his Dreadnaught and ended him, breaking his hold over the Taken."),
    (4_200_000_015, "The Fallen (Eliksni)", "A once-proud spacefaring people who lost their own Traveler and fell into ruin. Splintered into Houses, most now scavenge and raid — though some, like the House of Light, seek peace with humanity."),
    (4_200_000_016, "The Cabal", "A vast militaristic empire of hulking aliens. Their Red Legion, under Dominus Ghaul, stormed the Last City in the Red War and briefly severed Guardians from the Light."),
    (4_200_000_017, "The Vex", "A hostile machine race that computes and manipulates time and space. The Vex labor to convert all of reality into their own endless simulation, indifferent to every other power."),
    (4_200_000_018, "The Taken", "Beings torn from their own existence into a Darkness-warped state, first by Oryx and later by others who inherit the power. Hollow, glowing, and bound to a single will."),
    (4_200_000_019, "The Witness", "The architect of the Darkness's war on the Light and the system's gravest threat. Commanding the Black Fleet of pyramid ships, it seeks to impose a single, final shape on all of existence."),
    (4_200_000_020, "Savathun, the Witch Queen", "Hive god of cunning and trickery and Oryx's sister. A master of deception across millennia, she stole the Light itself and built the Lucent Hive before her schemes met the Guardians."),
    (4_200_000_021, "The Speaker", "For long years, the masked interpreter of the Traveler's silent will, who counseled the City and the Vanguard while the Traveler slept."),
    (4_200_000_022, "The Crucible", "Sanctioned Guardian-versus-Guardian combat overseen by Lord Shaxx, who believes that only by fighting one another can Guardians stay sharp enough to defend the City."),
    (4_200_000_023, "Gambit", "A contest run by the Drifter that blends fighting aliens and fighting Guardians: rival teams bank motes of Darkness, summon a Primeval, and invade one another to win."),
    (4_200_000_024, "The Dreaming City", "The Awoken's hidden realm beyond the Reef — a place of impossible beauty cursed into a repeating three-week loop, where Mara Sov's deepest designs play out."),
    (4_200_000_025, "Stasis and Strand", "Darkness subclasses Guardians learned to wield. Stasis freezes and controls, drawn from the cold Beyond; Strand weaves the very threads that connect all things, drawn from the Veil."),
];

/// Upserts the curated seed into `destiny_lore`. Idempotent; leaves any existing
/// embeddings intact when the text is unchanged.
pub async fn seed_lore(pool: &PgPool) -> Result<u64, anyhow::Error> {
    let mut count = 0u64;
    for (hash, name, description) in SEED {
        sqlx::query(
            "INSERT INTO destiny_lore (hash, name, description) VALUES ($1, $2, $3)
             ON CONFLICT (hash) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                embedding = CASE WHEN destiny_lore.description <> EXCLUDED.description
                                 THEN NULL ELSE destiny_lore.embedding END",
        )
        .bind(hash)
        .bind(*name)
        .bind(*description)
        .execute(pool)
        .await?;
        count += 1;
    }
    Ok(count)
}
