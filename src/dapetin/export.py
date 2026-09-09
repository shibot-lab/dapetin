from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from dapetin.domain.models import Opportunity


EXPORT_FIELDS = (
    "name",
    "category",
    "address",
    "city",
    "phone",
    "website",
    "email",
    "rating",
    "review_count",
    "source",
    "source_id",
    "score",
    "status",
    "reasons",
    "metadata",
)


def _record(opportunity: Opportunity) -> dict[str, object]:
    business = opportunity.business
    return {
        "name": business.name,
        "category": business.category,
        "address": business.address,
        "city": business.city,
        "phone": business.phone,
        "website": business.website,
        "email": business.email,
        "rating": business.rating,
        "review_count": business.review_count,
        "source": business.source,
        "source_id": business.source_id,
        "score": opportunity.score.score,
        "status": opportunity.status.value,
        "reasons": opportunity.score.reasons,
        "metadata": business.metadata,
    }


def export_json(opportunities: list[Opportunity], path: str | Path) -> None:
    """Write opportunities as a JSON array."""
    target = Path(path)
    target.write_text(
        json.dumps([_record(item) for item in opportunities], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export_csv(opportunities: list[Opportunity], path: str | Path) -> None:
    """Write opportunities as a flat CSV suitable for spreadsheets."""
    target = Path(path)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for opportunity in opportunities:
            record = _record(opportunity)
            record["reasons"] = " | ".join(opportunity.score.reasons)
            record["metadata"] = json.dumps(opportunity.business.metadata, ensure_ascii=False, sort_keys=True)
            writer.writerow(record)
