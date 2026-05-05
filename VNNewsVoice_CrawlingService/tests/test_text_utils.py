from datetime import datetime
from types import SimpleNamespace

from app.services.text_utils import (
    normalize_text,
    parse_datetime_flexible,
    parse_rss_date,
)


def test_normalize_text_cleans_whitespace_and_punctuation() -> None:
    raw = '  Xin   chao   ,   "  ban  "   !  '
    assert normalize_text(raw) == 'Xin chao,"ban"!'


def test_normalize_text_returns_empty_for_missing_input() -> None:
    assert normalize_text(None) == ""
    assert normalize_text("   ") == ""


def test_parse_datetime_flexible_handles_millisecond_timestamp() -> None:
    parsed = parse_datetime_flexible(1710057600000)
    assert parsed is not None
    assert parsed.utcoffset().total_seconds() == 7 * 3600


def test_parse_datetime_flexible_returns_none_for_invalid_string() -> None:
    assert parse_datetime_flexible("not-a-date") is None


def test_parse_rss_date_uses_published_field_when_present() -> None:
    entry = SimpleNamespace(published="2026-03-18T10:00:00Z")
    parsed = parse_rss_date(entry)

    assert parsed.year == 2026
    assert parsed.utcoffset().total_seconds() == 7 * 3600


def test_parse_rss_date_falls_back_to_now_when_missing_fields() -> None:
    entry = SimpleNamespace()
    parsed = parse_rss_date(entry)

    assert isinstance(parsed, datetime)
    assert parsed.utcoffset().total_seconds() == 7 * 3600
