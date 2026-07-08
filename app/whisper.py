"""Local Whisper backend boundary.

This stage provides only a deterministic Mock backend. It does not read media
files, call ffmpeg, run Whisper, or access the network.
"""

from __future__ import annotations

from typing import Protocol

from app.models import TranscriptResult, TranscriptSegment, VideoMetadata


LOCAL_WHISPER_MOCK_PROVIDER_ID = "local_whisper_mock"


class WhisperBackend(Protocol):
    """Interface for local transcription backends."""

    provider_id: str

    def transcribe(self, metadata: VideoMetadata) -> TranscriptResult:
        """Return transcript data for a video metadata record."""


class MockWhisperBackend:
    """Deterministic mock backend for validating fallback orchestration."""

    provider_id = LOCAL_WHISPER_MOCK_PROVIDER_ID

    def transcribe(self, metadata: VideoMetadata) -> TranscriptResult:
        title = metadata.title or "Untitled video"
        platform = metadata.platform or "unknown"
        return TranscriptResult(
            segments=[
                TranscriptSegment(
                    start="00:00:00",
                    end="00:00:15",
                    text=f"Mock Whisper fallback transcript for {title}.",
                ),
                TranscriptSegment(
                    start="00:00:15",
                    end="00:00:35",
                    text=(
                        "This mock local transcription validates fallback "
                        f"orchestration for {platform} without reading media."
                    ),
                ),
                TranscriptSegment(
                    start="00:00:35",
                    end="00:00:55",
                    text=(
                        "Real audio acquisition, ffmpeg processing, and Whisper "
                        "execution remain disabled."
                    ),
                ),
            ],
            provider=self.provider_id,
            attempted_providers=[self.provider_id],
        )
