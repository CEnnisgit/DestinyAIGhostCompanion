//! `db` crate — outbound Postgres adapters for the Ghost Companion domain ports.

pub mod d1_grimoire;
pub mod embedding_client;
pub mod grimoire_search;
pub mod lore_import;
pub mod lore_library;
pub mod lore_seed;
pub mod manifest_activity_resolver;
pub mod manifest_definition_resolver;
pub mod manifest_item_resolver;
pub mod manifest_sync;
pub mod postgres_chat_store;
pub mod postgres_session_revocation;
pub mod postgres_token_storage;

pub use d1_grimoire::{fetch_d1_grimoire, load_d1_grimoire_file};
pub use embedding_client::EmbeddingClient;
pub use grimoire_search::GrimoireSearch;
pub use lore_import::import_lore_dir;
pub use lore_library::{LoreCategory, LoreEntry, LoreLibrary};
pub use lore_seed::seed_lore;
pub use manifest_activity_resolver::ManifestActivityResolver;
pub use manifest_definition_resolver::{DefinitionEntry, ManifestDefinitionResolver};
pub use manifest_item_resolver::ManifestItemResolver;
pub use manifest_sync::ManifestSync;
pub use postgres_chat_store::PostgresChatStore;
pub use postgres_session_revocation::PostgresSessionRevocationStore;
pub use postgres_token_storage::PostgresTokenStorageAdapter;
