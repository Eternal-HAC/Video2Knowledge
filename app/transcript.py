"""Transcript provider boundary.

The default provider is Mock. Real subtitle and Whisper providers are explicit
placeholders until external dependencies are introduced.
"""

from __future__ import annotations

from typing import Protocol

from app.errors import ProviderNotImplementedError
from app.models import TranscriptResult, TranscriptSegment, VideoMetadata


TRANSCRIPT_PROVIDER_ORDER = [
    "official_subtitles",
    "transcript_api",
    "whisper",
]


class TranscriptProvider(Protocol):
    """Interface for acquiring transcript segments."""

    name: str

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        """Acquire transcript data for a video."""


class MockTranscriptProvider:
    name = "mock"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        return acquire_transcript_mock(metadata)


class RealFallbackTranscriptProvider:
    name = "real-fallback"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        raise ProviderNotImplementedError(
            "Real transcript fallback is not implemented yet. "
            "Future order: official subtitles, transcript API, Whisper."
        )


def get_mock_transcript(metadata: VideoMetadata) -> list[TranscriptSegment]:
    """Return deterministic transcript segments for Mock processing."""

    return [
        TranscriptSegment("00:00:00", "00:00:20", f"这是来自 {metadata.platform} 的 Mock 视频内容。"),
        TranscriptSegment("00:00:20", "00:00:45", "Video2Knowledge 会把视频信息转成结构化 Markdown。"),
        TranscriptSegment("00:00:45", "00:01:10", "当前阶段只验证本地流水线，不调用真实 API。"),
    ]


def acquire_transcript_mock(metadata: VideoMetadata) -> TranscriptResult:
    """Return Mock transcript data while preserving the future fallback order."""

    return TranscriptResult(
        segments=get_mock_transcript(metadata),
        provider="mock_official_subtitles",
        attempted_providers=TRANSCRIPT_PROVIDER_ORDER,
    )


def acquire_transcript_with_provider(
    metadata: VideoMetadata,
    provider_name: str = "mock",
) -> TranscriptResult:
    """Acquire transcript data with an explicit provider name."""

    provider = build_transcript_provider(provider_name)
    return provider.acquire(metadata)


def build_transcript_provider(provider_name: str) -> TranscriptProvider:
    """Create a transcript provider by name."""

    normalized = provider_name.lower()
    if normalized == "mock":
        return MockTranscriptProvider()
    if normalized == "real-fallback":
        return RealFallbackTranscriptProvider()
    raise ValueError(f"Unknown transcript provider: {provider_name}")
