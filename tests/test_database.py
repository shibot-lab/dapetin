from dapetin.database import LeadDatabase
from dapetin.domain.models import Business, Opportunity, OpportunityScore, PipelineStatus


def make_opportunity() -> Opportunity:
    return Opportunity(
        business=Business(
            name="Test Contractor",
            category="contractor",
            city="Samarinda",
            source="test",
            source_id="test:1",
            metadata={"whatsapp": "true"},
        ),
        score=OpportunityScore(55, ["test signal"]),
    )


def test_save_and_list(tmp_path) -> None:
    database = LeadDatabase(tmp_path / "dapetin.db")
    opportunity = make_opportunity()

    lead_id = database.save(opportunity)
    leads = database.list()

    assert lead_id == 1
    assert len(leads) == 1
    assert leads[0].business.name == "Test Contractor"
    assert leads[0].score.score == 55
    assert leads[0].status == PipelineStatus.DISCOVERED
    assert leads[0].business.metadata["whatsapp"] == "true"


def test_save_updates_existing_source_id(tmp_path) -> None:
    database = LeadDatabase(tmp_path / "dapetin.db")
    opportunity = make_opportunity()

    database.save(opportunity)
    opportunity.score = OpportunityScore(80, ["updated"])
    opportunity.status = PipelineStatus.QUALIFIED
    database.save(opportunity)

    leads = database.list()
    assert len(leads) == 1
    assert leads[0].score.score == 80
    assert leads[0].status == PipelineStatus.QUALIFIED


def test_update_status(tmp_path) -> None:
    database = LeadDatabase(tmp_path / "dapetin.db")
    lead_id = database.save(make_opportunity())

    database.update_status(lead_id, PipelineStatus.CONTACTED)

    assert database.list()[0].status == PipelineStatus.CONTACTED
    assert len(database.list(PipelineStatus.CONTACTED)) == 1
    assert database.list(PipelineStatus.DISCOVERED) == []
