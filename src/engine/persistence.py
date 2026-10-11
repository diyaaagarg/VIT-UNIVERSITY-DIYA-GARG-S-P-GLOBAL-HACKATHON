"""JSONL and SQLite persistence for Phase 1 processed documents."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from src.engine.models import ProcessedDocument, Signal


def persist_documents(documents: list[ProcessedDocument], jsonl_path: Path, db_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for doc in documents: handle.write(doc.model_dump_json() + "\n")
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, published_at TEXT, source TEXT, is_synthetic INTEGER, payload TEXT NOT NULL)")
        connection.executemany("INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)", [(d.id, d.published_at.isoformat(), d.source, int(d.is_synthetic), d.model_dump_json()) for d in documents])


def persist_signals(signals: list[Signal], jsonl_path: Path, db_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for signal in signals: handle.write(signal.model_dump_json() + "\n")
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS signals (id TEXT PRIMARY KEY, document_id TEXT, entity TEXT, event_type TEXT, impact_score REAL, published_at TEXT, payload TEXT NOT NULL)")
        connection.executemany("INSERT OR REPLACE INTO signals VALUES (?, ?, ?, ?, ?, ?, ?)", [(s.id, s.document_id, s.entity, s.event_type, s.impact_score, s.published_at.isoformat(), s.model_dump_json()) for s in signals])


def load_signals(db_path: Path, ticker: str | None = None, high_impact: float | None = None) -> list[Signal]:
    if not db_path.exists(): return []
    query, params = "SELECT payload FROM signals", []
    clauses = []
    if ticker:
        clauses.append("entity = ?"); params.append(ticker.upper())
    if high_impact is not None:
        clauses.append("impact_score >= ?"); params.append(high_impact)
    if clauses: query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY published_at DESC"
    with sqlite3.connect(db_path) as connection:
        return [Signal.model_validate_json(row[0]) for row in connection.execute(query, params).fetchall()]
