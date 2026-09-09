from dataclasses import dataclass, field
from enum import StrEnum


class PipelineStatus(StrEnum):
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    INTERESTED = "interested"
    MEETING = "meeting"
    CUSTOMER = "customer"
    ARCHIVED = "archived"


@dataclass(slots=True)
class Business:
    name: str
    category: str | None = None
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    website: str | None = None
    email: str | None = None
    rating: float | None = None
    review_count: int | None = None
    source: str | None = None
    source_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class OpportunityScore:
    score: int
    reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.score = max(0, min(100, self.score))


@dataclass(slots=True)
class Opportunity:
    business: Business
    score: OpportunityScore
    status: PipelineStatus = PipelineStatus.DISCOVERED
