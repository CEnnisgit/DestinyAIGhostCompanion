# Ghost-Companion
The AI Ghost Companion is a minimalist chat-based assistant for Destiny 2. It combines the Bungie.net API with an AI language model to answer questions in real time about quests, activities, vendors, lore, and even manage your Guardian’s gear—all through a simple conversational interface.

## Installation

Use Python 3.11 and Node.js 20. Install the API in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload
```

Fill in the local `.env` with your provider credentials. Desktop and voice
features use `requirements-desktop.txt`. Fine-tuning and local model inference
use `requirements-finetune.txt`, including accelerate and bitsandbytes for
8-bit loading and automatic device placement; compatible GPU drivers and model
access are required. Dataset generation uses only the standard library.

The React 18 frontend uses Vite:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Development runs on port 3000; `npm start` is an alias. Set `VITE_API_URL` in
`frontend/.env` to override `http://127.0.0.1:8000`. This build-time value is
shared by all API calls, including speech and streaming chat. No proxy is needed.
`npm run build` outputs `frontend/build`, as expected by the backend and both
PyInstaller specs. `npm run preview` previews the production build.

Install developer dependencies and run checks with:

```bash
python -m pip install -r requirements-dev.txt
env -u BUNGIE_API_KEY -u XAI_API_KEY python -m pytest -q tests
pip-audit -r requirements.txt
(cd frontend && npm audit --omit=dev --audit-level=high && npm run build)
```

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
python -m pytest -q tests
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

## Desktop App (No Browser)

Run the standalone desktop app with real-time voice in Python:

```bash
pip install -r requirements-desktop.txt
python run_desktop.py
```

Voice setup:
- STT (speech-to-text): set `OPENAI_API_KEY` to use Whisper API (default), or install `faster-whisper` and set `STT_PROVIDER=local` for on-device.
- TTS (text-to-speech): set `ELEVEN_API_KEY` and `ELEVEN_VOICE_ID` to use ElevenLabs, or it falls back to offline `pyttsx3` on Windows.
- Personality: pick from the Persona dropdown (e.g., `destiny_ghost`, `odst_vergil`). You can set default via `PERSONA=destiny_ghost`.

Tip: `run_desktop.py` bootstraps dependencies automatically. If a required package is missing, it installs it into the same interpreter (`sys.executable`) and restarts the import.

Build a production EXE without the web UI:

```bat
build_exe.bat --desktop
```
The EXE appears under `dist/GhostCompanion/`.

## Production Build & Installer

Goals:
- Small footprint, one-click install, Start Menu/desktop shortcuts, clean uninstall.
- Clear first-run setup for API keys and voice providers.
- Crash logs + stable updates.

Recommended approach (Windows):
- Build the desktop app in onefolder mode with PyInstaller: `build_exe.bat --desktop`
- Create a signed installer with Inno Setup using `installer/ghost_companion.iss`.

Size optimization tactics:
- Exclude heavy optional modules in `ghost_desktop.spec` (local STT stack: faster-whisper, onnxruntime, etc.). The app defaults to cloud STT when `OPENAI_API_KEY` is present.
- Keep Qt minimal: avoid WebEngine and unused Qt modules; current UI uses only core widgets.
- Enable UPX compression (already enabled in spec); install UPX for best results.
- Avoid bundling dev assets and logs.

Installer steps:
1) Build EXE folder: `build_exe.bat --desktop` (outputs `dist/GhostCompanion`)
2) Open `installer/ghost_companion.iss` in Inno Setup and compile
3) Optionally code sign the installer and EXE (recommended for Windows SmartScreen):
   - Acquire a code signing cert (EV ideally)
   - `signtool sign /fd SHA256 /a dist\GhostCompanion\GhostCompanion.exe`
   - `signtool sign /fd SHA256 /a dist\installer\GhostCompanion-Setup-<ver>.exe`

Enterprise polish checklist:
- Auto-update: add Squirrel.Windows or custom “check for updates” fetching latest installer.
- First-run wizard: detect missing `OPENAI_API_KEY` or `ELEVEN_API_KEY` and prompt to save.
- Logs: write to `%LOCALAPPDATA%/GhostCompanion/logs`.
- Privacy: toggle analytics off by default; document network calls and data handling.
- EULA and versioned change log.

Troubleshooting environment (PySide6):
- Ensure you install packages into the same interpreter you run:
  - `python -m pip install -r requirements-desktop.txt`
  - `python -c "import sys; print(sys.executable); import PySide6; print(PySide6.__file__)"`
- If multiple Pythons are present, use the launcher: `py -3.12 -m pip install -r requirements-desktop.txt` and `py -3.12 run_desktop.py`.

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

