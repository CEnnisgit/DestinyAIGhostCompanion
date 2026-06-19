# Phase 4A: Local Foundation — multi-stage build for the Rust backend.
#
# NOTE: the roadmap suggested `rust:1.78-slim`, but the workspace crates use
# `edition = "2024"`, which requires Rust >= 1.85. We track the latest stable
# 1.x to stay compatible.
#
# The runtime stage runs the `server` binary produced by `apps/server`
# (Phase 4C). Until that binary target exists, `docker build` is not part of
# the Phase 4A verification — only `docker compose up` (Postgres) is.

# ---- Stage 1: Builder ----
FROM rust:1-slim-bookworm AS builder

# sqlx / TLS build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy the workspace manifests and crate sources.
COPY Cargo.toml Cargo.lock ./
COPY crates ./crates
COPY apps ./apps
COPY migrations ./migrations

RUN cargo build --release

# ---- Stage 2: Runtime ----
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The server binary lands here once Phase 4C adds the apps/server bin target.
COPY --from=builder /build/target/release/server /usr/local/bin/server

EXPOSE 8080
CMD ["server"]
