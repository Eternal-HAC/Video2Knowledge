"""Platform source detection and adapter boundary.

Stage 2 starts by defining the adapter boundary while still using Mock data.
No real platform API or downloader is called here.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models import PlatformCapabilities, VideoSource

_SUPPORTED_HOST_DOMAINS = {
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "bilibili.com": "bilibili",
    "tiktok.com": "tiktok",
    "vimeo.com": "vimeo",
    "coursera.org": "coursera",
    "udemy.com": "udemy",
}
_EXACT_ONLY_HOST_DOMAINS = frozenset({"youtu.be"})
_RESERVED_PLATFORM_LABELS = frozenset(
    {
        "youtube",
        "bilibili",
        "tiktok",
        "vimeo",
        "coursera",
        "udemy",
        "local",
        "unknown",
    }
)


def resolve_video_source(raw_input: str) -> VideoSource:
    """Classify a user input as a URL or local path and infer a platform label."""

    parsed = urlparse(raw_input)
    if parsed.scheme in {"http", "https"}:
        return VideoSource(
            raw_input=raw_input,
            source_type="url",
            platform=_platform_from_url(parsed),
        )

    return VideoSource(
        raw_input=raw_input,
        source_type="local_file",
        platform="local",
    )


def get_platform_capabilities(platform: str) -> PlatformCapabilities:
    """Return the known capabilities for a platform label."""

    normalized = platform.lower()
    if normalized == "youtube":
        return PlatformCapabilities(
            supports_metadata=True,
            supports_transcript=True,
            supports_local_file=False,
            supports_cookies=True,
            supports_auth=False,
            metadata_providers=["mock", "yt-dlp"],
            transcript_providers=["mock", "official-subtitles", "real-fallback"],
        )
    if normalized in {"bilibili", "tiktok", "vimeo", "coursera", "udemy"}:
        return PlatformCapabilities(
            supports_metadata=True,
            supports_transcript=True,
            supports_local_file=False,
            supports_cookies=True,
            supports_auth=True,
            metadata_providers=["mock"],
            transcript_providers=["mock"],
        )
    if normalized == "local":
        return PlatformCapabilities(
            supports_metadata=True,
            supports_transcript=False,
            supports_local_file=True,
            supports_cookies=False,
            supports_auth=False,
            metadata_providers=["mock"],
            transcript_providers=["mock"],
        )
    return PlatformCapabilities(
        supports_metadata=False,
        supports_transcript=False,
        supports_local_file=False,
        supports_cookies=False,
        supports_auth=False,
        metadata_providers=["mock"],
        transcript_providers=["mock"],
    )


def _platform_from_url(parsed) -> str:
    """Map a parsed URL to a platform label using exact hostname matching."""

    try:
        host = parsed.hostname
    except ValueError:
        host = None
    normalized = host.lower().rstrip(".") if host else ""
    if parsed.username is not None or parsed.password is not None:
        return _safe_platform_label(normalized)
    if not normalized:
        return "unknown"
    for domain, platform in _SUPPORTED_HOST_DOMAINS.items():
        if normalized == domain:
            return platform
        if (
            domain not in _EXACT_ONLY_HOST_DOMAINS
            and normalized.endswith("." + domain)
        ):
            return platform
    return _safe_platform_label(normalized)


def _safe_platform_label(normalized_host: str) -> str:
    """Return a label that never collides with a reserved platform id."""

    if not normalized_host or normalized_host in _RESERVED_PLATFORM_LABELS:
        return "unknown"
    return normalized_host
