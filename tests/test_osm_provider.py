import io
import json
from unittest.mock import patch

from dapetin.discovery.osm_provider import OpenStreetMapDiscoveryProvider
from dapetin.discovery.providers import DiscoveryQuery


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_search_maps_overpass_businesses(monkeypatch):
    provider = OpenStreetMapDiscoveryProvider()
    payload = {
        "elements": [
            {
                "type": "node",
                "id": 123,
                "tags": {
                    "name": "PT Kontraktor Samarinda",
                    "craft": "builder",
                    "addr:street": "Jl. Contoh",
                    "addr:city": "Samarinda",
                    "phone": "+62541000000",
                    "website": "https://example.test",
                },
            }
        ]
    }

    with patch("dapetin.discovery.osm_provider.urlopen", return_value=FakeResponse(payload)) as mocked:
        result = provider.search(DiscoveryQuery("kontraktor", "Samarinda", 20))

    assert len(result) == 1
    assert result[0].name == "PT Kontraktor Samarinda"
    assert result[0].source == "openstreetmap"
    assert result[0].source_id == "osm:node:123"
    assert result[0].website == "https://example.test"
    assert result[0].metadata["license"] == "OpenStreetMap contributors, ODbL"
    request = mocked.call_args.args[0]
    assert request.full_url == provider.endpoint
    assert request.headers["User-agent"] == provider.user_agent


def test_search_respects_limit_and_deduplicates():
    provider = OpenStreetMapDiscoveryProvider()
    payload = {
        "elements": [
            {"type": "node", "id": 1, "tags": {"name": "Builder A"}},
            {"type": "node", "id": 1, "tags": {"name": "Builder A"}},
            {"type": "node", "id": 2, "tags": {"name": "Builder B"}},
        ]
    }

    with patch("dapetin.discovery.osm_provider.urlopen", return_value=FakeResponse(payload)):
        result = provider.search(DiscoveryQuery("builder", "Samarinda", 1))

    assert [item.name for item in result] == ["Builder A"]
