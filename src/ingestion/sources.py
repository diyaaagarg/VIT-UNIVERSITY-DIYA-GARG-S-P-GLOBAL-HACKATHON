"""Pluggable document sources with defensive network behavior."""
from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncIterator

import feedparser
import httpx

from src.engine.models import RawDocument, SourceType
from src.utils.config import ROOT, sources, universe

log = logging.getLogger(__name__)
SPEED_SECONDS = {"1": 1.0, "1x": 1.0, "10": 0.1, "10x": 0.1, "60": 1 / 60, "60x": 1 / 60, "instant": 0.0}


class BaseSource(ABC):
    name: str
    source_type: SourceType
    credibility_weight: float

    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    async def fetch(self) -> list[RawDocument]: ...

    async def stream(self) -> AsyncIterator[RawDocument]:
        for document in await self.fetch():
            yield document


class RssSource(BaseSource):
    name = "rss"
    source_type = SourceType.NEWS
    credibility_weight = 0.8

    async def is_available(self) -> bool:
        return bool(sources().get("rss", {}).get("enabled", True))

    async def fetch(self) -> list[RawDocument]:
        cfg = sources().get("rss", {})
        records: list[RawDocument] = []
        for feed in cfg.get("feeds", []):
            content = await self._download(feed["url"], cfg.get("timeout_seconds", 8), cfg.get("retries", 2))
            if not content:
                continue
            parsed = feedparser.parse(content)
            for entry in parsed.entries[:30]:
                stamp = entry.get("published") or entry.get("updated")
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if entry.get("published_parsed") else datetime.now(timezone.utc)
                except (TypeError, ValueError):
                    published = datetime.now(timezone.utc)
                records.append(RawDocument(source=feed["name"], source_type=SourceType.NEWS, title=entry.get("title", ""), text=entry.get("summary", entry.get("title", "")), url=entry.get("link"), author=entry.get("author"), published_at=published, raw_metadata={"feed_url": feed["url"], "raw_timestamp": stamp}))
        return records

    async def _download(self, url: str, timeout: int, retries: int) -> str | None:
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers={"User-Agent": "RiskEngineDemo/1.0"})
                    response.raise_for_status()
                    return response.text
            except (httpx.HTTPError, ValueError) as error:
                log.warning("rss_fetch_failed url=%s attempt=%s error=%s", url, attempt + 1, error)
                if isinstance(error, httpx.HTTPStatusError) and 400 <= error.response.status_code < 500 and error.response.status_code not in {408, 429}:
                    break
                if attempt < retries:
                    await asyncio.sleep(0.25 * (2**attempt))
        return None


class FinnhubSource(BaseSource):
    name = "finnhub"
    source_type = SourceType.NEWS
    credibility_weight = 0.85

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def is_available(self) -> bool:
        return bool(self.api_key and sources().get("finnhub", {}).get("enabled", True))

    async def fetch(self) -> list[RawDocument]:
        if not await self.is_available():
            return []
        config = sources()["finnhub"]
        limit = config.get("max_tickers_per_run", 3)
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=2)).date().isoformat()
        results: list[RawDocument] = []
        async with httpx.AsyncClient(timeout=10) as client:
            for ticker in list(universe()["tickers"])[:limit]:
                try:
                    response = await client.get("https://finnhub.io/api/v1/company-news", params={"symbol": ticker, "from": start, "to": now.date().isoformat(), "token": self.api_key})
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, list):
                        raise ValueError("unexpected Finnhub response shape")
                    for item in payload[:10]:
                        results.append(RawDocument(source="finnhub", source_type=SourceType.NEWS, title=str(item.get("headline", "")), text=str(item.get("summary", item.get("headline", ""))), url=item.get("url"), published_at=datetime.fromtimestamp(item.get("datetime", now.timestamp()), tz=timezone.utc), tickers=[ticker], raw_metadata={"category": item.get("category"), "id": item.get("id")}))
                except (httpx.HTTPError, ValueError, TypeError) as error:
                    log.warning("finnhub_fetch_failed ticker=%s error=%s", ticker, error)
                await asyncio.sleep(1 / max(config.get("requests_per_second", 1), 1))
        return results


class RedditSource(BaseSource):
    """Deliberately disabled unless a future credentialed adapter is configured."""
    name = "reddit"
    source_type = SourceType.SOCIAL
    credibility_weight = 0.45
    async def is_available(self) -> bool: return False
    async def fetch(self) -> list[RawDocument]: return []


class ReplaySource(BaseSource):
    name = "replay"
    source_type = SourceType.NEWS
    credibility_weight = 0.7

    def __init__(self, paths: list[Path] | None = None, speed: str = "instant") -> None:
        self.paths = paths or [ROOT / "data/replay/crisis_scenario.jsonl"]
        self.speed = speed
        self._paused = False
        self._cursor = 0

    async def is_available(self) -> bool:
        return any(path.exists() for path in self.paths)

    async def fetch(self) -> list[RawDocument]:
        documents: list[RawDocument] = []
        for path in self.paths:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    documents.append(RawDocument.model_validate_json(line))
        return sorted(documents, key=lambda item: item.published_at)

    def pause(self, paused: bool = True) -> None: self._paused = paused
    def seek(self, index: int) -> None: self._cursor = max(0, index)

    async def stream(self) -> AsyncIterator[RawDocument]:
        documents = await self.fetch()
        delay = SPEED_SECONDS.get(str(self.speed).lower(), 0.0)
        for index in range(self._cursor, len(documents)):
            while self._paused:
                await asyncio.sleep(0.05)
            self._cursor = index + 1
            yield documents[index]
            if delay:
                await asyncio.sleep(delay)
