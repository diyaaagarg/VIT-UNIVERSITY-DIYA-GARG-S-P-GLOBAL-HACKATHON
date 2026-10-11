"""Transparent impact formula; every component is persisted in the signal."""
from __future__ import annotations
import math
from datetime import datetime, timezone
from src.engine.models import ImpactExplanation
from src.utils.config import nlp_config


def impact_score(event_type: str, sentiment: float, credibility: float, published_at: datetime, duplicate_count: int, replay_mode: bool = False) -> tuple[float, ImpactExplanation]:
    config = nlp_config()["impact"]
    base = float(config["event_base_severity"].get(event_type, 3.0))
    age_hours = 0.0 if replay_mode else max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 3600)
    recency = math.exp(-math.log(2) * age_hours / config["recency_half_life_hours"])
    velocity = min(1.5, 1 + 0.15 * max(0, duplicate_count - 1))
    raw = base * (0.85 + 0.15 * abs(sentiment)) * (0.9 + 0.1 * credibility) * (0.9 + 0.1 * recency) * velocity
    score = round(min(10, max(1, raw)), 2)
    explanation = ImpactExplanation(formula="clamp(1,10,base*(0.85+0.15*|sentiment|)*(0.9+0.1*credibility)*(0.9+0.1*recency)*velocity)", base_severity=base, sentiment_magnitude=round(abs(sentiment), 3), credibility_weight=credibility, recency_factor=round(recency, 3), velocity_factor=round(velocity, 3), raw_score=round(raw, 3), rationale=f"{event_type} base severity adjusted for sentiment, source credibility, recency and duplicate-volume proxy.")
    return score, explanation
