from datetime import datetime, timezone
from src.engine.models import ProcessedDocument, SourceType
from src.engine.pipeline import RiskEngine
from src.engine.scoring import impact_score


def document(text: str, source_type: SourceType = SourceType.NEWS, duplicate_count: int = 1) -> ProcessedDocument:
    return ProcessedDocument(source="test", source_type=source_type, text=text, clean_text=text, published_at=datetime.now(timezone.utc), dedupe_cluster_id="test", duplicate_count=duplicate_count)


def test_engine_outputs_required_fields() -> None:
    signal = RiskEngine().analyze(document("Synthetic breaking alert: Hormuz blockade causes oil shock and market risk."))[0]
    assert signal.event_type == "Geopolitical"
    assert -1 <= signal.sentiment_score <= 1 and 1 <= signal.impact_score <= 10
    assert signal.explanation.base_severity == 8.0 and signal.confidence > 0


def test_impact_is_transparent_and_volume_sensitive() -> None:
    now = datetime.now(timezone.utc)
    low, explanation = impact_score("Credit Event", -0.8, 0.8, now, 1)
    high, _ = impact_score("Credit Event", -0.8, 0.8, now, 4)
    assert high > low and explanation.velocity_factor == 1.0
