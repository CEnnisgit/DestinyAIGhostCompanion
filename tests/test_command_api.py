import server


def test_parse_equip_command():
    parsed = server._parse_command_text("equip forerunner on my hunter")
    assert parsed["intent"] == "equip"
    assert parsed["item_query"] == "forerunner"
    assert parsed["target"] == "hunter"


def test_parse_vault_command():
    parsed = server._parse_command_text("vault hawkmoon")
    assert parsed["intent"] == "vault"
    assert parsed["item_query"] == "hawkmoon"


def test_parse_transfer_from_vault_command():
    parsed = server._parse_command_text("transfer ace of spades from my vault")
    assert parsed["intent"] == "transfer_from_vault"
    assert parsed["item_query"] == "ace of spades"


def test_parse_find_item_command():
    parsed = server._parse_command_text("where is conditional finality")
    assert parsed["intent"] == "find_item"
    assert parsed["item_query"] == "conditional finality"


def test_parse_confirmation_control():
    parsed = server._parse_command_text("yes")
    assert parsed["intent"] == "confirm"
