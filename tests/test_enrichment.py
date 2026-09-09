from dataclasses import dataclass

from dapetin.domain.models import Business, PipelineStatus
from dapetin.enrichment.website import WebsiteEnricher, apply_enrichment
from dapetin.pipeline import DiscoveryRun, enrich_run
from dapetin.discovery.providers import DiscoveryQuery
from dapetin.domain.models import Opportunity, OpportunityScore


@dataclass
class FakeHeaders:
    def get(self, name: str, default: str = "") -> str:
        return "text/html; charset=utf-8" if name == "Content-Type" else default


class FakeResponse:
    def __init__(self, html: str) -> None:
        self.html = html
        self.headers = FakeHeaders()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self) -> str:
        return "https://example.com/"

    def read(self, max_bytes: int) -> bytes:
        return self.html.encode()


def test_website_enricher_extracts_contact_signals(monkeypatch) -> None:
    html = '''
    <html><head><title>Example Business</title></head>
    <body>Contact sales@example.com or +62 812-3456-7890
    <a href="https://instagram.com/example">Instagram</a>
    <a href="https://wa.me/628123456789">WhatsApp</a></body></html>
    '''
    monkeypatch.setattr("dapetin.enrichment.website.urlopen", lambda *args, **kwargs: FakeResponse(html))

    result = WebsiteEnricher().enrich(Business(name="Example", website="example.com"))

    assert result.success is True
    assert result.title == "Example Business"
    assert "sales@example.com" in result.emails
    assert "+6281234567890" in result.phones
    assert result.whatsapp is True
    assert "https://instagram.com/example" in result.social_urls


def test_enrichment_updates_business_and_status() -> None:
    business = Business(name="Example", website="https://example.com")
    opportunity = Opportunity(business, OpportunityScore(20))
    run = DiscoveryRun(DiscoveryQuery("example", "Samarinda"), [opportunity])

    class Provider:
        name = "fake"

        def enrich(self, business):
            from dapetin.enrichment.website import EnrichmentResult
            return EnrichmentResult(success=True, title="Example", emails=["hello@example.com"], whatsapp=True)

    enrich_run(run, Provider())

    assert business.email == "hello@example.com"
    assert business.metadata["whatsapp"] == "true"
    assert opportunity.status == PipelineStatus.ENRICHED
    assert opportunity.score.score > 20
