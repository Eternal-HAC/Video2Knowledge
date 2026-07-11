# ARCHITECTURE

## Overview

Video2Knowledge is a Local First video-to-knowledge pipeline with replaceable provider modules. Its primary output is structured Markdown for local PKM systems such as Obsidian.

```text
Supported URL / local video or audio
-> platform adapter
-> downloader / metadata resolver
-> subtitle acquisition
-> explicitly permitted audio acquisition when needed
-> ffmpeg normalization
-> local ASR fallback
-> LLM knowledge extraction
-> Markdown writer
-> local exporter
```

The standard user workflow begins with a supported URL or local media file. It must not require manual video download as a normal prerequisite.

## v1.0 Pipeline Contract

The `v1.0` processing priority is:

```text
metadata
-> official subtitles
-> another explicitly supported transcript source
-> audio acquisition only when needed and explicitly permitted
-> ffmpeg normalization
-> local ASR
-> LLM knowledge extraction
-> structured Markdown export
```

The acquisition boundary exists to support knowledge processing, not to turn the product into a general-purpose downloader. Local ASR exists as a fallback, not as a standalone transcription product. LLM providers own extraction calls, while the pipeline owns orchestration and structured Markdown remains the durable output.

## Stage 1 Mock Flow

```text
example URL
-> Mock metadata
-> Mock transcript
-> Mock summary
-> Markdown template renderer
-> local Markdown file
```

## Interface Groundwork

The project started with replaceable boundaries and now has real YouTube metadata, official subtitle, and local ffmpeg normalization implementations alongside Mock defaults:

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
- `downloader` exposes Mock metadata and real YouTube metadata-only extraction.
- `transcript` provides Mock transcripts, official YouTube VTT/WebVTT subtitles, fallback eligibility policy, and Mock Whisper fallback orchestration.
- `audio` provides Mock audio boundaries and a real ffmpeg normalizer for existing local files.
- `whisper` currently provides only the deterministic Mock local backend.
- The CLI remains compatible with `python -m app.cli import-url ...`.

Implemented provider boundaries have narrow responsibilities:

- Metadata provider: `yt-dlp` for YouTube metadata only.
- Transcript provider: `official-subtitles` for YouTube official VTT/WebVTT subtitles only.
- Transcript strategy: `real-fallback` for official subtitles followed only by eligible Mock local fallback.
- Audio normalizer: `ffmpeg_audio_normalizer` for existing local audio files, not wired into the default fallback chain.

Real audio acquisition, real Whisper/faster-whisper, Transcript API fallback, and LLM knowledge extraction are not implemented.

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
- Prefer official subtitles before acquiring media.
- Require explicit permission before media acquisition or retained media cache.
- Keep browser and mobile clients as optional capture or reading surfaces around the local core.
- Do not claim support for arbitrary websites or all video platforms.

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

## Provider Direction

- `yt-dlp` is implemented for YouTube metadata-only extraction.
- Official YouTube VTT/WebVTT acquisition is implemented.
- `ffmpeg` normalization is implemented for existing local audio files.
- Future explicitly permitted audio acquisition remains separate from the current default pipeline.
- `youtube-transcript-api` for transcript fallback.
- `faster-whisper` for local transcription.
- OpenAI-compatible, Anthropic, or Gemini APIs for LLM summarization.

Transcript API fallback, real Whisper, and LLM providers remain unimplemented.

## v0.4.x Official Transcript

Official subtitles are acquired from `VideoMetadata.raw_metadata["subtitles"]`, which is populated by the `yt-dlp` metadata provider:

```text
YouTube URL
-> yt-dlp metadata
-> official subtitles from raw_metadata
-> VTT/WebVTT track selection
-> VTT parser
-> TranscriptResult
-> Mock summary
-> Markdown
```

This stage is intentionally VTT/WebVTT-only. It does not use `automatic_captions`, transcript API fallback, Whisper, LLMs, or subtitle file output. `attempted_providers` records only the stable provider id `yt_dlp_official_subtitles`.

