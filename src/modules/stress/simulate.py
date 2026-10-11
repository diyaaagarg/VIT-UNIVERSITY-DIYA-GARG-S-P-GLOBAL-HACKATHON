"""End-to-end breaking-news demonstration: text to signal to conditional stress run."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from src.engine.models import ProcessedDocument, RawDocument, SourceType
from src.engine.pipeline import RiskEngine
from src.modules.stress.engine import run_stress
from src.modules.stress.portfolio import load_or_create
from src.nlp.entity_linking import EntityLinker
from src.nlp.preprocessing import Deduplicator, clean_text, detect_language
from src.utils.config import ROOT, read_yaml


def simulate(headline: str) -> dict:
    raw = RawDocument(source="breaking_news_simulator", source_type=SourceType.NEWS, title=headline, text=headline, published_at=datetime.now(timezone.utc), is_synthetic=True)
    clean, has_url, hints = clean_text(headline); entities, tags = EntityLinker().link(clean, hints)
    payload = raw.model_dump()
    payload.update(clean_text=clean, language=detect_language(clean), entities=entities, macro_tags=tags, dedupe_cluster_id="simulator-0001", has_url=has_url)
    document = ProcessedDocument(**payload)
    signals = RiskEngine().analyze(document); threshold = read_yaml(ROOT / "config/stress.yaml")["auto_trigger_impact"]
    stresses = [run_stress(load_or_create(), signal.event_type, signal.impact_score, signal.id) for signal in signals if signal.impact_score >= threshold]
    return {"document": document.model_dump(mode="json"), "signals": [signal.model_dump(mode="json") for signal in signals], "auto_triggered": bool(stresses), "stress_runs": stresses}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("headline", nargs="?", default="Breaking simulation: Strait of Hormuz transit interruption triggers oil shock and broad market risk.")
    result = simulate(parser.parse_args().headline); output = ROOT / "reports/breaking_news_simulation.json"; output.write_text(json.dumps(result, indent=2)); print(f"simulation_report={output} auto_triggered={result['auto_triggered']}")
    for signal in result["signals"]: print(f"entity={signal['entity']} event={signal['event_type']} sentiment={signal['sentiment_score']} impact={signal['impact_score']}")


if __name__ == "__main__": main()
