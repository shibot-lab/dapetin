from __future__ import annotations

from dataclasses import dataclass

from dapetin.discovery.providers import DiscoveryProvider, DiscoveryQuery
from dapetin.domain.models import Opportunity, PipelineStatus
from dapetin.enrichment.base import EnrichmentProvider
from dapetin.enrichment.website import apply_enrichment
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


def enrich_run(run: DiscoveryRun, provider: EnrichmentProvider) -> DiscoveryRun:
    """Enrich discovered businesses, then re-score using the new signals."""
    for opportunity in run.opportunities:
        result = provider.enrich(opportunity.business)
        apply_enrichment(opportunity.business, result)
        opportunity.score = score_business(opportunity.business)
        opportunity.status = PipelineStatus.ENRICHED

    run.opportunities.sort(key=lambda item: item.score.score, reverse=True)
    return run
