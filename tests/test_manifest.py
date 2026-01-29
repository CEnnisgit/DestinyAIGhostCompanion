import os
from unittest.mock import patch, Mock

import pytest

from ghost.bungie import BungieClient, BASE_URL

def make_response(json_data, headers=None, status_code=200):
    resp = Mock()
    resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.status_code = status_code
    return resp


def test_get_manifest_caches_result():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result1 = client.get_manifest()
        result2 = client.get_manifest()
        assert result1 == data
        assert result2 == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Manifest/", params=None
        )


def test_get_entity_caches_by_hash():
    data = {"ErrorCode": 1, "Response": {}}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response(data)
        client = BungieClient("key")
        result1 = client.get_entity("DestinyInventoryItemDefinition", 123)
        result2 = client.get_entity("DestinyInventoryItemDefinition", 123)
        assert result1 == data
        assert result2 == data
        mock_get.assert_called_once_with(
            f"{BASE_URL}/Destiny2/Manifest/DestinyInventoryItemDefinition/123/",
            params=None,
        )
