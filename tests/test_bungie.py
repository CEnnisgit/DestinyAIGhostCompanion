import os
from unittest.mock import patch, Mock

import pytest

from ghost.bungie import BungieClient, BungieAPIError, BASE_URL


def make_response(
    json_data, headers=None, status_code=200, json_exc: Exception | None = None
):
    """Construct a mock response object for testing."""

    resp = Mock()
    if json_exc is not None:
        resp.json.side_effect = json_exc
    else:
        resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.status_code = status_code
    return resp


def test_get_raises_on_error_code():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_raises_on_rate_limit():
    headers = {"X-RateLimit-Remaining": "0"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 1}, headers)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_sleeps_when_retry_after():
    headers = {"Retry-After": "5"}
    with patch("ghost.bungie.requests.Session.get") as mock_get, patch(
        "ghost.bungie.time.sleep"
    ) as mock_sleep:
        mock_get.side_effect = [
            make_response({"ErrorCode": 1}, headers),
            make_response({"ErrorCode": 1}, {}),
        ]
        client = BungieClient("key")
        client._get("/foo")
        client._get("/foo")
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args.args[0] == pytest.approx(5, abs=0.1)


def test_user_agent_header(monkeypatch):
    monkeypatch.setenv("BUNGIE_APP_NAME", "TestApp")
    monkeypatch.setenv("BUNGIE_APP_VERSION", "1.2")
    monkeypatch.setenv("BUNGIE_APP_URL", "https://example.test")
    client = BungieClient("key")
    assert (
        client.session.headers["User-Agent"]
        == "TestApp/1.2 (+https://example.test)"
    )


def test_get_raises_on_http_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({}, status_code=503)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_raises_on_invalid_json():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({}, json_exc=ValueError("boom"))
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_post_raises_on_error_code():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._post("/foo")


def test_post_raises_on_rate_limit():
    headers = {"X-RateLimit-Remaining": "0"}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 1}, headers)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._post("/foo")


def test_post_sleeps_when_retry_after():
    headers = {"Retry-After": "5"}
    with patch("ghost.bungie.requests.Session.post") as mock_post, patch(
        "ghost.bungie.time.sleep"
    ) as mock_sleep:
        mock_post.side_effect = [
            make_response({"ErrorCode": 1}, headers),
            make_response({"ErrorCode": 1}, {}),
        ]
        client = BungieClient("key")
        client._post("/foo")
        client._post("/foo")
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args.args[0] == pytest.approx(5, abs=0.1)


def test_post_raises_on_http_error():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({}, status_code=503)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._post("/foo")


def test_post_raises_on_invalid_json():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({}, json_exc=ValueError("boom"))
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._post("/foo")


def test_post_sends_payload_and_headers():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 1})
        client = BungieClient("key")
        payload = {"a": 1}
        headers = {"X-Test": "1"}
        client._post("/foo", payload, headers)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/foo", json=payload, headers=headers
        )


def test_init_sets_authorization_header():
    client = BungieClient("key", access_token="abc")
    assert client.session.headers["Authorization"] == "Bearer abc"


def test_set_and_refresh_access_token():
    client = BungieClient("key")
    client.set_access_token("tok1")
    assert client.session.headers["Authorization"] == "Bearer tok1"
    client.refresh_access_token("tok2")
    assert client.session.headers["Authorization"] == "Bearer tok2"


def test_authenticated_get_includes_header():
    def fake_get(self, url, params=None, **kwargs):
        assert self.headers["Authorization"] == "Bearer tok"
        return make_response({"ErrorCode": 1})

    with patch("ghost.bungie.requests.Session.get", new=fake_get):
        client = BungieClient("key", access_token="tok")
        client._get("/foo")


def test_authenticated_post_includes_header():
    def fake_post(self, url, json=None, headers=None, **kwargs):
        assert self.headers["Authorization"] == "Bearer tok"
        return make_response({"ErrorCode": 1})

    with patch("ghost.bungie.requests.Session.post", new=fake_post):
        client = BungieClient("key")
        client.set_access_token("tok")
        client._post("/foo")


def test_search_destiny_player_success():
    data = {"ErrorCode": 1, "Response": []}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.search_destiny_player(1, "Foo")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/SearchDestinyPlayer/1/Foo/", params=None
        )


def test_search_destiny_player_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.search_destiny_player(1, "Foo")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/SearchDestinyPlayer/1/Foo/", params=None
        )


def test_get_profile_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_profile(1, "123", "100")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/", params={"components": "100"}
        )


def test_get_profile_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_profile(1, "123", "100")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/", params={"components": "100"}
        )


def test_get_character_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_character(1, "123", "456", "200")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/",
            params={"components": "200"},
        )


def test_get_character_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_character(1, "123", "456", "200")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/",
            params={"components": "200"},
        )


def test_search_player_by_name_success():
    data = {"ErrorCode": 1, "Response": []}
    payload = {"displayName": "Foo", "displayNameCode": 42}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.search_player_by_name(1, "Foo", 42)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/SearchDestinyPlayerByBungieName/1/",
            json=payload,
            headers=None,
        )


