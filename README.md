# Ghost-Companion
The AI Ghost Companion is a minimalist chat-based assistant for Destiny 2. It combines the Bungie.net API with an AI language model to answer questions in real time about quests, activities, vendors, lore, and even manage your Guardian’s gear—all through a simple conversational interface.

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

## Environment Variables

Export the variables required for Ghost-Companion and Ollama:

```bash
export BUNGIE_API_KEY="your_api_key"
export BUNGIE_APP_NAME="Ghost-Companion"
export BUNGIE_APP_VERSION="1.0"
export BUNGIE_APP_URL="https://example.com"
export OLLAMA_MODEL="llama2"
export OLLAMA_HOST="http://localhost:11434"
```

## Running the Server

With the environment variables above set, start the FastAPI server using

```bash
uvicorn server:app --reload
```

Then send chat messages with ``curl``:

```bash
curl -X POST http://localhost:8000/chat \
     -H 'Content-Type: application/json' \
     -d '{"message": "Hello"}'
```

## Example Conversation

```text
Guardian: What activities are available this week?
Ghost: Nightfall, Crucible, and Gambit are featured with increased rewards.

Guardian: Can you equip my highest power weapon?
Ghost: Equipped your 1810 power weapon from inventory.
```

