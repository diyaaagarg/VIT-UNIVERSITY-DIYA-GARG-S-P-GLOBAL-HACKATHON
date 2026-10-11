"""Phase 1 pipeline CLI."""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter
from pathlib import Path
from src.engine.models import ProcessedDocument
from src.engine.persistence import persist_documents
from src.ingestion.manager import IngestionManager
from src.nlp.entity_linking import EntityLinker
from src.nlp.preprocessing import Deduplicator, clean_text, detect_language, normalize_timestamp
from src.utils.config import ROOT, settings
from src.utils.logging import configure_logging


async def run(mode: str, speed: str) -> list[ProcessedDocument]:
    cfg = settings(); dedupe = Deduplicator(cfg.near_duplicate_threshold); linker = EntityLinker(); output = []
    async for raw in IngestionManager(mode=mode, speed=speed).stream():
        clean, has_url, hints = clean_text(f"{raw.title} {raw.text}")
        published, flag = normalize_timestamp(raw.published_at, cfg.future_timestamp_tolerance_minutes)
        language = raw.language or detect_language(clean)
        entities, tags = linker.link(clean, raw.tickers + hints)
        cluster, count = dedupe.assign(clean)
        payload = raw.model_dump()
        payload.update(published_at=published, language=language, clean_text=clean, has_url=has_url, entities=entities, macro_tags=tags, dedupe_cluster_id=cluster, duplicate_count=count, timestamp_flag=flag)
        output.append(ProcessedDocument(**payload))
    persist_documents(output, ROOT / cfg.processed_path, ROOT / cfg.database_path)
    summary(output, dedupe)
    return output


def summary(documents: list[ProcessedDocument], dedupe: Deduplicator) -> None:
    ticker_counts = Counter(entity.ticker for doc in documents for entity in doc.entities)
    tags = Counter(tag for doc in documents for tag in doc.macro_tags)
    languages = Counter(doc.language for doc in documents)
    confidence = [entity.confidence for doc in documents for entity in doc.entities]
    print(f"documents_in={len(documents)} duplicates_removed={len(documents)-len(dedupe.clusters)}")
    print(f"languages={dict(languages)}")
    print(f"per_ticker={dict(sorted(ticker_counts.items()))}")
    print(f"macro_tags={dict(tags)}")
    print(f"link_confidence={{'count': {len(confidence)}, 'mean': {round(sum(confidence)/len(confidence), 3) if confidence else 0}}}")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=["replay", "live"], default="replay"); parser.add_argument("--speed", default="instant")
    args = parser.parse_args(); configure_logging(); asyncio.run(run(args.mode, args.speed))

if __name__ == "__main__": main()