## v0.5.0a Fallback Policy

The first Whisper fallback stage defines only error taxonomy and fallback eligibility:

```text
official-subtitles
-> NoOfficialSubtitleError / UnsupportedSubtitleFormatError
-> eligible for future Whisper fallback
```

Platform or network access failures do not mean subtitles are missing:

```text
HTTP 429 / HTTP 403 / timeout / network request failed
-> PlatformAccessError or NetworkAccessError
-> stop, do not enter Whisper fallback
```

`real-fallback` validates this policy and returns official subtitles when available. If fallback is eligible, it enters deterministic Mock audio processing boundaries before the Mock local Whisper backend:

```text
official-subtitles
-> NoOfficialSubtitleError / UnsupportedSubtitleFormatError
-> mock_audio_provider
-> mock_ffmpeg_normalizer
-> local_whisper_mock
-> TranscriptResult
```

The Mock audio provider and normalizer do not read local media, write audio files, download audio, check ffmpeg, or run ffmpeg. The Mock Whisper backend still does not call Whisper. Real audio acquisition, ffmpeg processing, and faster-whisper integration remain future stages.

## v0.5.0c2 Cache/Temp Safety Policy

Real audio acquisition remains disabled. Future audio download and audio cache retention require explicit user confirmation per stage. Runtime media artifacts belong only under `output/` or `cache/` paths and are ignored by Git.

Signed media URLs, cookies, tokens, auth headers, and sensitive query parameters must not be written to logs, Markdown, `raw_metadata`, `TranscriptResult`, or error messages. Future audio and ffmpeg errors should report stable categories such as `audio download failed`, `audio processing failed`, or `ffmpeg not found` without exposing credentials or signed URLs.

## v0.5.0d ffmpeg Normalizer Boundary

The real ffmpeg normalizer boundary supports only existing local audio files:

```text
local audio file
-> ffmpeg
-> 16 kHz mono PCM WAV
-> NormalizedAudio
```

This boundary is not wired into `real-fallback` by default. The fallback path still uses `MockAudioNormalizer`. The ffmpeg boundary does not download audio, run Whisper, access YouTube, use Transcript API fallback, or call LLMs. A separate user-confirmed local smoke test verified 16 kHz mono PCM WAV output.

## Current v0.5.x State

Completed:

- Fallback eligibility and error taxonomy.
- Mock Whisper fallback orchestration.
- Mock audio acquisition and normalization boundaries.
- Runtime cache and media artifact safety policy.
- Real ffmpeg normalizer boundary for existing local audio.
- Local ffmpeg and ffprobe smoke test.

Not implemented:

- Real audio acquisition.
- Selection of real ffmpeg normalization in `real-fallback`.
- Real Whisper or faster-whisper execution.
- Transcript API fallback.
- LLM knowledge extraction.

## URL Intake Boundaries

`v1.0` accepts clean YouTube URLs with minimum validation needed by the current pipeline. Full share-text parsing, tracking-parameter cleanup, short-link expansion, mobile-link handling, video-position preservation, and multi-platform normalization belong to `v1.x` platform expansion. They must not be folded into the current `v0.5.x` audio and ASR work.

## Future Capture and Mobile Surfaces

A future browser extension may submit URLs, page metadata, and tasks to a local service. It may assist content capture only where the user is authenticated and authorized. It must not bypass authentication, circumvent DRM, or replace the local processing core.

Mobile is an input and reading surface first. Link collection, task submission, and note reading may run on mobile, while ffmpeg, local ASR, and knowledge extraction remain primarily on a PC or local service.

## Cost Boundaries

Metadata, subtitle acquisition, and ffmpeg do not consume LLM tokens. Local Whisper or faster-whisper consumes local compute, storage, and time rather than cloud LLM tokens. Token cost begins primarily at LLM knowledge extraction. Replaceable providers should support user-provided API keys and may later support local models, but the architecture does not promise zero-cost operation.
