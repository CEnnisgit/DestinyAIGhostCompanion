//! Curated foundational Destiny lore.
//!
//! The Bungie Manifest (`DestinyLoreDefinition`, loaded by `ManifestSync`) is the
//! canonical, exhaustive lore archive — but it needs a real API key and a sync.
//! This hand-written, categorized corpus gives the Ghost broad, accurate core
//! lore out of the box, even before a manifest sync. Seed hashes live in a high
//! reserved range to avoid colliding with manifest entries.

use sqlx::PgPool;

/// (hash, category, name, description) for the foundational lore set.
pub const SEED: &[(i64, &str, &str, &str)] = &[
    // ---- Cosmology ----
    (4_200_000_001, "Cosmology", "The Gardener and the Winnower", "The two fundamental forces of the Destiny cosmos, framed in a thought-game of flowers. The Gardener nurtures complexity, life, and possibility — the Light. The Winnower prunes everything down toward a single perfect shape — the Darkness. Their endless disagreement is the engine of the universe."),
    (4_200_000_002, "Cosmology", "Paracausality", "Power that breaks the chain of cause and effect, defying ordinary physics. Both the Light and the Darkness are paracausal, which is how Guardians return from death and the Hive's Sword Logic can rewrite reality by killing."),
    (4_200_000_003, "Cosmology", "The Final Shape", "The Winnower's goal: a perfect, unchanging, conflict-free universe, reached by cutting away everything that could be cut. The Witness pursues it as salvation; to all who would be pruned, it is annihilation."),
    (4_200_000_004, "Cosmology", "The Sword Logic", "The Hive's brutal philosophy, drawn from the Worm Gods and the Darkness: existence belongs to whatever is strong enough to take it. To kill is to prove you deserve to exist, feeding power up an endless hierarchy of slaughter."),

    // ---- Light & Darkness ----
    (4_200_000_005, "Light & Darkness", "The Traveler", "A vast white sphere of paracausal power that arrived in our solar system and ushered in the Golden Age of humanity. When the Darkness came during the Collapse, the Traveler sacrificed itself to shield the Last City, and has hung silent above it ever since — the source of the Light in every Guardian."),
    (4_200_000_006, "Light & Darkness", "The Light", "The paracausal power of the Traveler. Guardians channel it to resurrect, to fight, and to wield the elemental subclasses — Arc, Solar, and Void. The Light is life, growth, and creation set against the Darkness."),
    (4_200_000_007, "Light & Darkness", "The Darkness (the Deep)", "An ancient paracausal force opposed to the Light, wielded by the Witness and its followers. Its philosophy, the Deep, preaches self-determination forged through hardship. Guardians have since learned its powers — Stasis and Strand."),
    (4_200_000_008, "Light & Darkness", "The Veil", "A Darkness-aligned paracausal entity, a dark mirror to the Traveler, long hidden on Neomuna. The Witness needed it to connect with the Traveler and force the Final Shape."),
    (4_200_000_009, "Light & Darkness", "The Black Fleet (Pyramids)", "A fleet of black, tetrahedral Pyramid ships that serve the Witness and carry the Darkness across the universe, hounding every civilization the Traveler ever touched."),

    // ---- The Witness & Disciples ----
    (4_200_000_010, "The Witness", "The Witness", "The architect of the Darkness's war on the Light and the gravest threat the system has faced. Born from a species that found an abandoned Traveler and turned to the Darkness, it is the amalgamated will of that civilization, commanding the Black Fleet to impose one final shape on all existence."),
    (4_200_000_011, "The Witness", "Nezarec, Final God of Pain", "A Disciple of the Witness and a being of living nightmares, whose very presence radiates terror. Long imprisoned, his shadow loomed over Lightfall."),
    (4_200_000_012, "The Witness", "Rhulk, Disciple of the Witness", "The first Disciple, herald of the Witness, who hunted the Leviathan species to near-extinction and met his end deep within Savathun's Throne World."),
    (4_200_000_013, "The Witness", "The Disciples", "The Witness's most powerful servants, gifted Darkness power to advance the Final Shape — among them Rhulk, Nezarec, and the fallen Emperor Calus."),

    // ---- Eras ----
    (4_200_000_014, "Eras", "The Golden Age", "Humanity's era of unprecedented prosperity, science, and expansion across the solar system under the Traveler's gifts — extended lifespans, terraformed worlds, and wondrous technology — all lost in the Collapse."),
    (4_200_000_015, "Eras", "The Collapse", "The cataclysm that ended the Golden Age, when the forces of the Darkness swept through the system. Billions died. The Traveler made its final stand over the Last City, and from its sacrifice the first Ghosts and Guardians arose."),
    (4_200_000_016, "Eras", "The Dark Age", "The lawless centuries after the Collapse, before the Last City, when the first risen Guardians — the Risen — fought one another and the warlords who preyed on survivors."),
    (4_200_000_017, "Eras", "The Iron Lords", "A noble order of early Guardians led by Lord Saladin and Lady Efrideet, who imposed order in the Dark Age and died containing the rogue nanotechnology SIVA. They are honored at the Iron Temple."),
    (4_200_000_018, "Eras", "SIVA", "A self-replicating nanotechnology from the Golden Age, weaponized into a plague. The Iron Lords died sealing it away, and the Fallen House of Devils' Splicers later revived it beneath the Cosmodrome."),

    // ---- The City ----
    (4_200_000_019, "The City", "The Last City", "Humanity's final bastion, built in the shadow of the Traveler. The last safe city on Earth, it has weathered the Collapse and the Red War, and remains the heart of Guardian civilization."),
    (4_200_000_020, "The City", "The Tower", "The Guardians' home and command center at the edge of the Last City, where the Vanguard direct the defense of humanity and Guardians gather between missions."),
    (4_200_000_021, "The City", "The Vanguard", "The leadership of the Guardians, one mentor per class: Commander Zavala the Titan, Ikora Rey the Warlock, and — until his murder — Cayde-6 the Hunter."),
    (4_200_000_022, "The City", "The Speaker", "For long years, the masked interpreter of the Traveler's silent will, who counseled the City and the Vanguard while the Traveler slept."),
    (4_200_000_023, "The City", "The Factions", "Three rival movements once vied for the City's future: Dead Orbit, who would flee the system; Future War Cult, who prepare for endless war; and New Monarchy, who would restore a strong central rule."),

    // ---- Guardians & Powers ----
    (4_200_000_024, "Guardians", "Guardians", "The honored dead, raised by Ghosts and the Traveler's Light to defend the Last City. So long as their Ghost survives, a Guardian can return from death again and again."),
    (4_200_000_025, "Guardians", "Ghosts", "Small, sapient machines created by the Traveler at the moment of its sacrifice. Each Ghost searches the ruins of the old world for the one Guardian it is destined to raise, then serves as companion, conscience, and lifeline."),
    (4_200_000_026, "Guardians", "The Three Classes", "Guardians follow three traditions: Titans, armored defenders who hold the line; Hunters, agile lone scouts and gunslingers; and Warlocks, warrior-scholars who study the Light as a weapon."),
    (4_200_000_027, "Subclasses", "Arc, Solar, and Void", "The three Light subclasses. Arc is lightning and speed; Solar is fire, healing, and radiance; Void is gravity, suppression, and the hungering devour."),
    (4_200_000_028, "Subclasses", "Stasis", "The first Darkness subclass Guardians mastered, on Europa under the Exo Stranger's guidance — ice that freezes, shatters, and controls the battlefield."),
    (4_200_000_029, "Subclasses", "Strand", "A Darkness subclass woven from the very threads that connect all things, discovered on Neomuna. Guardians grapple across the field and suspend foes in living matter."),

    // ---- Awoken ----
    (4_200_000_030, "Awoken", "The Awoken", "Descendants of humans caught between Light and Darkness during the Collapse, emerging changed. Many dwell in the Reef under Queen Mara Sov, walking a careful path between the powers that made them."),
    (4_200_000_031, "Awoken", "The Reef", "The Awoken's domain among the asteroids beyond Mars, long ruled from the Vestian Outpost by Queen Mara Sov and her brother Uldren."),
    (4_200_000_032, "Awoken", "Mara Sov", "Queen of the Awoken and a master of schemes that span millennia. She has spent lives and worlds to position the Awoken against the Hive and the Darkness."),
    (4_200_000_033, "Awoken", "Uldren Sov / The Crow", "Mara's brother, who — manipulated by Riven and grief — murdered Cayde-6. Slain for it, he was later reborn as the amnesiac Guardian called Crow, seeking redemption for a life he cannot remember."),
    (4_200_000_034, "Awoken", "The Dreaming City", "The Awoken's hidden realm beyond the Reef — a place of impossible beauty cursed by Riven's dying wish into a repeating three-week loop, where Mara Sov's deepest designs play out."),
    (4_200_000_035, "Awoken", "Riven and the Ahamkara", "Riven was the last Ahamkara — wish-granting dragons whose bargains always hid a price. Taken by Oryx's heirs, her dying wish locked the Dreaming City in its curse. The rest of her kind were hunted to near-extinction in the Great Hunt."),

    // ---- Exo ----
    (4_200_000_036, "Exo", "The Exo", "Sentient war machines built in the Golden Age by Clovis Bray, each housing a transferred human mind. Repeated resets blur their memories, and few recall the people they once were."),
    (4_200_000_037, "Exo", "Clovis Bray", "The Golden Age megacorporation and its ruthless founder, whose research on Europa created the Exo, raised the Warmind Rasputin, and dug too deep into the Darkness."),
    (4_200_000_038, "Exo", "The Exo Stranger (Elsie Bray)", "A time-traveling Exo from a doomed future, granddaughter of Clovis Bray, who warned Guardians across timelines and taught them to wield Stasis."),

    // ---- Fallen ----
    (4_200_000_039, "Fallen", "The Fallen (Eliksni)", "A once-proud spacefaring people who lost their own Traveler and fell into ruin. Splintered into Houses, most now scavenge and raid — though some, like the House of Light, seek peace with humanity."),
    (4_200_000_040, "Fallen", "The Whirlwind", "The cataclysm that destroyed the Eliksni homeworld of Riis when their Great Machine — their Traveler — abandoned them, scattering the survivors across the stars as scavengers."),
    (4_200_000_041, "Fallen", "The Houses of the Fallen", "Eliksni society is organized into Houses — Devils, Kings, Winter, Wolves, Dusk, and Light — each led by a Kell and bound to the spherical Servitors that ration their life-giving Ether."),
    (4_200_000_042, "Fallen", "Mithrax, Kell of Light", "An Eliksni leader who renounced the old ways, sought peace between his people and humanity, and brought the House of Light to live within the Last City."),
    (4_200_000_043, "Fallen", "Variks, the Loyal", "An Eliksni scribe of the House of Judgment who long aided Guardians from the Reef, dreaming of a reborn, united Eliksni people."),

    // ---- Hive ----
    (4_200_000_044, "Hive", "The Hive", "An ancient, parasitic species that worships the Darkness and is bound to the Worm Gods by a pact of endless killing. Their god-kings — Oryx, Crota, Savathun, Xivu Arath — have menaced the system for eons."),
    (4_200_000_045, "Hive", "The Worm Gods", "Monstrous immortal worms of the Darkness who struck a bargain with the proto-Hive: feed us through endless slaughter, and you will never die. The Worms' hunger now drives the whole Hive."),
    (4_200_000_046, "Hive", "Oryx, the Taken King", "The Hive god-king who mastered the Taken and crossed the system aboard his Dreadnaught to avenge his slain son Crota. Guardians boarded his ship and ended him."),
    (4_200_000_047, "Hive", "Crota, Son of Oryx", "Oryx's son, who tore a wound in reality on the Moon and slaughtered an entire Guardian army at the Great Disaster before a fireteam descended into the Hellmouth to kill him."),
    (4_200_000_048, "Hive", "Savathun, the Witch Queen", "Hive god of cunning and trickery and Oryx's sister. A master of deception across millennia, she stole the Light itself and raised the Lucent Hive before her schemes met the Guardians."),
    (4_200_000_049, "Hive", "Xivu Arath, God of War", "Oryx's sister, who grows stronger with every war fought anywhere in the universe. A relentless, rising threat who feeds on conflict itself."),
    (4_200_000_050, "Hive", "The Lucent Hive", "Savathun's Hive, who stole the Light and now raise their own immortal Guardians with stolen Ghosts — Hive that can resurrect, just like the Risen."),
    (4_200_000_051, "Hive", "Throne Worlds & the Ascendant Realm", "Pocket dimensions Hive gods carve from the Darkness. Within a Throne World a god is nearly invincible; to truly kill one, you must follow it there and end it in its own realm."),

    // ---- Vex ----
    (4_200_000_052, "Vex", "The Vex", "A hostile machine race that computes and manipulates time and space. The Vex labor to convert all of reality into their own endless simulation, indifferent to every other power."),
    (4_200_000_053, "Vex", "The Black Garden", "A timeless Vex paradise outside normal space, tended by the Sol Divisive who worship the Darkness; once home to the Black Heart."),
    (4_200_000_054, "Vex", "The Vault of Glass", "A Vex stronghold on Venus where the Vex experiment on time itself, erasing things from history. Its guardian-mind Atheon exists at every moment at once."),
    (4_200_000_055, "Vex", "Atheon, Time's Conflux", "The temporal nexus-mind at the heart of the Vault of Glass, able to hurl Guardians forward and backward through time."),
    (4_200_000_056, "Vex", "Radiolaria", "The white, living fluid that is the true substance of the Vex. Their metal bodies are merely shells for this shared, calculating mind-milk."),

    // ---- Cabal ----
    (4_200_000_057, "Cabal", "The Cabal", "A vast militaristic empire of hulking aliens. Their Red Legion, under Dominus Ghaul, stormed the Last City in the Red War and briefly severed Guardians from the Light."),
    (4_200_000_058, "Cabal", "Emperor Calus & the Leviathan", "The exiled, hedonist Cabal Emperor and his world-eating pleasure-ship, the Leviathan. A doomsayer who came to serve the Witness as a Disciple before his end."),
    (4_200_000_059, "Cabal", "Dominus Ghaul", "Leader of the Red Legion who stole the Traveler's Light in the Red War, trying to take by force what he believed he had earned. The Traveler refused him."),
    (4_200_000_060, "Cabal", "Empress Caiatl", "Calus's daughter and Ghaul's successor, who allied her Cabal with the Last City against the Witness — a wary, hard-won partnership."),

    // ---- Taken & The Nine ----
    (4_200_000_061, "Taken", "The Taken", "Beings torn from their own existence into a Darkness-warped state, first by Oryx and later by others who inherit the power. Hollow, glowing, and bound to a single will."),
    (4_200_000_062, "The Nine", "The Nine", "Enigmatic beings born of dark matter and the gravity of the system's worlds. They observe events through agents and emissaries, and their true motives remain inscrutable."),
    (4_200_000_063, "The Nine", "Xur, Agent of the Nine", "A tentacle-faced Agent of the Nine who appears at the weekend's edge to trade Exotic gear, a strange and silent merchant of the unknown."),

    // ---- Warmind ----
    (4_200_000_064, "Warmind", "Rasputin", "The last Warmind — a colossal Golden Age defense AI built to protect the system. He survived the Collapse by going silent, and has since become a wary, immensely powerful ally."),
    (4_200_000_065, "Warmind", "Ana Bray", "A Guardian of the Bray family who reconnected with Rasputin in the Hellas Basin on Mars and fought to recover her lost past."),

    // ---- Characters ----
    (4_200_000_066, "Characters", "Commander Zavala", "The stalwart Awoken Titan who commands the Vanguard — an anchor of duty, resolve, and hope for the City through its darkest hours."),
    (4_200_000_067, "Characters", "Ikora Rey", "The Warlock Vanguard, a brilliant and formidable scholar of the Light and a former student of Osiris, who guides the City's hidden warlocks."),
    (4_200_000_068, "Characters", "Cayde-6", "The roguish Exo Hunter Vanguard, beloved for his humor and his Ace of Spades. Murdered by Uldren in the Prison of Elders, he later returned within the Pale Heart."),
    (4_200_000_069, "Characters", "Lord Shaxx", "The booming, battle-loving Titan who runs the Crucible, certain that Guardians must spar relentlessly to be ready for the true war."),
    (4_200_000_070, "Characters", "The Drifter", "A secretive, roguish lightbearer who runs Gambit and has long walked the razor's edge between the Light and the Dark."),
    (4_200_000_071, "Characters", "Saint-14", "A legendary Titan and former hero of the City, devout protector of its people, lost in the Infinite Forest and saved across time by Osiris and the Guardian."),
    (4_200_000_072, "Characters", "Osiris", "A brilliant, exiled Warlock obsessed with the Vex and the future. Once Shaxx's rival and Saint-14's love, he later lost his Ghost Sagira and much of his power."),
    (4_200_000_073, "Characters", "Eris Morn", "A haunted Hunter, the lone survivor of a fireteam destroyed by Crota, who turned Hive knowledge into a weapon against the Darkness."),
    (4_200_000_074, "Characters", "Lord Saladin", "The last of the Iron Lords, keeper of their memory and the Iron Banner, who returns to lead Guardians in times of dire crisis."),
    (4_200_000_075, "Characters", "Petra Venj", "The Awoken Regent-Commander who governs the Reef and the Dreaming City in Queen Mara Sov's long absences."),

    // ---- Locations ----
    (4_200_000_076, "Locations", "The Cosmodrome", "The old Russian spaceport on Earth where many Guardians first rise from the dead amid the rusting wreckage of the Golden Age."),
    (4_200_000_077, "Locations", "The Moon", "Scarred by the Hive's Hellmouth and a buried Pyramid ship. Site of the Great Disaster, of Crota's slaughter, and of Eris Morn's long vigil."),
    (4_200_000_078, "Locations", "The Dreadnaught", "Oryx's titanic warship, grown from the remains of a slain god, which entered the system bent on vengeance for Crota."),
    (4_200_000_079, "Locations", "Europa", "Jupiter's frozen moon, home to Clovis Bray's dark experiments, the Deep Stone Crypt, the Fallen of Eramis, and the birth of Stasis."),
    (4_200_000_080, "Locations", "The Deep Stone Crypt", "The Clovis Bray facility on Europa where Exo minds are forged and reborn — and the site of a legendary Guardian raid."),
    (4_200_000_081, "Locations", "Neomuna", "A hidden, advanced human city on Neptune, defended by the augmented Cloud Striders, where the Veil was kept in secret."),
    (4_200_000_082, "Locations", "The Pale Heart", "A realm within the Traveler itself, shaped by memory and made real, where the final confrontation with the Witness took place."),
    (4_200_000_083, "Locations", "Savathun's Throne World", "The Witch Queen's ascendant realm — a deceptively beautiful domain that hides her schemes, her swamp of secrets, and her stolen Light."),

    // ---- Expansions / Events ----
    (4_200_000_084, "Events", "The Red War", "Dominus Ghaul's invasion that conquered the Last City and cut Guardians off from the Light — until the Guardian reached the Traveler and reclaimed it."),
    (4_200_000_085, "Events", "Forsaken & the Scorn", "The hunt across the Tangled Shore and Dreaming City after Cayde-6's murder, against the undead Scorn raised by Fikrul the Fanatic and the wish-dragon Riven."),
    (4_200_000_086, "Events", "Beyond Light", "On Europa, the Fallen Eramis rallied her people around Stasis and the Darkness. Guardians claimed that power for themselves, learning to wield the Dark without falling to it."),
    (4_200_000_087, "Events", "The Witch Queen", "Having stolen the Light, Savathun dared Guardians into her Throne World — a gambit that taught both sides how Light and Darkness truly work."),
    (4_200_000_088, "Events", "Lightfall", "The Witness struck Neomuna for the Veil, with Calus and the freed Nezarec at its side. Guardians gained Strand, but could not stop the Witness from piercing the Traveler."),
    (4_200_000_089, "Events", "The Final Shape", "The last stand within the Pale Heart against the Witness — joined by a returned Cayde-6 — to save the Traveler and deny the Final Shape to all creation."),

    // ---- Weapons ----
    (4_200_000_090, "Weapons", "Gjallarhorn", "The most storied rocket launcher in Destiny, whose Wolfpack Rounds turned the tide of countless desperate fights. To many Guardians it is a symbol of hope itself."),
    (4_200_000_091, "Weapons", "Thorn & The Last Word", "Twin legends of a duel. Thorn is the cursed hand cannon of the fallen Guardian Dredgen Yor; the Last Word was wielded by Shin Malphur, who avenged Yor's victims and ended him."),
    (4_200_000_092, "Weapons", "Ace of Spades", "Cayde-6's signature hand cannon, carried on by the Guardian in his memory after his murder."),
    (4_200_000_093, "Weapons", "Whisper of the Worm", "An Exotic sniper rifle born of the Hive Worm Gods, earned through a hidden and grueling trial."),

    // ---- Lore Books (paraphrased summaries) ----
    (4_200_000_094, "Lore Book", "The Books of Sorrow: The Sisters", "On the doomed gas giant Fundament, three Krill princesses — Aurash, Sathona, and Xi Ro — survived their world's drowning. Seeking why their gods had abandoned them, Aurash piloted a ship down toward Fundament's crushing core."),
    (4_200_000_095, "Lore Book", "The Books of Sorrow: The Worm Gods' Bargain", "At Fundament's core the sisters found the imprisoned Worm Gods, who offered immortality and limitless power — at a price. Each sister must forever obey her own nature and feed the Worm within her through endless conquest, or be devoured by it. They accepted, and were remade."),
    (4_200_000_096, "Lore Book", "The Books of Sorrow: The Taken King", "Reborn as Auryx, Savathun, and Xivu Arath, the sisters waged war across the stars and codified the Sword Logic — that existence belongs to the strong. Auryx journeyed to the edge of the universe, wrested the power to Take from a slain god, and returned as Oryx, the Taken King."),
    (4_200_000_097, "Lore Book", "Marasenna (Awoken Origin)", "When the Collapse tore reality, humans caught in the rupture were reborn in the Distributary — a sunlit pocket world of near-immortality — as the first Awoken. Mara Sov and her brother Uldren rose to lead them, and Mara chose to forsake paradise and return her people to the harsh Sol system to take up the war against the Darkness."),
    (4_200_000_098, "Lore Book", "Truth to Power", "A book of letters written in Savathun's deceiving voice that taunts and tempts the reader, blurring truth and lie. It hints at the nature of paracausality, the worm of ambition coiled within every powerful being, and Savathun's secret war against her own Worm God."),

    // ---- Raids (paraphrased story summaries) ----
    (4_200_000_099, "Raids", "Vault of Glass", "Beneath Venus, the fireteam of Kabr, Praedyth, and Pahanin breached the Vault to stop the Vex from mastering time itself. Kabr sacrificed his very being to forge the Aegis; only with that relic could later Guardians defeat Atheon, Time's Conflux."),
    (4_200_000_100, "Raids", "Crota's End", "Guardians descended into the Moon's Hellmouth, crossed the chasm of the damned, and struck down Crota, Son of Oryx — using a sword reaved from his own Hive — answering the Great Disaster at last."),
    (4_200_000_101, "Raids", "King's Fall", "Aboard the Dreadnaught, Guardians broke Oryx's defenses, climbed to his throne in the Ascendant realm, and killed the Taken King himself, ending his campaign of vengeance for Crota."),
    (4_200_000_102, "Raids", "Wrath of the Machine", "The Fallen House of Devils' Splicers revived the Golden Age plague SIVA and built the war-mind Aksis. Guardians, carrying the legacy of the Iron Lords, brought the machine down beneath the Cosmodrome."),
    (4_200_000_103, "Raids", "Last Wish", "In the Dreaming City, Guardians bargained with Riven, the last Ahamkara, and killed her — but her death-wish, twisted by Savathun, locked the City into its endless three-week curse."),
    (4_200_000_104, "Raids", "Garden of Salvation", "Following a Vex signal into the Black Garden, Guardians confronted the Consecrated and Sanctified Minds — Vex that had reached out to touch the Darkness's Pyramid on the Moon."),
    (4_200_000_105, "Raids", "Deep Stone Crypt", "On Europa, Guardians fought through Eramis's Fallen into Clovis Bray's hidden facility — the birthplace of the Exo — to stop a doomsday weapon and reckon with the Bray family's legacy."),
    (4_200_000_106, "Raids", "Vow of the Disciple", "Within Savathun's Throne World, Guardians entered a sunken Pyramid and faced Rhulk, the first Disciple of the Witness, learning how the Witness bends whole worlds to its will."),
    (4_200_000_107, "Raids", "Root of Nightmares", "Aboard a Pyramid grafted onto a captured Traveler near Neptune, Guardians faced Nezarec, the Final God of Pain, and severed the Witness's grip on the Light."),
    (4_200_000_108, "Raids", "Salvation's Edge", "Deep within the Traveler's Pale Heart, Guardians launched a final assault on the Witness itself, fighting to deny the Final Shape to all of creation."),

    // ---- More characters ----
    (4_200_000_109, "Characters", "Kabr, Praedyth, and Pahanin", "The doomed fireteam who first breached the Vault of Glass. Kabr became one with the Vault to forge the Aegis; Praedyth was lost to Vex time; only Pahanin escaped, to warn others away."),
    (4_200_000_110, "Characters", "Lord Felwinter", "A formidable Warlock of the Dark Age, once bound to the warlord Felwinter's Peak, whose name endures on the legendary shotgun Felwinter's Lie."),
    (4_200_000_111, "Characters", "The Crow's Companion, Glint", "Glint is the Ghost who resurrected the reborn Uldren Sov as the Guardian called Crow — a gentle, hopeful counterpart to the dark deeds of the man's past life."),
];

/// Upserts the curated seed into `destiny_lore`. Idempotent; leaves existing
/// embeddings intact when the text is unchanged.
pub async fn seed_lore(pool: &PgPool) -> Result<u64, anyhow::Error> {
    let mut count = 0u64;
    for (hash, category, name, description) in SEED {
        sqlx::query(
            "INSERT INTO destiny_lore (hash, name, description, category, source)
             VALUES ($1, $2, $3, $4, 'curated')
             ON CONFLICT (hash) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                category = EXCLUDED.category,
                source = 'curated',
                embedding = CASE WHEN destiny_lore.description <> EXCLUDED.description
                                 THEN NULL ELSE destiny_lore.embedding END",
        )
        .bind(hash)
        .bind(*name)
        .bind(*description)
        .bind(*category)
        .execute(pool)
        .await?;
        count += 1;
    }
    Ok(count)
}
