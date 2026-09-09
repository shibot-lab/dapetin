from __future__ import annotations

from dataclasses import dataclass

from dapetin.domain.models import Opportunity


@dataclass(frozen=True, slots=True)
class OpportunityAnalysis:
    summary: str
    strengths: list[str]
    risks: list[str]
    next_step: str


class OpportunityAnalysisProvider:
    """Interface for an AI provider that analyzes one opportunity."""

    def analyze(self, opportunity: Opportunity) -> OpportunityAnalysis:
        raise NotImplementedError


class PromptOpportunityAnalysisProvider(OpportunityAnalysisProvider):
    """Builds a compact, provider-neutral prompt for an AI model.

    The provider intentionally does not make network calls. A model integration can
    consume the prompt while keeping DAPETIN's domain model independent of an AI SDK.
    """

    def build_prompt(self, opportunity: Opportunity) -> str:
        business = opportunity.business
        reasons = "\n".join(f"- {reason}" for reason in opportunity.score.reasons) or "- none"
        return (
            "Analyze this business opportunity using only the supplied facts. "
            "Return a concise summary, strengths, risks, and one practical next step.\n\n"
            f"Business: {business.name}\n"
            f"Category: {business.category or 'unknown'}\n"
            f"Location: {business.address or business.city or 'unknown'}\n"
            f"Website: {business.website or 'unknown'}\n"
            f"Email: {business.email or 'unknown'}\n"
            f"Phone: {business.phone or 'unknown'}\n"
            f"Opportunity score: {opportunity.score.score}/100\n"
            f"Score reasons:\n{reasons}"
        )

    def analyze(self, opportunity: Opportunity) -> OpportunityAnalysis:
        raise RuntimeError(
            "No AI model is configured. Use build_prompt() with an AI provider."
        )
