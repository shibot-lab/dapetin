import json

from dapetin.domain.models import Business, Opportunity, OpportunityScore
from dapetin.export import export_csv, export_json


def sample_opportunity() -> Opportunity:
    return Opportunity(
        business=Business(
            name="Contoh Kontraktor",
            category="kontraktor",
            city="Samarinda",
            phone="+628123456789",
            website="https://example.com",
            email="hello@example.com",
            metadata={"whatsapp": "true"},
        ),
        score=OpportunityScore(75, ["Has a website", "Public business email available"]),
    )


def test_export_json(tmp_path) -> None:
    target = tmp_path / "opportunities.json"
    export_json([sample_opportunity()], target)

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload[0]["name"] == "Contoh Kontraktor"
    assert payload[0]["score"] == 75
    assert payload[0]["status"] == "discovered"
    assert payload[0]["metadata"]["whatsapp"] == "true"


def test_export_csv(tmp_path) -> None:
    target = tmp_path / "opportunities.csv"
    export_csv([sample_opportunity()], target)

    content = target.read_text(encoding="utf-8")
    assert "name," in content
    assert "Contoh Kontraktor" in content
    assert "Public business email available" in content
