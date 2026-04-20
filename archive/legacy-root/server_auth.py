"""JWT helpers and password hashing for the backend.

Responsibilities
- Create and validate short-lived JWTs for the web/desktop UI.
- Hash and verify user passwords (bcrypt) for server-managed accounts.
- Provide a small helper to resolve a DB user row from an Authorization token.

Environment
- `JWT_SECRET` (required in production), `JWT_TTL_SECONDS` for token lifetime.

Note: For OAuth with Bungie, this module is used to mint a JWT that the UI
stores locally; Bungie OAuth tokens themselves are stored in the DB via
`server_db.py` and associated with the user record.
"""

from __future__ import annotations

import os
import time
from typing import Optional

import jwt
import bcrypt
from passlib.context import CryptContext

from server_db import get_user_by_id, get_user_by_email


JWT_SECRET = os.getenv("JWT_SECRET", "ghost-companion-dev-secret-change-me-32bytes")
JWT_ALG = "HS256"
JWT_TTL = int(os.getenv("JWT_TTL_SECONDS", "86400"))

# Use bcrypt directly to avoid passlib compatibility issues
def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a 72-byte safety truncation."""
    # Truncate password to 72 bytes for bcrypt compatibility
    truncated_password = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(truncated_password, salt)
    return hashed.decode('utf-8')

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if `password` matches `password_hash` (bcrypt)."""
    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        truncated_password = password.encode('utf-8')[:72]
        return bcrypt.checkpw(truncated_password, password_hash.encode('utf-8'))
    except Exception:
        return False


def create_jwt(user_id: int, email: str) -> str:
    """Mint a signed JWT containing subject (`sub`) and email claims."""
    now = int(time.time())
    payload = {"sub": str(user_id), "email": email, "iat": now, "exp": now + JWT_TTL}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and verify a JWT; returns claims or None on failure."""
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return data
    except Exception:
        return None


def get_user_from_token(token: str):
    """Return DB user row for a valid JWT or None if invalid/expired."""
    data = decode_jwt(token)
    if not data:
        return None
    try:
        uid = int(data.get("sub", "0"))
    except Exception:
        return None
    return get_user_by_id(uid)
