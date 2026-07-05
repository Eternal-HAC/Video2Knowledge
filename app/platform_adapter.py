"""Platform source detection and adapter boundary.

Stage 2 starts by defining the adapter boundary while still using Mock data.
No real platform API or downloader is called here.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.models import VideoSource


def resolve_video_source(raw_input: str) -> VideoSource:
    """Classify a user input as a URL or local path and infer a platform label."""

    parsed = urlparse(raw_input)
    if parsed.scheme in {"http", "https"}:
        return VideoSource(
            raw_input=raw_input,
            source_type="url",
            platform=_platform_from_host(parsed.netloc),
        )

    return VideoSource(
        raw_input=raw_input,
        source_type="local_file",
        platform="local",
    )


def _platform_from_host(host: str) -> str:
    normalized = host.lower()
    if "youtube.com" in normalized or "youtu.be" in normalized:
        return "youtube"
    if "bilibili.com" in normalized:
        return "bilibili"
    if "tiktok.com" in normalized:
        return "tiktok"
    if "vimeo.com" in normalized:
        return "vimeo"
    if "coursera.org" in normalized:
        return "coursera"
    if "udemy.com" in normalized:
        return "udemy"
    if normalized:
        return normalized
    return Path(host).name or "unknown"

