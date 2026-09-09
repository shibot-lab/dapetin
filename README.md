# DAPETIN

> Turn the internet into opportunities.

DAPETIN is an opportunity discovery platform. It starts as a focused discovery and qualification engine for local businesses, then grows into a workspace for enrichment, scoring, outreach, CRM, and analytics.

## v0.1 goal

**Input:** keyword + location

**Output:** normalized business records with enrichment and an explainable opportunity score.

The first release deliberately avoids mass messaging. Outreach will be added later with safeguards for consent, opt-out, rate limits, and provider terms.

## Architecture

```text
DAPETIN
├── Discovery      -> find candidate businesses
├── Enrichment     -> normalize public business/site data
├── Qualification  -> determine fit and opportunity signals
├── Scoring        -> explain why a business is interesting
├── Outreach       -> future, targeted and compliant
├── CRM            -> future pipeline
└── Analytics      -> future performance metrics
```

## Repository layout

```text
src/dapetin/
├── domain/        # core models and business rules
├── discovery/     # provider-agnostic discovery interfaces
├── enrichment/   # normalization/enrichment
├── qualification/ # opportunity rules
└── cli.py         # local MVP command

tests/
└── test_scoring.py
```

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m dapetin.cli --help
pytest
```

## Design principles

1. Provider-agnostic: Google Maps or another source is an adapter, not the product.
2. Explainable scoring: every score has reasons.
3. Minimal data: store only what is useful for the workflow.
4. Responsible outreach: no spam-blast architecture.
5. Build for revenue: prove the workflow before adding SaaS complexity.

## Roadmap

- [x] Project foundation
- [x] Domain model
- [x] Explainable opportunity scoring
- [ ] First discovery provider adapter
- [ ] Website enrichment
- [ ] CSV/JSON export
- [ ] Lead database and pipeline
- [ ] Web dashboard
- [ ] AI-assisted opportunity analysis
- [ ] Targeted outreach automation
