from __future__ import annotations

import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dapetin.domain.models import Business
from dapetin.discovery.providers import DiscoveryQuery


class OpenStreetMapDiscoveryProvider:
    """Discover businesses from OpenStreetMap through a read-only Overpass API."""

    name = "openstreetmap"
    endpoint = "https://overpass-api.de/api/interpreter"
    user_agent = "DAPETIN/0.1 (business opportunity discovery)"

    def search(self, query: DiscoveryQuery) -> list[Business]:
        if query.limit <= 0:
            return []
        keyword = re.escape(query.keyword.strip())
        location = re.escape(query.location.strip())
        if not keyword or not location:
            return []

        # Match names containing the requested keyword. For contractor searches,
        # also include OSM's builder craft tag because many builders do not put
        # "kontraktor" in the business name.
        contractor = query.keyword.strip().lower() in {
            "kontraktor",
            "contractor",
            "builder",
            "construction",
        }
        extra = '\n  nwr["craft"="builder"](area.searchArea);' if contractor else ""
        overpass_query = f"""[out:json][timeout:60];
area["name"~"^{location}$",i]["boundary"="administrative"]->.searchArea;
(
  nwr["name"~"{keyword}",i](area.searchArea);{extra}
);
out center tags;"""

        payload = urlencode({"data": overpass_query}).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            method="POST",
        )
        with urlopen(request, timeout=75) as response:
            data = json.load(response)

        businesses: list[Business] = []
        seen: set[str] = set()
        for element in data.get("elements", []):
            tags = element.get("tags") or {}
            name = (tags.get("name") or "").strip()
            if not name:
                continue
            source_id = f"osm:{element.get('type')}:{element.get('id')}"
            if source_id in seen:
                continue
            seen.add(source_id)
            businesses.append(self._business_from_tags(name, tags, source_id))
            if len(businesses) >= query.limit:
                break
        return businesses

    @staticmethod
    def _business_from_tags(name: str, tags: dict[str, str], source_id: str) -> Business:
        address_parts = [
            tags.get("addr:housenumber", "").strip(),
            tags.get("addr:street", "").strip(),
            tags.get("addr:suburb", "").strip(),
        ]
        address = ", ".join(part for part in address_parts if part) or None
        category = tags.get("craft") or tags.get("office") or tags.get("shop") or tags.get("amenity")
        return Business(
            name=name,
            category=category,
            address=address,
            city=tags.get("addr:city") or None,
            phone=tags.get("phone") or tags.get("contact:phone") or None,
            website=tags.get("website") or tags.get("contact:website") or None,
            email=tags.get("email") or tags.get("contact:email") or None,
            source="openstreetmap",
            source_id=source_id,
            metadata={"license": "OpenStreetMap contributors, ODbL"},
        )
