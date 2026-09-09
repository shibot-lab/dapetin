# DAPETIN

> Turn the internet into opportunities.

DAPETIN is an opportunity discovery platform. It starts as a focused discovery and qualification engine for local businesses, then grows into a workspace for enrichment, scoring, outreach, CRM, and analytics.

## v0.1 goal

**Input:** keyword + location

**Output:** normalized business records with enrichment and an explainable opportunity score.

The first release deliberately avoids mass messaging. Outreach is targeted to one qualified lead at a time with safeguards for consent, opt-out, cooldowns, and provider terms.

## Architecture

```text
DAPETIN
├── Discovery      -> find candidate businesses
├── Enrichment     -> normalize public business/site data
├── Qualification  -> determine fit and opportunity signals
├── Scoring        -> explain why a business is interesting
├── Outreach       -> targeted and compliant
├── CRM            -> future pipeline
└── Analytics      -> future performance metrics
```

## Repository layout

```text
src/dapetin/
├── domain/        # core models and business rules
├── discovery/     # provider-agnostic discovery interfaces
├── enrichment/    # normalization/enrichment
├── qualification/ # opportunity rules
├── database.py    # SQLite lead persistence
├── export.py      # CSV/JSON opportunity export
├── analysis.py    # AI-assisted opportunity analysis
├── outreach.py    # targeted outreach provider
├── dashboard.py   # local web dashboard
└── cli.py         # local MVP command

tests/
├── test_scoring.py
├── test_export.py
├── test_database.py
├── test_analysis.py
├── test_outreach.py
└── test_dashboard.py
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

## Lead database and pipeline

Discovery runs are persisted to SQLite. The CLI can list saved leads, filter them by pipeline status, and move a lead through the existing pipeline statuses.

```bash
python -m dapetin.cli discover kontraktor Samarinda --csv businesses.csv --enrich
python -m dapetin.cli leads
python -m dapetin.cli leads --status qualified
python -m dapetin.cli leads --set-status 1 contacted
```

## Web dashboard

The local dashboard reads the existing SQLite lead database, shows saved opportunities with their explainable scores, filters by pipeline status, and updates an existing lead's pipeline status.

```bash
python -m dapetin.cli dashboard
```

Then open `http://127.0.0.1:8000` in a browser. Use `--db`, `--host`, or `--port` when a different local database or port is needed.

## AI-assisted opportunity analysis

AI analysis uses the existing opportunity record and score reasons as input. The integration uses the OpenAI Responses API without adding an SDK dependency.

```bash
export OPENAI_API_KEY="your-api-key"
python -m dapetin.cli analyze 1
```

Set `DAPETIN_AI_MODEL` or pass `--model` to choose the model.

## Targeted outreach automation

Outreach sends one explicitly requested email through a configured SMTP provider. Leads without an email, archived leads, and customers are blocked. A configurable cooldown prevents repeated sends.

```bash
export DAPETIN_SMTP_HOST="smtp.example.com"
export DAPETIN_SMTP_PORT="587"
export DAPETIN_SMTP_USERNAME="username"
export DAPETIN_SMTP_PASSWORD="password"
export DAPETIN_SMTP_SENDER="sender@example.com"
python -m dapetin.cli outreach 1 "Partnership" "Hello, I would like to discuss a potential partnership."
```

The command moves a successfully contacted lead to `contacted`.

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
- [x] First discovery provider adapter
- [x] Website enrichment
- [x] CSV/JSON export
- [x] Lead database and pipeline
- [x] Web dashboard
- [x] AI-assisted opportunity analysis
- [x] Targeted outreach automation
