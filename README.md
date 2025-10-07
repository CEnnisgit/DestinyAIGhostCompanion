# Ghost-Companion
The AI Ghost Companion is a minimalist chat-based assistant for Destiny 2. It combines the Bungie.net API with an AI language model to answer questions in real time about quests, activities, vendors, lore, and even manage your Guardian’s gear—all through a simple conversational interface.

## Quick Start
1. Launch both the FastAPI backend and the React frontend with the convenience script:
   ```bash
   python launch.py
   ```
   The launcher exits cleanly on <kbd>Ctrl+C</kbd> and exposes a few optional flags:
   - `python launch.py --backend-only` – start only the API server.
   - `python launch.py --frontend-only` – start only the React development server.

   The launcher walks through the remaining setup steps for you:
   - Installs Python dependencies from `requirements.txt` via `pip`.
   - Verifies that **Node.js** and **npm** are available, guiding you to install them if they are missing.
   - Runs `npm install` the first time you launch (or whenever `frontend/node_modules/` is absent).
   - Confirms that the `ollama` CLI is installed, starts `ollama serve` if it is not already running, and pulls the default `llama3` model.
   - Loads required environment variables from `.env`, prompting you to supply any missing Bungie or Ollama credentials (with sensible defaults where possible).

   If a prerequisite is missing, the launcher prints a clear message describing what to install and where to find it before exiting.

The root endpoint (`GET /`) returns usage instructions once the API is running.

Execute the backend test suite with:

```bash
pytest
```

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
Environment variables are loaded automatically from a `.env` file via
[`python-dotenv`](https://github.com/theskumar/python-dotenv). Fill in the `.env` file with your own values for the variables below,
or export them directly. The Bungie OAuth flow requires the redirect URI to match the one you configure in the Bungie developer portal.

```dotenv
# .env
BUNGIE_API_KEY=your_api_key
BUNGIE_REDIRECT_URI=http://localhost:8000/oauth/callback
```

```bash
export BUNGIE_API_KEY="your_api_key"
export BUNGIE_CLIENT_ID="your_oauth_client_id"
export BUNGIE_CLIENT_SECRET="your_oauth_client_secret"
export BUNGIE_REDIRECT_URI="http://localhost:8000/oauth/callback"
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

## Testing Stubs

For the unit tests this project provides lightweight stand-ins for the
third-party `requests` and `responses` libraries.  These modules live under
`tests/stubs/` and intentionally raise `NotImplementedError` for any real
network operations.  They exist purely to support the test suite and should
not be used in production deployments.

## Packaging into an Executable

You can ship the launcher as a self-contained desktop executable using [PyInstaller](https://pyinstaller.org/). The repository includes a ready-made spec file and helper script that bundle the backend, the React frontend, and supporting assets.

1. Install PyInstaller in your environment:
   ```bash
   pip install pyinstaller
   ```
2. Make sure dependencies are primed before packaging (this mirrors what `launch.py` does at runtime):
   ```bash
   python -m pip install -r requirements.txt
   (cd frontend && npm install)
   ```
3. Build the executable with the custom spec file so the `frontend/` directory is copied alongside the launcher:
   ```bash
   pyinstaller --clean --noconfirm ghost_companion.spec
   ```
4. The compiled app will live in `dist/GhostCompanionLauncher/`. Double-click `GhostCompanionLauncher.exe` (on Windows) or run it from the terminal to start the orchestrated backend, frontend, and Ollama services. The executable bundles the Python runtime, backend dependencies, and the React `frontend/` directory, so launching the `.exe` is the only action required to bring the stack online (it still expects Node.js, npm, and Ollama to be installed on the machine).

When the packaged launcher runs, it creates/updates a `.env` file next to the executable and prompts for any missing Bungie or Ollama credentials. Subsequent launches reuse the saved values, automatically restart Ollama if needed, and open the FastAPI backend from inside the bundle while delegating `npm start` to your installed Node toolchain.

### Optional helper script (Windows)

The repository also provides `build_exe.bat`, which automates the commands above. Run it from `cmd.exe` or PowerShell:

```bat
build_exe.bat
```

The batch file refreshes Python packages, ensures frontend dependencies are installed, and invokes PyInstaller with the supplied spec file. Adjust `ghost_companion.spec` if you need to bundle additional assets (for example, prebuilt environment files or extra models).

## Running the Server
With the environment variables above set, use the launcher or start the FastAPI server manually:
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
