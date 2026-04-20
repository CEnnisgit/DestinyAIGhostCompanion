# Bounded Context: Auth

> **Core Responsibility:** Managing the Bungie.net OAuth2 Lifecycle securely.

This module houses the vertical features associated with session authentication.

## Defined Feature Slices
1. **[oauth_session](./oauth_session/)**: Handles the Bearer / Refresh token loops safely, storing them in the Postgres DB to prevent leakage.
