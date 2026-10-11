"""Deterministic cleaning, language flags, and near-duplicate clustering."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Iterable
from bs4 import BeautifulSoup
from langdetect import DetectorFactory, detect
from rapidfuzz.fuzz import ratio
from src.engine.models import RawDocument

DetectorFactory.seed = 17
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
TAG_RE = re.compile(r"\$([A-Za-z]{1,5})\b")
EMOJI_RE = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)


def clean_text(value: str) -> tuple[str, bool, list[str]]:
    """Remove presentation noise while retaining cashtag ticker hints."""
    has_url = bool(URL_RE.search(value))
    tickers = [item.upper() for item in TAG_RE.findall(value)]
    text = BeautifulSoup(unescape(value), "html.parser").get_text(" ")
    text = URL_RE.sub(" ", text)
    text = re.sub(r"#([\w-]+)", r"\1", text)
    text = EMOJI_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, has_url, tickers


def detect_language(text: str) -> str:
    if len(text.strip()) < 20:
        return "unknown"
    try:
        return detect(text)
    except Exception:
        return "unknown"


def normalize_timestamp(value: datetime, tolerance_minutes: int = 5) -> tuple[datetime, str | None]:
    timestamp = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if timestamp > datetime.now(timezone.utc) + timedelta(minutes=tolerance_minutes):
        return datetime.now(timezone.utc), "future_timestamp_replaced"
    return timestamp, None


class Deduplicator:
    def __init__(self, threshold: int = 92) -> None:
        self.threshold = threshold
        self._clusters: dict[str, tuple[str, int]] = {}
        self._hashes: dict[str, str] = {}

    def assign(self, clean_text: str) -> tuple[str, int]:
        normalized = re.sub(r"[^a-z0-9 ]", "", clean_text.lower())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        if digest in self._hashes:
            cluster = self._hashes[digest]
            representative, count = self._clusters[cluster]
            self._clusters[cluster] = (representative, count + 1)
            return cluster, count + 1
        for cluster, (representative, count) in self._clusters.items():
            if ratio(normalized, representative) >= self.threshold:
                self._clusters[cluster] = (representative, count + 1)
                self._hashes[digest] = cluster
                return cluster, count + 1
        cluster = f"cluster-{len(self._clusters) + 1:04d}"
        self._clusters[cluster] = (normalized, 1)
        self._hashes[digest] = cluster
        return cluster, 1

    @property
    def clusters(self) -> dict[str, tuple[str, int]]: return self._clusters
