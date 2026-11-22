#!/usr/bin/env python3
"""SQLite Structured Research Data Warehouse (`D — Data warehouse`).

Consolidates scattered benchmark observations into a typed SQLite store inside
`.cache/monarch-studio-os/research_warehouse.sqlite`. Enforces schema rule:
`views_descriptive_only = 1` (never causal prediction).
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / ".cache" / "monarch-studio-os" / "research_warehouse.sqlite"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS benchmark_videos (
    source_id TEXT PRIMARY KEY,
    channel_cohort TEXT NOT NULL,
    creator TEXT NOT NULL,
    title TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('long-16x9', 'short-9x16', 'compilation')),
    runtime_s INTEGER,
    title_promise TEXT NOT NULL,
    thumbnail_features TEXT NOT NULL,
    observed_age TEXT NOT NULL,
    displayed_views INTEGER,
    views_descriptive_only INTEGER NOT NULL CHECK (views_descriptive_only = 1),
    script_avg_words_per_sent REAL,
    confidence_and_limitations TEXT NOT NULL
);
"""


def build_warehouse(rows: Iterable[Mapping], db_path: Path = DEFAULT_DB) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_SQL)
        for r in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO benchmark_videos (
                    source_id, channel_cohort, creator, title, format, runtime_s,
                    title_promise, thumbnail_features, observed_age, displayed_views,
                    views_descriptive_only, script_avg_words_per_sent, confidence_and_limitations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    r["source_id"],
                    r["channel_cohort"],
                    r["creator"],
                    r["title"],
                    r["format"],
                    r.get("runtime_s"),
                    r["title_promise"],
                    r["thumbnail_features"],
                    r["observed_age"],
                    r.get("displayed_views"),
                    r.get("script_avg_words_per_sent"),
                    r["confidence_and_limitations"],
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path