def test_search_player_by_name_error():
    payload = {"displayName": "Foo", "displayNameCode": 42}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.search_player_by_name(1, "Foo", 42)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/SearchDestinyPlayerByBungieName/1/",
            json=payload,
            headers=None,
        )


def test_get_linked_profiles_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_linked_profiles(1, "123", True)
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/LinkedProfiles/",
            params={"getAllMemberships": True},
        )


def test_get_linked_profiles_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_linked_profiles(1, "123", True)
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/LinkedProfiles/",
            params={"getAllMemberships": True},
        )


def test_get_item_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_item(1, "123", "456", "300")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Item/456/",
            params={"components": "300"},
        )


def test_get_item_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_item(1, "123", "456", "300")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Item/456/",
            params={"components": "300"},
        )


def test_get_character_vendors_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_character_vendors(1, "123", "456", "400")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/Vendors/",
            params={"components": "400"},
        )


def test_get_character_vendors_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_character_vendors(1, "123", "456", "400")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/Vendors/",
            params={"components": "400"},
        )


def test_get_vendor_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_vendor(1, "123", "456", "789", "400")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/Vendors/789/",
            params={"components": "400"},
        )


def test_get_vendor_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_vendor(1, "123", "456", "789", "400")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/Vendors/789/",
            params={"components": "400"},
        )


def test_get_collectibles_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_collectibles(1, "123", "456", "789", "800")
        assert result == data
        mock_get.assert_called_once_with(
            (
                f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/"
                "Collectibles/789/"
            ),
            params={"components": "800"},
        )


def test_get_collectibles_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_collectibles(1, "123", "456", "789", "800")
        mock_get.assert_called_once_with(
            (
                f"{BASE_URL}/Destiny2/1/Profile/123/Character/456/"
                "Collectibles/789/"
            ),
            params={"components": "800"},
        )


def test_transfer_item_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "itemReferenceHash": 789,
        "stackSize": 2,
        "transferToVault": True,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.transfer_item(1, "123", "456", 789, 2, True)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/TransferItem/",
            json=payload,
            headers=None,
        )


def test_transfer_item_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "itemReferenceHash": 789,
        "stackSize": 2,
        "transferToVault": True,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.transfer_item(1, "123", "456", 789, 2, True)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/TransferItem/",
            json=payload,
            headers=None,
        )


def test_pull_from_postmaster_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "itemReferenceHash": 789,
        "stackSize": 2,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.pull_from_postmaster(1, "123", "456", 789, 2)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/PullFromPostmaster/",
            json=payload,
            headers=None,
        )


def test_pull_from_postmaster_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "itemReferenceHash": 789,
        "stackSize": 2,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.pull_from_postmaster(1, "123", "456", 789, 2)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/PullFromPostmaster/",
            json=payload,
            headers=None,
        )


def test_equip_item_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.equip_item(1, "123", "456")
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/EquipItem/",
            json=payload,
            headers=None,
        )


def test_equip_item_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.equip_item(1, "123", "456")
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/EquipItem/",
            json=payload,
            headers=None,
        )


def test_equip_items_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemIds": ["1", "2"],
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.equip_items(1, "123", ["1", "2"])
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/EquipItems/",
            json=payload,
            headers=None,
        )


def test_equip_items_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemIds": ["1", "2"],
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.equip_items(1, "123", ["1", "2"])
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/EquipItems/",
            json=payload,
            headers=None,
        )


def test_equip_loadout_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "loadoutIndex": 0,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.equip_loadout(1, "123", 0)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Loadouts/EquipLoadout/",
            json=payload,
            headers=None,
        )


def test_equip_loadout_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "loadoutIndex": 0,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.equip_loadout(1, "123", 0)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Loadouts/EquipLoadout/",
            json=payload,
            headers=None,
        )


def test_snapshot_loadout_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "loadoutIndex": 0,
        "nameHash": 1,
        "iconHash": 2,
        "colorHash": 3,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.snapshot_loadout(1, "123", 0, 1, 2, 3)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Loadouts/SnapshotLoadout/",
            json=payload,
            headers=None,
        )


def test_snapshot_loadout_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "loadoutIndex": 0,
        "nameHash": 1,
        "iconHash": 2,
        "colorHash": 3,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.snapshot_loadout(1, "123", 0, 1, 2, 3)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Loadouts/SnapshotLoadout/",
            json=payload,
            headers=None,
        )


def test_set_lock_state_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "state": True,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.set_lock_state(1, "123", "456", True)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/SetLockState/",
            json=payload,
            headers=None,
        )


def test_set_lock_state_error():
    payload = {
        "membershipType": 1,
        "characterId": "123",
        "itemId": "456",
        "state": True,
    }
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(
            {"ErrorCode": 2, "Message": "Bad"}
        )
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.set_lock_state(1, "123", "456", True)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Actions/Items/SetLockState/",
            json=payload,
            headers=None,
        )
