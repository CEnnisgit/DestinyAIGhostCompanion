from unittest.mock import Mock

import server


def _inventory_payload():
    return {
        "membership_id": "mid",
        "membership_type": 2,
        "active_character_id": "c1",
        "characters": [
            {"character_id": "c1", "class_type": 1, "class_name": "Hunter"},
            {"character_id": "c2", "class_type": 2, "class_name": "Warlock"},
        ],
        "sections": {
            "equipped": [
                {
                    "instance_id": "eq1",
                    "name": "Forerunner",
                    "source": "equipped",
                    "character_id": "c1",
                }
            ],
            "inventory": [],
            "vault": [],
            "postmaster": [],
        },
        "items": [
            {
                "instance_id": "i1",
                "item_hash": 123,
                "name": "Forerunner",
                "source": "inventory",
                "character_id": "c1",
                "class_type": 3,
                "actions": ["equip", "vault"],
                "power": 1810,
                "tier": "Exotic",
                "class_name": "Any",
            },
            {
                "instance_id": "eq1",
                "item_hash": 124,
                "name": "Conditional Finality",
                "source": "equipped",
                "character_id": "c1",
                "class_type": 3,
                "actions": ["equip"],
                "power": 1810,
                "tier": "Exotic",
                "class_name": "Any",
            },
        ],
    }


def test_voice_turn_lists_equipped(monkeypatch):
    monkeypatch.setattr(server, "_require_user", Mock(return_value={"id": 1}))
    monkeypatch.setattr(server, "_normalized_inventory_payload", Mock(return_value=_inventory_payload()))
    monkeypatch.setattr(server, "ensure_conversation", Mock())
    monkeypatch.setattr(server, "append_message", Mock())
    result = server.api_voice_turn(
        server.VoiceTurnRequest(text="show equipped gear", session_id="conv-1"),
        authorization="Bearer token",
    )
    assert result["resolution_state"] == "resolved"
    assert "Forerunner" in result["reply_text"]


def test_voice_turn_requires_confirmation_for_equip(monkeypatch):
    monkeypatch.setattr(server, "_require_user", Mock(return_value={"id": 1}))
    monkeypatch.setattr(server, "_normalized_inventory_payload", Mock(return_value=_inventory_payload()))
    monkeypatch.setattr(server, "ensure_conversation", Mock())
    monkeypatch.setattr(server, "append_message", Mock())
    monkeypatch.setattr(
        server,
        "_resolve_item_for_user",
        Mock(
            return_value={
                "membership_id": "mid",
                "membership_type": 2,
                "target_character_id": "c1",
                "resolution": {"state": "resolved", "candidate": _inventory_payload()["items"][0]},
            }
        ),
    )
    result = server.api_voice_turn(
        server.VoiceTurnRequest(text="equip forerunner", session_id="conv-2"),
        authorization="Bearer token",
    )
    assert result["confirmation_required"] is True
    assert result["confirmation_token"].startswith("cmd_")
    assert result["planned_steps"]


def test_voice_turn_confirm_executes_pending(monkeypatch):
    monkeypatch.setattr(server, "_require_user", Mock(return_value={"id": 1}))
    monkeypatch.setattr(server, "_normalized_inventory_payload", Mock(return_value=_inventory_payload()))
    monkeypatch.setattr(server, "ensure_conversation", Mock())
    monkeypatch.setattr(server, "append_message", Mock())
    monkeypatch.setattr(
        server,
        "_execute_confirmation_token",
        Mock(return_value={"action_id": "act_1", "result": {"message": "Equipped Forerunner."}}),
    )
    state = server._ensure_voice_state(1, "conv-3")
    state["pending_confirmation_token"] = "cmd_ready"

    result = server.api_voice_turn(
        server.VoiceTurnRequest(text="yes", session_id="conv-3"),
        authorization="Bearer token",
    )
    assert result["resolution_state"] == "executed"
    assert result["reply_text"] == "Equipped Forerunner."
