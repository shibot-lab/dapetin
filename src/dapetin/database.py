from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from dapetin.domain.models import Business, Opportunity, OpportunityScore, PipelineStatus


class LeadDatabase:
    """SQLite persistence for discovered business opportunities."""

    def __init__(self, path: str | Path = "dapetin.db") -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    address TEXT,
                    city TEXT,
                    phone TEXT,
                    website TEXT,
                    email TEXT,
                    rating REAL,
                    review_count INTEGER,
                    source TEXT,
                    source_id TEXT UNIQUE,
                    score INTEGER NOT NULL,
                    reasons TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save(self, opportunity: Opportunity) -> int:
        business = opportunity.business
        values = (
            business.name,
            business.category,
            business.address,
            business.city,
            business.phone,
            business.website,
            business.email,
            business.rating,
            business.review_count,
            business.source,
            business.source_id,
            opportunity.score.score,
            json.dumps(opportunity.score.reasons, ensure_ascii=False),
            opportunity.status.value,
            json.dumps(business.metadata, ensure_ascii=False, sort_keys=True),
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    name, category, address, city, phone, website, email,
                    rating, review_count, source, source_id, score, reasons,
                    status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    address=excluded.address,
                    city=excluded.city,
                    phone=excluded.phone,
                    website=excluded.website,
                    email=excluded.email,
                    rating=excluded.rating,
                    review_count=excluded.review_count,
                    source=excluded.source,
                    score=excluded.score,
                    reasons=excluded.reasons,
                    status=excluded.status,
                    metadata=excluded.metadata
                """,
                values,
            )
            connection.commit()
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            row = connection.execute(
                "SELECT id FROM leads WHERE source_id = ?", (business.source_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("lead was saved but could not be located")
            return int(row["id"])

    def list(self, status: PipelineStatus | None = None) -> list[Opportunity]:
        with self._connect() as connection:
            if status is None:
                rows = connection.execute("SELECT * FROM leads ORDER BY score DESC, id DESC").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM leads WHERE status = ? ORDER BY score DESC, id DESC",
                    (status.value,),
                ).fetchall()
        return [_row_to_opportunity(row) for row in rows]

    def update_status(self, lead_id: int, status: PipelineStatus) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                (status.value, lead_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"lead {lead_id} not found")
            connection.commit()


def _row_to_opportunity(row: sqlite3.Row) -> Opportunity:
    business = Business(
        name=row["name"],
        category=row["category"],
        address=row["address"],
        city=row["city"],
        phone=row["phone"],
        website=row["website"],
        email=row["email"],
        rating=row["rating"],
        review_count=row["review_count"],
        source=row["source"],
        source_id=row["source_id"],
        metadata=json.loads(row["metadata"]),
    )
    return Opportunity(
        business=business,
        score=OpportunityScore(row["score"], json.loads(row["reasons"])),
        status=PipelineStatus(row["status"]),
    )
