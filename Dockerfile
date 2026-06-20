# Production image for the Ghost Companion backend (apps/server).
#
# The workspace crates use edition 2024 (Rust >= 1.85), so we track the latest
# stable 1.x rather than the roadmap's 1.78.

# ---- Stage 1: Builder ----
FROM rust:1-slim-bookworm AS builder

# C toolchain + pkg-config for native deps (ring/rustls, bundled libsqlite3-sys).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy the workspace manifests and the crates the server needs.
COPY Cargo.toml Cargo.lock ./
COPY crates ./crates
COPY apps/server ./apps/server
COPY migrations ./migrations

# Build only the server binary (and its deps), pinned to Cargo.lock.
RUN cargo build --release --locked -p server

# ---- Stage 2: Runtime ----
FROM debian:bookworm-slim AS runtime

# CA roots for outbound HTTPS (Bungie / LLM). TLS is rustls, so no OpenSSL needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/target/release/server /usr/local/bin/server

EXPOSE 8080
CMD ["server"]
