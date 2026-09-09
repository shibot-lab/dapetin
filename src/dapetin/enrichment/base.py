from __future__ import annotations

from typing import Protocol

from dapetin.domain.models import Business
from dapetin.enrichment.website import EnrichmentResult


class EnrichmentProvider(Protocol):
    name: str

    def enrich(self, business: Business) -> EnrichmentResult:
        """Return public enrichment signals for one business."""
