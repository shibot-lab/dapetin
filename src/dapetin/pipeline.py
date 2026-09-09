from __future__ import annotations

from dataclasses import dataclass

from dapetin.discovery.providers import DiscoveryProvider, DiscoveryQuery
from dapetin.domain.models import Opportunity
from dapetin.qualification.scoring import score_business


@dataclass(slots=True)
class DiscoveryRun:
    query: DiscoveryQuery
    opportunities: list[Opportunity]


def run_discovery(provider: DiscoveryProvider, query: DiscoveryQuery) -> DiscoveryRun:
    businesses = provider.search(query)
    opportunities = [
        Opportunity(business=business, score=score_business(business))
        for business in businesses
    ]
    opportunities.sort(key=lambda item: item.score.score, reverse=True)
    return DiscoveryRun(query=query, opportunities=opportunities)
