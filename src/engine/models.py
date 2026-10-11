"""Stable Phase 1 document contracts."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceType(str, Enum):
    NEWS = "news"
    SOCIAL = "social"


class Entity(BaseModel):
    ticker: str
    name: str
    match_type: str
    confidence: float = Field(ge=0, le=1)


class RawDocument(BaseModel):
    """Source-agnostic raw record; times are normalized to UTC."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    source_type: SourceType
    title: str = ""
    text: str
    url: str | None = None
    author: str | None = None
    published_at: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str | None = None
    tickers: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = False
    content_hash: str | None = None

    @field_validator("published_at", "fetched_at", mode="before")
    @classmethod
    def utc_time(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        else:
            text = str(value).replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)

    @model_validator(mode="after")
    def set_hash(self) -> "RawDocument":
        if not self.content_hash:
            material = f"{self.title.strip().lower()}|{self.text.strip().lower()}"
            self.content_hash = hashlib.sha256(material.encode()).hexdigest()
        self.tickers = sorted({ticker.upper().lstrip("$") for ticker in self.tickers})
        return self


class ProcessedDocument(RawDocument):
    clean_text: str
    entities: list[Entity] = Field(default_factory=list)
    macro_tags: list[str] = Field(default_factory=list)
    dedupe_cluster_id: str
    duplicate_count: int = 1
    has_url: bool = False
    timestamp_flag: str | None = None


class ImpactExplanation(BaseModel):
    formula: str
    base_severity: float
    sentiment_magnitude: float
    credibility_weight: float
    recency_factor: float
    velocity_factor: float
    raw_score: float
    rationale: str


class Signal(BaseModel):
    """Phase 2 analysis output; fields remain stable for API consumers."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    source: str
    source_type: SourceType
    entity: str
    tickers: list[str] = Field(default_factory=list)
    text: str
    published_at: datetime
    sentiment_score: float = Field(ge=-1, le=1)
    sentiment_label: str
    event_type: str
    impact_score: float = Field(ge=1, le=10)
    confidence: float = Field(ge=0, le=1)
    explanation: ImpactExplanation
    is_synthetic: bool
