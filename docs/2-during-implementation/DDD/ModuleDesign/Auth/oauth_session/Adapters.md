# Ports & Adapters: OAuth Session

## Secondary Driven Ports

**`trait DestinyOAuthClient`**
- **Method**: `refresh_token(refresh_token: String) -> Result<TokenResponse, AuthError>`
- **Real Adapter**: A specialized `reqwest` module hitting Bungie's auth endpoint.

**`trait TokenStorage`**
- **Method**: `save_session(user_id: i64, tokens: TokenPayload)`
- **Method**: `get_active_session(user_id: i64) -> Session`
- **Real Adapter**: The `sqlx` module inside `crates/db` interacting with PostgreSQL, encrypting the token before writing.
