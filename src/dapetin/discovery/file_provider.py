from __future__ import annotations

import csv
import json
from pathlib import Path

from dapetin.domain.models import Business
from dapetin.discovery.providers import DiscoveryQuery


class CsvDiscoveryProvider:
    """Load business records from a CSV export produced by a compliant source."""

    name = "csv"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def search(self, query: DiscoveryQuery) -> list[Business]:
        businesses: list[Business] = []
        with self.path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if not self._matches(row, query):
                    continue
                businesses.append(self._business_from_row(row))
                if len(businesses) >= query.limit:
                    break
        return businesses

    @staticmethod
    def _matches(row: dict[str, str], query: DiscoveryQuery) -> bool:
        haystack = " ".join(row.get(key, "") for key in ("name", "category", "address", "city")).lower()
        return query.keyword.lower() in haystack and query.location.lower() in haystack

    @staticmethod
    def _business_from_row(row: dict[str, str]) -> Business:
        rating = _float_or_none(row.get("rating"))
        review_count = _int_or_none(row.get("review_count"))
        return Business(
            name=row.get("name", "").strip(),
            category=_clean(row.get("category")),
            address=_clean(row.get("address")),
            city=_clean(row.get("city")),
            phone=_clean(row.get("phone")),
            website=_clean(row.get("website")),
            email=_clean(row.get("email")),
            rating=rating,
            review_count=review_count,
            source=_clean(row.get("source")) or self_source(),
            source_id=_clean(row.get("source_id")),
        )


def load_json_businesses(path: str | Path) -> list[Business]:
    """Load a JSON array of business objects for scripts and future providers."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON discovery input must be an array")
    return [Business(**item) for item in data if isinstance(item, dict) and item.get("name")]


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _float_or_none(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def self_source() -> str:
    return "csv"
