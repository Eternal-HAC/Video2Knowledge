"""Local Whisper backend boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypeVar

from app.audio import NormalizedAudio
from app.errors import LocalTranscriptionError
from app.models import TranscriptResult, TranscriptSegment, VideoMetadata


LOCAL_WHISPER_MOCK_PROVIDER_ID = "local_whisper_mock"
FASTER_WHISPER_PROVIDER_ID = "faster_whisper"
WhisperInput = TypeVar("WhisperInput", contravariant=True)


class WhisperBackend(Protocol[WhisperInput]):
    """Interface for local transcription backends."""

    provider_id: str

    def transcribe(self, source: WhisperInput) -> TranscriptResult:
        """Return transcript data for a backend-specific local input."""


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


class FasterWhisperBackend:
    """Transcribe existing normalized audio through optional faster-whisper."""

    provider_id = FASTER_WHISPER_PROVIDER_ID

    def __init__(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "default",
        language: str | None = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language

    def transcribe(self, audio: NormalizedAudio) -> TranscriptResult:
        input_path = _validated_audio_path(audio)

        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise LocalTranscriptionError(
                "faster-whisper is not installed"
            ) from error

        try:
            model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            raw_segments, _info = model.transcribe(
                str(input_path),
                language=self.language,
            )
            segments = [
                TranscriptSegment(
                    start=_format_timestamp(segment.start),
                    end=_format_timestamp(segment.end),
                    text=text,
                )
                for segment in raw_segments
                if (text := str(segment.text).strip())
            ]
        except Exception as error:
            raise LocalTranscriptionError("local transcription failed") from error

        if not segments:
            raise LocalTranscriptionError("local transcription produced no segments")

        return TranscriptResult(
            segments=segments,
            provider=self.provider_id,
            attempted_providers=[self.provider_id],
        )


def _validated_audio_path(audio: NormalizedAudio) -> Path:
    """Validate local audio before loading the optional ASR dependency."""

    if not isinstance(audio, NormalizedAudio):
        raise LocalTranscriptionError("normalized audio input required")
    input_path = audio.path
    if not input_path.exists():
        raise LocalTranscriptionError("normalized audio input file not found")
    if not input_path.is_file():
        raise LocalTranscriptionError("normalized audio input must be a file")
    return input_path


def _format_timestamp(value: object) -> str:
    """Format a faster-whisper second offset as a stable transcript timestamp."""

    seconds = float(value)
    if seconds < 0:
        raise ValueError("negative transcription timestamp")
    total_milliseconds = round(seconds * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"
