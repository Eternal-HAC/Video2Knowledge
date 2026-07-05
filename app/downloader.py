"""Mock metadata resolver.

This module does not download media in Stage 1.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models import VideoMetadata, VideoSource


def get_mock_metadata(source_url: str, platform: str | None = None) -> VideoMetadata:
    """Return deterministic Mock metadata for a source URL."""

    parsed = urlparse(source_url)
    platform_name = platform or parsed.netloc or "local"

    return VideoMetadata(
        title="Mock Video Knowledge Note",
        platform=platform_name,
        source_url=source_url,
        author="Mock Author",
        published_at="2026-07-05",
        duration="00:05:00",
        language="zh-CN",
        tags=["video2knowledge", "mock", "pkm"],
        status="mock",
    )


def get_metadata_for_source(source: VideoSource) -> VideoMetadata:
    """Resolve metadata through the current Mock provider boundary."""

    return get_mock_metadata(source.raw_input, platform=source.platform)
