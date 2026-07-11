# Video2Knowledge

Video2Knowledge is a Local First video-to-knowledge pipeline that turns supported video or audio sources into structured Markdown knowledge notes.

The project is designed for local personal knowledge management, with Obsidian-friendly Markdown as the primary durable output:

```text
supported URL / local video or audio
-> metadata
-> official subtitles first
-> explicitly permitted audio acquisition when needed
-> ffmpeg normalization
-> local ASR fallback
-> LLM knowledge extraction
-> structured Markdown
-> local folder / Obsidian-friendly export
```

Video2Knowledge is not positioned as a general-purpose downloader, a standalone transcription script, or a generic chat summarizer. The product value is the complete path from source material to a portable knowledge artifact.

## Current Version

Latest tagged release: `v0.4.0 Official Transcript`

Current development milestone: `v0.5.x Whisper Fallback`

## Implemented

- CLI and import pipeline orchestration.
- Mock metadata, transcript, summary, Markdown, and local export flow.
- Platform classification and capability boundaries.
- YouTube metadata-only extraction through `yt-dlp`.
- YouTube official VTT/WebVTT subtitle acquisition and parsing.
- Sanitized transcript access error handling.
- Verified public YouTube official `zh-CN` VTT smoke test.
- Whisper fallback eligibility policy and error taxonomy.
- Deterministic Mock Whisper fallback for eligible subtitle failures.
- Mock audio acquisition and normalization boundaries.
- Runtime cache and media artifact safety policy.
- `FfmpegAudioNormalizer` for existing local audio files.
- Verified local ffmpeg smoke test producing 16 kHz mono PCM WAV.

## Not Implemented

- Real audio acquisition or media download for fallback.
- ffmpeg integration into the default `real-fallback` chain.
- Real Whisper or faster-whisper transcription.
- Automatic captions.
- Transcript API fallback.
- LLM knowledge extraction.
- Automated Obsidian note update/import behavior.
- Notion or Feishu synchronization.
- MCP server.
- Browser extension.
- Full Bilibili or all-platform support.

## Run the Mock CLI

```powershell
python -m app.cli import-url "https://example.com/watch?v=mock" --metadata-provider mock --transcript-provider mock --output-dir output/markdown
```

The CLI delegates business orchestration to `app.pipeline`:

```text
source -> metadata -> transcript -> summary -> Markdown -> export
```

Mock providers remain the default deterministic path.

## Real YouTube Metadata

```powershell
python -m app.cli import-url "https://www.youtube.com/watch?v=VIDEO_ID" --metadata-provider yt-dlp --transcript-provider mock
```

The `yt-dlp` metadata provider uses metadata-only extraction and must not download video, audio, subtitles, or thumbnails.

## Official YouTube Subtitles

```powershell
python -m app.cli import-url "https://www.youtube.com/watch?v=VIDEO_ID" --metadata-provider yt-dlp --transcript-provider official-subtitles
```

The official subtitle provider:

- Uses only official VTT/WebVTT tracks.
- Does not use `automatic_captions`.
- Does not write subtitle files to the project.
- Does not fall back on platform or network access failures.

## Current Fallback Behavior

`real-fallback` first requests official subtitles.

- Official subtitle success returns `yt_dlp_official_subtitles`.
- Missing official subtitles or unsupported official subtitle formats enter Mock audio processing and `local_whisper_mock`.
- HTTP 429, HTTP 403, timeout, network failures, and generic transcript errors stop without fallback.

The current eligible fallback chain is still deterministic and Mock-only:

```text
official subtitles
-> MockAudioProvider
-> MockAudioNormalizer
-> MockWhisperBackend
-> TranscriptResult
```

It does not download or read media, run ffmpeg, or run Whisper.

## ffmpeg Boundary

`FfmpegAudioNormalizer` can normalize an existing local audio file to:

- WAV
- mono
- 16000 Hz
- PCM signed 16-bit little-endian (`pcm_s16le`)

A user-confirmed local smoke test passed with `ffprobe` validation. This boundary is not connected to `real-fallback` by default.

Audio acquisition, media download, and retained audio cache require explicit user confirmation per stage. Runtime media artifacts belong under ignored `output/` or `cache/` paths.

## Run Tests

```powershell
python -m unittest discover -s tests
```

Current test baseline: `52` tests.

## Markdown Output

Generated notes contain YAML Frontmatter and these sections:

- 一句话摘要
- 核心观点
- 知识点
- 技术术语
- 可执行事项
- 原始转录（带时间戳）

`raw_metadata` is retained in memory for provider debugging and extension but is not rendered into Markdown Frontmatter or body content.

## Repository

GitHub repository:

https://github.com/Eternal-HAC/Video2Knowledge
