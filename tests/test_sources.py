import asyncio
from datetime import datetime, timezone
from pathlib import Path
from src.engine.models import RawDocument, SourceType
from src.ingestion.manager import IngestionManager
from src.ingestion.sources import BaseSource, ReplaySource


def test_replay_ordering_and_merge(tmp_path: Path) -> None:
    late = RawDocument(source="a", source_type=SourceType.NEWS, text="late", published_at="2026-01-01T02:00:00Z")
    early = RawDocument(source="b", source_type=SourceType.SOCIAL, text="early", published_at="2026-01-01T01:00:00Z")
    (tmp_path / "one.jsonl").write_text(late.model_dump_json() + "\n")
    (tmp_path / "two.jsonl").write_text(early.model_dump_json() + "\n")
    async def collect(): return [item.text async for item in ReplaySource([tmp_path / "one.jsonl", tmp_path / "two.jsonl"], "instant").stream()]
    assert asyncio.run(collect()) == ["early", "late"]


class EmptySource(BaseSource):
    name = "empty"; source_type = SourceType.NEWS; credibility_weight = 0.1
    async def is_available(self) -> bool: return True
    async def fetch(self): return []


def test_live_empty_falls_back_to_replay() -> None:
    async def collect():
        manager = IngestionManager("live", speed="instant", live_sources=[EmptySource()])
        return [item async for item in manager.stream()]
    docs = asyncio.run(collect())
    assert docs and all(item.is_synthetic for item in docs)
