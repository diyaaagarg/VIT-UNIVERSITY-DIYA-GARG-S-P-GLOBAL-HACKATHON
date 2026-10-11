"""Mode selection and resilient replay fallback."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import AsyncIterator
from src.engine.models import RawDocument
from src.ingestion.sources import BaseSource, FinnhubSource, ReplaySource, RssSource
from src.utils.config import ROOT, settings

log = logging.getLogger(__name__)


class IngestionManager:
    def __init__(self, mode: str | None = None, replay_paths: list[Path] | None = None, speed: str = "instant", live_sources: list[BaseSource] | None = None) -> None:
        self.mode = (mode or settings().mode).lower()
        self.replay = ReplaySource(replay_paths or [ROOT / "data/replay/crisis_scenario.jsonl"], speed)
        self.live_sources = live_sources or [RssSource(), FinnhubSource(settings().finnhub_api_key)]

    async def stream(self) -> AsyncIterator[RawDocument]:
        if self.mode == "replay":
            async for doc in self.replay.stream(): yield doc
            return
        live: list[RawDocument] = []
        for source in self.live_sources:
            try:
                if await source.is_available():
                    live.extend(await source.fetch())
            except Exception as error:  # source implementations must never break the demo
                log.warning("live_source_failed source=%s error=%s", source.name, error)
        if not live:
            log.warning("live_sources_empty_falling_back_to_replay")
            async for doc in self.replay.stream(): yield doc
            return
        for doc in sorted(live, key=lambda item: item.published_at): yield doc
