from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import request

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


class OpenAIOpportunityAnalysisProvider(OpportunityAnalysisProvider):
    """Analyze opportunities with the OpenAI Responses API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("DAPETIN_AI_MODEL", "gpt-5-mini")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for AI analysis")

    def analyze(self, opportunity: Opportunity) -> OpportunityAnalysis:
        payload = {
            "model": self.model,
            "input": self.build_prompt(opportunity),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "opportunity_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "risks": {"type": "array", "items": {"type": "string"}},
                            "next_step": {"type": "string"},
                        },
                        "required": ["summary", "strengths", "risks", "next_step"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:
            result = json.load(response)
        text = result.get("output_text")
        if not text:
            raise RuntimeError("AI provider returned no output_text")
        data = json.loads(text)
        return OpportunityAnalysis(
            summary=data["summary"],
            strengths=data["strengths"],
            risks=data["risks"],
            next_step=data["next_step"],
        )

    def build_prompt(self, opportunity: Opportunity) -> str:
        business = opportunity.business
        reasons = "\n".join(f"- {reason}" for reason in opportunity.score.reasons) or "- none"
        return (
            "Analyze this business opportunity using only the supplied facts. "
            "Do not invent missing information. Return a concise summary, strengths, "
            "risks, and one practical next step.\n\n"
            f"Business: {business.name}\n"
            f"Category: {business.category or 'unknown'}\n"
            f"Location: {business.address or business.city or 'unknown'}\n"
            f"Website: {business.website or 'unknown'}\n"
            f"Email: {business.email or 'unknown'}\n"
            f"Phone: {business.phone or 'unknown'}\n"
            f"Opportunity score: {opportunity.score.score}/100\n"
            f"Score reasons:\n{reasons}"
        )


def analyze_opportunity(
    opportunity: Opportunity, provider: OpportunityAnalysisProvider
) -> OpportunityAnalysis:
    return provider.analyze(opportunity)
