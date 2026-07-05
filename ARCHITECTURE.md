# ARCHITECTURE

## Overview

Video2Knowledge is designed as a local pipeline with replaceable provider modules.

```text
Video URL / local video
-> platform adapter
-> downloader / metadata resolver
-> subtitle acquisition
-> Whisper fallback
-> summarizer
-> Markdown writer
-> local exporter
```

## Stage 1 Mock Flow

```text
example URL
-> Mock metadata
-> Mock transcript
-> Mock summary
-> Markdown template renderer
-> local Markdown file
```

## Stage 2 Interface Groundwork

The current code defines the first replaceable boundaries without calling real providers:

```text
raw input
-> platform adapter
-> platform capabilities
-> metadata provider
-> transcript provider strategy
-> summarizer
-> Markdown writer
-> local exporter
```

- `platform_adapter` classifies URL and local file inputs and infers platform labels.
- `platform_adapter` exposes platform capabilities for provider planning.
- `pipeline` owns the import business flow so CLI stays thin.
- `downloader` exposes a metadata boundary that is still backed by Mock data.
- `transcript` records the future fallback order: official subtitles, transcript API, Whisper.
- The CLI remains compatible with `python -m app.cli import-url ...`.

Non-Mock provider boundaries exist with narrow responsibilities:

- Metadata provider: `yt-dlp` for YouTube metadata only.
- Transcript provider placeholder: `real-fallback`.

Transcript fallback is intentionally not split into `OfficialSubtitleProvider`,
`TranscriptApiProvider`, and `WhisperProvider` yet. That split belongs to the
real subtitle stage, when provider-specific inputs and failure modes are known.

## Design Principles

- Local First.
- CLI first, GUI later.
- Keep modules decoupled.
- Providers fetch data only and stay stateless.
- Pipeline owns business orchestration.
- CLI stays lightweight.
- Prefer mature external infrastructure for media processing later.
- Put project value in knowledge extraction and durable output.
- Keep provider APIs replaceable.

## v0.3.x Real Metadata

`yt-dlp` is used only for metadata extraction:

```text
YouTube URL
-> yt-dlp extract_info(download=False)
-> sanitized metadata
-> VideoMetadata
-> Mock transcript
-> Mock summary
-> Markdown
```

This stage does not download media, fetch subtitles, run Whisper, call LLMs, or export to external systems. `raw_metadata` stores the sanitized provider payload for debugging and future mapping, but it is not rendered into Markdown frontmatter or body content.

## Future Real Providers

- `yt-dlp` for video metadata.
- Future media download remains out of scope for `v0.3.x`.
- `ffmpeg` for media processing.
- `youtube-transcript-api` for transcript fallback.
- `faster-whisper` for local transcription.
- OpenAI-compatible, Anthropic, or Gemini APIs for LLM summarization.

Transcript, Whisper, and LLM providers remain out of scope for `v0.3.x`.
