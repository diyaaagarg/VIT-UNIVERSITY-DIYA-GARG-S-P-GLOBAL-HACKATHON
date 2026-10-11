from datetime import datetime, timedelta, timezone
from src.nlp.preprocessing import Deduplicator, clean_text, detect_language, normalize_timestamp


def test_cleaning_preserves_cashtag_hint() -> None:
    clean, has_url, hints = clean_text("<b>Buy $AAPL</b> now! https://example.test #earnings 😀")
    assert clean == "Buy $AAPL now! earnings"
    assert has_url and hints == ["AAPL"]


def test_dedupe_exact_and_near() -> None:
    dedupe = Deduplicator(90)
    first = dedupe.assign("Oil shock affects markets")
    assert dedupe.assign("Oil shock affects markets") == (first[0], 2)
    assert dedupe.assign("Oil shock affects the markets") == (first[0], 3)


def test_timestamp_and_language() -> None:
    result, flag = normalize_timestamp(datetime.now(timezone.utc) + timedelta(days=1))
    assert flag == "future_timestamp_replaced" and result <= datetime.now(timezone.utc) + timedelta(seconds=1)
    assert detect_language("Este es un boletín financiero sobre los mercados y la inflación.") == "es"
