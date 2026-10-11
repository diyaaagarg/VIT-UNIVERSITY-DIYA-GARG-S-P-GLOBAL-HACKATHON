"""Explainable rule-based event taxonomy for offline-first operation."""
from __future__ import annotations
from dataclasses import dataclass

RULES = {
    "Geopolitical": ("hormuz", "sanctions", "blockade", "military", "conflict", "geopolitical"),
    "Macroeconomic": ("inflation", "interest rate", "federal reserve", "cpi", "yield"),
    "Credit Event": ("default", "downgrade", "credit spread", "bankruptcy", "delinquency"),
    "Merger/Acquisition": ("merger", "acquisition", "takeover", "buyout"),
    "Product Launch": ("product", "launch", "previews", "platform feature"),
    "Regulatory": ("regulatory", "regulator", "antitrust", "compliance", "sec "),
    "Earnings": ("earnings", "quarterly", "revenue", "guidance", "profit"),
    "Cybersecurity/Operational": ("cyber", "ransomware", "breach", "hack", "outage", "operational"),
}


@dataclass(frozen=True)
class EventResult:
    event_type: str
    confidence: float
    matched_terms: list[str]


class EventClassifier:
    def classify(self, text: str) -> EventResult:
        lower = text.lower()
        scores = {event: [term for term in terms if term in lower] for event, terms in RULES.items()}
        event, matches = max(scores.items(), key=lambda item: len(item[1]))
        if not matches: return EventResult("Other", 0.4, [])
        return EventResult(event, min(0.92, 0.55 + 0.12 * len(matches)), matches)
