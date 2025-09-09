# Ghost-Companion
The AI Ghost Companion is a minimalist chat-based assistant for Destiny 2. It combines the Bungie.net API with an AI language model to answer questions in real time about quests, activities, vendors, lore, and even manage your Guardian’s gear—all through a simple conversational interface.

## Quick Start
**Note:** Set the `BUNGIE_API_KEY` environment variable before running the examples below.
```python
from ghost.assistant import GhostAssistant

assistant = GhostAssistant()
print(assistant.chat("Equip Sunshot on my Hunter"))
# -> "Sunshot is in your vault. Equip it? (yes/no)"

if input().strip().lower() == "yes":
    print(assistant.chat("yes"))
    # -> "Equipped Sunshot on your Hunter."
```

## Ollama Setup

### Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Download a Model
```bash
ollama pull llama2
```

### Start the Local Server
```bash
ollama serve
```

## OAuth Setup
1. [Register a Bungie application](https://www.bungie.net/en/Application) and note your **client ID** and **client secret**.
2. Set the credentials as environment variables (`BUNGIE_CLIENT_ID` and `BUNGIE_CLIENT_SECRET`).
3. Generate an authorization link and exchange the returned code for tokens:
```python
import os
from ghost import auth

url = auth.get_authorization_url(
    os.environ["BUNGIE_CLIENT_ID"], scopes=["ReadDestinyInventoryAndVault"]
)
print("Visit:", url)
code = input("Paste authorization code: ")
tokens = auth.exchange_code_for_token(
    os.environ["BUNGIE_CLIENT_ID"], os.environ["BUNGIE_CLIENT_SECRET"], code
)
auth.save_tokens(tokens)  # encrypted storage
```
4. Provide the tokens to `BungieClient` or `GhostAssistant`:
```python
from ghost.bungie import BungieClient

client = BungieClient(os.environ["BUNGIE_API_KEY"])
client.authenticate_user(auth.load_tokens())
```

Tokens are stored encrypted on disk at `~/.ghost_tokens` (or the path
specified by `GHOST_TOKEN_FILE`). The encryption key is derived from the
`GHOST_TOKEN_KEY` environment variable.

## Environment Variables
Fill in the `.env` file with your own values for the variables below, or export them directly:

```dotenv
# .env
BUNGIE_API_KEY=your_api_key
```

```bash
export BUNGIE_API_KEY="your_api_key"
export BUNGIE_CLIENT_ID="your_oauth_client_id"
export BUNGIE_CLIENT_SECRET="your_oauth_client_secret"
export BUNGIE_MANIFEST_TTL="3600"     # optional cache TTL in seconds
export BUNGIE_PROFILE_TTL="60"        # optional cache TTL in seconds
export BUNGIE_APP_NAME="Ghost-Companion"
export BUNGIE_APP_VERSION="1.0"
export BUNGIE_APP_URL="https://example.com"
export OLLAMA_MODEL="llama2"
export OLLAMA_HOST="http://localhost:11434"
export GHOST_TOKEN_KEY="change_me"       # key for encrypted token storage
# export GHOST_TOKEN_FILE="/tmp/tokens"   # optional custom path
```

## Running the Server
With the environment variables above set, start the FastAPI server using:
```bash
uvicorn server:app --reload
```
Then send chat messages with `curl`:
```bash
curl -X POST http://localhost:8000/chat \
     -H 'Content-Type: application/json' \
     -d '{"message": "Hello"}'
```

## Bungie API Examples
```python
import os
from ghost.bungie import BungieClient

client = BungieClient(os.environ["BUNGIE_API_KEY"], access_token=tokens["access_token"])

# Vendor query
vendor = client.get_vendor(2, "MEMBERSHIP_ID", "CHARACTER_ID", "VENDOR_HASH", components="402")

# Transfer an item to a character
client.transfer_item(2, "CHARACTER_ID", "ITEM_INSTANCE_ID", item_reference_hash=123456)

# Fireteam lookup
fireteams = client.fireteam_search(platform=2, activity_type=5, date_range=0, slot_filter=0, page=0)
```

## Example Conversation
```text
Guardian: What activities are available this week?
Ghost: Nightfall, Crucible, and Gambit are featured with increased rewards.

Guardian: Can you equip my highest power weapon?
Ghost: Equipped your 1810 power weapon from inventory.
```
