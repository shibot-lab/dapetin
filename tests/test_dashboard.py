from dapetin.dashboard import render_dashboard
from dapetin.database import LeadDatabase
from dapetin.domain.models import Business, Opportunity, OpportunityScore, PipelineStatus


def make_opportunity(name: str, score: int = 80) -> Opportunity:
    return Opportunity(
        business=Business(
            name=name,
            category="kontraktor",
            address="Samarinda",
            website="https://example.com",
            email="hello@example.com",
            source="test",
            source_id=name.lower().replace(" ", "-"),
        ),
        score=OpportunityScore(score, ["Has public website"]),
    )


def test_dashboard_renders_lead_and_status_form(tmp_path):
    database = LeadDatabase(tmp_path / "test.db")
    lead_id = database.save(make_opportunity("Prima Karya"))

    html = render_dashboard(database.list_with_ids())

    assert "Prima Karya" in html
    assert "80/100" in html
    assert f'name="id" value="{lead_id}"' in html
    assert "Has public website" in html
    assert "qualified" in html


def test_dashboard_filter_uses_pipeline_status(tmp_path):
    database = LeadDatabase(tmp_path / "test.db")
    first_id = database.save(make_opportunity("First Lead"))
    second_id = database.save(make_opportunity("Second Lead"))
    database.update_status(second_id, PipelineStatus.QUALIFIED)

    records = database.list_with_ids(PipelineStatus.QUALIFIED)
    html = render_dashboard(records, PipelineStatus.QUALIFIED)

    assert "Second Lead" in html
    assert "First Lead" not in html
    assert f'name="id" value="{second_id}"' in html
    assert f'name="id" value="{first_id}"' not in html
