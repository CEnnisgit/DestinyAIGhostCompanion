//! `db` crate — outbound Postgres adapters for the Ghost Companion domain ports.

pub mod embedding_client;
pub mod grimoire_search;
pub mod lore_seed;
pub mod manifest_item_resolver;
pub mod manifest_sync;
pub mod postgres_token_storage;

pub use embedding_client::EmbeddingClient;
pub use grimoire_search::GrimoireSearch;
pub use lore_seed::seed_lore;
pub use manifest_item_resolver::ManifestItemResolver;
pub use manifest_sync::ManifestSync;
pub use postgres_token_storage::PostgresTokenStorageAdapter;
