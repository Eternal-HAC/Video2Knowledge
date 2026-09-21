"""Import pipeline orchestration.

This module owns the business flow. CLI and future integrations should call
the pipeline instead of directly composing provider modules.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from stat import S_ISREG

from app.audio import (
    AudioArtifact,
    AudioNormalizer,
    AudioProvider,
    AudioWorkspace,
    FfmpegAudioNormalizer,
    LocalFileAudioProvider,
    NormalizedAudio,
)
from app.downloader import get_metadata_with_provider
from app.errors import AudioAcquisitionError, AudioProcessingError
from app.exporter.obsidian import export_markdown
from app.markdown_writer import render_markdown
from app.models import Summary, TranscriptResult, VideoMetadata, VideoSource
from app.platform_adapter import get_platform_capabilities, resolve_video_source
from app.summarizer import summarize_mock
from app.transcript import acquire_transcript_with_provider
from app.whisper import WhisperBackend


_NormalizerFactory = Callable[[Path], AudioNormalizer]


@dataclass(frozen=True)
class ImportPipelineOptions:
    output_dir: Path | str = "output/markdown"
    metadata_provider: str = "mock"
    transcript_provider: str = "mock"


@dataclass(frozen=True)
class ImportPipelineResult:
    source: VideoSource
    metadata: VideoMetadata
    transcript_result: TranscriptResult
    summary: Summary
    output_path: Path


def transcribe_local_media(
    metadata: VideoMetadata,
    *,
    whisper_backend: WhisperBackend[NormalizedAudio],
    audio_provider: AudioProvider | None = None,
    normalizer_factory: _NormalizerFactory | None = None,
) -> TranscriptResult:
    """Transcribe one user-owned local media file through injected boundaries.

    An injected provider must return an existing, regular, user-owned
    ``AudioArtifact`` with ``temporary=False``. An injected normalizer factory
    must write only into its supplied workspace, return the one
    ``temporary=True`` output it created, and best-effort clean any partial
    output before raising.
    """

    if metadata.platform.lower() != "local":
        raise AudioAcquisitionError("local audio input required")

    provider = audio_provider or LocalFileAudioProvider()
    original_artifact = provider.acquire(metadata)
    _validate_local_original_artifact(original_artifact)

    with AudioWorkspace() as workspace:
        if normalizer_factory is None:
            normalizer: AudioNormalizer = FfmpegAudioNormalizer(
                output_dir=workspace.path
            )
        else:
            normalizer = normalizer_factory(workspace.path)
        normalized_artifact = normalizer.normalize(original_artifact)
        try:
            workspace.register(normalized_artifact)
        except AudioProcessingError:
            _cleanup_unregistered_workspace_output(
                workspace.path,
                normalized_artifact,
            )
            raise
        return whisper_backend.transcribe(normalized_artifact)


def _validate_local_original_artifact(artifact: object) -> None:
    """Require a user-owned local file before workspace processing begins."""

    if not isinstance(artifact, AudioArtifact) or artifact.temporary:
        raise AudioAcquisitionError("local audio input must be user-owned")
    try:
        mode = artifact.path.stat().st_mode
        is_symlink = artifact.path.is_symlink()
    except FileNotFoundError:
        raise AudioAcquisitionError("local audio input file not found") from None
    except OSError:
        raise AudioAcquisitionError("local audio input inaccessible") from None
    if is_symlink or not S_ISREG(mode):
        raise AudioAcquisitionError("local audio input must be a file")


def _cleanup_unregistered_workspace_output(
    workspace_path: Path,
    artifact: object,
) -> None:
    """Best-effort cleanup of one exact normalizer output rejected at register."""

    try:
        candidate = artifact.path
        if not isinstance(candidate, Path) or not candidate.is_absolute():
            return
        if candidate == workspace_path or candidate.is_symlink():
            return
        relative_candidate = candidate.relative_to(workspace_path)
        if not relative_candidate.parts or ".." in relative_candidate.parts:
            return
        candidate.parent.relative_to(workspace_path)

        resolved_workspace = workspace_path.resolve()
        resolved_candidate = candidate.resolve()
        if resolved_candidate == resolved_workspace:
            return
        if not resolved_candidate.is_relative_to(resolved_workspace):
            return

        if candidate.is_file():
            candidate.unlink()
        elif candidate.is_dir():
            candidate.rmdir()
    except (AttributeError, OSError, ValueError):
        return


def run_import_pipeline(
    raw_input: str,
    options: ImportPipelineOptions | None = None,
) -> ImportPipelineResult:
    """Run the Mock import pipeline for a URL or local source."""

    pipeline_options = options or ImportPipelineOptions()
    source = resolve_video_source(raw_input)
    _ = get_platform_capabilities(source.platform)
    metadata = get_metadata_with_provider(
        source,
        provider_name=pipeline_options.metadata_provider,
    )
    transcript_result = acquire_transcript_with_provider(
        metadata,
        provider_name=pipeline_options.transcript_provider,
    )
    summary = summarize_mock(metadata, transcript_result.segments)
    markdown = render_markdown(metadata, transcript_result.segments, summary)
    output_path = export_markdown(
        markdown,
        metadata.title,
        pipeline_options.output_dir,
    )
    return ImportPipelineResult(
        source=source,
        metadata=metadata,
        transcript_result=transcript_result,
        summary=summary,
        output_path=output_path,
    )
