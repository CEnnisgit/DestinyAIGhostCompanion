//! `db` crate — outbound Postgres adapters for the Ghost Companion domain ports.

pub mod postgres_token_storage;

pub use postgres_token_storage::PostgresTokenStorageAdapter;
