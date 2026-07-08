"""Audio acquisition and normalization boundaries.

This stage provides only deterministic Mock implementations. They do not read
media files, access URLs, write audio files, check ffmpeg, or run ffmpeg.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models import VideoMetadata


MOCK_AUDIO_PROVIDER_ID = "mock_audio_provider"
MOCK_AUDIO_NORMALIZER_ID = "mock_ffmpeg_normalizer"


@dataclass(frozen=True)
class AudioArtifact:
    """Represents an acquired local audio artifact."""

    path: Path
    provider: str
    format: str
    temporary: bool


@dataclass(frozen=True)
class NormalizedAudio:
    """Represents audio normalized for transcription."""

    path: Path
    provider: str
    format: str
    sample_rate: int
    channels: int
    temporary: bool


class AudioProvider(Protocol):
    """Interface for obtaining audio before transcription."""

    provider_id: str

    def acquire(self, metadata: VideoMetadata) -> AudioArtifact:
        """Return an audio artifact for a metadata record."""


class AudioNormalizer(Protocol):
    """Interface for preparing audio for transcription."""

    provider_id: str

    def normalize(self, artifact: AudioArtifact) -> NormalizedAudio:
        """Return normalized audio for a previously acquired artifact."""


class MockAudioProvider:
    """Pure mock audio provider for fallback orchestration tests."""

    provider_id = MOCK_AUDIO_PROVIDER_ID

    def acquire(self, metadata: VideoMetadata) -> AudioArtifact:
        source_id = metadata.source_id or "mock"
        return AudioArtifact(
            path=Path(f"mock-audio-{source_id}.wav"),
            provider=self.provider_id,
            format="wav",
            temporary=True,
        )


class MockAudioNormalizer:
    """Pure mock normalizer for validating the ffmpeg boundary."""

    provider_id = MOCK_AUDIO_NORMALIZER_ID

    def normalize(self, artifact: AudioArtifact) -> NormalizedAudio:
        return NormalizedAudio(
            path=Path(f"normalized-{artifact.path.name}"),
            provider=self.provider_id,
            format="wav",
            sample_rate=16000,
            channels=1,
            temporary=True,
        )
