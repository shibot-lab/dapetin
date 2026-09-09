from dapetin.analysis import OpportunityAnalysis, OpportunityAnalysisProvider, analyze_opportunity
from dapetin.domain.models import Business, Opportunity, OpportunityScore


class FakeProvider(OpportunityAnalysisProvider):
    def analyze(self, opportunity: Opportunity) -> OpportunityAnalysis:
        return OpportunityAnalysis(
            summary=opportunity.business.name,
            strengths=["website"],
            risks=["unknown"],
            next_step="review",
        )


def test_analyze_opportunity_delegates_to_provider():
    opportunity = Opportunity(
        business=Business(name="Prima Karya", website="https://example.com"),
        score=OpportunityScore(80, ["Has public website"]),
    )

    result = analyze_opportunity(opportunity, FakeProvider())

    assert result.summary == "Prima Karya"
    assert result.strengths == ["website"]
    assert result.risks == ["unknown"]
    assert result.next_step == "review"
