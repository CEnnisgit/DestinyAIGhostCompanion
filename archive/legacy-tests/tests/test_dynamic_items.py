from unittest.mock import Mock

from ghost.assistant import GhostAssistant


def _build_profile():
    return {
        "Response": {
            "profileInventory": {
                "data": {
                    "items": [
                        {"itemInstanceId": "v1", "itemHash": 1001, "location": 2, "bucketHash": 1},
                        {"itemInstanceId": "v2", "itemHash": 1002, "location": 2, "bucketHash": 1},
                    ]
                }
            },
            "characterInventories": {
                "data": {
                    "c_hunter": {
                        "items": [
                            {"itemInstanceId": "i1", "itemHash": 2001, "location": 1, "bucketHash": 2},
                        ]
                    },
                    "c_warlock": {"items": []},
                }
            },
            "characterEquipment": {
                "data": {
                    "c_hunter": {"items": []},
                    "c_warlock": {"items": []},
                }
            },
            "characters": {
                "data": {
                    "c_hunter": {"classType": 1, "dateLastPlayed": "2026-03-08T00:00:00Z"},
                    "c_warlock": {"classType": 2, "dateLastPlayed": "2026-03-09T00:00:00Z"},
                }
            },
        }
    }


def _item_defs():
    return {
        1001: {"Response": {"displayProperties": {"name": "The Last Word"}, "itemType": 3, "classType": 3}},
        1002: {"Response": {"displayProperties": {"name": "Last Rites"}, "itemType": 3, "classType": 3}},
        2001: {"Response": {"displayProperties": {"name": "Ahamkara Grips"}, "itemType": 2, "classType": 1}},
    }


def test_dynamic_resolver_ambiguous_equip():
    bungie = Mock()
    ollama = Mock()
    assistant = GhostAssistant(bungie_client=bungie, ollama_client=ollama)
    assistant._get_destiny_membership = Mock(return_value=("mid", 2))

    defs = _item_defs()
    defs[1001]["Response"]["displayProperties"]["name"] = "Hawkmoon"
    defs[1002]["Response"]["displayProperties"]["name"] = "Hawkmoon"
    profile = _build_profile()
    bungie.get_profile.return_value = profile
    bungie.get_inventory_item_definition.side_effect = lambda h: defs[int(h)]

    msg = assistant._handle_equip_item("hawkmoon")
    assert "multiple matching items" in msg.lower()
    assert "Hawkmoon" in msg


def test_dynamic_transfer_from_vault_then_equip():
    bungie = Mock()
    ollama = Mock()
    assistant = GhostAssistant(bungie_client=bungie, ollama_client=ollama)
    assistant._get_destiny_membership = Mock(return_value=("mid", 2))

    defs = _item_defs()
    profile = _build_profile()
    bungie.get_profile.return_value = profile
    bungie.get_inventory_item_definition.side_effect = lambda h: defs[int(h)]
    bungie.transfer_item.return_value = {"ErrorCode": 1}
    bungie.equip_item.return_value = {"ErrorCode": 1}

    msg = assistant._handle_equip_item("the last word", "warlock")
    assert "equipped the last word" in msg.lower()
    bungie.transfer_item.assert_called_once()
    bungie.equip_item.assert_called_once()


def test_dynamic_vault_weapon_or_armor_only():
    bungie = Mock()
    ollama = Mock()
    assistant = GhostAssistant(bungie_client=bungie, ollama_client=ollama)
    assistant._get_destiny_membership = Mock(return_value=("mid", 2))

    profile = _build_profile()
    profile["Response"]["characterInventories"]["data"]["c_hunter"]["items"].append(
        {"itemInstanceId": "junk1", "itemHash": 3001, "location": 1, "bucketHash": 99}
    )
    defs = _item_defs()
    defs[3001] = {"Response": {"displayProperties": {"name": "Enhancement Core"}, "itemType": 19, "classType": 3}}

    bungie.get_profile.return_value = profile
    bungie.get_inventory_item_definition.side_effect = lambda h: defs[int(h)]

    msg = assistant._handle_vault_item("enhancement core")
    assert "weapons or armor" in msg.lower()
