# ==============================================================================
# Stage 1: Builder
# ==============================================================================
FROM rust:1.95-slim AS builder

WORKDIR /app

# Install build deps for sqlx (OpenSSL, pkg-config)
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace manifests first for dependency caching
COPY Cargo.toml Cargo.lock ./
COPY crates/domain/Cargo.toml crates/domain/Cargo.toml
COPY crates/db/Cargo.toml crates/db/Cargo.toml
COPY crates/api/Cargo.toml crates/api/Cargo.toml
COPY apps/server/Cargo.toml apps/server/Cargo.toml

# Create dummy src files to cache dependency compilation
RUN mkdir -p crates/domain/src crates/db/src crates/api/src apps/server/src && \
    echo "pub fn _dummy() {}" > crates/domain/src/lib.rs && \
    echo "pub fn _dummy() {}" > crates/db/src/lib.rs && \
    echo "pub fn _dummy() {}" > crates/api/src/lib.rs && \
    echo "fn main() {}" > apps/server/src/main.rs

# Enable sqlx offline mode for container builds (no live DB needed)
ENV SQLX_OFFLINE=true

RUN cargo build --release --bin ghost-server || true

# Copy real source code
COPY crates/ crates/
COPY apps/ apps/
COPY migrations/ migrations/

# Touch to invalidate cached dummy files
RUN touch crates/domain/src/lib.rs crates/db/src/lib.rs crates/api/src/lib.rs apps/server/src/main.rs

RUN cargo build --release --bin ghost-server

# ==============================================================================
# Stage 2: Runtime
# ==============================================================================
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/ghost-server /usr/local/bin/ghost-server

EXPOSE 8080

CMD ["ghost-server"]
