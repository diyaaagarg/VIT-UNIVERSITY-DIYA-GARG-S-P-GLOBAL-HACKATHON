"""Build persisted Phase 2 signals from a Phase 1 processed JSONL file."""
from __future__ import annotations
import json
from pathlib import Path
from src.engine.models import ProcessedDocument
from src.engine.persistence import persist_signals
from src.engine.pipeline import RiskEngine
from src.utils.config import ROOT, settings


def main() -> None:
    cfg = settings(); input_path = ROOT / cfg.processed_path
    documents = [ProcessedDocument.model_validate_json(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line]
    engine = RiskEngine(); signals = [signal for document in documents for signal in engine.analyze(document)]
    persist_signals(signals, ROOT / "data/processed/signals.jsonl", ROOT / cfg.database_path)
    print(f"signals_written={len(signals)} high_impact={sum(item.impact_score >= 7 for item in signals)}")


if __name__ == "__main__": main()
