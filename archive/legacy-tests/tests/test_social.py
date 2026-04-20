import pytest
from unittest.mock import patch, Mock

from ghost.bungie import BungieClient, BungieAPIError, BASE_URL


def make_response(json_data, headers=None, status_code=200):
    resp = Mock()
    resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.status_code = status_code
    return resp


def test_group_search_success():
    data = {"ErrorCode": 1, "Response": {}}
    payload = {"name": "ghosts"}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.group_search(payload)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/Search/", json=payload, headers=None
        )


def test_group_search_error():
    payload = {"name": "ghosts"}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.group_search(payload)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/Search/", json=payload, headers=None
        )


def test_get_clan_members_success():
    data = {"ErrorCode": 1, "Response": {}}
    params = {"memberType": 1, "nameSearch": "foo", "currentPage": 2}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.get_clan_members("123", member_type=1, name_search="foo", current_page=2)
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/GroupV2/123/Members/", params=params
        )


def test_get_clan_members_error():
    params = {"memberType": 1, "nameSearch": "foo", "currentPage": 2}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.get_clan_members("123", member_type=1, name_search="foo", current_page=2)
        mock_get.assert_called_once_with(
            f"{BASE_URL}/GroupV2/123/Members/", params=params
        )


def test_set_membership_type_success():
    data = {"ErrorCode": 1, "Response": 0}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.set_membership_type("1", "2", "3", "4")
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/SetMembershipType/4/", json={}, headers=None
        )


def test_set_membership_type_error():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.set_membership_type("1", "2", "3", "4")
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/SetMembershipType/4/", json={}, headers=None
        )


def test_kick_member_success():
    data = {"ErrorCode": 1, "Response": 0}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.kick_member("1", "2", "3")
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/Kick/", json={}, headers=None
        )


def test_kick_member_error():
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.kick_member("1", "2", "3")
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/Kick/", json={}, headers=None
        )


def test_ban_member_success():
    data = {"ErrorCode": 1, "Response": 0}
    payload = {"comment": "bad", "length": 1}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response(data)
        client = BungieClient("key")
        result = client.ban_member("1", "2", "3", comment="bad", length=1)
        assert result == data
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/Ban/", json=payload, headers=None
        )


def test_ban_member_error():
    payload = {"comment": "bad", "length": 1}
    with patch("ghost.bungie.requests.Session.post") as mock_post:
        mock_post.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.ban_member("1", "2", "3", comment="bad", length=1)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/GroupV2/1/Members/2/3/Ban/", json=payload, headers=None
        )


def test_fireteam_search_success():
    data = {"ErrorCode": 1, "Response": {}}
    params = {"excludeImmediate": True, "langFilter": "en"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.fireteam_search(1, 2, 3, 4, 5, exclude_immediate=True, lang_filter="en")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Search/Available/1/2/3/4/5/", params=params
        )


def test_fireteam_search_error():
    params = {"excludeImmediate": True, "langFilter": "en"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.fireteam_search(1, 2, 3, 4, 5, exclude_immediate=True, lang_filter="en")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Search/Available/1/2/3/4/5/", params=params
        )


def test_list_clan_fireteams_success():
    data = {"ErrorCode": 1, "Response": {}}
    params = {"excludeImmediate": True, "langFilter": "en"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.list_clan_fireteams("10", 1, 2, 3, 4, 5, 6, exclude_immediate=True, lang_filter="en")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Clan/10/Available/1/2/3/4/5/6/", params=params
        )


def test_list_clan_fireteams_error():
    params = {"excludeImmediate": True, "langFilter": "en"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.list_clan_fireteams("10", 1, 2, 3, 4, 5, 6, exclude_immediate=True, lang_filter="en")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Clan/10/Available/1/2/3/4/5/6/", params=params
        )


def test_fireteam_summary_success():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result = client.fireteam_summary("10", "20")
        assert result == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Clan/10/Summary/20/", params=None
        )


def test_fireteam_summary_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client.fireteam_summary("10", "20")
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Fireteam/Clan/10/Summary/20/", params=None
        )
