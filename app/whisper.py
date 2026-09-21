"""Local Whisper backend boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol, TypeVar

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
        local_files_only: bool = False,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.local_files_only = local_files_only

    def transcribe(self, audio: NormalizedAudio) -> TranscriptResult:
        input_path = _validated_audio_path(audio)

        try:
            from faster_whisper import WhisperModel, download_model
        except ImportError:
            raise LocalTranscriptionError(
                "faster-whisper is not installed"
            ) from None
        except Exception:
            raise LocalTranscriptionError("local transcription failed") from None

        if self.local_files_only:
            loaded_model = _resolve_local_model_path(
                self.model_size,
                download_model,
            )
        else:
            loaded_model = _resolve_online_model_path(self.model_size)

        try:
            model = WhisperModel(
                loaded_model,
                device=self.device,
                compute_type=self.compute_type,
                local_files_only=self.local_files_only,
                use_auth_token=False,
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
        except Exception:
            raise LocalTranscriptionError("local transcription failed") from None

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


def _resolve_local_model_path(
    model_size: str,
    download_model: Callable[..., str],
) -> str:
    """Resolve an offline model reference and require its tokenizer locally.

    ``WhisperModel(local_files_only=True)`` only constrains the model-snapshot
    download. If the resolved snapshot has no ``tokenizer.json``, the library
    still calls ``Tokenizer.from_pretrained`` against the Hub, so this helper
    resolves the model to a local directory first and refuses anything that
    cannot serve its tokenizer from disk. Every failure is sanitized.
    """

    try:
        model_path = Path(model_size)
        if model_path.is_dir():
            resolved_model = model_path
        else:
            # ``download_model(local_files_only=True)`` returns an existing
            # cached snapshot, or raises when nothing is cached locally.
            resolved_model = Path(
                download_model(
                    model_size,
                    local_files_only=True,
                    use_auth_token=False,
                )
            )
        _require_local_tokenizer(resolved_model)
        return str(resolved_model)
    except LocalTranscriptionError:
        raise
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise LocalTranscriptionError("local transcription failed") from None


def _resolve_online_model_path(model_size: str) -> str:
    """Reject incomplete local model directories before upstream construction."""

    try:
        model_path = Path(model_size)
        if not model_path.is_dir():
            return model_size
        _require_local_tokenizer(model_path)
        return str(model_path)
    except LocalTranscriptionError:
        raise
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise LocalTranscriptionError("local transcription failed") from None


def _require_local_tokenizer(model_path: Path) -> None:
    """Require the local tokenizer needed to keep a directory self-contained."""

    tokenizer_path = model_path / "tokenizer.json"
    if not tokenizer_path.is_file():
        raise LocalTranscriptionError("local transcription failed") from None


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