## AI and Bungie settings

Open **Settings** in the main UI. Select xAI, OpenAI, Anthropic, an OpenAI-compatible endpoint, or Ollama/local; enter the model, optional HTTP/HTTPS base URL, and API key. Compatible endpoints require a base URL (including any `/v1` prefix) and model. Use **Test connection** to make a small request.

Settings live only in this device's browser localStorage and are sent to the configured API server with each request. Use a trusted server and HTTPS. AI keys are request-scoped and never written to the server database, disk, or environment. `/chat`, `/chat/stream`, and `/ai/test` use `X-AI-Provider`, `X-AI-Model`, `X-AI-Key`, and optional `X-AI-Base-URL`. The stream route sends buffered text chunks; upstream streaming is optional and currently unused.

Shared `XAI_API_KEY` is ignored unless `GHOST_ALLOW_ENV_AI_KEY=1` explicitly enables the development fallback. No opt-in flags are enabled by default. Copy `.env.example` to your own untracked `.env` and fill only the values you need.

Bungie uses a public client with PKCE/state by default, without a secret. Settings also accepts the device Bungie API key and client ID. Hosted servers can supply `BUNGIE_API_KEY` and `BUNGIE_CLIENT_ID`. Confidential token proxy mode requires both `GHOST_BUNGIE_TOKEN_PROXY=1` and a server-only `BUNGIE_CLIENT_SECRET`.

See [Bungie registration, permissions, redirect URIs, and deployment limitations](docs/BUNGIE_SETUP.md), including the need to verify Bungie's PKCE enforcement before release.

## Bungie API Direct Calls

All public methods on `BungieClient` are now callable directly via chat for complete coverage of the Bungie API. Use an explicit trigger with simple key=value args or JSON.

- List available methods:
  - `bungie help`
  - `api help`
- Call with key=value:
  - `bungie get_profile membership_type=2 destiny_membership_id=4611686018429783296 components=[100,200]`
- Call with JSON:
  - `api get_entity {"entity_type":"DestinyInventoryItemDefinition","hash_id":1274330687}`
- Alternate trigger:
  - `call bungie equip_item item_id=6917529027640862394 character_id=2305843009264962724 membership_type=2`

Notes:
- Values auto-coerce common types: integers, floats, true/false, null/none, and Python-style lists/dicts.
- OAuth is required for endpoints that need authorization; provide tokens in the request context or authenticate first.

## Voice Troubleshooting

If microphone or text-to-speech isn’t working, run a quick diagnostic in Python:

```python
from ghost.voice import diagnose_audio
print(diagnose_audio())
```

For automated debugging (and CI/automation), use the helper script which prints
structured JSON, including detected PortAudio devices:

```bash
python tools/audio_diag.py
```

When the FastAPI server is running you can also hit the new endpoint to capture
diagnostics remotely:

```bash
curl http://127.0.0.1:8000/diagnostics/audio | jq
```

If the embedded browser cannot access your microphone (for example, when running
inside the desktop Qt shell), the backend can now capture audio directly via
PortAudio. Trigger a short capture + transcription manually with:

```bash
curl -X POST http://127.0.0.1:8000/stt/local -H "Content-Type: application/json" -d "{\"device_index\": 1, \"duration\": 5}"
```

In the UI, microphone entries marked “(desktop)” route through the same API so
the Ghost can still listen even when `navigator.mediaDevices` is unavailable.

Common fixes (Windows):
- Install PortAudio + sounddevice: `python -m pip install sounddevice`
- Install offline TTS: `python -m pip install pyttsx3`
- Or configure ElevenLabs TTS by setting `ELEVEN_API_KEY` and `ELEVEN_VOICE_ID`
- For STT via OpenAI Whisper, set `OPENAI_API_KEY` (or set `STT_PROVIDER=local` to use `faster-whisper`).

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

## GitHub Release Bundles (clean output)
- Build and stage downloadable zips without touching your dev setup:
  ```bash
  python tools/build_release.py --version 0.1.0 --overwrite
  ```
- Outputs land in `release/artifacts/v0.1.0/`:
  - `GhostCompanionLauncher-v0.1.0.zip` (backend + web UI)
  - `GhostCompanion-v0.1.0.zip` (desktop app)
  - `SHA256SUMS.txt` and `RELEASE-NOTES.txt`
- Use `--launcher-only` or `--desktop-only` to package a single target; add `--skip-build` to reuse existing `dist/` outputs.
- Upload the zips to a GitHub Release; the `.env` file is intentionally excluded so credentials stay local.

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
