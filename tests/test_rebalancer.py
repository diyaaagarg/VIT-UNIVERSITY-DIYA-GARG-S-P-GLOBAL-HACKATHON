from datetime import datetime, timezone
from src.engine.models import ImpactExplanation, Signal, SourceType
from src.modules.rebalancer.core import aggregate_sentiment, constrained_weights


def signal(ticker: str, score: float) -> Signal:
    return Signal(document_id="d", source="x", source_type=SourceType.NEWS, entity=ticker, text="x", published_at=datetime.now(timezone.utc), sentiment_score=score, sentiment_label="positive", event_type="Other", impact_score=3, confidence=0.9, explanation=ImpactExplanation(formula="x", base_severity=3, sentiment_magnitude=0, credibility_weight=.8, recency_factor=1, velocity_factor=1, raw_score=3, rationale="x"), is_synthetic=True)


def test_sentiment_aggregation_and_constraints() -> None:
    result = aggregate_sentiment([signal("AAPL", 0.8)], datetime.now(timezone.utc), 8, 0.5)
    assert result["AAPL"] > 0.7
    base = {"AAPL": .5, "MSFT": .5}
    weights, turnover = constrained_weights(base, {"AAPL": 1, "MSFT": -1}, 1, .2, .8, .1)
    assert round(sum(weights.values()), 8) == 1 and all(.2 <= value <= .8 for value in weights.values()) and turnover <= .1
