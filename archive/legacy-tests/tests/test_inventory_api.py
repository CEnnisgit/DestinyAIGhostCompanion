from unittest.mock import Mock

import pytest

import server


def test_normalized_inventory_payload_groups_items(monkeypatch):
    profile = {
        "Response": {
            "profileInventory": {"data": {"items": [{"itemInstanceId": "v1", "itemHash": 1001, "bucketHash": 1}]}},
            "characterInventories": {
                "data": {
                    "c1": {"items": [{"itemInstanceId": "i1", "itemHash": 2001, "bucketHash": 2, "primaryStat": {"value": 1810}}]}
                }
            },
            "characterEquipment": {"data": {"c1": {"items": []}}},
            "characters": {"data": {"c1": {"classType": 1, "light": 1810, "dateLastPlayed": "2026-04-04T00:00:00Z"}}},
        }
    }
    monkeypatch.setattr(server, "_load_profile_for_user", Mock(return_value=("mid", 2, profile)))
    monkeypatch.setattr(server.assistant, "_active_character_id", Mock(return_value="c1"))
    monkeypatch.setattr(
        server.assistant,
        "_collect_owned_items",
        Mock(
            return_value=[
                {"item": {"itemInstanceId": "v1", "itemHash": 1001, "bucketHash": 1}, "source": "vault", "character_id": None},
                {"item": {"itemInstanceId": "i1", "itemHash": 2001, "bucketHash": 2, "primaryStat": {"value": 1810}}, "source": "inventory", "character_id": "c1"},
            ]
        ),
    )
    monkeypatch.setattr(server.assistant, "_get_item_name", Mock(side_effect=lambda h: {1001: "The Last Word", 2001: "Ahamkara Grips"}[h]))
    monkeypatch.setattr(server.assistant, "_item_class_type", Mock(side_effect=lambda h: {1001: 3, 2001: 1}[h]))
    monkeypatch.setattr(
        server.assistant.bungie,
        "get_inventory_item_definition",
        Mock(
            side_effect=lambda h: {
                1001: {"Response": {"itemType": 3, "displayProperties": {"icon": "/x.png"}, "inventory": {"tierTypeName": "Exotic"}}},
                2001: {"Response": {"itemType": 2, "displayProperties": {"icon": "/y.png"}, "inventory": {"tierTypeName": "Exotic"}}},
            }[h]
        ),
    )

    payload = server._normalized_inventory_payload(1)

    assert payload["active_character_id"] == "c1"
    assert len(payload["sections"]["vault"]) == 1
    assert len(payload["sections"]["inventory"]) == 1
    assert payload["sections"]["vault"][0]["actions"]


def test_preview_inventory_action_creates_confirmation(monkeypatch):
    monkeypatch.setattr(server, "_require_user", Mock(return_value={"id": 1}))
    monkeypatch.setattr(
        server,
        "_normalized_inventory_payload",
        Mock(
            return_value={
                "membership_id": "mid",
                "membership_type": 2,
                "active_character_id": "c1",
                "characters": [{"character_id": "c1", "class_type": 1, "class_name": "Hunter"}],
                "items": [
                    {
                        "instance_id": "i1",
                        "item_hash": 123,
                        "name": "Forerunner",
                        "source": "inventory",
                        "character_id": "c1",
                        "class_type": 3,
                        "actions": ["equip", "vault"],
                    }
                ],
            }
        ),
    )

    result = server.api_preview_inventory_action(
        server.InventoryActionPreviewRequest(action="equip", item_instance_id="i1", target_character_id="c1"),
        authorization="Bearer token",
    )

    assert result["intent"] == "equip"
    assert result["confirmation_token"].startswith("cmd_")
    assert result["planned_steps"]


def test_execute_command_rejects_stale_item_state(monkeypatch):
    monkeypatch.setattr(server, "_require_user", Mock(return_value={"id": 1}))
    monkeypatch.setattr(
        server,
        "_normalized_inventory_payload",
        Mock(
            return_value={
                "items": [
                    {
                        "instance_id": "i1",
                        "actions": ["vault"],
                    }
                ]
            }
        ),
    )
    server._COMMAND_CONFIRMATIONS["cmd_test"] = {
        "uid": 1,
        "intent": "equip",
        "candidate": {"instance_id": "i1"},
    }

    with pytest.raises(server.HTTPException) as exc:
        server.api_execute_command(server.CommandExecuteRequest(confirmation_token="cmd_test"), authorization="Bearer token")

    assert exc.value.status_code == 409


def test_mobile_callback_scheme_sanitizes_values():
    assert server._mobile_callback_scheme("ghostcompanion") == "ghostcompanion"
    assert server._mobile_callback_scheme("ghost+beta") == "ghost+beta"
    assert server._mobile_callback_scheme("bad scheme") == "ghostcompanion"
