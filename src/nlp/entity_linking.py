"""Conservative dictionary-first company and macro linker."""
from __future__ import annotations
import re
import logging
from typing import Any
from rapidfuzz import process
from src.engine.models import Entity
from src.utils.config import universe

FINANCE_CONTEXT = re.compile(r"\b(stock|shares|investor|earnings|revenue|market|company|inc\.?|corp\.?|bank|fund|trading|quarter|guidance)\b", re.I)
log = logging.getLogger(__name__)


class EntityLinker:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or universe()
        self.tickers = self.config["tickers"]
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
            log.warning("spaCy model en_core_web_sm unavailable; entity linker is using aliases and macro rules only")

    def link(self, text: str, ticker_hints: list[str] | None = None) -> tuple[list[Entity], list[str]]:
        found: dict[str, Entity] = {}
        lower = text.lower()
        for ticker in ticker_hints or []:
            ticker = ticker.upper().lstrip("$")
            if ticker in self.tickers:
                found[ticker] = self._entity(ticker, "cashtag", 1.0)
        for ticker, details in self.tickers.items():
            for alias in details["aliases"] + [details["name"]]:
                if not re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.I):
                    continue
                if self._ambiguous(alias, lower) and not FINANCE_CONTEXT.search(text):
                    continue
                confidence = 0.94 if alias.lower() == details["name"].lower() else 0.88
                found.setdefault(ticker, self._entity(ticker, "alias", confidence))
        if self.nlp:
            aliases = {alias.lower(): ticker for ticker, d in self.tickers.items() for alias in d["aliases"] + [d["name"]]}
            for ent in self.nlp(text).ents:
                if ent.label_ != "ORG": continue
                candidate, score, _ = process.extractOne(ent.text.lower(), aliases.keys(), score_cutoff=90) or (None, 0, None)
                if candidate:
                    found.setdefault(aliases[candidate], self._entity(aliases[candidate], "spacy_fuzzy", round(score / 100 * 0.75, 2)))
        tags = [tag for tag, phrases in self.config.get("macro_tags", {}).items() if any(phrase.lower() in lower for phrase in phrases)]
        for tag in tags:
            for ticker in self.config.get("macro_sector_mapping", {}).get(tag, []):
                found.setdefault(ticker, self._entity(ticker, "macro_sector", 0.45))
        if tags and not found:
            found["MARKET"] = Entity(ticker="MARKET", name="Broad Market", match_type="macro_fallback", confidence=0.55)
        return list(found.values()), tags

    def _entity(self, ticker: str, match_type: str, confidence: float) -> Entity:
        detail = self.tickers[ticker]
        return Entity(ticker=ticker, name=detail["name"], match_type=match_type, confidence=confidence)

    @staticmethod
    def _ambiguous(alias: str, lower: str) -> bool:
        if alias.lower() == "apple" and any(word in lower for word in ("fruit", "orchard", "recipe")): return True
        if alias.lower() == "amazon" and any(word in lower for word in ("rainforest", "river", "jungle")): return True
        if alias.lower() == "meta" and "metaphor" in lower: return True
        return False
