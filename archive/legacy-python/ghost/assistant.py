"""High level assistant orchestrating Bungie and model clients.

Supports per-request provider routing between Grok, Ollama, and a local
fine-tuned model.
"""

from __future__ import annotations

import os
import re
from typing import Any
import time
import logging
import difflib

from . import auth
from .bungie import BungieClient, BungieAPIError
from .grok import GrokClient
from .ollama import OllamaClient
from .finetune import FineTuneClient
from . import personalities
from . import lore as lore_search
import requests as _requests


class GhostAssistant:
    """Orchestrates requests between Bungie and Ollama.

    The assistant performs a very small amount of intent detection. If the
    incoming message asks for Destiny player information (``player <name>``)
    the Bungie API is queried and the results are fed into the language
    model. Otherwise the message is passed directly to the model.
    """

    def __init__(
        self,
        bungie_client: BungieClient | None = None,
        grok_client: GrokClient | None = None,
        ollama_client: OllamaClient | None = None,
        finetune_client: FineTuneClient | None = None,
        api_key: str | None = None,
    ) -> None:
        """Create a new assistant instance.

        Parameters
        ----------
        bungie_client:
            Optional preconfigured :class:`BungieClient` instance.
        grok_client:
            Optional client used for language model interactions.
        api_key:
            If ``None``, the key is read from the ``BUNGIE_API_KEY`` environment
            variable.
        """
        if bungie_client is None:
            key = api_key or os.getenv("BUNGIE_API_KEY", "")
            bungie_client = BungieClient(key)
        self.bungie = bungie_client
        # Store current tokens for handler methods (set from auth or per-request)
        self._current_tokens: dict | None = None
        if auth.STORED_TOKENS:
            # Apply any tokens loaded at import time and keep them available
            self.bungie.authenticate_user(auth.STORED_TOKENS)
            self._current_tokens = auth.STORED_TOKENS
        # Defer model client instantiation until used
        self._clients: dict[str, Any] = {}
        if grok_client is not None:
            self._clients["grok"] = grok_client
        if ollama_client is not None:
            self._clients["ollama"] = ollama_client
        if finetune_client is not None:
            self._clients["finetune"] = finetune_client
        # Track last resolved item for pronoun-based commands
        self._last_item: dict[str, Any] | None = None
        # Track last inventory location mentioned for context-aware transfers
        self._last_location: str | None = None
        # Bucket location cache: bucketHash -> ItemLocation enum value
        self._bucket_loc_cache: dict[int, int] = {}
        self._postmaster_bucket_cache: dict[int, bool] = {}
        # Pending confirmation for destructive actions
        self._pending_action: dict | None = None
        # Conversational context beyond items/locations
        self._last_vendor_hash: int | None = None
        self._last_trending: tuple[str, int] | None = None  # (category, page)
        self._last_activity_id: str | None = None
        # Common item name aliases to normalize frequent user phrasing/typos
        self._item_aliases: dict[str, str] = {
            "fore runner": "forerunner",
            "for runner": "forerunner",
            "last word": "the last word",
            "tlw": "the last word",
            "ace spades": "ace of spades",
            "sun shot": "sunshot",
        }

    def _get_client(self, provider: str) -> Any:
        """Return a model client keyed by provider string.

        Supports provider variants like ``"ollama:llama3"`` to select a
        specific Ollama model per conversation without changing global env.
        The cache key is the full provider string so different models are
        cached independently.
        """
        key = (provider or "").lower()
        if key in self._clients:
            return self._clients[key]
        base = key.split(":", 1)[0]
        if base == "grok":
            client = GrokClient()
        elif base == "ollama":
            # Optional model override: "ollama:<model>"
            model_override = None
            if ":" in key:
                model_override = key.split(":", 1)[1] or None
            client = OllamaClient(model=model_override)
        elif base == "finetune":
            client = FineTuneClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")
        self._clients[key] = client
        return client

    def _default_provider(self) -> str:
        # Prefer explicitly injected clients first (useful for tests)
        if "ollama" in self._clients:
            return "ollama"
        if "grok" in self._clients:
            return "grok"
        if "finetune" in self._clients:
            return "finetune"
        # Fall back to environment hints
        if os.getenv("OLLAMA_MODEL"):
            # Only prefer Ollama if the API appears reachable to avoid hard failures
            host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
            try:
                r = _requests.get(f"{host}/api/tags", timeout=1.0)
                if r.status_code == 200:
                    return "ollama"
            except Exception:
                pass
        if os.getenv("XAI_API_KEY"):
            return "grok"
        # Default to local fine-tuned wrapper
        return "finetune"

    def _get_destiny_membership(self) -> tuple[str, int] | None:
        """Get the Destiny membership ID and type from current authentication.

        Prefers per-request tokens if provided, but will also proceed when the
        underlying ``BungieClient`` already has an access token.
        """
        logger = logging.getLogger("ghost")
        try:
            logger.info(
                "[assistant] Resolving membership: has_tokens=%s has_access_token=%s",
                bool(self._current_tokens),
                bool(getattr(self.bungie, "access_token", None)),
            )
        except Exception:
            pass
        # If tokens already include membership details, prefer them
        if self._current_tokens and "membership_id" in self._current_tokens and "membership_type" in self._current_tokens:
            try:
                mid = str(self._current_tokens["membership_id"])
                mtype_raw = self._current_tokens["membership_type"]
                mtype = int(mtype_raw) if mtype_raw is not None else None
                valid_types = {1, 2, 3, 4, 5, 10}
                if mid and (mtype in valid_types):
                    logger.info("[assistant] Using membership from tokens (type=%s)", mtype)
                    return mid, mtype
                else:
                    logger.info("[assistant] Ignoring invalid membership_type from tokens: %s", mtype_raw)
            except Exception as e:
                logger.exception("[assistant] Error reading membership from tokens: %s", e)

        if not (self._current_tokens or getattr(self.bungie, "access_token", None)):
            logger.info("[assistant] No tokens or access token available")
            return None

        try:
            memberships = self.bungie.get_memberships_for_current_user()
            logger.info(f"[assistant] Memberships response: {memberships}")
            resp = memberships.get("Response", {}) if isinstance(memberships, dict) else {}
            destiny_memberships = resp.get("destinyMemberships", []) or []
            primary = resp.get("primaryMembershipId")
            if destiny_memberships:
                logger.info("[assistant] Found %s memberships; primary=%s", len(destiny_memberships), primary)
                logger.info(f"[assistant] Destiny memberships: {destiny_memberships}")
                if primary:
                    for m in destiny_memberships:
                        if str(m.get("membershipId")) == str(primary):
                            return m.get("membershipId"), m.get("membershipType")
                # fallback to first
                m = destiny_memberships[0]
                return m.get("membershipId"), m.get("membershipType")
        except Exception:
            pass

        # Last resort: if we only have a Bungie.net user id, resolve linked Destiny memberships
        try:
            if self._current_tokens and self._current_tokens.get("membership_id") and not self._current_tokens.get("membership_type"):
                logger.info("[assistant] Falling back to GetMembershipsById using Bungie user id")
                bungie_user_id = str(self._current_tokens["membership_id"])
                data = self.bungie.get_memberships_by_id(bungie_user_id, 254)  # 254 = BungieNext
                resp = data.get("Response", {}) if isinstance(data, dict) else {}
                dms = resp.get("destinyMemberships", []) or []
                if dms:
                    m = dms[0]
                    return m.get("membershipId"), m.get("membershipType")
        except Exception:
            pass
        return None

    # Ensure consistent, in-character responses across providers
    def _postprocess_response(self, text: str, persona: str | None) -> str:
        import re as _re
        msg = (text or "").strip()
        lower = msg.lower()
        # Remove common disclaimers that break immersion
        bad_starts = (
            "i'm not a ghost",
            "i am not a ghost",
            "as an ai language model",
            "as an ai,",
            "i cannot ",
            "i'm just an ai",
        )
        for bs in bad_starts:
            if lower.startswith(bs):
                parts = _re.split(r"(?<=[.!?])\s+", msg)
                msg = " ".join(parts[1:]).lstrip() or msg
                lower = msg.lower()
                break
        # Ensure we address the user as Guardian
        if not lower.startswith("guardian"):
            msg = f"Guardian, {msg}" if msg else "Guardian."
        # Keep it concise: trim to ~3 sentences
        sentences = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", msg) if s.strip()]
        if len(sentences) > 3:
            msg = " ".join(sentences[:3])
        return msg

    # ---------------------------------------------------------------
    # Bungie generic dispatcher helpers
    def _bungie_public_methods(self) -> dict[str, Any]:
        """Return mapping of public BungieClient methods available for dispatch.

        Filters out private/dunder methods and attributes that are not callables.
        """
        methods: dict[str, Any] = {}
        for name in dir(self.bungie):
            if name.startswith("_"):
                continue
            try:
                attr = getattr(self.bungie, name)
            except Exception:
                continue
            if callable(attr):
                methods[name] = attr
        return methods

    def _parse_args_kwargs(self, args_str: str) -> tuple[list[Any], dict[str, Any]]:
        """Parse a lightweight args string into (args, kwargs).

        Accepted forms:
        - JSON object -> kwargs
        - JSON array  -> args
        - key=value pairs separated by spaces or commas
          Values can be quoted strings, numbers, true/false, null/none.
        - function-style: method(key=value, ...) or method(v1, v2, key=value)
        """
        import json as _json
        import ast as _ast
        text = args_str.strip()
        if not text:
            return [], {}
        # If function-style with surrounding parentheses, drop them
        if (text.startswith("(") and text.endswith(")")):
            text = text[1:-1].strip()
        # Try JSON first
        if text.startswith("{") or text.startswith("["):
            try:
                data = _json.loads(text)
                if isinstance(data, dict):
                    return [], data
                if isinstance(data, list):
                    return data, {}
            except Exception:
                pass
        # Split on commas or spaces but keep quoted substrings intact
        tokens: list[str] = []
        buf = ''
        in_quote: str | None = None
        i = 0
        while i < len(text):
            ch = text[i]
            if in_quote:
                if ch == in_quote:
                    in_quote = None
                elif ch == "\\" and i + 1 < len(text):
                    # keep escaped char
                    buf += text[i+1]
                    i += 2
                    continue
                else:
                    buf += ch
            else:
                if ch in ('"', "'"):
                    in_quote = ch
                elif ch in [',', ' ']:
                    if buf:
                        tokens.append(buf)
                        buf = ''
                else:
                    buf += ch
            i += 1
        if buf:
            tokens.append(buf)
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        def _coerce(val: str) -> Any:
            low = val.lower()
            if low in ("true", "false"):
                return low == "true"
            if low in ("null", "none"):
                return None
            # Try int
            try:
                if low.startswith("0x"):
                    return int(val, 16)
                return int(val)
            except Exception:
                pass
            # Try float
            try:
                return float(val)
            except Exception:
                pass
            # Try Python literal for simple lists/dicts
            try:
                lit = _ast.literal_eval(val)
                return lit
            except Exception:
                pass
            return val
        for tok in tokens:
            if not tok:
                continue
            if "=" in tok:
                k, v = tok.split("=", 1)
                k = k.strip()
                v = v.strip()
                kwargs[k] = _coerce(v)
            else:
                args.append(_coerce(tok))
        return args, kwargs

    def _maybe_dispatch_bungie_call(self, message: str) -> str | None:
        """If message looks like an explicit Bungie API call, execute it.

        Triggers:
        - Starts with: "bungie", "api", or "call bungie"
        - Contains: "bungie help" or "api help" to list methods
        Syntax examples:
        - "bungie get_profile membership_type=2 destiny_membership_id=123 components=[100,200]"
        - "api get_entity {\"entity_type\": \"DestinyInventoryItemDefinition\", \"hash_id\": 1274330687}"
        - "call bungie equip_item item_id=... character_id=... membership_type=2"
        """
        text = message.strip()
        low = text.lower()
        if low.startswith("bungie help") or low.startswith("api help"):
            names = sorted(self._bungie_public_methods().keys())
            shown = ", ".join(names)
            return f"Guardian, I can call any of these Bungie methods: {shown}. Use: bungie <method> key=value ... or JSON."
        # Determine trigger and extract method + args
        method_name = None
        args_str = ""
        if low.startswith("bungie "):
            parts = text.split(None, 2)
            if len(parts) >= 2:
                method_name = parts[1]
                args_str = parts[2] if len(parts) >= 3 else ""
        elif low.startswith("api "):
            parts = text.split(None, 2)
            if len(parts) >= 2:
                method_name = parts[1]
                args_str = parts[2] if len(parts) >= 3 else ""
        elif low.startswith("call bungie "):
            parts = text.split(None, 3)
            if len(parts) >= 3:
                method_name = parts[2]
                args_str = parts[3] if len(parts) >= 4 else ""
        else:
            return None

        if not method_name:
            return "Guardian, specify a method name. Try: bungie help"
        methods = self._bungie_public_methods()
        target = methods.get(method_name)
        if target is None:
            # fuzzy match to suggest
            try:
                import difflib as _difflib
                close = _difflib.get_close_matches(method_name, list(methods.keys()), n=3)
                if close:
                    return f"I couldn't find '{method_name}'. Did you mean: {', '.join(close)}?"
            except Exception:
                pass
            return f"I couldn't find a Bungie method named '{method_name}'. Try 'bungie help'."

        args, kwargs = self._parse_args_kwargs(args_str)
        try:
            result = target(*args, **kwargs)
        except BungieAPIError as e:
            return f"Bungie API error: {e}"
        except Exception as e:
            return f"Error calling {method_name}: {e}"
        # Return concise JSON
        try:
            import json as _json
            return _json.dumps(result)
        except Exception:
            return str(result)

    # ------------------------------------------------------------------
    def chat(self, message: str, provider: str | None = None, tokens: dict | None = None, persona: str | None = None) -> str:
        """Return a reply for ``message``.

        When the message matches ``player <name>`` the Bungie ``search_destiny_player``
        endpoint is invoked and the resulting payload is included in the prompt
        sent to the language model.
        """
        self._current_tokens = tokens
        if tokens:
            try:
                self.bungie.authenticate_user(tokens)
            except Exception:
                pass

        model_provider = (provider or self._default_provider()).lower()
        client = self._get_client(model_provider)

        # Explicit Bungie API call support before other handlers
        # Examples:
        #  - "bungie get_profile membership_type=2 destiny_membership_id=123 components=[100,200]"
        #  - "api get_entity {\"entity_type\": \"DestinyInventoryItemDefinition\", \"hash_id\": 1274330687}"
        #  - "call bungie equip_item item_id=... character_id=... membership_type=2"
        try:
            _maybe = self._maybe_dispatch_bungie_call(message)
            if _maybe is not None:
                return _maybe
        except Exception:
            pass

        def send_with_system(system_prompt: str, user_prompt: str) -> str:
            try:
                if isinstance(client, OllamaClient):
                    combined = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
                    result = client.generate(combined)  # type: ignore[no-any-return]
                    return self._postprocess_response(result, persona)
            except Exception:
                pass
            if hasattr(client, "generate_with_system"):
                result = client.generate_with_system(system_prompt, user_prompt)  # type: ignore[no-any-return]
                return self._postprocess_response(result, persona)
            combined = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
            result = client.generate(combined)  # type: ignore[no-any-return]
            return self._postprocess_response(result, persona)

        

        # Simple greeting
        if re.match(r"^\s*(hi|hello|hey|hiya|yo|greetings)\b", message, re.IGNORECASE):
            return "Guardian, hello. How can I assist?"

        # Quick season response
        if "season" in message.lower():
            return "Ah, my Guardian! We're currently in Season of the Wish - the season of wishes granted and mysteries revealed. What adventures shall we pursue in this magical time?"

        match = re.search(r"player\s+(\w+)", message, flags=re.IGNORECASE)
        if match:
            name = match.group(1)
            data: Any = self.bungie.search_destiny_player(0, name)
            
            system_prompt = personalities.get_prompt(persona) or (
                "You are the Ghost from Destiny 2. Respond briefly in character. "
                "Always address the user as 'Guardian' (never traveler, player, friend, etc.). "
                "Use Bungie API data to answer accurately. Keep responses short and simple."
            )
            user_prompt = f"User asked about player {name}.\n\nBungie API search results: {data}\n\nRespond as the Ghost using this data."
            return send_with_system(system_prompt, user_prompt)

        # Multi-command handling: split on ",", "and", "then" for action verbs
        # Note: do NOT trigger on the word "vault" alone to avoid false positives like "vault of glass"
        lowered_all = message.lower()
        if any(v in lowered_all for v in ("transfer", "move", "equip")) and re.search(r"(,|\band\b|\bthen\b)", lowered_all):
            try:
                parts = re.split(r"\s*(?:,|\band\b|\bthen\b)\s*", message, flags=re.IGNORECASE)
            except Exception:
                parts = [message]
            results: list[str] = []
            for seg in parts:
                seg = seg.strip()
                if not seg:
                    continue
                out = self._handle_command_segment(seg)
                if out:
                    results.append(out)
            if results:
                return " ".join(results)

        # Handle inventory/vault listing commands
        # General vault query
        # Be forgiving of a common typo: "vaul" (missing trailing 't')
        general_vault_match = re.search(r'\bwhat\s+is\s+in\s+my\s+vaul[t]?\b', message, re.IGNORECASE)
        if general_vault_match:
            return self._handle_inventory_list("items", "vault")

        # General inventory query (accept common misspelling 'invetory')
        general_inventory_match = re.search(r'\bwhat\s+is\s+in\s+my\s+(?:inventory|invetory|inventorie)\b', message, re.IGNORECASE)
        if general_inventory_match:
            return self._handle_inventory_list("items", "inventory")

        vault_list_match = re.search(r'\b(?:what\s+)?(weapons|armor|gear|items)\s+(?:do\s+(?:i|you)\s+have\s*|are\s*)?(?:in\s*)?(?:my\s*)?vaul[t]?\b', message, re.IGNORECASE)
        if vault_list_match:
            item_type = vault_list_match.group(1).lower()
            return self._handle_inventory_list(item_type, "vault")

        inventory_list_match = re.search(r'\b(?:what\s+)?(weapons|armor|gear|items)\s+(?:do\s+(?:i|you)\s+have\s*|are\s*)?(?:in\s*)?(?:my\s*)?(?:inventory|invetory|inventorie)\b', message, re.IGNORECASE)
        if inventory_list_match:
            item_type = inventory_list_match.group(1).lower()
            return self._handle_inventory_list(item_type, "inventory")

        # Postmaster listing
        # Accepts variations: "postmaster", "post master", "mypost master", with optional class target
        postmaster_list_match = re.search(r"(?:what(?:'s|s)?\s+in\s+|what\s+is\s+in\s+|show\s+|list\s+)(?:my\s*)?post[-\s]?master(?:\s+on\s+my\s+(hunter|warlock|titan)s?)?\b", message, re.IGNORECASE)
        if postmaster_list_match:
            class_target = None
            if postmaster_list_match.lastindex and postmaster_list_match.group(1):
                class_target = postmaster_list_match.group(1).lower()
            return self._handle_postmaster_list(class_target)

        # Alternate phrasing: "my hunter's postmaster" / "my hunters post master"
        postmaster_possessive = re.search(r'my\s+(hunter|warlock|titan)[’\']?s?\s+post[-\s]?master\b', message, re.IGNORECASE)
        if postmaster_possessive:
            return self._handle_postmaster_list(postmaster_possessive.group(1).lower())

        # Handle item management commands
        lowered = message.lower()
        # Direct vault command: "vault my thorn", "vault the last word"
        direct_vault_match = re.search(r"\bvault\s+(?:my\s+|the\s+)?(.+)$", message, re.IGNORECASE)
        if direct_vault_match:
            item_name = self._canonicalize_item_query(direct_vault_match.group(1).strip())
            return self._handle_vault_item(item_name)
        # Equip <item>
        # Be tolerant of common typos and allow target class: eqip/equp/equi, and "on/to my <class>"
        equip_match = re.search(r"\b(?:can\s+you\s+)?e(?:qui?p|q?uip)\s+(?:my\s+)?(.+?)(?:\s+(?:on|to|ot)\s+(?:my\s+)?(hunter|warlock|titan|me)s?)?(?:\?)?$", message, re.IGNORECASE)
        if equip_match:
            item_name = self._canonicalize_item_query(equip_match.group(1).strip())
            class_target = (equip_match.group(2) or '').lower() if equip_match.lastindex and equip_match.lastindex >= 2 else None
            # Handle pronouns
            if item_name.lower() in {"it", "it back"} and self._last_item:
                item_name = self._last_item.get("name", item_name)
            return self._handle_equip_item(item_name, class_target)

        # Combined transfer + equip in one sentence
        if ("transfer" in lowered or "move" in lowered) and ("equip" in lowered):
            explicit_from_vault = ("from my vault" in lowered)
            # Prefer the name after 'equip' if present and not a pronoun
            m_equip = re.search(r'\bequip\s+(?:my\s+)?(.+)$', message, re.IGNORECASE)
            equip_name = m_equip.group(1).strip() if m_equip else None
            # Also extract name after 'transfer/move' (up to " from| to| and|$")
            m_transfer = re.search(r'(?:transfer|move)\s+(?:my\s+)?(.+?)(?=\s+(?:from|to|and)\b|$)', message, re.IGNORECASE)
            transfer_name = m_transfer.group(1).strip() if m_transfer else None
            # Resolve final item name
            item_name = None
            if equip_name and equip_name.lower() not in {"it", "it back"}:
                item_name = equip_name
            elif transfer_name:
                item_name = transfer_name
            elif equip_name:
                item_name = equip_name  # fallback even if pronoun
            if item_name:
                return self._handle_transfer_then_equip(item_name, explicit_from_vault)

        # Pronoun transfer before generic transfer
        pronoun_transfer = re.search(r'\b(?:transfer|move)\s+it\s+(?:back\s+)?(?:to\s+)?(?:my\s+)?(vault|inventory)\b', message, re.IGNORECASE)
        if pronoun_transfer:
            target = pronoun_transfer.group(1).lower()
            return self._handle_transfer_pronoun(target)

        # Transfer <item> to my vault
        transfer_to_vault_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?vault\b', message, re.IGNORECASE)
        if transfer_to_vault_match:
            item_name = transfer_to_vault_match.group(1).strip()
            return self._handle_vault_item(item_name)

        # Transfer <item> from my vault (to inventory implied)
        transfer_from_vault_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+vault\b', message, re.IGNORECASE)
        if transfer_from_vault_match:
            item_name = transfer_from_vault_match.group(1).strip()
            return self._handle_transfer_from_vault(item_name)

        # Transfer <item> to my inventory (from last location or vault implied)
        transfer_to_inventory_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?inventory\b', message, re.IGNORECASE)
        if transfer_to_inventory_match:
            item_name = transfer_to_inventory_match.group(1).strip()
            if self._last_location == "postmaster":
                return self._handle_pull_from_postmaster(item_name)
            else:
                return self._handle_transfer_from_vault(item_name)

        # Transfer <item> from my inventory (to vault implied)
        transfer_from_inventory_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+inventory\b', message, re.IGNORECASE)
        if transfer_from_inventory_match:
            item_name = transfer_from_inventory_match.group(1).strip()
            return self._handle_transfer_to_vault(item_name)

        # Transfer <item> from my <character> to my <character>
        transfer_between_characters_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+(hunter|warlock|titan)\s+to\s+my\s+(hunter|warlock|titan)\b', message, re.IGNORECASE)
        if transfer_between_characters_match:
            item_name = transfer_between_characters_match.group(1).strip()
            from_class = transfer_between_characters_match.group(2).lower()
            to_class = transfer_between_characters_match.group(3).lower()
            return self._handle_transfer_between_characters(item_name, from_class, to_class)

        # Transfer <item> to my <character>
        transfer_to_character_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?(hunter|warlock|titan|me)\b', message, re.IGNORECASE)
        if transfer_to_character_match:
            item_name = transfer_to_character_match.group(1).strip()
            target_class = transfer_to_character_match.group(2).lower()
            # Handle pronouns
            if item_name.lower() in {"it", "it back"} and self._last_item:
                item_name = self._last_item.get("name", item_name)
            return self._handle_transfer_to_character(item_name, target_class)

        # Transfer me <item>  -> treat as transfer <item> to my active character ("me")
        transfer_me_match = re.search(r"\b(?:transfer|move)\s+me\s+(?:my\s+)?(.+)$", message, re.IGNORECASE)
        if transfer_me_match:
            item_name = transfer_me_match.group(1).strip().rstrip('\\/?.!')
            if item_name.lower() in {"it", "it back"} and self._last_item:
                item_name = self._last_item.get("name", item_name)
            return self._handle_transfer_to_character(item_name, "me")

        # Pull <item> from my postmaster
        pull_from_postmaster_match = re.search(r'\b(?:pull|get|transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+post[-\s]?master\b', message, re.IGNORECASE)
        if pull_from_postmaster_match:
            item_name = pull_from_postmaster_match.group(1).strip()
            return self._handle_pull_from_postmaster(item_name)

        # Dismantle <item> (optionally from postmaster)
        dismantle_match = re.search(r'\bdismantle\s+(?:my\s+)?(.+?)(?:\s+from\s+my\s+post[-\s]?master)?$', message, re.IGNORECASE)
        if dismantle_match:
            item_name = dismantle_match.group(1).strip()
            return self._handle_dismantle_item(item_name)

        transfer_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?(?:inventory|invetory|inventorie)\b', message, re.IGNORECASE)
        if transfer_match:
            item_name = transfer_match.group(1).strip()
            return self._handle_transfer_from_vault(item_name)

        # Transfer <item> to my <class>
        transfer_to_char = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+to\s+my\s+(hunter|warlock|titan)\b', message, re.IGNORECASE)
        if transfer_to_char:
            item_name = transfer_to_char.group(1).strip()
            class_target = transfer_to_char.group(2).lower()
            return self._handle_transfer_to_character(item_name, class_target)

        # Transfer <item> to my vault
        transfer_to_vault_match = re.search(r'\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?vault\b', message, re.IGNORECASE)
        if transfer_to_vault_match:
            item_name = transfer_to_vault_match.group(1).strip()
            return self._handle_vault_item(item_name)

        # Pronoun: "transfer it (back) to my <vault|inventory>"
        pronoun_transfer = re.search(r'\b(?:transfer|move)\s+it\s+(?:back\s+)?(?:to\s+)?(?:my\s+)?(vault|inventory)\b', message, re.IGNORECASE)
        if pronoun_transfer:
            target = pronoun_transfer.group(1).lower()
            return self._handle_transfer_pronoun(target)

        vault_match = re.search(r'\bvault\s+(?:my\s+)?(.+)', message, re.IGNORECASE)
        if vault_match:
            item_name = vault_match.group(1).strip()
            return self._handle_vault_item(item_name)

        equip_match = re.search(r"\be(?:qui?p|q?uip)\s+(?:my\s+)?(.+?)(?:\s+(?:on|to|ot)\s+(?:my\s+)?(hunter|warlock|titan|me)s?)?$", message, re.IGNORECASE)
        if equip_match:
            item_name = equip_match.group(1).strip()
            class_target = (equip_match.group(2) or '').lower() if equip_match.lastindex and equip_match.lastindex >= 2 else None
            # Handle pronouns like "equip it to my titan"
            if item_name.lower() in {"it", "it back"} and self._last_item:
                item_name = self._last_item.get("name", item_name)
            return self._handle_equip_item(item_name, class_target)

        # Check for stats requests
        stats_match = re.search(r'\b(?:show\s+|what\s+are\s+|tell\s+me\s+)?(?:my\s+|the\s+|guardian.?s?\s+)?stats(?:\s+for\s+(.+))?', message, re.IGNORECASE)
        if stats_match:
            stat_type = stats_match.group(1) if stats_match.group(1) else None
            return self._handle_stats_request(stat_type, send_with_system, model_provider)

        # Check for vendor requests
        vendor_match = re.search(r'\b(?:show\s+)?(?:visit\s+)?vendors?(?:\s+in\s+(.+))?', message, re.IGNORECASE)
        if vendor_match:
            location = vendor_match.group(1) if vendor_match.group(1) else None
            return self._handle_vendor_request(location)

        # Check for milestone requests
        milestone_match = re.search(r'\b(?:show\s+|what\s+are\s+the\s+)?milestones?(?:\s+for\s+(.+))?', message, re.IGNORECASE)
        if milestone_match:
            milestone_type = milestone_match.group(1) if milestone_match.group(1) else None
            return self._handle_milestone_request(milestone_type)

        # Check for activity history requests
        activity_match = re.search(r'\b(?:show\s+)?(?:my\s+)?(?:recent\s+)?activities?(?:\s+for\s+(.+))?', message, re.IGNORECASE)
        if activity_match:
            activity_type = activity_match.group(1) if activity_match.group(1) else None
            return self._handle_activity_request(activity_type)

        # Check for character info requests
        character_match = re.search(r'\b(?:show\s+)?(?:my\s+)?characters?(?:\s+info)?', message, re.IGNORECASE)
        if character_match:
            return self._handle_character_request()

        # Check for leaderboard requests
        leaderboard_match = re.search(r'\b(?:show\s+)?leaderboards?(?:\s+for\s+(.+))?', message, re.IGNORECASE)
        if leaderboard_match:
            stat_name = leaderboard_match.group(1) if leaderboard_match.group(1) else None
            return self._handle_leaderboard_request(stat_name)

        # Clan search: common phrasings
        # e.g. "find a good clan", "recommend a clan", "what clans are recruiting", "clan that does vault of glass"
        msg_norm = self._normalize_user_text(message)
        clan_search_match = re.search(r"\b(?:(?:find|recommend|suggest|looking\s+for)\s+(?:a\s+)?)?clans?(?:\s+(?:that\s+)?(?:do|run|play))?(?:\s+for)?\s*(.*?)(?:\s+raids?)?\??$", msg_norm, re.IGNORECASE)
        if clan_search_match:
            pref = clan_search_match.group(1).strip() if clan_search_match.group(1) else None
            # Avoid false triggers where nothing meaningful was captured
            if pref and pref.lower() not in {"", "clan", "clans", "recruiting"}:
                return self._handle_clan_search(pref)
            # If user said "what clans are recruiting" with no preference, just list a few popular groups
            return self._handle_clan_search(None)

        # Clan members: "show clan members" or "show clan members of <name>"
        clan_members_match = re.search(r"\b(?:show|list)\s+(?:my\s+)?clan\s+members(?:\s+(?:of|for)\s+(.+))?\b", message, re.IGNORECASE)
        if clan_members_match:
            target = clan_members_match.group(1).strip() if clan_members_match.group(1) else None
            return self._handle_clan_members(target)

        # Fireteams: "find a fireteam" / "search fireteams" / "list clan fireteams"
        fireteam_search_match = re.search(r"\b(?:find|search)\s+(?:a\s+)?fireteams?\b(?:\s+for\s+(.+))?", message, re.IGNORECASE)
        if fireteam_search_match:
            act = fireteam_search_match.group(1).strip() if fireteam_search_match.group(1) else None
            return self._handle_fireteam_search(act)

        clan_fireteams_match = re.search(r"\b(?:list|show)\s+clan\s+fireteams(?:\s+(?:for|of)\s+(.+))?\b", message, re.IGNORECASE)
        if clan_fireteams_match:
            target = clan_fireteams_match.group(1).strip() if clan_fireteams_match.group(1) else None
            return self._handle_clan_fireteams(target)

        # Loadouts
        loadout_equip_match = re.search(r"\b(?:equip|load)\s+loadout\s+(\d+)\b(?:.*?(hunter|warlock|titan))?", message, re.IGNORECASE)
        if loadout_equip_match:
            idx = int(loadout_equip_match.group(1))
            class_target = loadout_equip_match.group(2).lower() if loadout_equip_match.lastindex and loadout_equip_match.group(2) else None
            return self._handle_equip_loadout(idx, class_target)

        loadout_snapshot_match = re.search(r"\b(?:snapshot|save)\s+loadout\s+(\d+)\b", message, re.IGNORECASE)
        if loadout_snapshot_match:
            idx = int(loadout_snapshot_match.group(1))
            return self._handle_snapshot_loadout(idx)

        # Lock/Unlock items
        lock_match = re.search(r"\b(?:please\s+)?lock\s+(?:my\s+)?(.+)$", message, re.IGNORECASE)
        if lock_match:
            return self._handle_lock_unlock(lock_match.group(1).strip(), True)
        unlock_match = re.search(r"\b(?:please\s+)?unlock\s+(?:my\s+)?(.+)$", message, re.IGNORECASE)
        if unlock_match:
            return self._handle_lock_unlock(unlock_match.group(1).strip(), False)

        # Dismantle with confirmation flow
        dismantle_match = re.search(r"\b(?:dismantle|shard|delete)\s+(?:my\s+)?(.+)$", message, re.IGNORECASE)
        if dismantle_match:
            return self._handle_dismantle_request(dismantle_match.group(1).strip())
        confirm_dismantle_match = re.search(r"\bconfirm\s+(?:dismantle|shard|delete)\s+(?:my\s+)?(.+)$", message, re.IGNORECASE)
        if confirm_dismantle_match:
            return self._handle_dismantle_confirm(confirm_dismantle_match.group(1).strip())

        # Vendor detail by name or hash
        vendor_detail_match = re.search(r"\b(?:show|visit|open)\s+vendor\s+(.+)$", message, re.IGNORECASE)
        if vendor_detail_match:
            vq = vendor_detail_match.group(1).strip()
            if re.fullmatch(r"\d+", vq):
                return self._handle_vendor_detail(int(vq))
            return self._handle_vendor_detail_by_name(vq)
        # Shorthand: "visit xur", "show banshee", etc.
        vendor_short = re.search(r"\b(?:show|visit|open)\s+([a-z][a-z0-9\-\s]+)\b", message, re.IGNORECASE)
        if vendor_short:
            name = vendor_short.group(1).strip()
            # Avoid triggering on unrelated words by checking against common vendor synonyms quickly
            if any(k in name.lower() for k in ["xur", "banshee", "gunsmith", "shaxx", "zavala", "rahool", "ada"]):
                return self._handle_vendor_detail_by_name(name)

        # Collectibles by node hash
        collectibles_match = re.search(r"\b(?:show\s+)?collectibles?\s+(?:for\s+)?(?:node\s+)?(\d+)\b", message, re.IGNORECASE)
        if collectibles_match:
            return self._handle_collectibles(int(collectibles_match.group(1)))

        # Public milestone content by name or hash
        pmc_match = re.search(r"\bmilestone\s+content\s+(.+)$", message, re.IGNORECASE)
        if pmc_match:
            q = pmc_match.group(1).strip()
            if re.fullmatch(r"\d+", q):
                return self._handle_public_milestone_content(int(q))
            return self._handle_public_milestone_by_name(q)

        # Trending paging and categories
        trending_match = re.search(r"\btrending\s+([A-Za-z]+)\s+page\s+(\d+)\b", message, re.IGNORECASE)
        if trending_match:
            cat = trending_match.group(1)
            page = int(trending_match.group(2))
            return self._handle_trending_category(cat, page)
        next_page_match = re.search(r"\b(next|more)\s+(?:page|results)\b", message, re.IGNORECASE)
        if next_page_match and self._last_trending:
            cat, page = self._last_trending
            return self._handle_trending_category(cat, page + 1)

        # Manifest / Entity lookup
        if re.search(r"\bmanifest\b", message, re.IGNORECASE):
            return self._handle_manifest()
        entity_match = re.search(r"\bentity\s+([A-Za-z0-9_]+)\s+(\d+)\b", message, re.IGNORECASE)
        if entity_match:
            return self._handle_entity(entity_match.group(1), int(entity_match.group(2)))

        # Historical stats
        if re.search(r"\baccount\s+stats\b", message, re.IGNORECASE):
            return self._handle_account_stats()
        if re.search(r"\bcharacter\s+stats\b", message, re.IGNORECASE):
            return self._handle_character_stats()
        if re.search(r"\bweapon\s+history\b", message, re.IGNORECASE):
            return self._handle_unique_weapon_history()
        if re.search(r"\baggregate\s+(?:activity\s+)?stats\b", message, re.IGNORECASE):
            return self._handle_aggregate_activity_stats()

        # Player lookup by name or Bungie name
        bungie_name_match = re.search(r"\b(?:search|find|lookup|look\s*up)\s+(?:player\s+)?([\w\s]+#\d{1,4})\b", message, re.IGNORECASE)
        if bungie_name_match:
            return self._handle_player_search_by_bungie_name(bungie_name_match.group(1).strip())

        player_name_match = re.search(r"\b(?:search|find|lookup|look\s*up)\s+player\s+([\w\s]+)\b", message, re.IGNORECASE)
        if player_name_match:
            return self._handle_player_search(player_name_match.group(1).strip())

        # Profile and character summaries
        profile_match = re.search(r"\b(?:show|view|what\s+is)\s+(?:my\s+)?profile\b", message, re.IGNORECASE)
        if profile_match:
            return self._handle_profile_summary()

        char_summary_match = re.search(r"\b(?:show|view)\s+(?:my\s+)?(hunter|warlock|titan)\b", message, re.IGNORECASE)
        if char_summary_match:
            return self._handle_character_summary(char_summary_match.group(1).lower())

        # Global alerts
        alerts_match = re.search(r"\b(global\s+alerts?|announcements?)\b", message, re.IGNORECASE)
        if alerts_match:
            return self._handle_alerts_request()

        # Post Game Carnage Report (PGCR)
        pgcr_match = re.search(r"\b(?:pgcr|carnage\s+report)\s+(\d{6,})\b", message, re.IGNORECASE)
        if pgcr_match:
            return self._handle_pgcr(pgcr_match.group(1))
        last_pgcr_match = re.search(r"\b(?:last|recent)\s+(?:pgcr|match|activity)(?:\s+report)?\b", message, re.IGNORECASE)
        if last_pgcr_match:
            return self._handle_last_pgcr()

        # Bulk equip items: "equip items sunshot, ace of spades" or "equip sunshot and ace ..."
        bulk_equip_match = re.search(r"\bequip\s+(?:items?\s+)?(.+?)(?:\s+(?:on|to)\s+(?:my\s+)?(hunter|warlock|titan))?$", message, re.IGNORECASE)
        if bulk_equip_match and ("," in bulk_equip_match.group(1) or " and " in bulk_equip_match.group(1).lower()):
            names_str = bulk_equip_match.group(1)
            class_target = (bulk_equip_match.group(2) or '').lower() if bulk_equip_match.lastindex and bulk_equip_match.group(2) else None
            names = [self._canonicalize_item_query(n.strip()) for n in re.split(r",|\band\b", names_str, flags=re.IGNORECASE) if n.strip()]
            return self._handle_bulk_equip(names, class_target)

        if "destiny" in message.lower() or "bungie" in message.lower():
            try:
                milestones = self.bungie.get_milestones()
                trending = self.bungie.get_trending_categories()
                latest_trending = self.bungie.get_trending_category("Latest", 0)
                global_alerts = self.bungie.get_global_alerts()

                # Parse milestones into readable names
                milestone_names = []
                for key in list(milestones["Response"].keys())[:5]:  # Limit to first 5
                    try:
                        definition = self.bungie._get(
                            f"/Destiny2/Manifest/DestinyMilestoneDefinition/{key}/",
                            authenticated=False
                        )
                        name = definition["Response"]["displayProperties"]["name"]
                        milestone_names.append(name)
                    except:
                        continue

                # Parse trending categories
                trending_info = []
                for category in trending["Response"]["categories"][:3]:  # First 3 categories
                    cat_name = category["categoryName"]
                    if cat_name == "News" and "entries" in category and "results" in category["entries"]:
                        recent_news = []
                        for entry in category["entries"]["results"][:2]:  # First 2 news
                            if entry["creationDate"].startswith("2024") or entry["creationDate"].startswith("2025"):
                                recent_news.append(entry["displayName"])
                        if recent_news:
                            trending_info.append(f"{cat_name}: {', '.join(recent_news)}")
                        else:
                            trending_info.append(f"{cat_name}: No recent updates")
                    else:
                        trending_info.append(f"{cat_name}: {len(category.get('entries', {}).get('results', []))} items")

                # Parse latest trending
                latest_info = ""
                if "Response" in latest_trending and latest_trending["Response"]["results"]:
                    latest_creations = [entry["displayName"] for entry in latest_trending["Response"]["results"][:3]]
                    if latest_creations:
                        latest_info = f"Latest creations: {', '.join(latest_creations)}."

                # Parse global alerts
                alerts_info = ""
                if "Response" in global_alerts and global_alerts["Response"]:
                    active_alerts = [alert["AlertHtml"] for alert in global_alerts["Response"] if alert.get("AlertHtml")]
                    if active_alerts:
                        alerts_info = f"Global Alerts: {'; '.join(active_alerts)}."

                # Prepare data for Ollama
                destiny_data = f"Current Destiny 2 Milestones: {', '.join(milestone_names)}\nTrending: {'; '.join(trending_info)}\n{latest_info}\n{alerts_info}"

                system_prompt = personalities.get_prompt(persona) or (
                    "You are the Ghost from Destiny 2. Respond briefly in character. "
                    "Always address the user as 'Guardian' (never traveler, player, friend, etc.). "
                    "Use only the provided Bungie API data. Keep responses short."
                )

                user_prompt = f"User query: {message}\n\nCurrent Bungie API data (as of October 6, 2025):\n{destiny_data}\n\nRespond as the Ghost using only this data."

                return send_with_system(system_prompt, user_prompt)
            except Exception as e:
                # If API fails, fall back to general response
                pass

        # Check for season-specific questions
        if "season" in message.lower() and ("what" in message.lower() or "current" in message.lower() or "now" in message.lower()):
            return "Ah, my Guardian! We're currently in Season of the Wish - the season of wishes granted and mysteries revealed. What adventures shall we pursue in this magical time?"

        # General response with lightweight lore retrieval
        system_prompt = personalities.get_prompt(persona) or (
            "You are Ghost from Destiny. Respond briefly in character. "
            "Always address the user as 'Guardian'."
        )
        lore_bits = []
        try:
            for _doc, snippet, _score in lore_search.search(message, k=3):
                if snippet:
                    lore_bits.append(snippet)
        except Exception:
            pass
        if lore_bits:
            user_prompt = (
                f"{message}\n\nLore context (may be relevant):\n- "
                + "\n- ".join(lore_bits[:3])
                + "\nUse this context when helpful. Keep it concise."
            )
        else:
            user_prompt = message
        return send_with_system(system_prompt, user_prompt)

    def _handle_command_segment(self, segment: str) -> str:
        """Route a single command-like segment to the appropriate handler."""
        msg = segment.strip()
        low = msg.lower()
        # Combined transfer + equip
        if ("transfer" in low or "move" in low) and ("equip" in low):
            explicit_from_vault = ("from my vault" in low)
            m_equip = re.search(r"\bequip\s+(?:my\s+)?(.+)$", msg, re.IGNORECASE)
            equip_name = m_equip.group(1).strip() if m_equip else None
            m_transfer = re.search(r"(?:transfer|move)\s+(?:my\s+)?(.+?)(?=\s+(?:from|to|and)\b|$)", msg, re.IGNORECASE)
            transfer_name = m_transfer.group(1).strip() if m_transfer else None
            name = None
            if equip_name and equip_name.lower() not in {"it", "it back"}:
                name = equip_name
            elif transfer_name:
                name = transfer_name
            elif equip_name:
                name = equip_name
            if name:
                return self._handle_transfer_then_equip(name, explicit_from_vault)
        # Pronoun transfer
        m_pr = re.search(r"\b(?:transfer|move)\s+it\s+(?:back\s+)?(?:to\s+)?(?:my\s+)?(vault|inventory)\b", msg, re.IGNORECASE)
        if m_pr:
            return self._handle_transfer_pronoun(m_pr.group(1).lower())
        # Transfer to vault
        m_tv = re.search(r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:back\s+)?(?:to\s+)?(?:my\s+)?vault\b", msg, re.IGNORECASE)
        if m_tv:
            return self._handle_vault_item(m_tv.group(1).strip())
        # Transfer from vault
        m_fv = re.search(r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+vault\b", msg, re.IGNORECASE)
        if m_fv:
            return self._handle_transfer_from_vault(m_fv.group(1).strip())
        # Transfer to inventory
        m_ti = re.search(r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?(?:inventory|invetory|inventorie)\b", msg, re.IGNORECASE)
        if m_ti:
            return self._handle_transfer_from_vault(m_ti.group(1).strip())
        # Pull from postmaster
        m_pm = re.search(r"\b(?:pull|get|transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+post[-\s]?master\b", msg, re.IGNORECASE)
        if m_pm:
            return self._handle_pull_from_postmaster(m_pm.group(1).strip())
        # Dismantle
        m_dis = re.search(r"\bdismantle\s+(?:my\s+)?(.+)$", msg, re.IGNORECASE)
        if m_dis:
            return self._handle_dismantle_item(m_dis.group(1).strip())
        # Equip
        m_eq = re.search(r"\bequip\s+(?:my\s+)?(.+)$", msg, re.IGNORECASE)
        if m_eq:
            return self._handle_equip_item(m_eq.group(1).strip())
        # Vault <name>
        m_v = re.search(r"\bvault\s+(?:my\s+)?(.+)$", msg, re.IGNORECASE)
        if m_v:
            return self._handle_vault_item(m_v.group(1).strip())
        return ""


    # ------------------------------
    # Fuzzy match helpers
    # ------------------------------
    def _canonicalize_item_query(self, q: str) -> str:
        # Normalize some common user phrases/aliases to canonical item names
        s = (q or "").strip()
        low = s.lower()
        for k, v in getattr(self, "_item_aliases", {}).items():
            if low == k or low.startswith(k + " "):
                return v + s[len(k):]
        return s
    def _normalize_text(self, s: str) -> str:
        s = (s or "").lower()
        s = re.sub(r"[\-_/]+", " ", s)
        s = re.sub(r"[^a-z0-9\s]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _normalize_user_text(self, s: str) -> str:
        """Lightweight input normalization to catch common typos and synonyms."""
        t = s
        t = re.sub(r"\bclaid\b", "clan", t, flags=re.IGNORECASE)
        t = re.sub(r"\bcrotas\s+run\b", "Crota's End", t, flags=re.IGNORECASE)
        t = re.sub(r"\bvog\b", "vault of glass", t, flags=re.IGNORECASE)
        return t

    def _similarity(self, a: str, b: str) -> float:
        a_n = self._normalize_text(a)
        b_n = self._normalize_text(b)
        if not a_n or not b_n:
            return 0.0
        # Sequence ratio
        seq = difflib.SequenceMatcher(None, a_n, b_n).ratio()
        # Token set Jaccard
        ta, tb = set(a_n.split()), set(b_n.split())
        inter = len(ta & tb)
        union = len(ta | tb) or 1
        jacc = inter / union
        # Weighted blend favors sequence, keeps token overlap influence
        return 0.7 * seq + 0.3 * jacc

    def _get_item_name(self, item_hash: int | str) -> str:
        try:
            # Use client's cached definition helper to avoid repeated network calls
            item_def = self.bungie.get_inventory_item_definition(item_hash)
            return (
                item_def.get("Response", {})
                .get("displayProperties", {})
                .get("name", "")
            )
        except Exception:
            return ""

    def _bucket_location_safe(self, bucket_hash: int | str) -> int | None:
        try:
            bh = int(bucket_hash)
        except Exception:
            return None
        try:
            if bh in self._bucket_loc_cache:
                return self._bucket_loc_cache[bh]
            data = self.bungie.get_entity("DestinyInventoryBucketDefinition", bh)
            loc = (
                data.get("Response", {})
                .get("location")
            )
            if isinstance(loc, int):
                self._bucket_loc_cache[bh] = loc
                return loc
        except Exception:
            pass
        return None

    def _item_bucket_location(self, item_hash: int | str) -> int | None:
        try:
            idef = self.bungie.get_inventory_item_definition(item_hash)
            bh = (
                idef.get("Response", {})
                .get("inventory", {})
                .get("bucketTypeHash")
            )
            if bh is None:
                return None
            return self._bucket_location_safe(bh)
        except Exception:
            return None

    def _is_postmaster_bucket(self, bucket_hash: int | str) -> bool:
        try:
            bh = int(bucket_hash)
            return bh == 215593132  # Postmaster bucket hash
        except Exception:
            return False

    def _active_character_id(self, profile: dict) -> str | None:
        try:
            chars = (
                profile.get("Response", {})
                .get("characters", {})
                .get("data", {})
            )
            if not isinstance(chars, dict) or not chars:
                return None
            # Pick most recently played character
            best_cid = None
            best_dt = None
            import datetime as _dt
            for cid, cdata in chars.items():
                dt_s = cdata.get("dateLastPlayed") or cdata.get("dateLastPlayed", "")
                try:
                    dt = _dt.datetime.fromisoformat(dt_s.replace("Z", "+00:00")) if dt_s else None
                except Exception:
                    dt = None
                if best_dt is None or (dt and dt > best_dt):
                    best_dt = dt
                    best_cid = cid
            return best_cid or list(chars.keys())[0]
        except Exception:
            return None
        if bh in self._postmaster_bucket_cache:
            return self._postmaster_bucket_cache[bh]
        try:
            data = self.bungie.get_entity("DestinyInventoryBucketDefinition", bh)
            resp = data.get("Response", {}) if isinstance(data, dict) else {}
            name = (
                resp.get("displayProperties", {})
                .get("name", "")
            )
            loc = resp.get("location")
            is_pm = False
            if isinstance(name, str) and name:
                low = name.lower()
                if ("postmaster" in low) or ("lost" in low and "item" in low):
                    is_pm = True
            if not is_pm and isinstance(loc, int) and loc == 4:
                is_pm = True
            self._postmaster_bucket_cache[bh] = is_pm
            return is_pm
        except Exception:
            return False

    def _best_vault_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        """Return (item_instance_id, character_id, item_hash, item_name) best matching query from vault."""
        best_score = 0.0
        best_instance = None
        best_char = None
        best_hash = None
        best_name = None
        items = (
            profile.get("Response", {})
            .get("profileInventory", {})
            .get("data", {})
            .get("items", [])
        )
        for it in items:
            try:
                loc = it.get("location")
                if loc is None:
                    # Fallback: resolve from bucketHash
                    bh = it.get("bucketHash")
                    if bh is None:
                        continue
                    loc = self._bucket_location_safe(bh)
                if loc != 2:
                    continue
                ih = it.get("itemHash")
                if ih is None:
                    continue
                name = self._get_item_name(ih)
                if not name:
                    continue
                score = self._similarity(name, query)
                if score >= 0.75 and score > best_score:
                    best_score = score
                    best_instance = it.get("itemInstanceId")
                    best_char = None
                    best_hash = ih
                    best_name = name
                    if best_score >= 0.96:
                        break
            except Exception:
                continue
        return best_instance, best_char, best_hash, best_name

    def _best_inventory_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        """Return (item_instance_id, character_id, item_hash, item_name) best matching query from character inventories."""
        best_score = 0.0
        best_instance = None
        best_char = None
        best_hash = None
        best_name = None
        invs = (
            profile.get("Response", {})
            .get("characterInventories", {})
            .get("data", {})
        )
        for char_id, cdata in invs.items():
            for it in cdata.get("items", []):
                try:
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if not name:
                        continue
                    score = self._similarity(name, query)
                    if score >= 0.75 and score > best_score:
                        best_score = score
                        best_instance = it.get("itemInstanceId")
                        best_char = char_id
                        best_hash = ih
                        best_name = name
                        if best_score >= 0.96:
                            break
                except Exception:
                    continue
            if best_score >= 0.96:
                break
        return best_instance, best_char, best_hash, best_name

    def _best_postmaster_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        """Return (item_instance_id, character_id, item_hash, item_name) best matching query from postmaster buckets."""
        best_score = 0.0
        best_instance = None
        best_char = None
        best_hash = None
        best_name = None
        # Check per-character inventories for Postmaster: location==4 or bucket identified as Postmaster/Lost Items
        invs = (
            profile.get("Response", {})
            .get("characterInventories", {})
            .get("data", {})
        )
        for char_id, cdata in invs.items():
            for it in cdata.get("items", []):
                try:
                    loc = it.get("location")
                    bh = it.get("bucketHash")
                    if loc is None and bh is not None:
                        loc = self._bucket_location_safe(bh)
                    is_pm = (loc == 4) or (bh is not None and self._is_postmaster_bucket(bh))
                    if not is_pm:
                        continue
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if not name:
                        continue
                    score = self._similarity(name, query)
                    if score >= 0.75 and score > best_score:
                        best_score = score
                        best_instance = it.get("itemInstanceId")
                        best_char = char_id
                        best_hash = ih
                        best_name = name
                        if best_score >= 0.96:
                            break
                except Exception:
                    continue
            if best_score >= 0.96:
                break
        # Fallback: check profile inventory for postmaster buckets if needed
        if not best_instance:
            items = (
                profile.get("Response", {})
                .get("profileInventory", {})
                .get("data", {})
                .get("items", [])
            )
            for it in items:
                try:
                    loc = it.get("location")
                    bh = it.get("bucketHash")
                    if loc is None and bh is not None:
                        loc = self._bucket_location_safe(bh)
                    is_pm = (loc == 4) or (bh is not None and self._is_postmaster_bucket(bh))
                    if not is_pm:
                        continue
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if not name:
                        continue
                    score = self._similarity(name, query)
                    if score >= 0.75 and score > best_score:
                        best_score = score
                        best_instance = it.get("itemInstanceId")
                        best_hash = ih
                        best_name = name
                        # character unknown in this path
                except Exception:
                    continue
        return best_instance, best_char, best_hash, best_name

    def _find_least_valuable_item(self, profile: dict, bucket_hash: int, exclude_instance_id: str | None = None) -> dict | None:
        """Find the least valuable item in the given bucket across all characters and vault."""
        least_power = float('inf')
        least_item = None
        instances = profile.get("Response", {}).get("itemComponents", {}).get("instances", {}).get("data", {})

        # Check character inventories
        cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
        for cid, cdata in cinv.items():
            for it in cdata.get("items", []):
                if it.get("bucketHash") == bucket_hash and it.get("itemInstanceId") != exclude_instance_id:
                    iid = it.get("itemInstanceId")
                    if iid and iid in instances:
                        power = instances[iid].get("primaryStat", {}).get("value", 0)
                        if power < least_power:
                            least_power = power
                            least_item = {**it, "character_id": cid}

        # Check vault
        vinv = profile.get("Response", {}).get("profileInventory", {}).get("data", {}).get("items", [])
        for it in vinv:
            if it.get("bucketHash") == bucket_hash and it.get("itemInstanceId") != exclude_instance_id:
                iid = it.get("itemInstanceId")
                if iid and iid in instances:
                    power = instances[iid].get("primaryStat", {}).get("value", 0)
                    if power < least_power:
                        least_power = power
                        least_item = {**it, "character_id": None}

        return least_item

    def _best_equipped_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        """Return (item_instance_id, character_id, item_hash, item_name) from equipped items best matching query."""
        best_score = 0.0
        best_instance = None
        best_char = None
        best_hash = None
        best_name = None
        eq = (
            profile.get("Response", {})
            .get("characterEquipment", {})
            .get("data", {})
        )
        for char_id, cdata in eq.items():
            for it in cdata.get("items", []):
                try:
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if not name:
                        continue
                    score = self._similarity(name, query)
                    if score > 0.8 and score > best_score:
                        best_score = score
                        best_instance = it.get("itemInstanceId")
                        best_char = char_id
                        best_hash = ih
                        best_name = name
                        if best_score >= 0.96:
                            break
                except Exception:
                    continue
            if best_score >= 0.96:
                break
        return best_instance, best_char, best_hash, best_name

    def _handle_vault_item(self, item_name: str) -> str:
        """Handle vaulting an item."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get character inventories and equipment and profile inventory
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])
            # Warm up definitions in background for speed
            try:
                hashes = set()
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for _, cdata in cinv.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Fuzzy search in character inventories
            item_instance_id, character_id, item_hash, _ = self._best_inventory_match(profile, item_name)

            if not item_instance_id:
                # Check if it's already in vault
                v_inst, _, _, _ = self._best_vault_match(profile, item_name)
                if v_inst:
                    return f"{item_name} is already in your vault, Guardian."
                # Check if it's equipped
                e_inst, e_char, _, _ = self._best_equipped_match(profile, item_name)
                if e_inst:
                    return (
                        f"I found '{item_name}' equipped on a character, Guardian. Equip another item first, then ask me to vault it, "
                        f"or say 'equip <other item>, then vault {item_name}'."
                    )
                return f"I couldn't find '{item_name}' in your inventory or vault, Guardian."

            # Vault the item (transfer to vault)
            transfer_result = self.bungie.transfer_item(
                membership_type=destiny_membership_type,
                character_id=character_id,
                item_id=item_instance_id,
                item_reference_hash=item_hash,
                stack_size=1,
                transfer_to_vault=True,
            )

            if transfer_result.get("ErrorCode") == 1:
                # Remember last item for pronoun-based follow-ups
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": character_id,
                    "hash": item_hash,
                }
                return f"I've successfully vaulted your {item_name}, Guardian. It's now safely stored away."
            else:
                return f"Sorry Guardian, I couldn't vault your {item_name}. The transfer failed."

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while trying to vault your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while trying to vault your item: {str(e)}"

    def _handle_transfer_from_vault(self, item_name: str) -> str:
        """Handle transferring an item from vault to inventory."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile with inventory and character data
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])
            # Warm up definitions in background
            try:
                hashes = set()
                pinv = profile.get("Response", {}).get("profileInventory", {}).get("data", {}).get("items", [])
                for it in pinv:
                    ih = it.get("itemHash")
                    if ih is not None:
                        hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Fuzzy search for the item in vault (location 2)
            item_instance_id, _, item_hash, _ = self._best_vault_match(profile, item_name)

            if not item_instance_id:
                return f"I couldn't find '{item_name}' in your vault, Guardian. Make sure the name is spelled correctly."

            # Get the first available character to transfer to
            character_id = None
            if "characters" in profile.get("Response", {}):
                character_id = list(profile["Response"]["characters"]["data"].keys())[0]

            if not character_id:
                return "I couldn't find an active character to transfer the item to, Guardian."

            # Transfer the item from vault to character inventory
            transfer_result = self.bungie.transfer_item(
                membership_type=destiny_membership_type,
                character_id=character_id,
                item_id=item_instance_id,
                item_reference_hash=item_hash,
                stack_size=1,
                transfer_to_vault=False  # False means transfer TO character
            )

            if transfer_result.get("ErrorCode") == 1:
                # Remember last item
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": character_id,
                    "hash": item_hash,
                }
                return f"I've successfully transferred your {item_name} to your inventory, Guardian. It's ready for use."
            else:
                return f"Sorry Guardian, I couldn't transfer your {item_name}. The transfer failed."

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"

    def _handle_transfer_to_character(self, item_name: str, target_class: str) -> str:
        """Handle transferring an item to a specific character."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile with inventory, character data, and item instances
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])
            # Warm up definitions in background
            try:
                hashes = set()
                pinv = profile.get("Response", {}).get("profileInventory", {}).get("data", {}).get("items", [])
                for it in pinv:
                    ih = it.get("itemHash")
                    if ih is not None:
                        hashes.add(ih)
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for _, cdata in cinv.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                ceq = profile.get("Response", {}).get("characterEquipment", {}).get("data", {})
                for _, cdata in ceq.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Find target character
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            target_cid = None
            target_display_class = target_class
            if target_class == "me":
                target_cid = self._active_character_id(profile)
                if target_cid and target_cid in chars:
                    class_type = chars[target_cid].get("classType")
                    class_names = {0: "Titan", 1: "Hunter", 2: "Warlock"}
                    target_display_class = class_names.get(class_type, "Guardian").lower()
            else:
                class_map = {"titan": 0, "hunter": 1, "warlock": 2}
                target_class_type = class_map.get(target_class)
                if target_class_type is not None:
                    for cid, cdata in chars.items():
                        if cdata.get("classType") == target_class_type:
                            target_cid = cid
                            break
            if not target_cid:
                return f"I couldn't find your {target_class} character, Guardian."

            # Initialize variables
            item_instance_id = None
            item_hash = None
            did_move = False
            source_location = None
            source_cid = None
            actual_item_name = None

            # Helper: free one slot in target inventory for this item's bucket (used when destination is full)
            def _free_slot_on_target(for_item_hash: int | str | None) -> bool:
                try:
                    if for_item_hash is None:
                        return False
                    idef = self.bungie.get_inventory_item_definition(for_item_hash)
                    bucket_hash = (
                        idef.get("Response", {})
                        .get("inventory", {})
                        .get("bucketTypeHash")
                    )
                    if not bucket_hash:
                        return False
                    profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205, 300])
                    invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                    instances = (
                        profx.get("Response", {})
                        .get("itemComponents", {})
                        .get("instances", {})
                        .get("data", {})
                    )
                    best = None  # (tierType, power, instanceId, itemHash)
                    for itx in (invx.get(target_cid, {}) or {}).get("items", []):
                        if itx.get("bucketHash") != bucket_hash:
                            continue
                        ihx = itx.get("itemHash")
                        try:
                            idef2 = self.bungie.get_inventory_item_definition(ihx)
                            inv2 = idef2.get("Response", {}).get("inventory", {})
                            tier = inv2.get("tierType", 999)
                        except Exception:
                            tier = 999
                        iid2 = itx.get("itemInstanceId")
                        power = 9999
                        if iid2 and str(iid2) in instances:
                            power = instances[str(iid2)].get("primaryStat", {}).get("value", 9999)
                        cand = (int(tier) if isinstance(tier, int) else 999, int(power), iid2, ihx)
                        if best is None or cand < best:
                            best = cand
                    if best is None or best[2] is None:
                        return False
                    _, _, rid, rhash = best
                    tr_out = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=str(rid),
                        item_reference_hash=int(rhash),
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    return tr_out.get("ErrorCode") == 1 if isinstance(tr_out, dict) else True
                except Exception:
                    return False

            # First, try to find the item in vault
            item_instance_id, source_cid, item_hash, actual_item_name = self._best_vault_match(profile, item_name)
            if item_instance_id:
                item_name = actual_item_name or item_name
                source_location = "vault"

            if not item_instance_id:
                # Try to find in any character's inventory
                item_instance_id, source_cid, item_hash, actual_item_name = self._best_inventory_match(profile, item_name)
                if item_instance_id:
                    item_name = actual_item_name or item_name
                    source_location = "inventory"
                else:
                    # Try to find in equipped items
                    item_instance_id, source_cid, item_hash, actual_item_name = self._best_equipped_match(profile, item_name)
                    if item_instance_id:
                        item_name = actual_item_name or item_name
                        source_location = "equipped"
                    else:
                        # Try to find in postmaster
                        item_instance_id, source_cid, item_hash, actual_item_name = self._best_postmaster_match(profile, item_name)
                        if item_instance_id:
                            item_name = actual_item_name or item_name
                            source_location = "postmaster"
                
                # Handle equipped items
                if source_location == "equipped":
                    # Unequip the item
                    try:
                        item_def = self.bungie.get_inventory_item_definition(item_hash)
                        bucket_hash = item_def.get("Response", {}).get("inventory", {}).get("bucketTypeHash")
                        if bucket_hash:
                            # Find another item in the same bucket on the same character
                            invs = profile.get("Response", {}).get("characterInventories", {}).get("data", {}).get(source_cid, {}).get("items", [])
                            other_item = None
                            for it in invs:
                                bh = it.get("bucketHash")
                                if bh == bucket_hash and it.get("itemInstanceId") != item_instance_id:
                                    other_item = it
                                    break
                            if other_item:
                                equip_result = self.bungie.equip_item(
                                    membership_type=destiny_membership_type,
                                    character_id=source_cid,
                                    item_id=other_item.get("itemInstanceId")
                                )
                                if equip_result.get("ErrorCode") == 1:
                                    source_location = "inventory"
                                else:
                                    return f"Sorry Guardian, I couldn't unequip {item_name}."
                            else:
                                return f"Sorry Guardian, no other item to equip in that slot for {item_name}."
                    except Exception as e:
                        return f"Sorry Guardian, error unequipping {item_name}: {str(e)}"
                
                if item_instance_id and source_cid == target_cid:
                    try:
                        self._last_item = {
                            "name": item_name,
                            "instance_id": item_instance_id,
                            "character_id": target_cid,
                            "hash": item_hash,
                        }
                    except Exception:
                        pass
                    return f"{item_name} is already on your {target_display_class}, Guardian."

            if not item_instance_id:
                return f"I couldn't find '{item_name}' in your vault or any character's inventory, Guardian."

            # Handle postmaster items
            if source_location == "postmaster":
                # Pull from postmaster to inventory
                pull_result = self.bungie.pull_from_postmaster(
                    membership_type=destiny_membership_type,
                    character_id=source_cid,
                    item_id=item_instance_id,
                    item_reference_hash=item_hash,
                    stack_size=1
                )
                if pull_result.get("ErrorCode") != 1:
                    return f"Sorry Guardian, I couldn't pull {item_name} from the postmaster."
                # Now it's in inventory
                source_location = "inventory"

            # If item is in another character's inventory, transfer to vault first
            if source_location == "inventory" and source_cid != target_cid:
                transfer_result = self.bungie.transfer_item(
                    membership_type=destiny_membership_type,
                    character_id=source_cid,
                    item_id=item_instance_id,
                    item_reference_hash=item_hash,
                    stack_size=1,
                    transfer_to_vault=True  # Transfer to vault
                )
                if transfer_result.get("ErrorCode") != 1:
                    return f"Sorry Guardian, I couldn't transfer {item_name} from your current character to the vault."

            # Now transfer from vault to target character (handle full slot by freeing one)
            try:
                transfer_result = self.bungie.transfer_item(
                    membership_type=destiny_membership_type,
                    character_id=target_cid,
                    item_id=item_instance_id,
                    item_reference_hash=item_hash,
                    stack_size=1,
                    transfer_to_vault=False  # Transfer to character
                )
            except BungieAPIError as be:
                txt = str(be)
                if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                    if _free_slot_on_target(item_hash):
                        transfer_result = self.bungie.transfer_item(
                            membership_type=destiny_membership_type,
                            character_id=target_cid,
                            item_id=item_instance_id,
                            item_reference_hash=item_hash,
                            stack_size=1,
                            transfer_to_vault=False,
                        )
                    else:
                        return f"Your {target_display_class} has no free slots for {item_name}, Guardian. I couldn't make room."
                else:
                    raise

            if transfer_result.get("ErrorCode") == 1:
                # Remember last item
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": target_cid,
                    "hash": item_hash,
                }
                return f"I've successfully transferred your {item_name} to your {target_display_class}, Guardian. It's ready for action."
            else:
                return f"Sorry Guardian, I couldn't transfer your {item_name} to your {target_display_class}. The transfer failed."

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"

    def _handle_transfer_between_characters(self, item_name: str, from_class: str, to_class: str) -> str:
        """Handle transferring an item between specific characters."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile with inventory, character data, and item instances
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])
            # Warm up definitions in background
            try:
                hashes = set()
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for _, cdata in cinv.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                ceq = profile.get("Response", {}).get("characterEquipment", {}).get("data", {})
                for _, cdata in ceq.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Find from and to characters
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            from_cid = None
            to_cid = None
            class_map = {"titan": 0, "hunter": 1, "warlock": 2}
            from_class_type = class_map.get(from_class)
            to_class_type = class_map.get(to_class)
            for cid, cdata in chars.items():
                if cdata.get("classType") == from_class_type:
                    from_cid = cid
                if cdata.get("classType") == to_class_type:
                    to_cid = cid
            if not from_cid:
                return f"I couldn't find your {from_class} character, Guardian."
            if not to_cid:
                return f"I couldn't find your {to_class} character, Guardian."
            if from_cid == to_cid:
                return f"Your {from_class} is the same as your {to_class}, Guardian. No transfer needed."

            # Find the item in the from character's inventory or equipped
            item_instance_id = None
            item_hash = None
            source_location = None
            cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
            ceq = profile.get("Response", {}).get("characterEquipment", {}).get("data", {})
            # Check inventory
            if from_cid in cinv:
                for it in cinv[from_cid].get("items", []):
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if name and self._similarity(name, item_name) >= 0.75:
                        item_instance_id = it.get("itemInstanceId")
                        item_hash = ih
                        source_location = "inventory"
                        break
            # Check equipped if not found
            if not item_instance_id and from_cid in ceq:
                for it in ceq[from_cid].get("items", []):
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    name = self._get_item_name(ih)
                    if name and self._similarity(name, item_name) >= 0.75:
                        item_instance_id = it.get("itemInstanceId")
                        item_hash = ih
                        source_location = "equipped"
                        break

            if not item_instance_id:
                return f"I couldn't find '{item_name}' on your {from_class}, Guardian."

            # If equipped, unequip
            if source_location == "equipped":
                item_def = self.bungie.get_inventory_item_definition(item_hash)
                bucket_hash = item_def.get("Response", {}).get("inventory", {}).get("bucketTypeHash")
                if bucket_hash:
                    # Find another item in the same bucket on the same character
                    other_item = None
                    if from_cid in cinv:
                        for it in cinv[from_cid].get("items", []):
                            bh = it.get("bucketHash")
                            if bh == bucket_hash and it.get("itemInstanceId") != item_instance_id:
                                other_item = it
                                break
                    if not other_item:
                        # Find globally the least valuable item in that bucket
                        least_valuable = self._find_least_valuable_item(profile, bucket_hash, exclude_instance_id=item_instance_id)
                        if least_valuable:
                            other_item = least_valuable
                            # Transfer it to from_cid if not already there
                            if least_valuable.get("character_id") != from_cid:
                                if least_valuable.get("character_id"):
                                    # Transfer from other character to vault
                                    self.bungie.transfer_item(
                                        membership_type=destiny_membership_type,
                                        character_id=least_valuable["character_id"],
                                        item_id=least_valuable["itemInstanceId"],
                                        item_reference_hash=least_valuable["itemHash"],
                                        stack_size=1,
                                        transfer_to_vault=True
                                    )
                                # Transfer from vault to from_cid
                                self.bungie.transfer_item(
                                    membership_type=destiny_membership_type,
                                    character_id=from_cid,
                                    item_id=least_valuable["itemInstanceId"],
                                    item_reference_hash=least_valuable["itemHash"],
                                    stack_size=1,
                                    transfer_to_vault=False
                                )
                    if other_item:
                        equip_result = self.bungie.equip_item(
                            membership_type=destiny_membership_type,
                            character_id=from_cid,
                            item_id=other_item["itemInstanceId"]
                        )
                        if equip_result.get("ErrorCode") == 1:
                            source_location = "inventory"
                        else:
                            return f"Sorry Guardian, I couldn't unequip {item_name}."
                    else:
                        return f"Sorry Guardian, no replacement item found for {item_name}."

            # Transfer from from_cid to vault
            transfer_result = self.bungie.transfer_item(
                membership_type=destiny_membership_type,
                character_id=from_cid,
                item_id=item_instance_id,
                item_reference_hash=item_hash,
                stack_size=1,
                transfer_to_vault=True
            )
            if transfer_result.get("ErrorCode") != 1:
                return f"Sorry Guardian, I couldn't transfer {item_name} from your {from_class} to the vault."

            # Transfer from vault to to_cid
            transfer_result = self.bungie.transfer_item(
                membership_type=destiny_membership_type,
                character_id=to_cid,
                item_id=item_instance_id,
                item_reference_hash=item_hash,
                stack_size=1,
                transfer_to_vault=False
            )

            if transfer_result.get("ErrorCode") == 1:
                # Remember last item
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": to_cid,
                    "hash": item_hash,
                }
                return f"I've successfully transferred your {item_name} from your {from_class} to your {to_class}, Guardian. It's ready for action."
            else:
                return f"Sorry Guardian, I couldn't transfer your {item_name} to your {to_class}. The transfer failed."

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while trying to transfer your item: {str(e)}"

    def _handle_equip_item(self, item_name: str, class_target: str | None = None) -> str:
        """Handle equipping an item."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get characters, inventories, equipment, and profile inventory (vault)
            profile = self.bungie.get_profile(
                destiny_membership_type,
                destiny_membership_id,
                [102, 200, 201, 205],
            )
            # Warm up definitions in background
            try:
                hashes = set()
                # From vault/profile inventory
                pinv = (
                    profile.get("Response", {})
                    .get("profileInventory", {})
                    .get("data", {})
                    .get("items", [])
                )
                for it in pinv:
                    ih = it.get("itemHash")
                    if ih is not None:
                        hashes.add(ih)
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for _, cdata in cinv.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Decide target character: requested class -> most recently played
            target_cid = None
            if class_target:
                try:
                    class_map = {"titan": 0, "hunter": 1, "warlock": 2}
                    want = class_map.get(class_target)
                    chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                    if want is not None:
                        for cid, cdata in (chars or {}).items():
                            if cdata.get("classType") == want:
                                target_cid = cid
                                break
                except Exception:
                    target_cid = None
            if not target_cid:
                target_cid = self._active_character_id(profile)
            if not target_cid:
                chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                if not chars:
                    return "I couldn't find a character to equip the item on, Guardian."
                target_cid = list(chars.keys())[0]

            # Helper: free one slot in target inventory for this item's bucket (when destination is full)
            def _free_slot_on_target(for_item_hash: int | str | None) -> bool:
                try:
                    if for_item_hash is None:
                        return False
                    idef = self.bungie.get_inventory_item_definition(for_item_hash)
                    bucket_hash = (
                        idef.get("Response", {})
                        .get("inventory", {})
                        .get("bucketTypeHash")
                    )
                    if not bucket_hash:
                        return False
                    profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205, 300])
                    invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                    instances = (
                        profx.get("Response", {})
                        .get("itemComponents", {})
                        .get("instances", {})
                        .get("data", {})
                    )
                    best = None  # (tierType, power, instanceId, itemHash)
                    for itx in (invx.get(target_cid, {}) or {}).get("items", []):
                        if itx.get("bucketHash") != bucket_hash:
                            continue
                        ihx = itx.get("itemHash")
                        try:
                            idef2 = self.bungie.get_inventory_item_definition(ihx)
                            inv2 = idef2.get("Response", {}).get("inventory", {})
                            tier = inv2.get("tierType", 999)
                        except Exception:
                            tier = 999
                        iid2 = itx.get("itemInstanceId")
                        power = 9999
                        if iid2 and str(iid2) in instances:
                            power = instances[str(iid2)].get("primaryStat", {}).get("value", 9999)
                        cand = (int(tier) if isinstance(tier, int) else 999, int(power), iid2, ihx)
                        if best is None or cand < best:
                            best = cand
                    if best is None or best[2] is None:
                        return False
                    _, _, rid, rhash = best
                    tr_out = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=str(rid),
                        item_reference_hash=int(rhash),
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    return tr_out.get("ErrorCode") == 1 if isinstance(tr_out, dict) else True
                except Exception:
                    return False

            # Prepare local state used across branches
            item_instance_id: str | None = None
            item_hash: int | str | None = None
            did_move: bool = False

            # If already equipped on target character, report success
            eq_iid, eq_char, eq_hash, _ = self._best_equipped_match(profile, item_name)
            if eq_iid and eq_char == target_cid:
                return f"Your {item_name} is already equipped, Guardian."

            # If equipped on another character, inform user (cannot auto-unequip without a replacement)
            if eq_iid and eq_char and eq_char != target_cid:
                # Safe swap: equip the lowest-rarity replacement on that character, then move
                # Determine the requested item's bucket
                requested_bucket = None
                try:
                    idef = self.bungie.get_inventory_item_definition(eq_hash)
                    requested_bucket = (
                        idef.get("Response", {})
                        .get("inventory", {})
                        .get("bucketTypeHash")
                    )
                except Exception:
                    requested_bucket = None

                # Find lowest rarity candidate in source character inventory for same bucket
                replacement = None  # tuple(tierType, instanceId, itemHash)
                try:
                    cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                    for it in (cinv.get(eq_char, {}) or {}).get("items", []):
                        try:
                            if it.get("itemInstanceId") == eq_iid:
                                continue
                            ih = it.get("itemHash")
                            if ih is None:
                                continue
                            idef = self.bungie.get_inventory_item_definition(ih)
                            inv = idef.get("Response", {}).get("inventory", {})
                            bkt = inv.get("bucketTypeHash")
                            if requested_bucket is not None and bkt != requested_bucket:
                                continue
                            tier = inv.get("tierType", 999)
                            cand = (int(tier) if isinstance(tier, int) else 999, it.get("itemInstanceId"), ih)
                            if replacement is None or cand[0] < replacement[0]:
                                replacement = cand
                        except Exception:
                            continue
                except Exception:
                    pass

                # If none in inventory, try vault: bring a low-tier to source char
                if replacement is None and requested_bucket is not None:
                    try:
                        pinv = (
                            profile.get("Response", {})
                            .get("profileInventory", {})
                            .get("data", {})
                            .get("items", [])
                        )
                        best_vault = None  # (tierType, instanceId, itemHash)
                        for it in pinv:
                            try:
                                ih = it.get("itemHash")
                                if ih is None:
                                    continue
                                idef = self.bungie.get_inventory_item_definition(ih)
                                inv = idef.get("Response", {}).get("inventory", {})
                                bkt = inv.get("bucketTypeHash")
                                if bkt != requested_bucket:
                                    continue
                                tier = inv.get("tierType", 999)
                                cand = (int(tier) if isinstance(tier, int) else 999, it.get("itemInstanceId"), ih)
                                if best_vault is None or cand[0] < best_vault[0]:
                                    best_vault = cand
                            except Exception:
                                continue
                        if best_vault is not None:
                            _, viid2, vhash2 = best_vault
                            tr_in = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=eq_char,
                                item_id=viid2,
                                item_reference_hash=vhash2,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                            if tr_in.get("ErrorCode") == 1:
                                replacement = (0, viid2, vhash2)
                    except Exception:
                        pass

                if replacement is None:
                    return (
                        f"I found {item_name} equipped on another character, but I couldn't find a replacement weapon to free it. Equip any filler weapon there and ask me again."
                    )

                # Equip replacement on source character to free the item
                _, rep_iid, _rep_hash = replacement
                try:
                    eq_rep = self.bungie.equip_item(
                        membership_type=destiny_membership_type,
                        item_id=str(rep_iid),
                        character_id=str(eq_char),
                    )
                    if eq_rep.get("ErrorCode") != 1:
                        return f"I tried to equip a replacement to free {item_name}, but Bungie rejected the equip."
                except Exception as _:
                    return f"I tried to equip a replacement to free {item_name}, but something went wrong."

                # Move the requested item from source -> vault -> target
                try:
                    to_vault = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=str(eq_char),
                        item_id=str(eq_iid),
                        item_reference_hash=int(eq_hash),
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    if to_vault.get("ErrorCode") != 1:
                        return f"I equipped a replacement, but couldn't move {item_name} out from that character."
                    try:
                        to_target = self.bungie.transfer_item(
                            membership_type=destiny_membership_type,
                            character_id=target_cid,
                            item_id=str(eq_iid),
                            item_reference_hash=int(eq_hash),
                            stack_size=1,
                            transfer_to_vault=False,
                        )
                    except BungieAPIError as be:
                        txt = str(be)
                        if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                            if _free_slot_on_target(eq_hash):
                                to_target = self.bungie.transfer_item(
                                    membership_type=destiny_membership_type,
                                    character_id=target_cid,
                                    item_id=str(eq_iid),
                                    item_reference_hash=int(eq_hash),
                                    stack_size=1,
                                    transfer_to_vault=False,
                                )
                            else:
                                return f"I moved {item_name} to the vault, but your character has no free slots for it, Guardian."
                        else:
                            raise
                    item_instance_id = eq_iid
                    item_hash = eq_hash
                    did_move = True
                except Exception:
                    return f"I ran into an issue moving {item_name} between characters, Guardian."

            # If still unknown, try to find in the target character's inventory
            if not item_instance_id:
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for it in (cinv.get(target_cid, {}) or {}).get("items", []):
                    try:
                        ih = it.get("itemHash")
                        if ih is None:
                            continue
                        name = self._get_item_name(ih)
                        if not name:
                            continue
                        if self._similarity(name, item_name) >= 0.75:
                            item_instance_id = it.get("itemInstanceId")
                            item_hash = ih
                            break
                    except Exception:
                        continue

            # If not found in target inventory, try other characters, then vault, then postmaster
            if not item_instance_id:
                # Try other character inventories
                o_iid, o_cid, o_hash, _ = self._best_inventory_match(profile, item_name)
                if o_iid and o_cid and o_cid != target_cid:
                    # Cross-character moves must go through the vault: source -> vault -> target
                    tr_to_vault = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=o_cid,
                        item_id=o_iid,
                        item_reference_hash=o_hash,
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    if tr_to_vault.get("ErrorCode") != 1:
                        return f"I tried to move {item_name} from your other character but couldn't send it to the vault, Guardian."
                    tr_to_target = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=o_iid,
                        item_reference_hash=o_hash,
                        stack_size=1,
                        transfer_to_vault=False,
                    )
                    if tr_to_target.get("ErrorCode") != 1:
                        return f"I moved {item_name} to the vault but couldn't bring it to your {class_target or 'current character'}, Guardian."
                    item_instance_id = o_iid
                    item_hash = o_hash
                    did_move = True
                # Try vault/profile inventory
                if not item_instance_id:
                    viid, _, vhash, _ = self._best_vault_match(profile, item_name)
                    if viid and vhash:
                        try:
                            tr = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=target_cid,
                                item_id=viid,
                                item_reference_hash=vhash,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                        except BungieAPIError as be:
                            txt = str(be)
                            if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                                # Free one slot then retry
                                if _free_slot_on_target(vhash):
                                    tr = self.bungie.transfer_item(
                                        membership_type=destiny_membership_type,
                                        character_id=target_cid,
                                        item_id=viid,
                                        item_reference_hash=vhash,
                                        stack_size=1,
                                        transfer_to_vault=False,
                                    )
                                else:
                                    return f"I couldn't make room on your character to transfer {item_name}, Guardian. Try freeing a slot."
                            else:
                                raise
                        item_instance_id = viid
                        item_hash = vhash
                        did_move = True
                # Try postmaster anywhere -> pull to its character, transfer to target
                if not item_instance_id:
                    p_iid, p_char, p_hash, _ = self._best_postmaster_match(profile, item_name)
                    if p_iid and p_char and p_hash:
                        pr = self.bungie.pull_from_postmaster(
                            item_reference_hash=int(p_hash),
                            stack_size=1,
                            item_id=str(p_iid),
                            character_id=str(p_char),
                            membership_type=int(destiny_membership_type),
                        )
                        if pr.get("ErrorCode") != 1:
                            return f"I found {item_name} in your postmaster but couldn't pull it, Guardian."
                        # Now transfer from that character to target
                        try:
                            tr2 = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=target_cid,
                                item_id=p_iid,
                                item_reference_hash=p_hash,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                        except BungieAPIError as be:
                            txt = str(be)
                            if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                                if _free_slot_on_target(p_hash):
                                    tr2 = self.bungie.transfer_item(
                                        membership_type=destiny_membership_type,
                                        character_id=target_cid,
                                        item_id=p_iid,
                                        item_reference_hash=p_hash,
                                        stack_size=1,
                                        transfer_to_vault=False,
                                    )
                                else:
                                    return f"I pulled {item_name}, but couldn't make room on your character to move it, Guardian."
                            else:
                                raise
                        item_instance_id = p_iid
                        item_hash = p_hash
                        did_move = True
                if not item_instance_id:
                    # As a last resort after moves, refresh target inventory to find instance id by hash
                    if did_move and item_hash is not None:
                        try:
                            time.sleep(0.2)
                            profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                            invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                            for itx in (invx.get(target_cid, {}) or {}).get("items", []):
                                if itx.get("itemHash") == item_hash:
                                    item_instance_id = itx.get("itemInstanceId")
                                    break
                            if not item_instance_id:
                                eqx = profx.get("Response", {}).get("characterEquipment", {}).get("data", {})
                                for itx in (eqx.get(target_cid, {}) or {}).get("items", []):
                                    if itx.get("itemHash") == item_hash:
                                        item_instance_id = itx.get("itemInstanceId")
                                        break
                        except Exception:
                            pass
                    if not item_instance_id:
                        return f"I couldn't find '{item_name}' in your inventory, postmaster, or vault, Guardian."

            # Equip the item
            # Retry and refresh profile to resolve DestinyItemNotFound after transfers
            def _refind_instance_on_target(by_hash: int | str | None) -> str | None:
                try:
                    if by_hash is None:
                        return None
                    prof2 = self.bungie.get_profile(
                        destiny_membership_type,
                        destiny_membership_id,
                        [201, 205],
                    )
                    inv2 = prof2.get("Response", {}).get("characterInventories", {}).get("data", {})
                    for it in (inv2.get(target_cid, {}) or {}).get("items", []):
                        if it.get("itemHash") == by_hash:
                            return it.get("itemInstanceId")
                    # Also check equipment in case it was auto-equipped
                    eq2 = prof2.get("Response", {}).get("characterEquipment", {}).get("data", {})
                    for it in (eq2.get(target_cid, {}) or {}).get("items", []):
                        if it.get("itemHash") == by_hash:
                            return it.get("itemInstanceId")
                except Exception:
                    return None
                return None

            # Helper: clear currently equipped exotics on target by equipping non-exotic replacements
            def _clear_exotics_on_target(for_item_hash: int | str | None) -> bool:
                try:
                    prof = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 200, 201, 205, 300])
                    eq = prof.get("Response", {}).get("characterEquipment", {}).get("data", {})
                    inv = prof.get("Response", {}).get("characterInventories", {}).get("data", {})
                    chars = prof.get("Response", {}).get("characters", {}).get("data", {})
                    instances = (
                        prof.get("Response", {})
                        .get("itemComponents", {})
                        .get("instances", {})
                        .get("data", {})
                    )
                    # Determine which buckets we need to clear based on the requested item's category (armor vs. weapon)
                    desired_bucket = None
                    allowed_buckets: set[int] | None = None
                    try:
                        if for_item_hash is not None:
                            idef_req = self.bungie.get_inventory_item_definition(for_item_hash)
                            desired_bucket = (
                                idef_req.get("Response", {})
                                .get("inventory", {})
                                .get("bucketTypeHash")
                            )
                            # Known armor and weapon bucket hashes
                            armor_buckets = {
                                3448275574,  # Helmet
                                3551918588,  # Gauntlets
                                14239492,    # Chest
                                20886954,    # Legs
                                1585787867,  # Class Item
                            }
                            weapon_buckets = {
                                1498876634,  # Kinetic
                                2465295065,  # Energy
                                953998645,   # Power
                            }
                            if isinstance(desired_bucket, int):
                                if desired_bucket in armor_buckets:
                                    allowed_buckets = armor_buckets
                                elif desired_bucket in weapon_buckets:
                                    allowed_buckets = weapon_buckets
                                else:
                                    allowed_buckets = {desired_bucket}
                    except Exception:
                        desired_bucket = None
                        allowed_buckets = None
                    changed = False
                    for it in (eq.get(target_cid, {}) or {}).get("items", []):
                        try:
                            ih = it.get("itemHash")
                            if ih is None:
                                continue
                            idef = self.bungie.get_inventory_item_definition(ih)
                            tier = idef.get("Response", {}).get("inventory", {}).get("tierType")
                            if int(tier) != 6:
                                continue  # not exotic
                            bucket = idef.get("Response", {}).get("inventory", {}).get("bucketTypeHash")
                            # Clear exotics across the relevant category:
                            # - if requested is armor: any exotic armor bucket
                            # - if requested is weapon: any exotic weapon bucket
                            if allowed_buckets is not None and isinstance(bucket, int) and bucket not in allowed_buckets:
                                continue
                            # Find best non-exotic candidate on character in same bucket
                            best = None  # (power, instanceId, itemHash)
                            for it2 in (inv.get(target_cid, {}) or {}).get("items", []):
                                if it2.get("bucketHash") != bucket:
                                    continue
                                ih2 = it2.get("itemHash")
                                idef2 = self.bungie.get_inventory_item_definition(ih2)
                                tier2 = idef2.get("Response", {}).get("inventory", {}).get("tierType")
                                if int(tier2) == 6:
                                    continue
                                iid2 = it2.get("itemInstanceId")
                                power = 0
                                if iid2 and str(iid2) in instances:
                                    power = int(instances[str(iid2)].get("primaryStat", {}).get("value", 0))
                                cand = (power, iid2, ih2)
                                if best is None or cand[0] > best[0]:
                                    best = cand
                            # If none on character, try vault
                            if best is None:
                                pinv = (
                                    prof.get("Response", {})
                                    .get("profileInventory", {})
                                    .get("data", {})
                                    .get("items", [])
                                )
                                for itv in pinv:
                                    if itv.get("bucketHash") != bucket:
                                        continue
                                    ihv = itv.get("itemHash")
                                    idefv = self.bungie.get_inventory_item_definition(ihv)
                                    tierv = idefv.get("Response", {}).get("inventory", {}).get("tierType")
                                    if int(tierv) == 6:
                                        continue
                                    # Bring to character (make room if needed)
                                    try:
                                        tr = self.bungie.transfer_item(
                                            membership_type=destiny_membership_type,
                                            character_id=target_cid,
                                            item_id=itv.get("itemInstanceId"),
                                            item_reference_hash=ihv,
                                            stack_size=1,
                                            transfer_to_vault=False,
                                        )
                                    except BungieAPIError as be2:
                                        t2 = str(be2)
                                        if ("DestinyNoRoomInDestination" in t2) or ('"ErrorCode":1642' in t2) or ("ErrorCode 1642" in t2):
                                            _free_slot_on_target(ihv)
                                            tr = self.bungie.transfer_item(
                                                membership_type=destiny_membership_type,
                                                character_id=target_cid,
                                                item_id=itv.get("itemInstanceId"),
                                                item_reference_hash=ihv,
                                                stack_size=1,
                                                transfer_to_vault=False,
                                            )
                                        else:
                                            raise
                                    # After transfer, set as candidate with default power 0
                                    best = (0, itv.get("itemInstanceId"), ihv)
                                    break
                            # If still none, try other characters' inventories
                            if best is None:
                                for ocid, _cdata in (chars or {}).items():
                                    if ocid == target_cid:
                                        continue
                                    for ito in (inv.get(ocid, {}) or {}).get("items", []):
                                        if ito.get("bucketHash") != bucket:
                                            continue
                                        ihoe = ito.get("itemHash")
                                        try:
                                            idefo = self.bungie.get_inventory_item_definition(ihoe)
                                            tiero = idefo.get("Response", {}).get("inventory", {}).get("tierType")
                                        except Exception:
                                            tiero = 999
                                        if int(tiero) == 6:
                                            continue
                                        # Move via vault then to target
                                        self.bungie.transfer_item(
                                            membership_type=destiny_membership_type,
                                            character_id=ocid,
                                            item_id=ito.get("itemInstanceId"),
                                            item_reference_hash=ihoe,
                                            stack_size=1,
                                            transfer_to_vault=True,
                                        )
                                        try:
                                            self.bungie.transfer_item(
                                                membership_type=destiny_membership_type,
                                                character_id=target_cid,
                                                item_id=ito.get("itemInstanceId"),
                                                item_reference_hash=ihoe,
                                                stack_size=1,
                                                transfer_to_vault=False,
                                            )
                                        except BungieAPIError as be3:
                                            t3 = str(be3)
                                            if ("DestinyNoRoomInDestination" in t3) or ('"ErrorCode":1642' in t3) or ("ErrorCode 1642" in t3):
                                                _free_slot_on_target(ihoe)
                                                self.bungie.transfer_item(
                                                    membership_type=destiny_membership_type,
                                                    character_id=target_cid,
                                                    item_id=ito.get("itemInstanceId"),
                                                    item_reference_hash=ihoe,
                                                    stack_size=1,
                                                    transfer_to_vault=False,
                                                )
                                            else:
                                                continue
                                        best = (0, ito.get("itemInstanceId"), ihoe)
                                        break
                                    if best is not None:
                                        break
                            if best is None or best[1] is None:
                                continue
                            # Equip replacement in that bucket
                            eqr = self.bungie.equip_item(
                                membership_type=destiny_membership_type,
                                item_id=str(best[1]),
                                character_id=str(target_cid),
                            )
                            if eqr.get("ErrorCode") == 1:
                                changed = True
                        except Exception:
                            continue
                    return changed
                except Exception:
                    return False


            # Ensure we have a valid instance id on target before attempting equip
            # First pass: small settle and re-find by hash (handles cross-character moves)
            if item_hash is not None:
                time.sleep(0.6 if did_move else 0.35)
                re_iid = _refind_instance_on_target(item_hash)
                if re_iid:
                    item_instance_id = re_iid
            # If still missing, try a short retry loop to let Bungie sync the move
            if (item_instance_id is None) and (item_hash is not None):
                for wait in (0.25, 0.4, 0.6):
                    time.sleep(wait)
                    re_iid = _refind_instance_on_target(item_hash)
                    if re_iid:
                        item_instance_id = re_iid
                        break
            # As a last resort before equip, if we recently moved it and still don't see the instance,
            # refresh a wider set of components and try to resolve by hash or fuzzy name on the target character.
            if (item_instance_id is None) and (did_move):
                try:
                    profw = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 201, 205])
                    invw = profw.get("Response", {}).get("characterInventories", {}).get("data", {})
                    # Try by hash
                    for itw in (invw.get(target_cid, {}) or {}).get("items", []):
                        if item_hash is not None and itw.get("itemHash") == item_hash:
                            item_instance_id = itw.get("itemInstanceId")
                            break
                    # Try by name if still missing
                    if item_instance_id is None:
                        for itw in (invw.get(target_cid, {}) or {}).get("items", []):
                            ih = itw.get("itemHash")
                            if ih is None:
                                continue
                            nm = self._get_item_name(ih)
                            if nm and self._similarity(nm, item_name) >= 0.75:
                                item_instance_id = itw.get("itemInstanceId")
                                item_hash = ih
                                break
                except Exception:
                    pass

            equip_result = {"ErrorCode": -1}
            for attempt in range(4):
                try:
                    eq = self.bungie.equip_item(
                        membership_type=destiny_membership_type,
                        item_id=item_instance_id,
                        character_id=target_cid
                    )
                    equip_result = eq
                    if eq.get("ErrorCode") == 1:
                        break
                    # Non-success dict response; attempt gentle retry
                    ec = eq.get("ErrorCode")
                    emsg = str(eq)
                    if ec == 1623 or "DestinyItemNotFound" in emsg or "ItemNotFound" in emsg:
                        time.sleep(0.3 * (attempt + 1))
                        new_iid = _refind_instance_on_target(item_hash)
                        if new_iid:
                            item_instance_id = new_iid
                            continue
                    # Handle exotic unique-equip restriction by clearing an equipped exotic first
                    if ec == 1641 or "DestinyItemUniqueEquipRestricted" in emsg:
                        try:
                            if _clear_exotics_on_target(item_hash):
                                time.sleep(0.2)
                                continue
                        except Exception:
                            pass
                except BungieAPIError as be:
                    txt = str(be)
                    # Handle common transient case by refreshing instance id and retrying
                    if "DestinyItemNotFound" in txt or '"ErrorCode":1623' in txt or "ErrorCode 1623" in txt:
                        time.sleep(0.35 * (attempt + 1))
                        new_iid = _refind_instance_on_target(item_hash)
                        if new_iid:
                            item_instance_id = new_iid
                            continue
                        # brief wait before next attempt even if not found
                        time.sleep(0.2)
                        continue
                    # Handle exotic unique-equip restriction when Bungie returns an error
                    if ("DestinyItemUniqueEquipRestricted" in txt) or ('"ErrorCode":1641' in txt) or ("ErrorCode 1641" in txt):
                        try:
                            if _clear_exotics_on_target(item_hash):
                                time.sleep(0.2)
                                continue
                        except Exception:
                            pass
                        # If we couldn't clear, surface original error
                        raise
                    # Other errors: surface them
                    raise
                time.sleep(0.25 * (attempt + 1))

            if equip_result.get("ErrorCode") == 1:
                # Optionally verify equip took effect; do not block success if confirmation lags
                try:
                    time.sleep(0.25)
                    profv = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                    eqv = profv.get("Response", {}).get("characterEquipment", {}).get("data", {})
                    equipped_ok = False
                    for itv in (eqv.get(target_cid, {}) or {}).get("items", []):
                        if (itv.get("itemInstanceId") == item_instance_id) or (item_hash is not None and itv.get("itemHash") == item_hash):
                            equipped_ok = True
                            break
                    if not equipped_ok:
                        try:
                            bulk2 = self.bungie.equip_items(
                                membership_type=destiny_membership_type,
                                character_id=target_cid,
                                item_ids=[item_instance_id],
                            )
                            if bulk2.get("ErrorCode") == 1:
                                time.sleep(0.25)
                                profv2 = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                                eqv2 = profv2.get("Response", {}).get("characterEquipment", {}).get("data", {})
                                for itv in (eqv2.get(target_cid, {}) or {}).get("items", []):
                                    if (itv.get("itemInstanceId") == item_instance_id) or (item_hash is not None and itv.get("itemHash") == item_hash):
                                        equipped_ok = True
                                        break
                        except Exception:
                            pass
                    # Even if not confirmed yet, return success; Bungie may lag a moment
                except Exception:
                    pass
                # Remember last item
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": target_cid,
                }
                return f"Your {item_name} has been equipped, Guardian. Ready for battle!"
            else:
                # Final fallback: small settle, refresh, and try bulk EquipItems once
                try:
                    time.sleep(0.35)
                    # Try to re-find instance and use EquipItems
                    if item_hash is not None:
                        new_iid = _refind_instance_on_target(item_hash)
                        if new_iid:
                            item_instance_id = new_iid
                    # As a final attempt, try clearing exotics once before bulk equip
                    try:
                        _ = _clear_exotics_on_target(item_hash)
                    except Exception:
                        pass
                    bulk = self.bungie.equip_items(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_ids=[item_instance_id],
                    )
                    if bulk.get("ErrorCode") == 1:
                        self._last_item = {
                            "name": item_name,
                            "instance_id": item_instance_id,
                            "character_id": target_cid,
                        }
                        return f"Your {item_name} has been equipped, Guardian. Ready for battle!"
                except Exception:
                    pass
                return f"Sorry Guardian, I couldn't equip your {item_name}. The equip action failed."

        except BungieAPIError as e:
            msg = str(e)
            if "HTTP error 401" in msg:
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            # Friendly mapping for common Bungie equip failures
            if ("DestinyItemFailedUnlockCheck" in msg) or ('"ErrorCode":1639' in msg):
                return (
                    "I can’t equip that, Guardian — Bungie says this character doesn’t meet the item’s equip requirements. "
                    "This usually means the required DLC/license isn’t owned on your active platform, or the item isn’t unlocked on this account yet. "
                    "Try claiming it from Collections, switching characters, or equipping a different item first."
                )
            # Final resilience for DestinyItemNotFound (1623): re-resolve and try bulk equip once
            if ("DestinyItemNotFound" in msg) or ('"ErrorCode":1623' in msg) or ("ErrorCode 1623" in msg):
                try:
                    time.sleep(0.6)
                    def _refind_on_target(by_hash: int | str | None) -> str | None:
                        try:
                            if by_hash is None:
                                return None
                            profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                            invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                            for itx in (invx.get(target_cid, {}) or {}).get("items", []):
                                if itx.get("itemHash") == by_hash:
                                    return itx.get("itemInstanceId")
                            eqx = profx.get("Response", {}).get("characterEquipment", {}).get("data", {})
                            for itx in (eqx.get(target_cid, {}) or {}).get("items", []):
                                if itx.get("itemHash") == by_hash:
                                    return itx.get("itemInstanceId")
                        except Exception:
                            return None
                        return None
                    nid = _refind_on_target(item_hash)
                    if not nid:
                        try:
                            profw = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 201, 205])
                            invw = profw.get("Response", {}).get("characterInventories", {}).get("data", {})
                            for itw in (invw.get(target_cid, {}) or {}).get("items", []):
                                ih = itw.get("itemHash")
                                if ih is None:
                                    continue
                                nm = self._get_item_name(ih)
                                if (item_hash is not None and ih == item_hash) or (nm and self._similarity(nm, item_name) >= 0.75):
                                    nid = itw.get("itemInstanceId")
                                    item_hash = ih
                                    break
                        except Exception:
                            nid = None
                    if nid:
                        bulk = self.bungie.equip_items(
                            membership_type=destiny_membership_type,
                            character_id=target_cid,
                            item_ids=[nid],
                        )
                        if bulk.get("ErrorCode") == 1:
                            return f"Your {item_name} has been equipped, Guardian. Ready for battle!"
                except Exception:
                    pass
            return f"Sorry Guardian, I encountered an error while trying to equip your item: {msg}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while trying to equip your item: {str(e)}"

    def _handle_postmaster_list(self, class_target: str | None = None) -> str:
        """List items currently in the Postmaster across characters."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to check your postmaster."
            destiny_membership_id, destiny_membership_type = destiny_info

            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 200, 201, 205])

            items_by_char: dict[str, list[str]] = {}
            # Determine target character first
            invs = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            # Choose character: class -> active -> first
            target_cid = None
            if class_target:
                class_map = {"titan": 0, "hunter": 1, "warlock": 2}
                target_class = class_map.get(class_target)
                if target_class is not None and isinstance(chars, dict):
                    for _cid, _cdata in chars.items():
                        if _cdata.get("classType") == target_class:
                            target_cid = _cid
                            break
            if not target_cid:
                target_cid = self._active_character_id(profile)
            if not target_cid and isinstance(chars, dict) and chars:
                target_cid = list(chars.keys())[0]

            # Scan character inventories for Postmaster items (location == 4)
            # Always show Lost Items for the active (or specified) character only.
            if isinstance(invs, dict):
                for cid, cdata in invs.items():
                    if target_cid and cid != target_cid:
                        continue
                    for it in cdata.get("items", []):
                        loc = it.get("location")
                        bh = it.get("bucketHash")
                        if loc is None and bh is not None:
                            loc = self._bucket_location_safe(bh)
                        is_pm = (loc == 4) or (bh is not None and self._is_postmaster_bucket(bh))
                        if is_pm:
                            name = self._get_item_name(it.get("itemHash")) or "Unknown Item"
                            items_by_char.setdefault(cid, []).append(name)            # If nothing detected for the chosen character, report empty and suggest targeting
            total = sum(len(v) for v in items_by_char.values())
            if total == 0:
                # If no explicit class was requested and nothing found, try a quick vendor-based hint instead of a false empty
                hint = " Try specifying a character, e.g. 'on my Hunter'." if class_target is None else ""
                return f"Your postmaster is empty, Guardian.{hint}"

            response = "Here's what's in your Postmaster, Guardian:\n\n"
            shown = 0
            for char_id, names in items_by_char.items():
                for nm in names:
                    response += f"- {nm}\n"
                    shown += 1
                    if shown >= 20:
                        break
                if shown >= 20:
                    break
            if total > shown:
                response += f"\n...and {total - shown} more items."
            self._last_location = "postmaster"
            return response
        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate."
            return f"Sorry Guardian, I couldn't list your postmaster: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't list your postmaster: {str(e)}"

    def _handle_pull_from_postmaster(self, item_name: str) -> str:
        """Pull an item from the Postmaster to inventory and remember it."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your postmaster."
            destiny_membership_id, destiny_membership_type = destiny_info

            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])

            item_instance_id, character_id, item_hash, _ = self._best_postmaster_match(profile, item_name)
            if not item_instance_id:
                return f"I couldn't find '{item_name}' in your postmaster, Guardian."

            # If character id unknown, choose first character as target
            if not character_id:
                chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                if not chars:
                    return "I couldn't find a character to receive the item, Guardian."
                character_id = list(chars.keys())[0]

            # Pull from postmaster
            pr = self.bungie.pull_from_postmaster(
                item_reference_hash=int(item_hash),
                stack_size=1,
                item_id=str(item_instance_id),
                character_id=str(character_id),
                membership_type=int(destiny_membership_type),
            )
            if pr.get("ErrorCode") == 1:
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": character_id,
                    "hash": item_hash,
                }
                return f"I've pulled {item_name} from your postmaster to your inventory, Guardian."
            return f"Sorry Guardian, I couldn't pull {item_name} from your postmaster."
        except BungieAPIError as e:
            if "DestinyCannotPerformActionAtThisLocation" in str(e):
                return "I can't pull that from the postmaster right now, Guardian. Try visiting the Tower first."
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate."
            return f"Sorry Guardian, I encountered an error pulling your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error pulling your item: {str(e)}"

    def _handle_dismantle_item(self, item_name: str) -> str:
        """Dismantle an item by name. If found in Postmaster, pull first then dismantle."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to dismantle items."
            destiny_membership_id, destiny_membership_type = destiny_info

            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])

            # Prefer items already in inventory
            item_instance_id, character_id, _, _ = self._best_inventory_match(profile, item_name)
            # If not in inventory, check postmaster and pull first
            if not item_instance_id:
                pm_iid, pm_char, pm_hash, _ = self._best_postmaster_match(profile, item_name)
                if not pm_iid:
                    return f"I couldn't find '{item_name}' to dismantle, Guardian."
                if not pm_char:
                    chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                    if not chars:
                        return "I couldn't find a character to receive the item, Guardian."
                    pm_char = list(chars.keys())[0]
                pr = self.bungie.pull_from_postmaster(
                    item_reference_hash=int(pm_hash),
                    stack_size=1,
                    item_id=str(pm_iid),
                    character_id=str(pm_char),
                    membership_type=int(destiny_membership_type),
                )
                if pr.get("ErrorCode") != 1:
                    return f"I found {item_name} in your postmaster but couldn't pull it to dismantle, Guardian."
                item_instance_id = pm_iid
                character_id = pm_char

            # Dismantle
            dr = self.bungie.dismantle_item(
                membership_type=destiny_membership_type,
                character_id=str(character_id),
                item_id=str(item_instance_id),
            )
            if dr.get("ErrorCode") == 1:
                return f"I've dismantled {item_name}, Guardian."
            return f"Sorry Guardian, I couldn't dismantle {item_name}."
        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate."
            return f"Sorry Guardian, I encountered an error while dismantling: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while dismantling: {str(e)}"

    def _handle_stats_request(self, stat_type: str | None = None, send_with_system=None, model_provider: str = "ollama") -> str:
        """Handle stats requests."""
        logger = logging.getLogger("ghost")
        try:
            destiny_info = self._get_destiny_membership()
            logger.info(f"[assistant] Destiny info: {destiny_info}")
            if not destiny_info:
                return "Ah, Guardian! To show you your glorious stats, I need you to authenticate with Bungie first. Head over to the authentication page and link your account!"

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile to find characters
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])

            if not profile.get("Response", {}).get("characters", {}).get("data"):
                return "Hmm, I can't seem to find your character information, Guardian. Make sure your Bungie account is properly linked."

            # Get stats for the first character
            character_id = list(profile["Response"]["characters"]["data"].keys())[0]

            stats = self.bungie.get_historical_stats_for_account(destiny_membership_type, destiny_membership_id, groups=[1])

            # If no merged stats, try per character
            if not stats.get("Response", {}).get("mergedAllCharacters", {}).get("results"):
                logger.info("[assistant] No merged stats, trying per character")
                stats = self.bungie.get_historical_stats(destiny_membership_type, destiny_membership_id, character_id, groups=[1])

            if not stats.get("Response"):
                return "I couldn't retrieve your stats from Bungie, Guardian. Their servers might be having a moment."

            # Debug logging
            logger = logging.getLogger("ghost")
            logger.info(f"[assistant] Stats response: {stats}")

            # Parse and format key stats
            merged_stats = None
            if "mergedAllCharacters" in stats["Response"] and stats["Response"]["mergedAllCharacters"].get("results"):
                merged_stats = stats["Response"]["mergedAllCharacters"]["results"]
            elif isinstance(stats["Response"], dict) and any(key in stats["Response"] for key in ["activitiesCleared", "kills", "deaths"]):
                merged_stats = stats["Response"]
            else:
                # Try to find stats in other possible locations
                response_data = stats["Response"]
                if "characters" in response_data:
                    # Per-character response structure
                    char_data = response_data["characters"]
                    if isinstance(char_data, dict) and character_id in char_data:
                        merged_stats = char_data[character_id].get("stats", {})

            logger.info(f"[assistant] Merged stats: {merged_stats}")

            if not merged_stats:
                return "I can see your account, Guardian, but it looks like you haven't played enough Destiny 2 yet to have meaningful stats. Get out there and make some Light!"

            # Let the AI model format the stats response naturally

            # Prepare stats data for the model
            stats_data = {}
            for category, category_data in merged_stats.items():
                if not isinstance(category_data, dict) or "allTime" not in category_data:
                    continue
                all_time_stats = category_data["allTime"]
                category_stats = {}
                for stat_key, stat_data in all_time_stats.items():
                    if isinstance(stat_data, dict) and "basic" in stat_data:
                        display_value = stat_data["basic"].get("displayValue", "")
                        if display_value and display_value not in ["0", "0.0", "0.00"]:
                            display_name = stat_data["basic"].get("displayName", stat_key.replace('weaponKills', '').replace('Kills', ' Kills'))
                            category_stats[display_name] = display_value
                if category_stats:
                    category_name = category.replace('all', '').upper()  # allPvE -> PvE
                    stats_data[category_name] = category_stats

            if not stats_data:
                return "🫥 I found your account, but your stats seem to be hiding from me. Try playing a few more games to unlock some statistics!"

            # Use AI to format the response
            system_prompt = (
                "You are the Ghost from Destiny 2. Respond in short, simple sentences like in the game. "
                "For stats, use simple bullet point lists. Keep responses brief. "
                "Group by PvE and PvP categories. No verbose commentary."
            )

            user_prompt = f"Format these Destiny 2 stats for the player:\n\n{stats_data}\n\nRespond as the Ghost."

            return send_with_system(system_prompt, user_prompt)

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            logger.exception(f"[assistant] Bungie API error in stats request: {e}")
            return f"Sorry Guardian, I encountered an error while retrieving your stats: {str(e)}. Try again in a moment."
        except Exception as e:
            logger.exception(f"[assistant] Error in stats request: {e}")
            return f"Sorry Guardian, I encountered an error while retrieving your stats: {str(e)}. Try again in a moment."

    def _handle_transfer_pronoun(self, target: str) -> str:
        """Handle pronoun-based transfer using the last referenced item.

        target must be 'vault' or 'inventory'.
        """
        try:
            if not self._last_item or not self._last_item.get("instance_id"):
                return "I don't recall which item you mean, Guardian. Please say the item name."

            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            destiny_membership_id, destiny_membership_type = destiny_info

            # Prefer last known character; if moving to inventory and missing, pick first
            character_id = self._last_item.get("character_id")
            if target == "inventory" and not character_id:
                profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])
                chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                if not chars:
                    return "I couldn't find a character to transfer to, Guardian."
                character_id = list(chars.keys())[0]

            item_instance_id = self._last_item.get("instance_id")
            item_hash = self._last_item.get("hash")

            to_vault = (target == "vault")
            result = self.bungie.transfer_item(
                membership_type=destiny_membership_type,
                character_id=character_id,
                item_id=item_instance_id,
                item_reference_hash=item_hash,
                stack_size=1,
                transfer_to_vault=to_vault,
            )
            if result.get("ErrorCode") == 1:
                if to_vault:
                    return f"All set, Guardian. I've moved {self._last_item.get('name','the item')} back to your vault."
                return f"Done, Guardian. I've moved {self._last_item.get('name','the item')} to your inventory."
            return "Sorry Guardian, the transfer failed."
        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while transferring your item: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while transferring your item: {str(e)}"

    def _handle_transfer_to_character(self, item_name: str, class_target: str) -> str:
        """Transfer an item to the specified class (hunter/warlock/titan) or active character (me)."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            destiny_membership_id, destiny_membership_type = destiny_info

            # Load characters + inventories + equipment + profile inventory
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 200, 201, 205])
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            class_map = {"titan": 0, "hunter": 1, "warlock": 2}
            want = class_map.get(class_target)
            target_cid = None
            if class_target == "me":
                target_cid = self._active_character_id(profile)
            elif want is not None:
                for cid, cdata in (chars or {}).items():
                    if cdata.get("classType") == want:
                        target_cid = cid
                        break
            if not target_cid:
                return ("I couldn't find your current character, Guardian." if class_target == "me"
                        else "I couldn't find your {0} character, Guardian.".format(class_target))

            # Human-friendly name for target: if 'me', translate to actual class name
            if class_target == "me":
                class_type = None
                try:
                    if target_cid and target_cid in (chars or {}):
                        class_type = (chars or {}).get(target_cid, {}).get("classType")
                except Exception:
                    class_type = None
                class_names = {0: "titan", 1: "hunter", 2: "warlock"}
                display_target = class_names.get(class_type, "current character")
            else:
                display_target = class_target

            # Helper: free one slot in target inventory for this item's bucket (handles 1642)
            def _free_slot_on_target(for_item_hash: int | str | None) -> bool:
                try:
                    if for_item_hash is None:
                        return False
                    idef = self.bungie.get_inventory_item_definition(for_item_hash)
                    bucket_hash = (
                        idef.get("Response", {})
                        .get("inventory", {})
                        .get("bucketTypeHash")
                    )
                    if not bucket_hash:
                        return False
                    profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205, 300])
                    invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                    instances = (
                        profx.get("Response", {})
                        .get("itemComponents", {})
                        .get("instances", {})
                        .get("data", {})
                    )
                    best = None  # (tierType, power, instanceId, itemHash)
                    for itx in (invx.get(target_cid, {}) or {}).get("items", []):
                        if itx.get("bucketHash") != bucket_hash:
                            continue
                        ihx = itx.get("itemHash")
                        try:
                            idef2 = self.bungie.get_inventory_item_definition(ihx)
                            inv2 = idef2.get("Response", {}).get("inventory", {})
                            tier = inv2.get("tierType", 999)
                        except Exception:
                            tier = 999
                        iid2 = itx.get("itemInstanceId")
                        power = 9999
                        if iid2 and str(iid2) in instances:
                            power = instances[str(iid2)].get("primaryStat", {}).get("value", 9999)
                        cand = (int(tier) if isinstance(tier, int) else 999, int(power), iid2, ihx)
                        if best is None or cand < best:
                            best = cand
                    if best is None or best[2] is None:
                        return False
                    _, _, rid, rhash = best
                    tr_out = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=str(rid),
                        item_reference_hash=int(rhash),
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    return tr_out.get("ErrorCode") == 1 if isinstance(tr_out, dict) else True
                except Exception:
                    return False

            # If the request likely refers to the last item ('it') or a near match,
            # prefer resolving by the last known instance to avoid fuzzy mismatches.
            preferred_iid = None
            preferred_hash = None
            preferred_source = None
            try:
                if self._last_item and self._similarity(self._last_item.get("name", ""), item_name) >= 0.75:
                    preferred_iid = str(self._last_item.get("instance_id")) if self._last_item.get("instance_id") else None
                    preferred_hash = self._last_item.get("hash")
                    preferred_source = self._last_item.get("character_id")
                    # Verify current location of preferred_iid across inventories/equipment
                    if preferred_iid:
                        found_now = False
                        cinv_now = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                        for cid_now, cdata_now in (cinv_now or {}).items():
                            for it_now in cdata_now.get("items", []) or []:
                                if str(it_now.get("itemInstanceId")) == preferred_iid:
                                    preferred_source = cid_now
                                    preferred_hash = it_now.get("itemHash", preferred_hash)
                                    found_now = True
                                    break
                            if found_now:
                                break
                        if not found_now:
                            ceq_now = profile.get("Response", {}).get("characterEquipment", {}).get("data", {})
                            for cid_now, cdata_now in (ceq_now or {}).items():
                                for it_now in cdata_now.get("items", []) or []:
                                    if str(it_now.get("itemInstanceId")) == preferred_iid:
                                        preferred_source = cid_now
                                        preferred_hash = it_now.get("itemHash", preferred_hash)
                                        found_now = True
                                        break
                                if found_now:
                                    break
                        # If still not found, quick refresh of inventory/equipment components
                        if not found_now:
                            try:
                                time.sleep(0.2)
                                prof_now = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                                cinv2 = prof_now.get("Response", {}).get("characterInventories", {}).get("data", {})
                                for cid_now, cdata_now in (cinv2 or {}).items():
                                    for it_now in cdata_now.get("items", []) or []:
                                        if str(it_now.get("itemInstanceId")) == preferred_iid:
                                            preferred_source = cid_now
                                            preferred_hash = it_now.get("itemHash", preferred_hash)
                                            found_now = True
                                            break
                                    if found_now:
                                        break
                                if not found_now:
                                    ceq2 = prof_now.get("Response", {}).get("characterEquipment", {}).get("data", {})
                                    for cid_now, cdata_now in (ceq2 or {}).items():
                                        for it_now in cdata_now.get("items", []) or []:
                                            if str(it_now.get("itemInstanceId")) == preferred_iid:
                                                preferred_source = cid_now
                                                preferred_hash = it_now.get("itemHash", preferred_hash)
                                                found_now = True
                                                break
                                        if found_now:
                                            break
                            except Exception:
                                pass
            except Exception:
                preferred_iid = None

            # Try character inventories (any character)
            item_instance_id, source_cid, item_hash, _ = self._best_inventory_match(profile, item_name)
            # Override with preferred instance if available
            if preferred_iid is not None and preferred_source is not None:
                item_instance_id = preferred_iid
                source_cid = preferred_source
                if preferred_hash is not None:
                    item_hash = preferred_hash
            if item_instance_id and source_cid:
                if source_cid != target_cid:
                    # Cross-character transfer must go via the vault
                    to_vault = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=source_cid,
                        item_id=item_instance_id,
                        item_reference_hash=item_hash,
                        stack_size=1,
                        transfer_to_vault=True,
                    )
                    if to_vault.get("ErrorCode") != 1:
                        return f"I tried to move {item_name} to your {class_target}, but couldn't send it to the vault first, Guardian."
                    to_target = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=item_instance_id,
                        item_reference_hash=item_hash,
                        stack_size=1,
                        transfer_to_vault=False,
                    )
                    if to_target.get("ErrorCode") == 1:
                        self._last_item = {"name": item_name, "instance_id": item_instance_id, "character_id": target_cid, "hash": item_hash}
                        return f"I've moved {item_name} to your {display_target}, Guardian."
                    return f"I moved {item_name} to the vault but couldn't bring it to your {display_target}, Guardian."
                else:
                    # Item appears to already be on target; if recent context disagrees, verify after a short settle
                    try:
                        needs_verify = False
                        if self._last_item and self._similarity(self._last_item.get("name", ""), item_name) >= 0.75:
                            if self._last_item.get("character_id") and self._last_item.get("character_id") != target_cid:
                                needs_verify = True
                        if needs_verify:
                            time.sleep(0.35)
                            profile2 = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 200, 201, 205])
                            i2, s2, h2, _ = self._best_inventory_match(profile2, item_name)
                            if i2 and s2 and s2 != target_cid:
                                # Update state to continue flow to transfer
                                item_instance_id, source_cid, item_hash = i2, s2, h2
                            else:
                                # Remember last item context on confirm
                                try:
                                    self._last_item = {"name": item_name, "instance_id": item_instance_id, "character_id": target_cid, "hash": item_hash}
                                except Exception:
                                    pass
                                return f"{item_name} is already on your {display_target}, Guardian."
                        else:
                            try:
                                self._last_item = {"name": item_name, "instance_id": item_instance_id, "character_id": target_cid, "hash": item_hash}
                            except Exception:
                                pass
                            return f"{item_name} is already on your {display_target}, Guardian."
                    except Exception:
                        try:
                            self._last_item = {"name": item_name, "instance_id": item_instance_id, "character_id": target_cid, "hash": item_hash}
                        except Exception:
                            pass
                        return f"{item_name} is already on your {display_target}, Guardian."

            # Try vault
            v_iid, _, v_hash, _ = self._best_vault_match(profile, item_name)
            if v_iid and v_hash:
                try:
                    tr = self.bungie.transfer_item(
                        membership_type=destiny_membership_type,
                        character_id=target_cid,
                        item_id=v_iid,
                        item_reference_hash=v_hash,
                        stack_size=1,
                        transfer_to_vault=False,
                    )
                except BungieAPIError as be:
                    txt = str(be)
                    if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                        if _free_slot_on_target(v_hash):
                            tr = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=target_cid,
                                item_id=v_iid,
                                item_reference_hash=v_hash,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                        else:
                            return f"Your {class_target} has no free slots for {item_name}, Guardian. I couldn't make room."
                    else:
                        raise
                if tr.get("ErrorCode") == 1:
                    self._last_item = {"name": item_name, "instance_id": v_iid, "character_id": target_cid, "hash": v_hash}
                    return f"I've moved {item_name} from your vault to your {display_target}, Guardian."
                return f"Sorry Guardian, I couldn't transfer {item_name} from your vault."

            # Try postmaster
            p_iid, p_cid, p_hash, _ = self._best_postmaster_match(profile, item_name)
            if p_iid and p_hash:
                if not p_cid:
                    # pick first character to pull
                    if not chars:
                        return "I couldn't find a character to receive the item, Guardian."
                    p_cid = list(chars.keys())[0]
                pr = self.bungie.pull_from_postmaster(
                    item_reference_hash=int(p_hash),
                    stack_size=1,
                    item_id=str(p_iid),
                    character_id=str(p_cid),
                    membership_type=int(destiny_membership_type),
                )
                if pr.get("ErrorCode") != 1:
                    return f"I found {item_name} in your postmaster but couldn't pull it, Guardian."
                if p_cid != target_cid:
                    try:
                        tr2 = self.bungie.transfer_item(
                            membership_type=destiny_membership_type,
                            character_id=target_cid,
                            item_id=p_iid,
                            item_reference_hash=p_hash,
                            stack_size=1,
                            transfer_to_vault=False,
                        )
                    except BungieAPIError as be:
                        txt = str(be)
                        if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                            if _free_slot_on_target(p_hash):
                                tr2 = self.bungie.transfer_item(
                                    membership_type=destiny_membership_type,
                                    character_id=target_cid,
                                    item_id=p_iid,
                                    item_reference_hash=p_hash,
                                    stack_size=1,
                                    transfer_to_vault=False,
                                )
                            else:
                                return f"I pulled {item_name}, but couldn't make room on your {display_target}, Guardian."
                        else:
                            raise
                self._last_item = {"name": item_name, "instance_id": p_iid, "character_id": target_cid, "hash": p_hash}
                return f"I've moved {item_name} to your {display_target}, Guardian."

            # Try equipped: safe swap on source, then move via vault -> target
            e_iid, e_cid, e_hash, _ = self._best_equipped_match(profile, item_name)
            if e_iid and e_cid:
                if e_cid == target_cid:
                    try:
                        self._last_item = {"name": item_name, "instance_id": e_iid, "character_id": target_cid, "hash": e_hash}
                    except Exception:
                        pass
                    return f"{item_name} is already on your {display_target}, Guardian."
                # Determine bucket for requested item
                requested_bucket = None
                try:
                    idef = self.bungie.get_inventory_item_definition(e_hash)
                    requested_bucket = (
                        idef.get("Response", {})
                        .get("inventory", {})
                        .get("bucketTypeHash")
                    )
                except Exception:
                    requested_bucket = None
                # Find a low-tier replacement on source inventory or bring one from vault
                replacement = None  # (tierType, instanceId, itemHash)
                try:
                    cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                    for it in (cinv.get(e_cid, {}) or {}).get("items", []):
                        try:
                            if it.get("itemInstanceId") == e_iid:
                                continue
                            ih = it.get("itemHash")
                            if ih is None:
                                continue
                            idef2 = self.bungie.get_inventory_item_definition(ih)
                            inv2 = idef2.get("Response", {}).get("inventory", {})
                            bkt2 = inv2.get("bucketTypeHash")
                            if requested_bucket is not None and bkt2 != requested_bucket:
                                continue
                            tier = inv2.get("tierType", 999)
                            cand = (int(tier) if isinstance(tier, int) else 999, it.get("itemInstanceId"), ih)
                            if replacement is None or cand[0] < replacement[0]:
                                replacement = cand
                        except Exception:
                            continue
                except Exception:
                    pass
                if replacement is None and requested_bucket is not None:
                    try:
                        pinv = (
                            profile.get("Response", {})
                            .get("profileInventory", {})
                            .get("data", {})
                            .get("items", [])
                        )
                        best_vault = None
                        for it in pinv:
                            try:
                                ih = it.get("itemHash")
                                if ih is None:
                                    continue
                                idef3 = self.bungie.get_inventory_item_definition(ih)
                                inv3 = idef3.get("Response", {}).get("inventory", {})
                                bkt3 = inv3.get("bucketTypeHash")
                                if bkt3 != requested_bucket:
                                    continue
                                tier = inv3.get("tierType", 999)
                                cand = (int(tier) if isinstance(tier, int) else 999, it.get("itemInstanceId"), ih)
                                if best_vault is None or cand[0] < best_vault[0]:
                                    best_vault = cand
                            except Exception:
                                continue
                        if best_vault is not None:
                            _, viid2, vhash2 = best_vault
                            tr_in = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=e_cid,
                                item_id=viid2,
                                item_reference_hash=vhash2,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                            if tr_in.get("ErrorCode") == 1:
                                replacement = (0, viid2, vhash2)
                    except Exception:
                        pass
                if replacement is None:
                    return (
                        f"I found {item_name} equipped on another character, but I couldn't find a replacement to free it. Equip any filler weapon there and ask me again."
                    )
                # Equip replacement on source character
                _, rep_iid, _rep_hash = replacement
                try:
                    eq_rep = self.bungie.equip_item(
                        membership_type=destiny_membership_type,
                        item_id=str(rep_iid),
                        character_id=str(e_cid),
                    )
                    if eq_rep.get("ErrorCode") != 1:
                        return f"I tried to equip a replacement to free {item_name}, but Bungie rejected the equip."
                except Exception:
                    return f"I tried to equip a replacement to free {item_name}, but something went wrong."
                # Move requested from source -> vault -> target
                to_vault = self.bungie.transfer_item(
                    membership_type=destiny_membership_type,
                    character_id=str(e_cid),
                    item_id=str(e_iid),
                    item_reference_hash=int(e_hash),
                    stack_size=1,
                    transfer_to_vault=True,
                )
                if to_vault.get("ErrorCode") != 1:
                    return f"I equipped a replacement, but couldn't move {item_name} out from that character."
                to_target = self.bungie.transfer_item(
                    membership_type=destiny_membership_type,
                    character_id=target_cid,
                    item_id=str(e_iid),
                    item_reference_hash=int(e_hash),
                    stack_size=1,
                    transfer_to_vault=False,
                )
                if to_target.get("ErrorCode") != 1:
                    return f"I moved {item_name} to the vault but couldn't bring it to your {display_target}, Guardian."
                self._last_item = {"name": item_name, "instance_id": e_iid, "character_id": target_cid, "hash": e_hash}
                return f"I've moved {item_name} to your {display_target}, Guardian."

            return f"I couldn't find '{item_name}' in your inventory, postmaster, or vault, Guardian."
        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate."
            return f"Sorry Guardian, I encountered an error while transferring: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while transferring: {str(e)}"

    def _handle_transfer_then_equip(self, item_name: str, explicit_from_vault: bool) -> str:
        """Transfer an item from vault if necessary, then equip it."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            destiny_membership_id, destiny_membership_type = destiny_info

            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 107, 111, 112])

            # Warm up defs quickly in background
            try:
                hashes = set()
                pinv = profile.get("Response", {}).get("profileInventory", {}).get("data", {}).get("items", [])
                for it in pinv:
                    ih = it.get("itemHash")
                    if ih is not None:
                        hashes.add(ih)
                cinv = profile.get("Response", {}).get("characterInventories", {}).get("data", {})
                for _, cdata in cinv.items():
                    for it in cdata.get("items", []):
                        ih = it.get("itemHash")
                        if ih is not None:
                            hashes.add(ih)
                self._warmup_defs_async(hashes)
            except Exception:
                pass

            # Try to find in inventory first
            item_instance_id, character_id, item_hash, _ = self._best_inventory_match(profile, item_name)
            if not item_instance_id:
                # Try postmaster first
                pm_iid, pm_char, pm_hash, _ = self._best_postmaster_match(profile, item_name)
                if pm_iid:
                    if not pm_char:
                        characters = profile.get("Response", {}).get("characters", {}).get("data", {})
                        if not characters:
                            return "I couldn't find a character to receive the item, Guardian."
                        pm_char = list(characters.keys())[0]
                    pr = self.bungie.pull_from_postmaster(
                        item_reference_hash=int(pm_hash),
                        stack_size=1,
                        item_id=str(pm_iid),
                        character_id=str(pm_char),
                        membership_type=int(destiny_membership_type),
                    )
                    if pr.get("ErrorCode") != 1:
                        return f"I found {item_name} in your postmaster but couldn't pull it, Guardian."
                    item_instance_id = pm_iid
                    character_id = pm_char
                    item_hash = pm_hash
                else:
                    # If instructed or not found, bring from vault
                    if explicit_from_vault or True:
                        viid, _, vhash, _ = self._best_vault_match(profile, item_name)
                        if not viid:
                            return f"I couldn't find '{item_name}' in your postmaster, vault, or inventory, Guardian."
                        # pick a character
                        characters = profile.get("Response", {}).get("characters", {}).get("data", {})
                        if not characters:
                            return "I couldn't find a character to receive the item, Guardian."
                        character_id = list(characters.keys())[0]
                        try:
                            tr = self.bungie.transfer_item(
                                membership_type=destiny_membership_type,
                                character_id=character_id,
                                item_id=viid,
                                item_reference_hash=vhash,
                                stack_size=1,
                                transfer_to_vault=False,
                            )
                        except BungieAPIError as be:
                            txt = str(be)
                            if ("DestinyNoRoomInDestination" in txt) or ('"ErrorCode":1642' in txt) or ("ErrorCode 1642" in txt):
                                # free a slot on chosen character first
                                # reuse equip flow helper if same scope; otherwise implement quick free
                                try:
                                    # Minimal local free using item hash
                                    if _free_slot_on_target(vhash):
                                        tr = self.bungie.transfer_item(
                                            membership_type=destiny_membership_type,
                                            character_id=character_id,
                                            item_id=viid,
                                            item_reference_hash=vhash,
                                            stack_size=1,
                                            transfer_to_vault=False,
                                        )
                                    else:
                                        return f"I couldn't make room on your character to bring {item_name} from the vault, Guardian."
                                except Exception:
                                    return f"I couldn't make room on your character to bring {item_name} from the vault, Guardian."
                            else:
                                raise
                        # After transfer, set instance id for equip
                        item_instance_id = viid
                        item_hash = vhash
            if not item_instance_id or not character_id:
                return f"I couldn't prepare '{item_name}' for equip, Guardian."

            # Equip with a resilient retry similar to _handle_equip_item
            def _refind_on_target(by_hash: int | str | None) -> str | None:
                try:
                    if by_hash is None:
                        return None
                    profx = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                    invx = profx.get("Response", {}).get("characterInventories", {}).get("data", {})
                    for itx in (invx.get(character_id, {}) or {}).get("items", []):
                        if itx.get("itemHash") == by_hash:
                            return itx.get("itemInstanceId")
                    eqx = profx.get("Response", {}).get("characterEquipment", {}).get("data", {})
                    for itx in (eqx.get(character_id, {}) or {}).get("items", []):
                        if itx.get("itemHash") == by_hash:
                            return itx.get("itemInstanceId")
                except Exception:
                    return None
                return None

            eq_result = {"ErrorCode": -1}
            # Small settle after transfers
            time.sleep(0.35)
            for attempt in range(4):
                try:
                    eq = self.bungie.equip_item(
                        membership_type=destiny_membership_type,
                        item_id=item_instance_id,
                        character_id=character_id,
                    )
                    eq_result = eq
                    if eq.get("ErrorCode") == 1:
                        break
                    ec = eq.get("ErrorCode")
                    emsg = str(eq)
                    if ec == 1623 or "DestinyItemNotFound" in emsg or "ItemNotFound" in emsg:
                        time.sleep(0.3 * (attempt + 1))
                        new_iid = _refind_on_target(item_hash)
                        if new_iid:
                            item_instance_id = new_iid
                            continue
                    if ec == 1641 or "DestinyItemUniqueEquipRestricted" in emsg:
                        # Clear exotics and retry
                        if _clear_exotics_on_target(item_hash):
                            time.sleep(0.2)
                            continue
                except BungieAPIError as be:
                    txt = str(be)
                    if "DestinyItemNotFound" in txt or '"ErrorCode":1623' in txt or "ErrorCode 1623" in txt:
                        time.sleep(0.35 * (attempt + 1))
                        new_iid = _refind_on_target(item_hash)
                        if new_iid:
                            item_instance_id = new_iid
                            continue
                        time.sleep(0.2)
                        continue
                    if ("DestinyItemUniqueEquipRestricted" in txt) or ('"ErrorCode":1641' in txt) or ("ErrorCode 1641" in txt):
                        if _clear_exotics_on_target(item_hash):
                            time.sleep(0.2)
                            continue
                        # If we couldn't clear, surface error
                        raise
                    raise
                time.sleep(0.25 * (attempt + 1))

            if eq_result.get("ErrorCode") == 1:
                # Optionally verify, but do not block success if confirmation lags
                try:
                    time.sleep(0.25)
                    profv = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                    eqv = profv.get("Response", {}).get("characterEquipment", {}).get("data", {})
                    equipped_ok = False
                    for itv in (eqv.get(character_id, {}) or {}).get("items", []):
                        if (itv.get("itemInstanceId") == item_instance_id) or (item_hash is not None and itv.get("itemHash") == item_hash):
                            equipped_ok = True
                            break
                    if not equipped_ok:
                        try:
                            bulk2 = self.bungie.equip_items(
                                membership_type=destiny_membership_type,
                                character_id=character_id,
                                item_ids=[item_instance_id],
                            )
                            if bulk2.get("ErrorCode") == 1:
                                time.sleep(0.25)
                                profv2 = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [201, 205])
                                eqv2 = profv2.get("Response", {}).get("characterEquipment", {}).get("data", {})
                                for itv in (eqv2.get(character_id, {}) or {}).get("items", []):
                                    if (itv.get("itemInstanceId") == item_instance_id) or (item_hash is not None and itv.get("itemHash") == item_hash):
                                        equipped_ok = True
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
                self._last_item = {
                    "name": item_name,
                    "instance_id": item_instance_id,
                    "character_id": character_id,
                }
                return f"Transferred and equipped {item_name}, Guardian."
            # Final fallback: try EquipItems once
            try:
                time.sleep(0.3)
                if item_hash is not None:
                    ni = _refind_on_target(item_hash)
                    if ni:
                        item_instance_id = ni
                bulk = self.bungie.equip_items(
                    membership_type=destiny_membership_type,
                    character_id=character_id,
                    item_ids=[item_instance_id],
                )
                if bulk.get("ErrorCode") == 1:
                    self._last_item = {
                        "name": item_name,
                        "instance_id": item_instance_id,
                        "character_id": character_id,
                    }
                    return f"Transferred and equipped {item_name}, Guardian."
            except Exception:
                pass
            return f"I transferred {item_name}, but equipping failed, Guardian."
        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while transferring and equipping: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while transferring and equipping: {str(e)}"

    def _warmup_defs_async(self, hashes: set) -> None:
        """Background fetch of item definitions to warm cache."""
        try:
            import threading

            def worker(hs: set):
                for ih in hs:
                    try:
                        self.bungie.get_inventory_item_definition(ih)
                    except Exception:
                        continue

            if hashes:
                t = threading.Thread(target=worker, args=(set(hashes),), daemon=True)
                t.start()
        except Exception:
            pass

    def _handle_vendor_request(self, location: str | None = None) -> str:
        """Handle vendor requests."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to visit vendors, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile to find characters
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])

            if not profile.get("Response", {}).get("characters", {}).get("data"):
                return "I couldn't retrieve your character information, Guardian."

            # Get vendors for the first character
            character_id = list(profile["Response"]["characters"]["data"].keys())[0]

            vendors = self.bungie.get_vendors(destiny_membership_type, destiny_membership_id, character_id)

            if not vendors.get("Response", {}).get("vendors", {}).get("data"):
                return "I couldn't retrieve vendor information, Guardian."

            response = "Here are the vendors available to you, Guardian:\n\n"

            vendor_data = vendors["Response"]["vendors"]["data"]
            for vendor_hash, vendor_info in list(vendor_data.items())[:10]:  # Limit to first 10
                vendor_name = vendor_info.get("vendorLocationIndex", "Unknown Vendor")
                # Try to get vendor definition for name
                try:
                    vendor_def = self.bungie._get(f"/Destiny2/Manifest/DestinyVendorDefinition/{vendor_hash}/", authenticated=False)
                    if vendor_def.get("Response", {}).get("displayProperties", {}).get("name"):
                        vendor_name = vendor_def["Response"]["displayProperties"]["name"]
                except:
                    pass

                response += f"• {vendor_name}\n"

            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving vendor information: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving vendor information: {str(e)}"

    def _handle_milestone_request(self, milestone_type: str | None = None) -> str:
        """Handle milestone requests."""
        try:
            milestones = self.bungie.get_milestones()

            if not milestones.get("Response"):
                return "I couldn't retrieve milestone information, Guardian."

            response = "Here are the current milestones, Guardian:\n\n"

            milestone_data = milestones["Response"]
            for milestone_hash, milestone_info in list(milestone_data.items())[:5]:  # Limit to first 5
                try:
                    # Get milestone definition
                    milestone_def = self.bungie._get(f"/Destiny2/Manifest/DestinyMilestoneDefinition/{milestone_hash}/", authenticated=False)
                    name = milestone_def.get("Response", {}).get("displayProperties", {}).get("name", "Unknown Milestone")
                    description = milestone_def.get("Response", {}).get("displayProperties", {}).get("description", "")

                    response += f"• {name}\n"
                    if description:
                        response += f"  {description[:100]}{'...' if len(description) > 100 else ''}\n"
                    response += "\n"
                except:
                    continue

            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving milestone information: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving milestone information: {str(e)}"

    def _handle_activity_request(self, activity_type: str | None = None) -> str:
        """Handle activity history requests."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to view your activity history, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile to find characters
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])

            if not profile.get("Response", {}).get("characters", {}).get("data"):
                return "I couldn't retrieve your character information, Guardian."

            # Get activity history for the first character
            character_id = list(profile["Response"]["characters"]["data"].keys())[0]

            activities = self.bungie.get_activity_history(destiny_membership_type, destiny_membership_id, character_id, count=5)

            if not activities.get("Response", {}).get("activities"):
                return "I couldn't retrieve your recent activities, Guardian."

            response = "Here are your recent activities, Guardian:\n\n"

            activity_list = activities["Response"]["activities"]
            for activity in activity_list[:5]:  # Limit to 5 most recent
                activity_details = activity.get("activityDetails", {})
                period = activity.get("period", "")
                values = activity.get("values", {})

                # Get activity definition for name
                activity_hash = activity_details.get("referenceId")
                activity_name = "Unknown Activity"
                try:
                    activity_def = self.bungie._get(f"/Destiny2/Manifest/DestinyActivityDefinition/{activity_hash}/", authenticated=False)
                    activity_name = activity_def.get("Response", {}).get("displayProperties", {}).get("name", "Unknown Activity")
                except:
                    pass

                kills = values.get("kills", {}).get("basic", {}).get("displayValue", "0")
                deaths = values.get("deaths", {}).get("basic", {}).get("displayValue", "0")
                kd_ratio = values.get("killsDeathsRatio", {}).get("basic", {}).get("displayValue", "0")

                response += f"• {activity_name}\n"
                response += f"  Kills: {kills} | Deaths: {deaths} | K/D: {kd_ratio}\n"
                response += f"  Date: {period[:10] if period else 'Unknown'}\n\n"

            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving your activity history: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving your activity history: {str(e)}"

    def _handle_character_request(self) -> str:
        """Handle character information requests."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to view your characters, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get character information
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])

            if not profile.get("Response", {}).get("characters", {}).get("data"):
                return "I couldn't retrieve your character information, Guardian."

            response = "Here are your characters, Guardian:\n\n"

            character_data = profile["Response"]["characters"]["data"]
            for character_id, character_info in character_data.items():
                race = character_info.get("raceType", "Unknown")
                class_type = character_info.get("classType", "Unknown")
                gender = character_info.get("genderType", "Unknown")
                light_level = character_info.get("light", 0)
                last_played = character_info.get("dateLastPlayed", "")

                # Convert enums to readable names
                race_names = ["Human", "Awoken", "Exo"]
                class_names = ["Titan", "Hunter", "Warlock"]
                gender_names = ["Male", "Female", "Unknown"]

                race_name = race_names[race] if 0 <= race < len(race_names) else "Unknown"
                class_name = class_names[class_type] if 0 <= class_type < len(class_names) else "Unknown"
                gender_name = gender_names[gender] if 0 <= gender < len(gender_names) else "Unknown"

                response += f"• {race_name} {class_name} (Light: {light_level})\n"
                response += f"  Last played: {last_played[:10] if last_played else 'Never'}\n\n"

            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving your character information: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving your character information: {str(e)}"

    def _handle_leaderboard_request(self, stat_name: str | None = None) -> str:
        """Handle leaderboard requests."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to view leaderboards, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile to find characters
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [200])

            if not profile.get("Response", {}).get("characters", {}).get("data"):
                return "I couldn't retrieve your character information, Guardian."

            # Get leaderboards for the first character
            character_id = list(profile["Response"]["characters"]["data"].keys())[0]

            leaderboards = self.bungie.get_leaderboards_for_character(destiny_membership_type, destiny_membership_id, character_id)

            if not leaderboards.get("Response"):
                return "I couldn't retrieve leaderboard information, Guardian."

            response = "Here are the current leaderboards, Guardian:\n\n"

            # Parse leaderboard data
            leaderboard_data = leaderboards["Response"]
            for stat_key, stat_info in list(leaderboard_data.items())[:5]:  # Limit to first 5 stats
                stat_name_display = stat_info.get("displayName", stat_key)
                entries = stat_info.get("entries", [])

                response += f"• {stat_name_display}\n"

                # Show top 3 entries
                for i, entry in enumerate(entries[:3]):
                    rank = entry.get("rank", i + 1)
                    value = entry.get("value", {}).get("basic", {}).get("displayValue", "N/A")
                    player_name = entry.get("player", {}).get("destinyUserInfo", {}).get("displayName", "Unknown")

                    response += f"  {rank}. {player_name}: {value}\n"

                response += "\n"

            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving leaderboard information: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving leaderboard information: {str(e)}"

    # ---------------------- New Bungie NLP handlers ----------------------
    def _pick_character_for_class(self, profile: dict, class_target: str | None) -> str | None:
        chars = profile.get("Response", {}).get("characters", {}).get("data", {})
        if not chars:
            return None
        if not class_target:
            return next(iter(chars.keys()))
        cmap = {"titan": 0, "hunter": 1, "warlock": 2, "me": None}
        target = cmap.get(class_target)
        if target is None:
            return next(iter(chars.keys()))
        for cid, c in chars.items():
            if c.get("classType") == target:
                return cid
        return next(iter(chars.keys()))

    def _handle_equip_loadout(self, index: int, class_target: str | None) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your loadouts."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, class_target)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            res = self.bungie.equip_loadout(mtype, cid, index)
            if res.get("ErrorCode") == 1:
                return f"Equipped loadout {index} on your character, Guardian."
            return f"I couldn't equip loadout {index}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't equip the loadout: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't equip the loadout: {e}"

    def _handle_snapshot_loadout(self, index: int) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to snapshot a loadout."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            res = self.bungie.snapshot_loadout(mtype, cid, index)
            if res.get("ErrorCode") == 1:
                return f"Snapshotted loadout {index} with your current gear, Guardian."
            return f"I couldn't snapshot loadout {index}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't snapshot the loadout: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't snapshot the loadout: {e}"

    def _handle_lock_unlock(self, item_name: str, state: bool) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to lock or unlock items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 107, 200])
            item_instance_id, character_id, item_hash, _ = self._best_inventory_match(profile, item_name)
            if not item_instance_id or not character_id:
                return f"I couldn't find '{item_name}' in your character inventory, Guardian."
            res = self.bungie.set_lock_state(mtype, character_id, str(item_instance_id), bool(state))
            if res.get("ErrorCode") == 1:
                return f"{'Locked' if state else 'Unlocked'} {item_name}, Guardian."
            return f"I couldn't change the lock state for {item_name}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't change the lock state: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't change the lock state: {e}"

    def _handle_dismantle_request(self, item_name: str) -> str:
        # Stage a pending confirmation
        self._pending_action = {"action": "dismantle", "item": item_name, "expires": time.time() + 60}
        return f"This will permanently delete {item_name}, Guardian. If you're sure, reply: 'confirm dismantle {item_name}'."

    def _handle_dismantle_confirm(self, item_name: str) -> str:
        try:
            if not self._pending_action or self._pending_action.get("action") != "dismantle" or self._pending_action.get("item", "").lower() != item_name.lower() or self._pending_action.get("expires", 0) < time.time():
                return "I don't have a dismantle request to confirm, Guardian. Say 'dismantle <item>' first."
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to dismantle items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200])
            item_instance_id, character_id, item_hash, _ = self._best_inventory_match(profile, item_name)
            if not item_instance_id or not character_id:
                return f"I couldn't find '{item_name}' in your character inventory, Guardian."
            res = self.bungie.dismantle_item(mtype, character_id, str(item_instance_id))
            self._pending_action = None
            if res.get("ErrorCode") == 1:
                return f"Dismantled {item_name}, Guardian."
            return f"I couldn't dismantle {item_name}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't dismantle the item: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't dismantle the item: {e}"

    def _handle_vendor_detail(self, vendor_hash: int) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view vendors."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            v = self.bungie.get_vendor(mtype, mid, cid, vendor_hash)
            if not v.get("Response"):
                return "I couldn't retrieve that vendor, Guardian."
            sales = v["Response"].get("sales", {}).get("data", {})
            if not sales:
                return "That vendor has no visible sales for you right now, Guardian."
            lines = []
            count = 0
            for sale_id, sale in sales.items():
                ih = sale.get("itemHash")
                name = f"Item {ih}"
                try:
                    idef = self.bungie._get(f"/Destiny2/Manifest/DestinyInventoryItemDefinition/{ih}/", authenticated=False)
                    name = idef.get("Response", {}).get("displayProperties", {}).get("name", name)
                except Exception:
                    pass
                lines.append(f"- {name}")
                count += 1
                if count >= 12:
                    break
            self._last_vendor_hash = int(vendor_hash)
            return "Vendor items, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't retrieve the vendor: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't retrieve the vendor: {e}"

    def _resolve_vendor_hash_by_name(self, name: str) -> int | None:
        # Resolve against currently available vendors for the player
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return None
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            vendors = self.bungie.get_vendors(mtype, mid, cid)
            data = vendors.get("Response", {}).get("vendors", {}).get("data", {})
            best_hash = None
            best_score = 0.0
            for vh in data.keys():
                try:
                    vdef = self.bungie._get(f"/Destiny2/Manifest/DestinyVendorDefinition/{vh}/", authenticated=False)
                    vname = vdef.get("Response", {}).get("displayProperties", {}).get("name") or ""
                    score = self._similarity(vname, name)
                    if score > best_score:
                        best_score = score
                        best_hash = int(vh)
                        if score >= 0.96:
                            break
                except Exception:
                    continue
            return best_hash
        except Exception:
            return None

    def _handle_vendor_detail_by_name(self, vendor_name: str) -> str:
        # Common synonyms normalization
        vn = vendor_name.strip().lower()
        synonyms = {
            "xur": "xur",
            "xûr": "xur",
            "banshee": "banshee-44",
            "gunsmith": "banshee-44",
            "shaxx": "lord shaxx",
            "zavala": "commander zavala",
            "rahul": "master rahool",
            "ada": "ada-1",
        }
        vn = synonyms.get(vn, vn)
        vh = self._resolve_vendor_hash_by_name(vn)
        if vh is None:
            return f"I couldn't find a vendor named '{vendor_name}' in your current location, Guardian."
        return self._handle_vendor_detail(vh)

    def _handle_collectibles(self, node_hash: int) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view collectibles."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            cols = self.bungie.get_collectibles(mtype, mid, cid, node_hash)
            r = cols.get("Response", {}) if isinstance(cols, dict) else {}
            nodes = r.get("collectibles", {}) or r.get("presentationNodes", {})
            if not nodes:
                return "I couldn't retrieve collectibles for that node, Guardian."
            # Summarize first few collectibles by name if possible
            lines = []
            seen = 0
            for k, v in nodes.items():
                collected = v.get("state") == 0 if isinstance(v, dict) else False
                name = f"Collectible {k}"
                try:
                    cdef = self.bungie._get(f"/Destiny2/Manifest/DestinyCollectibleDefinition/{k}/", authenticated=False)
                    name = cdef.get("Response", {}).get("displayProperties", {}).get("name", name)
                except Exception:
                    pass
                lines.append(f"- {name} ({'Collected' if collected else 'Missing'})")
                seen += 1
                if seen >= 12:
                    break
            return "Collectibles, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't retrieve collectibles: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't retrieve collectibles: {e}"

    def _handle_public_milestone_content(self, milestone_hash: int) -> str:
        try:
            data = self.bungie.get_public_milestone_content(milestone_hash)
            if not data.get("Response"):
                return "I couldn't retrieve that milestone content, Guardian."
            name = data["Response"].get("title") or data["Response"].get("about") or "Milestone"
            return f"Milestone content: {name}"
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get milestone content: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get milestone content: {e}"

    def _handle_trending_category(self, category: str, page: int) -> str:
        try:
            data = self.bungie.get_trending_category(category, page)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return "I couldn't retrieve that trending category page, Guardian."
            results = r.get("results", [])
            lines = []
            for e in results[:10]:
                lines.append("- " + e.get("displayName", "Entry"))
            self._last_trending = (category, page)
            return f"Trending '{category}' page {page}, Guardian:\n\n" + ("\n".join(lines) if lines else "No entries")
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get trending category: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get trending category: {e}"

    def _handle_manifest(self) -> str:
        try:
            m = self.bungie.get_manifest()
            r = m.get("Response") if isinstance(m, dict) else m
            if not r:
                return "I couldn't load the manifest, Guardian."
            v = r.get("version") or r.get("mobileWorldContentPaths", {}).get("en")
            return f"Manifest loaded, version: {v}"
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load the manifest: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load the manifest: {e}"

    def _handle_entity(self, entity_type: str, hash_id: int) -> str:
        try:
            e = self.bungie.get_entity(entity_type, hash_id)
            # Try to print a sensible name
            name = None
            try:
                name = e.get("Response", {}).get("displayProperties", {}).get("name")
            except Exception:
                pass
            return f"{entity_type} {hash_id}: {name or 'Loaded.'}"
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load the entity: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load the entity: {e}"

    def _handle_account_stats(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view account stats."
            mid, mtype = dm
            data = self.bungie.get_historical_stats_for_account(mtype, mid)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return "I couldn't retrieve account stats, Guardian."
            return "Account stats loaded, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get account stats: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get account stats: {e}"

    def _handle_character_stats(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view character stats."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            data = self.bungie.get_historical_stats(mtype, mid, cid)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return "I couldn't retrieve character stats, Guardian."
            return "Character stats loaded, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get character stats: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get character stats: {e}"

    def _handle_unique_weapon_history(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view weapon history."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            data = self.bungie.get_unique_weapon_history(mtype, mid, cid)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return "I couldn't retrieve unique weapon history, Guardian."
            return "Unique weapon history loaded, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get weapon history: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get weapon history: {e}"

    def _handle_aggregate_activity_stats(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view aggregate stats."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            data = self.bungie.get_aggregate_activity_stats(mtype, mid, cid)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return "I couldn't retrieve aggregate stats, Guardian."
            return "Aggregate activity stats loaded, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get aggregate stats: {e}"

    def _handle_bulk_equip(self, item_names: list[str], class_target: str | None) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to equip items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 107, 200])
            # Choose character id
            cid = self._pick_character_for_class(profile, class_target)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            # Resolve each name in character inventory; fall back to postmaster/vault transfer is complex, so limit to inventory
            resolved: list[str] = []
            unresolved: list[str] = []
            for name in item_names:
                iid, item_cid, ihash, _ = self._best_inventory_match(profile, name)
                if iid and (item_cid == cid):
                    resolved.append(str(iid))
                else:
                    unresolved.append(name)
            if not resolved:
                return "I couldn't find those items in your current character inventory, Guardian."
            res = self.bungie.equip_items(mtype, cid, resolved)
            if res.get("ErrorCode") == 1:
                msg = f"Equipped {len(resolved)} item(s) on your {class_target or 'character'}, Guardian."
                if unresolved:
                    msg += f" I couldn't find: {', '.join(unresolved)}."
                return msg
            return "I couldn't equip those items, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't equip those items: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't equip those items: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get aggregate stats: {e}"
    def _handle_clan_search(self, preference: str | None = None) -> str:
        try:
            # Build a generous search payload. Bungie ignores unknown fields.
            query: dict[str, Any] = {
                "groupType": 1,
                "name": str(preference or ""),
                "creationDate": 0,
                "sortBy": 0,
                "clanMemberType": 0,
                "itemsPerPage": 20,
                "currentPage": 1,
                "localeFilter": "en",
            }
            data = self.bungie.group_search(query)
            resp = data.get("Response") if isinstance(data, dict) else data
            results = None
            if isinstance(resp, dict):
                results = resp.get("results") or resp.get("groups") or resp.get("resultsPage")
            # Fallback: try simplifying preference tokens
            if not results and preference:
                tokens = [w for w in re.split(r"\W+", preference) if w]
                for tok in tokens:
                    q2 = dict(query)
                    q2["name"] = tok
                    data2 = self.bungie.group_search(q2)
                    resp2 = data2.get("Response") if isinstance(data2, dict) else data2
                    results = isinstance(resp2, dict) and (resp2.get("results") or resp2.get("groups"))
                    if results:
                        break
            if not results:
                return "I couldn't find clans with those preferences, Guardian. Try 'find a clan for raids' or give me a keyword like 'vault' or 'trials'."
            out = []
            for g in (results[:5] if isinstance(results, list) else []):
                name = g.get("name") or g.get("groupName") or "Unknown Clan"
                gid = g.get("groupId") or g.get("groupId")
                motto = g.get("motto") or g.get("about") or ""
                mcount = g.get("memberCount") or g.get("memberCount")
                out.append(f"- {name} (id: {gid}, members: {mcount}){(f' — {motto}' if motto else '')}")
            if not out:
                return "I couldn't parse clan results, Guardian."
            header = "Here are some clans you might like, Guardian:\n" if not preference else f"Clans matching '{preference}':\n"
            return header + "\n".join(out)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't search clans: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't search clans: {e}"

    def _handle_clan_members(self, target: str | None = None) -> str:
        try:
            group_id = None
            if target and target.isdigit():
                group_id = int(target)
            elif target:
                sr = self.bungie.group_search({"groupType": 1, "name": target})
                r = sr.get("Response") if isinstance(sr, dict) else sr
                results = r.get("results") if isinstance(r, dict) else None
                if results:
                    group_id = results[0].get("groupId") or results[0].get("groupId")
            if not group_id:
                return "Tell me your clan name or id, Guardian. For example: 'show clan members of Dead Orbit'."
            members = self.bungie.get_clan_members(group_id)
            r = members.get("Response") if isinstance(members, dict) else members
            results = r.get("results") if isinstance(r, dict) else None
            if not results:
                return "I couldn't retrieve clan members, Guardian."
            lines = []
            for m in results[:15]:
                info = m.get("destinyUserInfo") or m.get("bungieNetUserInfo") or {}
                name = info.get("displayName") or info.get("bungieGlobalDisplayName") or "Unknown"
                role = m.get("memberType")  # numeric enum
                lines.append(f"- {name} (type {role})")
            return "Here are some clan members, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't get clan members: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't get clan members: {e}"

    def _handle_fireteam_search(self, activity: str | None = None) -> str:
        try:
            # Map common activity keywords to activity_type where possible (fallback to 0)
            act_map = {
                "raid": 4,
                "dungeon": 2,
                "nightfall": 3,
                "trials": 9,
                "gambit": 6,
                "crucible": 5,
                "iron banner": 10,
            }
            atype = 0
            if activity:
                low = activity.lower()
                for k, v in act_map.items():
                    if k in low:
                        atype = v
                        break
            # Default filters: platform=0 (all), date_range=0 (all), slot_filter=0 (any), page=0
            data = self.bungie.fireteam_search(0, atype, 0, 0, 0)
            r = data.get("Response") if isinstance(data, dict) else data
            results = r.get("results") if isinstance(r, dict) else None
            if not results:
                return "I couldn't find public fireteams right now, Guardian."
            lines = []
            for f in results[:5]:
                title = f.get("title") or f.get("activity") or "Fireteam"
                owner = (f.get("ownerInfo") or {}).get("displayName") or "Unknown"
                slots = f.get("playerSlotCount") or f.get("playerSlotsTotal")
                open_slots = f.get("availablePlayerSlots") or f.get("playerSlotsAvailable")
                lines.append(f"- {title} by {owner} ({open_slots}/{slots} slots open)")
            return "Here are some public fireteams, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            msg = str(e)
            if "SystemDisabled" in msg or "503" in msg:
                return "Guardian, Bungie services are temporarily down for maintenance. Let's try again in a bit."
            return f"Sorry Guardian, I couldn't search fireteams: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't search fireteams: {e}"

    def _handle_clan_fireteams(self, target: str | None = None) -> str:
        try:
            group_id = None
            if target and target.isdigit():
                group_id = int(target)
            elif target:
                sr = self.bungie.group_search({"groupType": 1, "name": target})
                r = sr.get("Response") if isinstance(sr, dict) else sr
                results = r.get("results") if isinstance(r, dict) else None
                if results:
                    group_id = results[0].get("groupId")
            if not group_id:
                return "Tell me which clan (name or id), Guardian."
            data = self.bungie.list_clan_fireteams(group_id, 0, 0, 0, 0, 1, 0)
            r = data.get("Response") if isinstance(data, dict) else data
            results = r.get("results") if isinstance(r, dict) else None
            if not results:
                return "I couldn't find clan fireteams right now, Guardian."
            lines = []
            for f in results[:5]:
                title = f.get("title") or f.get("activity") or "Fireteam"
                owner = (f.get("ownerInfo") or {}).get("displayName") or "Unknown"
                lines.append(f"- {title} by {owner}")
            return "Here are clan fireteams, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't list clan fireteams: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't list clan fireteams: {e}"

    def _handle_player_search_by_bungie_name(self, bungie_name: str) -> str:
        try:
            if "#" in bungie_name:
                display, code = bungie_name.split("#", 1)
                code_num = int(code) if code.isdigit() else 0
            else:
                display, code_num = bungie_name, 0
            data = self.bungie.search_destiny_player_by_bungie_name(0, display, code_num)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return f"I couldn't find '{bungie_name}', Guardian."
            # r may be a list of players
            lines = []
            for p in (r if isinstance(r, list) else []):
                dn = p.get("bungieGlobalDisplayName") or p.get("displayName")
                dnc = p.get("bungieGlobalDisplayNameCode")
                mid = p.get("membershipId") or (p.get("destinyMemberships") or [{}])[0].get("membershipId")
                mtype = p.get("membershipType") or (p.get("destinyMemberships") or [{}])[0].get("membershipType")
                name = f"{dn}#{dnc:04d}" if dn and isinstance(dnc, int) else (dn or "Unknown")
                lines.append(f"- {name} (id: {mid}, type: {mtype})")
            return "Here are the matching Guardians, Guardian:\n\n" + ("\n".join(lines) if lines else "No matches")
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't search players: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't search players: {e}"

    def _handle_player_search(self, name: str) -> str:
        try:
            data = self.bungie.search_destiny_player(0, name)
            r = data.get("Response") if isinstance(data, dict) else data
            if not r:
                return f"I couldn't find '{name}', Guardian."
            lines = []
            for p in (r if isinstance(r, list) else []):
                dn = p.get("displayName") or p.get("bungieGlobalDisplayName") or "Unknown"
                mid = p.get("membershipId")
                mtype = p.get("membershipType")
                lines.append(f"- {dn} (id: {mid}, type: {mtype})")
            return "Here are the matching Guardians, Guardian:\n\n" + ("\n".join(lines) if lines else "No matches")
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't search players: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't search players: {e}"

    def _handle_profile_summary(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view your profile."
            mid, mtype = dm
            prof = self.bungie.get_profile(mtype, mid, [100, 200])
            r = prof.get("Response", {}) if isinstance(prof, dict) else {}
            chars = r.get("characters", {}).get("data", {})
            num_chars = len(chars)
            light = []
            for c in chars.values():
                try:
                    light.append(int(c.get("light", 0)))
                except Exception:
                    pass
            best = max(light) if light else None
            return f"Profile loaded, Guardian. Characters: {num_chars}{(f', highest Power {best}' if best is not None else '')}."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load your profile: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load your profile: {e}"

    def _handle_character_summary(self, class_name: str) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view your character."
            mid, mtype = dm
            prof = self.bungie.get_profile(mtype, mid, [200])
            chars = prof.get("Response", {}).get("characters", {}).get("data", {})
            class_map = {"titan": 0, "hunter": 1, "warlock": 2}
            target_type = class_map.get(class_name)
            for cid, c in chars.items():
                if c.get("classType") == target_type:
                    l = c.get("light")
                    race = c.get("raceType")
                    gender = c.get("genderType")
                    return f"Your {class_name.capitalize()} (ID {cid}) is Power {l}, race {race}, gender {gender}."
            return f"I couldn't find a {class_name} on your account, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load your character: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load your character: {e}"

    def _handle_alerts_request(self) -> str:
        try:
            alerts = self.bungie.get_global_alerts()
            r = alerts.get("Response") if isinstance(alerts, dict) else alerts
            if not r:
                return "No global alerts right now, Guardian."
            def _strip_html(t: str) -> str:
                import re as _re
                return _re.sub(r"<[^>]+>", "", t or "")
            lines = []
            for a in r[:5]:
                html = a.get("AlertHtml") or a.get("AlertString") or ""
                lines.append("- " + _strip_html(html)[:140])
            return "Global alerts, Guardian:\n\n" + "\n".join(lines)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't retrieve alerts: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't retrieve alerts: {e}"

    def _handle_pgcr(self, activity_id: str) -> str:
        try:
            rep = self.bungie.get_post_game_carnage_report(activity_id)
            r = rep.get("Response") if isinstance(rep, dict) else rep
            if not r:
                return "I couldn't fetch that activity report, Guardian."
            entries = r.get("entries") or []
            lines = []
            for e in entries[:6]:
                p = e.get("player", {})
                stats = e.get("values", {})
                name = (p.get("destinyUserInfo") or {}).get("displayName") or "Unknown"
                kills = stats.get("kills", {}).get("basic", {}).get("value")
                deaths = stats.get("deaths", {}).get("basic", {}).get("value")
                kd = stats.get("killsDeathsRatio", {}).get("basic", {}).get("displayValue")
                lines.append(f"- {name}: K {kills} D {deaths} (K/D {kd})")
            self._last_activity_id = str(activity_id)
            return "Post Game Carnage Report, Guardian:\n\n" + ("\n".join(lines) if lines else "No entries")
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load the carnage report: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load the carnage report: {e}"

    def _handle_last_pgcr(self) -> str:
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to view your last match."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [200])
            cid = self._pick_character_for_class(profile, None)
            if not cid:
                return "I couldn't determine which character to use, Guardian."
            hist = self.bungie.get_activity_history(mtype, mid, cid, count=1)
            acts = hist.get("Response", {}).get("activities", []) if isinstance(hist, dict) else []
            if not acts:
                return "I couldn't find a recent activity, Guardian."
            aid = acts[0].get("activityDetails", {}).get("instanceId")
            if not aid:
                return "I couldn't read the last activity id, Guardian."
            return self._handle_pgcr(str(aid))
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't load your last match report: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't load your last match report: {e}"

    def _handle_public_milestone_by_name(self, name: str) -> str:
        try:
            data = self.bungie.get_milestones()
            mil = data.get("Response", {}) if isinstance(data, dict) else {}
            best = None
            best_score = 0.0
            for key in mil.keys():
                try:
                    mdef = self.bungie._get(f"/Destiny2/Manifest/DestinyMilestoneDefinition/{key}/", authenticated=False)
                    mname = mdef.get("Response", {}).get("displayProperties", {}).get("name", "")
                    sc = self._similarity(mname, name)
                    if sc > best_score:
                        best_score = sc
                        best = int(key)
                        if sc >= 0.96:
                            break
                except Exception:
                    continue
            if best is None:
                return f"I couldn't find a milestone named '{name}', Guardian."
            return self._handle_public_milestone_content(best)
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't look up that milestone: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't look up that milestone: {e}"

    def _handle_inventory_list(self, item_type: str, location: str) -> str:
        """Handle inventory/vault listing requests."""
        try:
            destiny_info = self._get_destiny_membership()
            if not destiny_info:
                return "Guardian, I need you to authenticate with Bungie first to check your inventory, or I couldn't find your Destiny 2 account."

            destiny_membership_id, destiny_membership_type = destiny_info

            # Get profile with profileInventory (102) and characterInventories (201)
            profile = self.bungie.get_profile(destiny_membership_type, destiny_membership_id, [102, 201])

            resp = profile.get("Response", {}) if isinstance(profile, dict) else {}
            p_items = resp.get("profileInventory", {}).get("data", {}).get("items", []) or []
            c_invs = resp.get("characterInventories", {}).get("data", {}) or {}
            # Build unified iterable depending on requested location
            # location mapping: inventory -> characterInventories; vault -> profileInventory; items -> both
            items = []
            if location.lower() == "inventory":
                for _, cdata in c_invs.items():
                    items.extend(cdata.get("items", []) or [])
            elif location.lower() == "vault":
                items.extend(p_items)
            else:
                items.extend(p_items)
                for _, cdata in c_invs.items():
                    items.extend(cdata.get("items", []) or [])

            # Map item types
            type_mapping = {
                "weapons": 3,  # DestinyItemType.Weapon
                "armor": 2,    # DestinyItemType.Armor
                "gear": None,  # Any gear
                "items": None  # Any items
            }

            target_type = type_mapping.get(item_type.lower())

            # Map locations
            location_mapping = {
                "vault": 2,      # ItemLocation.Vault
                "inventory": 1   # ItemLocation.Inventory
            }

            target_location = location_mapping.get(location.lower())
            logging.info(f"Filtering for item_type: {item_type} (target_type: {target_type}), location: {location} (target_location: {target_location})")

            # Filter items
            filtered_items = []
            for item in items:
                if target_location is not None:
                    loc = item.get("location")
                    if loc is None:
                        bh = item.get("bucketHash")
                        if bh is None:
                            continue
                        loc = self._bucket_location_safe(bh)
                    if loc != target_location:
                        continue
                if target_type is not None:
                    # Get itemType from definition if not in item
                    item_type_val = item.get("itemType")
                    if item_type_val is None:
                        try:
                            item_hash = item["itemHash"]
                            item_def = self.bungie._get(f"/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/", authenticated=False)
                            item_type_val = item_def.get("Response", {}).get("itemType")
                        except:
                            item_type_val = None
                    if item_type_val != target_type:
                        continue
                filtered_items.append(item)

            logging.info(f"Filtered items: {len(filtered_items)}")

            if not filtered_items:
                return f"Looks like you don't have any {item_type} in your {location}, Guardian."

            # Get item names (limit to 20)
            item_names = []
            for item in filtered_items[:20]:
                try:
                    # Get item definition
                    item_hash = item["itemHash"]
                    item_def = self.bungie._get(f"/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/", authenticated=False)
                    name = item_def.get("Response", {}).get("displayProperties", {}).get("name", "Unknown Item")
                    item_names.append(name)
                except:
                    item_names.append("Unknown Item")

            response = f"Here's what you have in your {location}, Guardian:\n\n"
            for name in item_names:
                response += f"• {name}\n"

            if len(filtered_items) > 20:
                response += f"\n...and {len(filtered_items) - 20} more items."

            self._last_location = location.lower()
            return response

        except BungieAPIError as e:
            if "HTTP error 401" in str(e):
                return "Guardian, your Bungie authentication has expired. Please re-authenticate by logging out and logging back in."
            return f"Sorry Guardian, I encountered an error while retrieving your {location} information: {str(e)}"
        except Exception as e:
            return f"Sorry Guardian, I encountered an error while retrieving your {location} information: {str(e)}"

    # ------------------------------
    # Dynamic item resolver overrides
    # ------------------------------
    def _item_is_weapon_or_armor(self, item_hash: int | str) -> bool:
        """Return True when the manifest definition is a weapon or armor piece."""
        try:
            idef = self.bungie.get_inventory_item_definition(item_hash)
            itype = idef.get("Response", {}).get("itemType")
            return itype in (2, 3)  # Armor / Weapon
        except Exception:
            return False

    def _item_class_type(self, item_hash: int | str) -> int | None:
        """Return Destiny classType for an item (0 titan, 1 hunter, 2 warlock, 3 any)."""
        try:
            idef = self.bungie.get_inventory_item_definition(item_hash)
            ct = idef.get("Response", {}).get("classType")
            if isinstance(ct, int):
                return ct
        except Exception:
            pass
        return None

    def _collect_owned_items(self, profile: dict) -> list[dict[str, Any]]:
        """Collect all owned item instances across vault, inventory, equipped, and postmaster."""
        out: list[dict[str, Any]] = []
        resp = profile.get("Response", {}) if isinstance(profile, dict) else {}
        profile_items = resp.get("profileInventory", {}).get("data", {}).get("items", []) or []
        character_invs = resp.get("characterInventories", {}).get("data", {}) or {}
        character_eq = resp.get("characterEquipment", {}).get("data", {}) or {}

        for it in profile_items:
            out.append(
                {
                    "item": it,
                    "source": "vault",
                    "character_id": None,
                }
            )
        for cid, cdata in character_invs.items():
            for it in cdata.get("items", []) or []:
                source = "inventory"
                loc = it.get("location")
                bh = it.get("bucketHash")
                if loc is None and bh is not None:
                    loc = self._bucket_location_safe(bh)
                if loc == 4 or (bh is not None and self._is_postmaster_bucket(bh)):
                    source = "postmaster"
                out.append(
                    {
                        "item": it,
                        "source": source,
                        "character_id": str(cid),
                    }
                )
        for cid, cdata in character_eq.items():
            for it in cdata.get("items", []) or []:
                out.append(
                    {
                        "item": it,
                        "source": "equipped",
                        "character_id": str(cid),
                    }
                )
        return out

    def _resolve_dynamic_item(
        self,
        profile: dict,
        query: str,
        *,
        allowed_sources: set[str] | None = None,
        target_class_type: int | None = None,
        only_weapon_or_armor: bool = True,
    ) -> dict[str, Any]:
        """Resolve a query to a specific owned item instance with ambiguity detection."""
        q = self._canonicalize_item_query(query or "").strip()
        qn = self._normalize_text(q)
        if not qn:
            return {"state": "unresolved", "candidates": []}

        # Pronoun support: use last referenced instance when available.
        if qn in {"it", "that", "this", "this one"} and self._last_item and self._last_item.get("instance_id"):
            last_iid = str(self._last_item.get("instance_id"))
            for ref in self._collect_owned_items(profile):
                it = ref.get("item", {})
                if str(it.get("itemInstanceId")) == last_iid:
                    ih = it.get("itemHash")
                    if ih is None:
                        continue
                    if only_weapon_or_armor and not self._item_is_weapon_or_armor(ih):
                        continue
                    return {
                        "state": "resolved",
                        "candidate": {
                            "instance_id": str(it.get("itemInstanceId")),
                            "item_hash": ih,
                            "name": self._get_item_name(ih) or "Unknown Item",
                            "source": ref.get("source"),
                            "character_id": ref.get("character_id"),
                            "score": 1.0,
                        },
                        "candidates": [],
                    }

        scored: list[dict[str, Any]] = []
        short_query = len(qn) <= 5 or len(qn.split()) <= 1
        min_score = 0.58 if short_query else 0.72

        for ref in self._collect_owned_items(profile):
            source = str(ref.get("source"))
            if allowed_sources and source not in allowed_sources:
                continue
            it = ref.get("item", {})
            item_hash = it.get("itemHash")
            if item_hash is None:
                continue
            if only_weapon_or_armor and not self._item_is_weapon_or_armor(item_hash):
                continue

            class_type = self._item_class_type(item_hash)
            # 3 is class-agnostic in Destiny definitions.
            if (
                target_class_type is not None
                and class_type is not None
                and class_type in (0, 1, 2)
                and class_type != target_class_type
            ):
                continue

            name = self._get_item_name(item_hash)
            if not name:
                continue
            score = self._similarity(name, q)
            nn = self._normalize_text(name)
            if nn == qn:
                score += 0.25
            elif qn and qn in nn:
                score += 0.12
            if source == "equipped":
                score += 0.03
            if score < min_score:
                continue
            scored.append(
                {
                    "instance_id": str(it.get("itemInstanceId")),
                    "item_hash": item_hash,
                    "name": name,
                    "source": source,
                    "character_id": ref.get("character_id"),
                    "score": round(float(score), 4),
                }
            )

        if not scored:
            return {"state": "unresolved", "candidates": []}

        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]
        # Ambiguous if multiple close candidates remain.
        close = [c for c in scored if c["score"] >= best["score"] - 0.04]
        if len(close) > 1 or (short_query and len(scored) > 1):
            return {"state": "ambiguous", "candidates": close[:5]}
        return {"state": "resolved", "candidate": best, "candidates": scored[:5]}

    def _format_item_candidates(self, candidates: list[dict[str, Any]]) -> str:
        lines = []
        for idx, c in enumerate(candidates[:3], 1):
            where = c.get("source") or "unknown"
            char = c.get("character_id")
            suffix = f" on character {char}" if char else ""
            lines.append(f"{idx}. {c.get('name', 'Unknown Item')} ({where}{suffix})")
        return "\n".join(lines)

    def _best_vault_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        res = self._resolve_dynamic_item(profile, query, allowed_sources={"vault"})
        cand = res.get("candidate") if res.get("state") == "resolved" else None
        if not cand:
            return None, None, None, None
        return cand.get("instance_id"), None, cand.get("item_hash"), cand.get("name")

    def _best_inventory_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        res = self._resolve_dynamic_item(profile, query, allowed_sources={"inventory"})
        cand = res.get("candidate") if res.get("state") == "resolved" else None
        if not cand:
            return None, None, None, None
        return cand.get("instance_id"), cand.get("character_id"), cand.get("item_hash"), cand.get("name")

    def _best_postmaster_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        res = self._resolve_dynamic_item(profile, query, allowed_sources={"postmaster"})
        cand = res.get("candidate") if res.get("state") == "resolved" else None
        if not cand:
            return None, None, None, None
        return cand.get("instance_id"), cand.get("character_id"), cand.get("item_hash"), cand.get("name")

    def _best_equipped_match(self, profile: dict, query: str) -> tuple[str | None, str | None, int | str | None, str | None]:
        res = self._resolve_dynamic_item(profile, query, allowed_sources={"equipped"})
        cand = res.get("candidate") if res.get("state") == "resolved" else None
        if not cand:
            return None, None, None, None
        return cand.get("instance_id"), cand.get("character_id"), cand.get("item_hash"), cand.get("name")

    def _handle_vault_item(self, item_name: str) -> str:
        """Vault any owned weapon/armor item by dynamic instance resolution."""
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200, 201, 205])

            res = self._resolve_dynamic_item(
                profile,
                item_name,
                allowed_sources={"inventory", "equipped", "vault", "postmaster"},
            )
            state = res.get("state")
            if state == "ambiguous":
                return (
                    "I found multiple matching items. Tell me which one:\n"
                    + self._format_item_candidates(res.get("candidates", []))
                )
            if state != "resolved":
                return f"I couldn't find '{item_name}' among your owned weapons or armor, Guardian."

            cand = res["candidate"]
            src = cand.get("source")
            iid = str(cand.get("instance_id"))
            ih = cand.get("item_hash")
            cid = cand.get("character_id")
            name = cand.get("name") or item_name

            if src == "vault":
                return f"{name} is already in your vault, Guardian."
            if src == "equipped":
                return f"{name} is equipped right now. Equip a replacement first, then ask me to vault it."
            if src == "postmaster":
                if not cid:
                    return f"I found {name} in postmaster but couldn't determine the source character."
                pr = self.bungie.pull_from_postmaster(int(ih), 1, iid, str(cid), int(mtype))
                if pr.get("ErrorCode") != 1:
                    return f"I found {name} in postmaster but couldn't pull it, Guardian."
                # After pull, same character can vault it.
            if not cid:
                return f"I couldn't determine where {name} is stored, Guardian."
            tr = self.bungie.transfer_item(
                membership_type=mtype,
                character_id=str(cid),
                item_id=iid,
                item_reference_hash=ih,
                stack_size=1,
                transfer_to_vault=True,
            )
            if tr.get("ErrorCode") == 1:
                self._last_item = {"name": name, "instance_id": iid, "character_id": None, "hash": ih}
                return f"I've vaulted {name}, Guardian."
            return f"I couldn't vault {name}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't vault that item: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't vault that item: {e}"

    def _handle_transfer_from_vault(self, item_name: str) -> str:
        """Transfer a vault item to the active character dynamically."""
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
            target_cid = self._active_character_id(profile)
            if not target_cid:
                chars = profile.get("Response", {}).get("characters", {}).get("data", {})
                if not chars:
                    return "I couldn't find a character to receive items, Guardian."
                target_cid = list(chars.keys())[0]

            res = self._resolve_dynamic_item(profile, item_name, allowed_sources={"vault"})
            if res.get("state") == "ambiguous":
                return (
                    "I found multiple vault matches. Tell me which one:\n"
                    + self._format_item_candidates(res.get("candidates", []))
                )
            if res.get("state") != "resolved":
                return f"I couldn't find '{item_name}' in your vault, Guardian."
            cand = res["candidate"]
            tr = self.bungie.transfer_item(
                membership_type=mtype,
                character_id=str(target_cid),
                item_id=str(cand.get("instance_id")),
                item_reference_hash=cand.get("item_hash"),
                stack_size=1,
                transfer_to_vault=False,
            )
            if tr.get("ErrorCode") == 1:
                self._last_item = {
                    "name": cand.get("name"),
                    "instance_id": str(cand.get("instance_id")),
                    "character_id": str(target_cid),
                    "hash": cand.get("item_hash"),
                }
                return f"I've moved {cand.get('name')} to your inventory, Guardian."
            return f"I couldn't transfer {cand.get('name')} from your vault, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't transfer from vault: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't transfer from vault: {e}"

    def _handle_pull_from_postmaster(self, item_name: str) -> str:
        """Pull a postmaster item to inventory dynamically."""
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your postmaster."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
            res = self._resolve_dynamic_item(profile, item_name, allowed_sources={"postmaster"})
            if res.get("state") == "ambiguous":
                return (
                    "I found multiple postmaster matches. Tell me which one:\n"
                    + self._format_item_candidates(res.get("candidates", []))
                )
            if res.get("state") != "resolved":
                return f"I couldn't find '{item_name}' in your postmaster, Guardian."
            cand = res["candidate"]
            cid = cand.get("character_id") or self._active_character_id(profile)
            if not cid:
                return "I couldn't find a character to receive that item, Guardian."
            pr = self.bungie.pull_from_postmaster(
                int(cand.get("item_hash")),
                1,
                str(cand.get("instance_id")),
                str(cid),
                int(mtype),
            )
            if pr.get("ErrorCode") == 1:
                self._last_item = {
                    "name": cand.get("name"),
                    "instance_id": str(cand.get("instance_id")),
                    "character_id": str(cid),
                    "hash": cand.get("item_hash"),
                }
                return f"I've pulled {cand.get('name')} from your postmaster, Guardian."
            return f"I couldn't pull {cand.get('name')} from your postmaster, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't pull that postmaster item: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't pull that postmaster item: {e}"

    def _handle_transfer_to_character(self, item_name: str, class_target: str) -> str:
        """Move a dynamically resolved owned weapon/armor to a target character."""
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            class_map = {"titan": 0, "hunter": 1, "warlock": 2}
            target_cid = None
            target_class = class_map.get(class_target)
            if class_target == "me":
                target_cid = self._active_character_id(profile)
            elif target_class is not None:
                for cid, cdata in (chars or {}).items():
                    if cdata.get("classType") == target_class:
                        target_cid = str(cid)
                        break
            if not target_cid:
                return f"I couldn't find your {class_target} character, Guardian."

            target_class_type = None
            if target_cid in chars:
                target_class_type = chars[target_cid].get("classType")

            res = self._resolve_dynamic_item(
                profile,
                item_name,
                allowed_sources={"inventory", "equipped", "vault", "postmaster"},
                target_class_type=target_class_type,
            )
            if res.get("state") == "ambiguous":
                return (
                    "I found multiple matches for that move. Tell me which one:\n"
                    + self._format_item_candidates(res.get("candidates", []))
                )
            if res.get("state") != "resolved":
                return f"I couldn't find '{item_name}' among your owned weapons or armor, Guardian."
            cand = res["candidate"]
            name = cand.get("name") or item_name
            src = cand.get("source")
            src_cid = cand.get("character_id")
            iid = str(cand.get("instance_id"))
            ih = cand.get("item_hash")

            if src == "equipped" and src_cid and str(src_cid) != str(target_cid):
                return f"{name} is equipped on another character. Unequip it first, then I can move it."

            if src == "postmaster":
                if not src_cid:
                    return f"I found {name} in postmaster but couldn't identify the source character."
                pr = self.bungie.pull_from_postmaster(int(ih), 1, iid, str(src_cid), int(mtype))
                if pr.get("ErrorCode") != 1:
                    return f"I found {name} in postmaster but couldn't pull it, Guardian."
                src = "inventory"

            if src == "vault":
                tr = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(target_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=False,
                )
                if tr.get("ErrorCode") == 1:
                    self._last_item = {"name": name, "instance_id": iid, "character_id": str(target_cid), "hash": ih}
                    return f"I've moved {name} to your {class_target}, Guardian."
                return f"I couldn't move {name} to your {class_target}, Guardian."

            if src in {"inventory", "equipped"} and src_cid and str(src_cid) != str(target_cid):
                to_vault = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(src_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=True,
                )
                if to_vault.get("ErrorCode") != 1:
                    return f"I couldn't move {name} to the vault first, Guardian."
                to_target = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(target_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=False,
                )
                if to_target.get("ErrorCode") == 1:
                    self._last_item = {"name": name, "instance_id": iid, "character_id": str(target_cid), "hash": ih}
                    return f"I've moved {name} to your {class_target}, Guardian."
                return f"I moved {name} to the vault but couldn't bring it to your {class_target}."

            self._last_item = {"name": name, "instance_id": iid, "character_id": str(target_cid), "hash": ih}
            return f"{name} is already on your {class_target}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't transfer that item: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't transfer that item: {e}"

    def _handle_equip_item(self, item_name: str, class_target: str | None = None) -> str:
        """Equip any owned weapon/armor piece on the selected character dynamically."""
        try:
            dm = self._get_destiny_membership()
            if not dm:
                return "Guardian, I need you to authenticate with Bungie first to manage your items."
            mid, mtype = dm
            profile = self.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
            chars = profile.get("Response", {}).get("characters", {}).get("data", {})
            class_map = {"titan": 0, "hunter": 1, "warlock": 2}

            target_cid = None
            target_class_type = None
            if class_target and class_target != "me":
                want = class_map.get(class_target)
                if want is not None:
                    for cid, cdata in (chars or {}).items():
                        if cdata.get("classType") == want:
                            target_cid = str(cid)
                            target_class_type = want
                            break
            if not target_cid:
                target_cid = self._active_character_id(profile)
            if not target_cid:
                if not chars:
                    return "I couldn't find a character to equip that item on, Guardian."
                target_cid = str(list(chars.keys())[0])
            if target_class_type is None and target_cid in chars:
                target_class_type = chars[target_cid].get("classType")

            res = self._resolve_dynamic_item(
                profile,
                item_name,
                allowed_sources={"inventory", "equipped", "vault", "postmaster"},
                target_class_type=target_class_type,
            )
            if res.get("state") == "ambiguous":
                return (
                    "I found multiple matching items. Tell me which one:\n"
                    + self._format_item_candidates(res.get("candidates", []))
                )
            if res.get("state") != "resolved":
                return f"I couldn't find '{item_name}' among your owned weapons or armor, Guardian."

            cand = res["candidate"]
            name = cand.get("name") or item_name
            src = cand.get("source")
            src_cid = cand.get("character_id")
            iid = str(cand.get("instance_id"))
            ih = cand.get("item_hash")

            if src == "equipped" and src_cid and str(src_cid) == str(target_cid):
                self._last_item = {"name": name, "instance_id": iid, "character_id": str(target_cid), "hash": ih}
                return f"{name} is already equipped, Guardian."

            if src == "postmaster":
                pull_to = src_cid or target_cid
                pr = self.bungie.pull_from_postmaster(int(ih), 1, iid, str(pull_to), int(mtype))
                if pr.get("ErrorCode") != 1:
                    return f"I found {name} in postmaster but couldn't pull it, Guardian."
                src = "inventory"
                src_cid = str(pull_to)

            if src == "vault":
                tr = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(target_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=False,
                )
                if tr.get("ErrorCode") != 1:
                    return f"I couldn't pull {name} from your vault, Guardian."
                src = "inventory"
                src_cid = str(target_cid)

            if src in {"inventory", "equipped"} and src_cid and str(src_cid) != str(target_cid):
                if src == "equipped":
                    return f"{name} is equipped on another character. Unequip it first, then I can equip it here."
                to_vault = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(src_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=True,
                )
                if to_vault.get("ErrorCode") != 1:
                    return f"I couldn't move {name} to the vault first, Guardian."
                to_target = self.bungie.transfer_item(
                    membership_type=mtype,
                    character_id=str(target_cid),
                    item_id=iid,
                    item_reference_hash=ih,
                    stack_size=1,
                    transfer_to_vault=False,
                )
                if to_target.get("ErrorCode") != 1:
                    return f"I moved {name} to the vault but couldn't bring it to your target character."

            eq = self.bungie.equip_item(membership_type=mtype, character_id=str(target_cid), item_id=iid)
            if eq.get("ErrorCode") == 1:
                self._last_item = {"name": name, "instance_id": iid, "character_id": str(target_cid), "hash": ih}
                return f"Equipped {name}, Guardian."
            return f"I couldn't equip {name}, Guardian."
        except BungieAPIError as e:
            return f"Sorry Guardian, I couldn't equip that item: {e}"
        except Exception as e:
            return f"Sorry Guardian, I couldn't equip that item: {e}"

