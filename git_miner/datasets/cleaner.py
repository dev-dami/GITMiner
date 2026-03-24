"""Data cleaning utilities for extracted GitHub repository records."""

import re
import unicodedata
from typing import Any


def _clean_text(value: str | None) -> str | None:
    """Normalize a text field: strip whitespace, collapse internal whitespace,
    and remove non-printable control characters.

    Args:
        value: Raw text value, may be None.

    Returns:
        Cleaned string, or None if the result would be empty.
    """
    if value is None:
        return None
    # Normalize unicode to NFC form
    value = unicodedata.normalize("NFC", value)
    # Replace all control characters (except tabs/spaces) with a space
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", value)
    # Collapse any run of whitespace (including newlines) to a single space
    value = re.sub(r"\s+", " ", value)
    value = value.strip()
    return value if value else None


def _clean_topics(topics: str | None) -> str | None:
    """Clean and normalize a comma-separated topics string.

    Each topic is stripped of whitespace and lowercased.  Empty topics are
    removed.  Returns None when no valid topics remain.

    Args:
        topics: Comma-separated topics string, may be None.

    Returns:
        Cleaned comma-separated topics string, or None.
    """
    if not topics:
        return None
    cleaned = [t.strip().lower() for t in topics.split(",") if t.strip()]
    return ",".join(cleaned) if cleaned else None


def _clamp_non_negative(value: int | None) -> int | None:
    """Ensure an integer field is non-negative.

    Args:
        value: Integer value, may be None.

    Returns:
        max(0, value) or None.
    """
    if value is None:
        return None
    return max(0, value)


def clean_repository_record(record: dict[str, Any]) -> dict[str, Any]:
    """Clean a single repository metadata record.

    Applies the following transformations:
    - Strips and normalises text fields (name, description, owner, etc.)
    - Cleans and lowercases topics
    - Ensures numeric counters (stars, forks, open_issues, size_kb) are non-negative
    - Strips whitespace from license / license_key

    Args:
        record: Raw repository metadata dictionary.

    Returns:
        Cleaned copy of the record.
    """
    cleaned = dict(record)

    text_fields = (
        "name",
        "owner",
        "full_name",
        "description",
        "primary_language",
        "license",
        "license_key",
        "url",
        "api_url",
    )
    for field in text_fields:
        if field in cleaned:
            cleaned[field] = _clean_text(cleaned[field])

    if "topics" in cleaned:
        cleaned["topics"] = _clean_topics(cleaned["topics"])

    for counter in ("stars", "forks", "open_issues", "size_kb"):
        if counter in cleaned:
            cleaned[counter] = _clamp_non_negative(cleaned[counter])

    return cleaned


def deduplicate_records(
    records: list[dict[str, Any]], key: str = "repository_id"
) -> list[dict[str, Any]]:
    """Remove duplicate records, keeping the first occurrence.

    Args:
        records: List of record dictionaries.
        key: Field name used as the uniqueness key.  Defaults to
             ``"repository_id"``.

    Returns:
        De-duplicated list preserving original order.
    """
    seen: set[Any] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        record_key = record.get(key)
        if record_key not in seen:
            seen.add(record_key)
            result.append(record)
    return result
