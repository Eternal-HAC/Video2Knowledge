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
- `FasterWhisperBackend` boundary for existing normalized audio, with lazy
  optional dependency loading and sanitized runtime errors.
- Verified non-CLI local-file ASR integration through `transcribe_local_media`:
  a user-owned local M4A was normalized by ffmpeg and transcribed by
  faster-whisper on CPU into `TranscriptResult`, while preserving the source
  file and cleaning the temporary normalized artifact and workspace.
- An explicit `transcribe-local` CLI subcommand for one user-owned local media
  file, with local-files-only model loading by default, an optional explicit
  ffmpeg executable, and stdout-only `TranscriptResult` output.

## Not Implemented

- Real audio acquisition or media download for fallback.
- ffmpeg integration into the default `real-fallback` chain.
- faster-whisper selection in the default import pipeline or `real-fallback`.
  The backend boundary, optional dependency combination, standalone CPU
  transcription, non-CLI local-file integration, and the explicit
  `transcribe-local` command exist, but the default import pipeline still does
  not select the real backend.
- A validated real `transcribe-local` CLI run. The command surface is
  implemented and covered by fully mocked tests only; no real
  ffmpeg/faster-whisper CLI smoke test has been run.
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

## Local ASR CLI

```powershell
python -m app.cli transcribe-local "path\to\user-owned-media.m4a"
python -m app.cli transcribe-local "path\to\media.mp4" --model small --device cpu --compute-type int8 --language zh --format json
python -m app.cli transcribe-local "path\to\media.mp4" --ffmpeg-path "C:\tools\ffmpeg.exe"
python -m app.cli transcribe-local "path\to\media.mp4" --allow-model-download
```

`transcribe-local` is an independent subcommand that accepts one user-owned
local media file path. `import-url` is unchanged.

- `--model` (default `small`), `--device` (default `cpu`),
  `--compute-type` (default `int8`), `--language` (unset by default).
- `--ffmpeg-path` selects an explicit ffmpeg executable; when it is omitted the
  existing PATH discovery inside `FfmpegAudioNormalizer` is used. A path that is
  not an existing regular file fails with the boundary's existing
  `ffmpeg not found` message.
- `--allow-model-download` is the only way to permit a model download. Without
  it, `FasterWhisperBackend` runs with `local_files_only=True`, resolves the
  model to an existing cached snapshot or to the supplied local model directory,
  and requires that directory to contain `tokenizer.json` before constructing
  `WhisperModel`, so neither the model snapshot nor the tokenizer can reach
  Hugging Face Hub. An uncached model name in offline mode fails with the
  offline hint below instead of downloading.
- `--format text|json` (default `text`) selects the stdout rendering.

Default text stdout:

```text
Provider: faster_whisper
Attempted providers: faster_whisper
[00:00:00.000 --> 00:00:05.000] transcript text
```

`--format json` prints `provider`, `attempted_providers`, and
`segments[{start, end, text}]` with `ensure_ascii=False`.

The command writes no transcript file and no Markdown, and renders only
`TranscriptResult` fields. It builds neutral metadata for the local file
(`title` from the path stem, falling back to `Local media`; `platform="local"`;
`source_url` set to the given path; `status="local_input"`; no Mock or provider
metadata).

Failures print one stable `Error: ...` line to stderr and return exit code 1.
Input the URL parser cannot parse at all, such as a malformed IPv6 URL, is still
treated as input to classify: it returns `Error: local media file path required`
with exit code 1 and no traceback. When the default offline mode fails with
exactly `local transcription failed`, stderr is two lines:

```text
Error: local transcription failed
Hint: offline model loading is enabled; use an existing cached model, a local model directory, or explicitly pass --allow-model-download.
```

The command is implemented and covered by fully mocked tests only. No real
`transcribe-local` CLI smoke test has been run, and the command is not selected
by the default import pipeline, `real-fallback`, or YouTube audio acquisition.
The offline model guard is also covered by mocked tests only: no model was
loaded, no cache was inspected, and no network call was made.

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

The `transcribe_local_media` boundary has also completed a separately approved
real local-file integration smoke test with the default local provider, private
workspace, real ffmpeg normalization, and `FasterWhisperBackend` on CPU. It
returned `TranscriptResult` while leaving the user-owned source file unchanged
and cleaning temporary output. That smoke test predates the `transcribe-local`
subcommand and drove the boundary directly; it did not connect real ASR to the
default import pipeline or `real-fallback`, and it did not validate YouTube
audio acquisition or the CLI command itself.

Audio acquisition, media download, and retained audio cache require explicit user confirmation per stage. Runtime media artifacts belong under ignored `output/` or `cache/` paths.

## Run Tests

```powershell
python -m unittest discover -s tests
```

Current test baseline: `257` tests, including the fully mocked
`tests/test_local_asr_cli.py` coverage of the `transcribe-local` command and the
offline model-resolution and tokenizer-guard coverage in
`tests/test_whisper_backend.py`. The current Windows environment skips one
platform-dependent symlink test when symlink creation is unavailable.

## Installation

Install the base project without local ASR dependencies:

```powershell
python -m pip install -e .
```

Install the optional local ASR dependency set:

```powershell
python -m pip install -e ".[asr]"
```

The `asr` extra installs the validated faster-whisper Python dependency. It
does not add model files or model caches to the repository. Model files are
acquired separately: `transcribe-local` loads models local-files-only unless
`--allow-model-download` is passed, and only that flag lets faster-whisper reach
Hugging Face Hub. In the default offline mode the backend resolves the model from
an existing local directory or the existing Hub cache and requires a local
`tokenizer.json` in the resolved directory, so a missing tokenizer cannot trigger
a fallback download; a model that is not present locally fails with a stable
error instead. Cache location and lifecycle remain environment or future
configuration concerns rather than a current product policy.

`FasterWhisperBackend` is reachable through the explicit `transcribe-local`
command. The default import pipeline and `real-fallback` still do not select
it, so these installation commands do not change the default Mock path.

## Markdown Output

Generated notes contain YAML Frontmatter and these sections:

- 一句话摘要
- 核心观点
- 知识点
- 技术术语
- 可执行事项
- 原始转录（带时间戳）

For yt-dlp metadata, `raw_metadata` retains only the minimal in-memory provider
and official-subtitle mapping required by the official subtitle provider. It is
not rendered into Markdown Frontmatter or body content.

## Repository

GitHub repository:

https://github.com/Eternal-HAC/Video2Knowledge
