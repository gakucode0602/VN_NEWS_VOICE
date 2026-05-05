import re
import typing
from typing import Optional
from datetime import datetime


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""

    # Collapse whitespace and trim.
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""

    # Remove space before punctuation.
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)

    # Remove spaces right after opening quotes and before closing quotes.
    cleaned = re.sub(r"([“‘\"'])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+([”’\"'])", r"\1", cleaned)

    return cleaned


def parse_datetime_flexible(
    date_input: typing.Union[str, int, float, datetime, None],
) -> Optional[datetime]:
    """Parse datetime from various formats."""
    import pytz

    if not date_input:
        return None

    if isinstance(date_input, datetime):
        return date_input

    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

    try:
        # Case 1: Timestamp (seconds or milliseconds)
        if isinstance(date_input, (int, float)):
            timestamp = float(date_input)
            if timestamp > 1e10:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=vietnam_tz)

        # Case 2: String formats
        if isinstance(date_input, str):
            from dateutil import parser

            parsed_date = parser.parse(date_input)
            if parsed_date.tzinfo is None:
                return vietnam_tz.localize(parsed_date)
            else:
                return parsed_date.astimezone(vietnam_tz)
    except Exception:
        import logging

        logging.getLogger(__name__).warning(
            "Error parsing datetime '%s'", date_input, exc_info=True
        )
        return None

    return None


def parse_rss_date(entry) -> Optional[datetime]:
    """Extract and parse the published date from an RSS feed entry."""
    import pytz
    import calendar

    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

    published_date = None
    if hasattr(entry, "published") and entry.published:
        try:
            from dateutil import parser

            published_date = parser.parse(entry.published)
            if published_date.tzinfo is not None:
                published_date = published_date.astimezone(vietnam_tz)
            else:
                published_date = vietnam_tz.localize(published_date)
        except Exception:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                utc_timestamp = calendar.timegm(entry.published_parsed)
                published_date = datetime.fromtimestamp(utc_timestamp, tz=pytz.UTC)
                published_date = published_date.astimezone(vietnam_tz)

    if not published_date:
        published_date = datetime.now(vietnam_tz)

    return published_date
