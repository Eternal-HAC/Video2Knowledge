"""Audio acquisition and normalization boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Protocol

from app.errors import (
    AudioAcquisitionError,
    AudioProcessingError,
    FfmpegNotFoundError,
)
from app.models import VideoMetadata


MOCK_AUDIO_PROVIDER_ID = "mock_audio_provider"
LOCAL_FILE_AUDIO_PROVIDER_ID = "local_file_audio"
MOCK_AUDIO_NORMALIZER_ID = "mock_ffmpeg_normalizer"
FFMPEG_AUDIO_NORMALIZER_ID = "ffmpeg_audio_normalizer"


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


class LocalFileAudioProvider:
    """Expose a user-owned local audio file without copying or modifying it."""

    provider_id = LOCAL_FILE_AUDIO_PROVIDER_ID

    def acquire(self, metadata: VideoMetadata) -> AudioArtifact:
        if metadata.platform.lower() != "local" or not metadata.source_url.strip():
            raise AudioAcquisitionError("local audio input required")

        input_path = Path(metadata.source_url)
        if not input_path.exists():
            raise AudioAcquisitionError("local audio input file not found")
        if not input_path.is_file():
            raise AudioAcquisitionError("local audio input must be a file")

        return AudioArtifact(
            path=input_path,
            provider=self.provider_id,
            format=input_path.suffix.lower().lstrip(".") or "unknown",
            temporary=False,
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


class FfmpegAudioNormalizer:
    """Normalize a local audio file to 16 kHz mono WAV through ffmpeg."""

    provider_id = FFMPEG_AUDIO_NORMALIZER_ID

    def __init__(
        self,
        output_dir: Path | str | None = None,
        ffmpeg_path: str | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.ffmpeg_path = ffmpeg_path
        self.timeout_seconds = timeout_seconds

    def normalize(self, artifact: AudioArtifact) -> NormalizedAudio:
        input_path = artifact.path
        if not input_path.exists():
            raise AudioProcessingError("audio input file not found")

        ffmpeg = self._resolve_ffmpeg()
        output_dir = self.output_dir or Path(tempfile.gettempdir())
        output_path = output_dir / f"{input_path.stem}-16k-mono.wav"
        if output_path.exists():
            raise AudioProcessingError("ffmpeg normalized output already exists")

        command = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-acodec",
            "pcm_s16le",
            "-f",
            "wav",
            str(output_path),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise AudioProcessingError(
                "ffmpeg audio normalization timed out"
            ) from error

        if result.returncode != 0:
            raise AudioProcessingError("ffmpeg audio normalization failed")
        if not output_path.exists():
            raise AudioProcessingError("ffmpeg normalized output missing")

        return NormalizedAudio(
            path=output_path,
            provider=self.provider_id,
            format="wav",
            sample_rate=16000,
            channels=1,
            temporary=True,
        )

    def _resolve_ffmpeg(self) -> str:
        if self.ffmpeg_path:
            return self.ffmpeg_path
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise FfmpegNotFoundError("ffmpeg not found")
        return ffmpeg
