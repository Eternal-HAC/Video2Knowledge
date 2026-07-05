"""Import pipeline orchestration.

This module owns the business flow. CLI and future integrations should call
the pipeline instead of directly composing provider modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.downloader import get_metadata_with_provider
from app.exporter.obsidian import export_markdown
from app.markdown_writer import render_markdown
from app.models import Summary, TranscriptResult, VideoMetadata, VideoSource
from app.platform_adapter import get_platform_capabilities, resolve_video_source
from app.summarizer import summarize_mock
from app.transcript import acquire_transcript_with_provider


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
