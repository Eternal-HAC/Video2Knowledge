"""Command-line interface for the Video2Knowledge Mock MVP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.audio import FfmpegAudioNormalizer
from app.errors import (
    AudioAcquisitionError,
    AudioProcessingError,
    FfmpegNotFoundError,
    LocalTranscriptionError,
    MetadataProviderError,
    ProviderNotImplementedError,
    TranscriptProviderError,
)
from app.models import TranscriptResult, VideoMetadata, VideoSource
from app.pipeline import (
    ImportPipelineOptions,
    run_import_pipeline,
    transcribe_local_media,
)
from app.platform_adapter import resolve_video_source
from app.whisper import FasterWhisperBackend


DEFAULT_LOCAL_ASR_MODEL = "small"
DEFAULT_LOCAL_ASR_DEVICE = "cpu"
DEFAULT_LOCAL_ASR_COMPUTE_TYPE = "int8"
LOCAL_TRANSCRIPTION_FAILED_MESSAGE = "local transcription failed"
OFFLINE_MODEL_HINT = (
    "Hint: offline model loading is enabled; use an existing cached model, "
    "a local model directory, or explicitly pass --allow-model-download."
)
LOCAL_MEDIA_TITLE_FALLBACK = "Local media"
_FFMPEG_EXECUTABLE_REQUIRED_MESSAGE = "ffmpeg not found"
_LOCAL_MEDIA_INPUT_REQUIRED_MESSAGE = "local media file path required"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Video2Knowledge",
        description="Local First video-to-knowledge Mock pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_url = subparsers.add_parser(
        "import-url",
        help="Run the Mock import pipeline for a video URL.",
    )
    import_url.add_argument("url", help="Video URL to process with Mock data.")
    import_url.add_argument(
        "--output-dir",
        default="output/markdown",
        help="Directory for generated Markdown files.",
    )
    import_url.add_argument(
        "--metadata-provider",
        choices=["mock", "yt-dlp"],
        default="mock",
        help="Metadata provider to use. yt-dlp supports YouTube metadata only.",
    )
    import_url.add_argument(
        "--transcript-provider",
        choices=["mock", "official-subtitles", "real-fallback"],
        default="mock",
        help="Transcript provider to use. official-subtitles supports YouTube "
        "VTT only; real-fallback uses the Mock audio/Whisper boundary.",
    )

    transcribe_local = subparsers.add_parser(
        "transcribe-local",
        help="Transcribe one user-owned local media file with faster-whisper.",
    )
    transcribe_local.add_argument(
        "path",
        help="Path to a user-owned local video or audio file.",
    )
    transcribe_local.add_argument(
        "--model",
        default=DEFAULT_LOCAL_ASR_MODEL,
        help="faster-whisper model name or local model path.",
    )
    transcribe_local.add_argument(
        "--device",
        default=DEFAULT_LOCAL_ASR_DEVICE,
        help="Inference device passed to faster-whisper.",
    )
    transcribe_local.add_argument(
        "--compute-type",
        default=DEFAULT_LOCAL_ASR_COMPUTE_TYPE,
        help="Compute type passed to faster-whisper.",
    )
    transcribe_local.add_argument(
        "--language",
        default=None,
        help="Optional spoken language code such as en or zh.",
    )
    transcribe_local.add_argument(
        "--ffmpeg-path",
        default=None,
        help="Explicit ffmpeg executable. Omitted uses existing PATH discovery.",
    )
    transcribe_local.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Permit model download. Default requires an existing local model.",
    )
    transcribe_local.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="stdout rendering for the transcript result.",
    )
    return parser


def run_import_url(
    url: str,
    output_dir: Path | str,
    metadata_provider: str = "mock",
    transcript_provider: str = "mock",
) -> Path:
    result = run_import_pipeline(
        url,
        ImportPipelineOptions(
            output_dir=output_dir,
            metadata_provider=metadata_provider,
            transcript_provider=transcript_provider,
        ),
    )
    return result.output_path


def run_transcribe_local(
    path: str,
    *,
    model: str = DEFAULT_LOCAL_ASR_MODEL,
    device: str = DEFAULT_LOCAL_ASR_DEVICE,
    compute_type: str = DEFAULT_LOCAL_ASR_COMPUTE_TYPE,
    language: str | None = None,
    ffmpeg_path: str | None = None,
    allow_model_download: bool = False,
) -> TranscriptResult:
    """Transcribe one user-owned local file, local-files-only by default.

    The command surfaces input classification and builds the dependencies;
    local-source validation stays in ``LocalFileAudioProvider`` and
    ``transcribe_local_media``.
    """

    source = _resolve_local_input_source(path)
    if source.source_type != "local_file" or source.platform != "local":
        raise AudioAcquisitionError(_LOCAL_MEDIA_INPUT_REQUIRED_MESSAGE)

    validated_ffmpeg = _validated_ffmpeg_path(ffmpeg_path)

    return transcribe_local_media(
        _build_local_metadata(path),
        whisper_backend=FasterWhisperBackend(
            model_size=model,
            device=device,
            compute_type=compute_type,
            language=language,
            local_files_only=not allow_model_download,
        ),
        normalizer_factory=lambda workspace_path: FfmpegAudioNormalizer(
            output_dir=workspace_path,
            ffmpeg_path=validated_ffmpeg,
        ),
    )


def _resolve_local_input_source(path: str) -> VideoSource:
    """Classify the input, mapping malformed-URL failures to a stable error.

    ``resolve_video_source`` can raise ``ValueError`` for input the URL parser
    cannot parse, such as a malformed IPv6 authority. That is still user input
    to classify, not a programming error to propagate, so only this
    classification step converts it. ``KeyboardInterrupt`` and ``SystemExit``
    are not intercepted.
    """

    try:
        return resolve_video_source(path)
    except ValueError:
        raise AudioAcquisitionError(_LOCAL_MEDIA_INPUT_REQUIRED_MESSAGE) from None


def _build_local_metadata(path: str) -> VideoMetadata:
    """Build neutral local metadata without Mock or provider metadata."""

    return VideoMetadata(
        title=Path(path).stem or LOCAL_MEDIA_TITLE_FALLBACK,
        platform="local",
        source_url=path,
        author="",
        published_at="",
        duration="",
        language="",
        tags=[],
        status="local_input",
        raw_metadata=None,
    )


def _validated_ffmpeg_path(ffmpeg_path: str | None) -> str | None:
    """Validate an explicit ffmpeg executable without exposing the path."""

    if ffmpeg_path is None:
        return None
    try:
        candidate = Path(ffmpeg_path)
        is_file = candidate.is_file()
    except (OSError, ValueError):
        is_file = False
    if not is_file:
        raise FfmpegNotFoundError(_FFMPEG_EXECUTABLE_REQUIRED_MESSAGE)
    return str(candidate)


def render_local_transcript_text(result: TranscriptResult) -> str:
    """Render one transcript result as concise plain-text stdout."""

    lines = [
        f"Provider: {result.provider}",
        "Attempted providers: " + ", ".join(result.attempted_providers),
    ]
    lines.extend(
        f"[{segment.start} --> {segment.end}] {segment.text}"
        for segment in result.segments
    )
    return "\n".join(lines)


def render_local_transcript_json(result: TranscriptResult) -> str:
    """Render one transcript result as JSON with only TranscriptResult fields."""

    payload = {
        "provider": result.provider,
        "attempted_providers": list(result.attempted_providers),
        "segments": [
            {"start": segment.start, "end": segment.end, "text": segment.text}
            for segment in result.segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import-url":
        try:
            output_path = run_import_url(
                args.url,
                args.output_dir,
                metadata_provider=args.metadata_provider,
                transcript_provider=args.transcript_provider,
            )
        except (
            MetadataProviderError,
            ProviderNotImplementedError,
            TranscriptProviderError,
            ValueError,
        ) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        print(f"Generated Markdown: {output_path}")
        return 0

    if args.command == "transcribe-local":
        return _run_transcribe_local(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _run_transcribe_local(args: argparse.Namespace) -> int:
    """Run the local ASR command, printing a stable error and 1 on failure."""

    try:
        result = run_transcribe_local(
            args.path,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            ffmpeg_path=args.ffmpeg_path,
            allow_model_download=args.allow_model_download,
        )
    except (
        AudioAcquisitionError,
        AudioProcessingError,
        FfmpegNotFoundError,
        LocalTranscriptionError,
    ) as error:
        message = f"Error: {error}"
        if (
            not args.allow_model_download
            and str(error) == LOCAL_TRANSCRIPTION_FAILED_MESSAGE
        ):
            message = f"{message}\n{OFFLINE_MODEL_HINT}"
        print(message, file=sys.stderr)
        return 1

    if args.format == "json":
        print(render_local_transcript_json(result))
    else:
        print(render_local_transcript_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
