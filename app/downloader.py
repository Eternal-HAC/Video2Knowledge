"""Mock metadata resolver.

This module does not download media in Stage 1.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models import VideoMetadata


def get_mock_metadata(source_url: str) -> VideoMetadata:
    """Return deterministic Mock metadata for a source URL."""

    parsed = urlparse(source_url)
    platform = parsed.netloc or "local"

    return VideoMetadata(
        title="Mock Video Knowledge Note",
        platform=platform,
        source_url=source_url,
        author="Mock Author",
        published_at="2026-07-05",
        duration="00:05:00",
        language="zh-CN",
        tags=["video2knowledge", "mock", "pkm"],
        status="mock",
    )

