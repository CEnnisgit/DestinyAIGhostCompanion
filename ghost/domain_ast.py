"""Domain AST (object tree) built from Bungie profile/character JSON.

This provides a typed, easy-to-traverse representation of a player's
profile: characters, equipment, inventory, and vault. It enriches items with
basic definitions (name, type, bucket) and item instance data (power) when
available.

Typical usage
-------------
from ghost.bungie import BungieClient
from ghost.domain_ast import build_profile_ast

client = BungieClient(api_key)
client.authenticate_user(tokens)
ast = build_profile_ast(client, membership_type=2, membership_id="...")
for cid, ch in ast.characters.items():
    print(cid, ch.light)
    for it in ch.equipped:
        print(" ", it.name, it.power)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ItemNode:
    instance_id: str
    item_hash: int
    bucket_hash: Optional[int] = None
    equipped: bool = False
    power: Optional[int] = None
    name: Optional[str] = None
    type_name: Optional[str] = None


@dataclass
class InventoryNode:
    bucket_to_items: Dict[int, List[ItemNode]] = field(default_factory=dict)


@dataclass
class CharacterNode:
    character_id: str
    class_type: Optional[int] = None
    light: Optional[int] = None
    equipped: List[ItemNode] = field(default_factory=list)
    inventory: InventoryNode = field(default_factory=InventoryNode)


@dataclass
class ProfileNode:
    membership_type: int
    membership_id: str
    characters: Dict[str, CharacterNode] = field(default_factory=dict)
    vault: List[ItemNode] = field(default_factory=list)


# Minimal component set to populate the AST with equipment, inventories, vault,
# and itemInstances for power/light.
AST_COMPONENTS_DEFAULT: List[int] = [
    100,  # Profiles
    200,  # Characters
    201,  # CharacterInventories
    205,  # CharacterEquipment
    102,  # ProfileInventories (vault)
    300,  # ItemInstances (power/light)
]


def _safe_get(d: dict, *path: str, default=None):  # type: ignore[no-untyped-def]
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _extract_def_fields(def_json: dict) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Return (name, type_display_name, bucket_hash) from a manifest definition JSON.

    Bungie manifest endpoints wrap the definition under "Response".
    """
    resp = def_json.get("Response", {}) if isinstance(def_json, dict) else {}
    name = _safe_get(resp, "displayProperties", "name")
    type_name = resp.get("itemTypeDisplayName")
    bucket = _safe_get(resp, "inventory", "bucketTypeHash")
    try:
        bucket_hash = int(bucket) if bucket is not None else None
    except Exception:
        bucket_hash = None
    return name, type_name, bucket_hash


def build_profile_ast(client, membership_type: int, membership_id: str, *, components: Optional[List[int]] = None) -> ProfileNode:
    """Build and return a ProfileNode for the given membership.

    - Fetches profile data with a sensible default component set.
    - Builds CharacterNode(s) and fills equipped and inventory items.
    - Adds vault items from profileInventory.
    - Enriches items with definitions and item instance power when available.
    """
    if components is None:
        components = AST_COMPONENTS_DEFAULT

    profile = client.get_profile(membership_type, membership_id, components=components)
    resp = profile.get("Response", {}) if isinstance(profile, dict) else {}

    pnode = ProfileNode(membership_type=membership_type, membership_id=membership_id)

    # Characters
    chars = _safe_get(resp, "characters", "data", default={}) or {}
    for cid, cdata in chars.items():
        pnode.characters[cid] = CharacterNode(
            character_id=cid,
            class_type=cdata.get("classType"),
            light=cdata.get("light"),
        )

    # Preload item instance data for power/light
    instances = _safe_get(resp, "itemComponents", "instances", "data", default={}) or {}

    def _mk_item(item_entry: dict, equipped: bool = False) -> ItemNode:
        inst_id = str(item_entry.get("itemInstanceId") or "")
        item_hash = int(item_entry.get("itemHash"))
        node = ItemNode(instance_id=inst_id, item_hash=item_hash, equipped=equipped)
        # Enrich from definitions
        try:
            defs = client.get_inventory_item_definition(item_hash)
            name, type_name, bucket_hash = _extract_def_fields(defs)
            node.name = name
            node.type_name = type_name
            node.bucket_hash = bucket_hash
        except Exception:
            pass
        # Enrich from itemInstances
        if inst_id and inst_id in instances:
            inst = instances.get(inst_id, {})
            try:
                node.power = int(_safe_get(inst, "primaryStat", "value", default=None) or 0) or None
            except Exception:
                node.power = None
        return node

    # Equipment
    equip = _safe_get(resp, "characterEquipment", "data", default={}) or {}
    for cid, edata in equip.items():
        ch = pnode.characters.get(cid)
        if not ch:
            continue
        for it in edata.get("items", []) or []:
            ch.equipped.append(_mk_item(it, equipped=True))

    # Character inventories
    inv = _safe_get(resp, "characterInventories", "data", default={}) or {}
    for cid, idata in inv.items():
        ch = pnode.characters.get(cid)
        if not ch:
            continue
        for it in idata.get("items", []) or []:
            item_node = _mk_item(it, equipped=False)
            bucket = item_node.bucket_hash if item_node.bucket_hash is not None else -1
            ch.inventory.bucket_to_items.setdefault(bucket, []).append(item_node)

    # Vault (profile inventory)
    p_inv = _safe_get(resp, "profileInventory", "data", default={}) or {}
    for it in p_inv.get("items", []) or []:
        pnode.vault.append(_mk_item(it, equipped=False))

    return pnode


# Convenience queries ---------------------------------------------------------

def equipped_items_by_bucket(character: CharacterNode) -> Dict[int, List[ItemNode]]:
    """Group equipped items by their bucket hash for a character."""
    out: Dict[int, List[ItemNode]] = {}
    for it in character.equipped:
        bucket = it.bucket_hash if it.bucket_hash is not None else -1
        out.setdefault(bucket, []).append(it)
    return out


def find_items_by_name(profile: ProfileNode, needle: str) -> List[ItemNode]:
    """Case-insensitive name match across all characters and the vault."""
    needle_l = needle.lower()
    hits: List[ItemNode] = []
    for ch in profile.characters.values():
        for it in ch.equipped:
            if (it.name or "").lower().find(needle_l) >= 0:
                hits.append(it)
        for items in ch.inventory.bucket_to_items.values():
            for it in items:
                if (it.name or "").lower().find(needle_l) >= 0:
                    hits.append(it)
    for it in profile.vault:
        if (it.name or "").lower().find(needle_l) >= 0:
            hits.append(it)
    return hits

