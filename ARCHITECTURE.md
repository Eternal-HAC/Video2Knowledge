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
-> metadata provider
-> transcript provider strategy
-> summarizer
-> Markdown writer
-> local exporter
```

- `platform_adapter` classifies URL and local file inputs and infers platform labels.
- `downloader` exposes a metadata boundary that is still backed by Mock data.
- `transcript` records the future fallback order: official subtitles, transcript API, Whisper.
- The CLI remains compatible with `python -m app.cli import-url ...`.

Non-Mock provider boundaries now exist but intentionally raise explicit not-implemented errors:

- Metadata provider placeholder: `yt-dlp`.
- Transcript provider placeholder: `real-fallback`.

## Design Principles

- Local First.
- CLI first, GUI later.
- Keep modules decoupled.
- Prefer mature external infrastructure for media processing later.
- Put project value in knowledge extraction and durable output.
- Keep provider APIs replaceable.

## Future Real Providers

- `yt-dlp` for video metadata and download.
- `ffmpeg` for media processing.
- `youtube-transcript-api` for transcript fallback.
- `faster-whisper` for local transcription.
- OpenAI-compatible, Anthropic, or Gemini APIs for LLM summarization.

These providers are not used in Stage 1.
