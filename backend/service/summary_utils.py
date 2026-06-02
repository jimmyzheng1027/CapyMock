from __future__ import annotations

FALLBACK_SUMMARY: dict = {
    "overview": "面试已完成",
    "highlights": [],
    "suggestions": ["继续练习以提升面试表现"],
    "_is_fallback": True,
}


def is_fallback_summary(summary: dict | None) -> bool:
    """Return True when the stored summary is the generic failure placeholder."""
    if not summary:
        return False
    # New flag-based detection (preferred)
    if summary.get("_is_fallback") is True:
        return True
    # Backward compat: detect old-format fallback by content
    return (
        summary.get("overview") == FALLBACK_SUMMARY["overview"]
        and summary.get("highlights") == FALLBACK_SUMMARY["highlights"]
        and summary.get("suggestions") == FALLBACK_SUMMARY["suggestions"]
    )
