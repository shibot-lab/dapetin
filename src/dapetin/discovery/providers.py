from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from dapetin.domain.models import Business


@dataclass(slots=True)
class DiscoveryQuery:
    keyword: str
    location: str
    limit: int = 20


class DiscoveryProvider(Protocol):
    name: str

    def search(self, query: DiscoveryQuery) -> list[Business]:
        """Return publicly discoverable business records for a query."""


class DemoDiscoveryProvider:
    """Deterministic provider used for local development and tests.

    Real providers can implement the same protocol without changing the rest
    of the DAPETIN pipeline.
    """

    name = "demo"

    def search(self, query: DiscoveryQuery) -> list[Business]:
        return [
            Business(
                name=f"Demo {query.keyword.title()}",
                category=query.keyword,
                address=query.location,
                city=query.location,
                phone="+620000000000",
                website=None,
                source=self.name,
                source_id=f"demo:{query.keyword}:{query.location}",
            )
        ][: query.limit]
