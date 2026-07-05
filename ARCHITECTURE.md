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

