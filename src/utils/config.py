"""Typed YAML-plus-environment configuration."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


class AppSettings(BaseModel):
    mode: str = "replay"
    replay_speed: str = "instant"
    database_path: str = "data/risk_engine.db"
    processed_path: str = "data/processed/processed.jsonl"
    near_duplicate_threshold: int = Field(default=92, ge=1, le=100)
    skip_non_english: bool = False
    future_timestamp_tolerance_minutes: int = 5
    finnhub_api_key: str | None = None


@lru_cache
def settings() -> AppSettings:
    values = read_yaml(ROOT / "config" / "app.yaml")
    values["mode"] = os.getenv("RISK_ENGINE_MODE", values.get("mode", "replay"))
    values["finnhub_api_key"] = os.getenv("FINNHUB_API_KEY") or None
    return AppSettings(**values)


@lru_cache
def universe() -> dict[str, Any]:
    return read_yaml(ROOT / "config" / "universe.yaml")


@lru_cache
def sources() -> dict[str, Any]:
    return read_yaml(ROOT / "config" / "sources.yaml")


@lru_cache
def nlp_config() -> dict[str, Any]:
    return read_yaml(ROOT / "config" / "nlp.yaml")
