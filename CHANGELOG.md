# CHANGELOG

## 2026-07-05

- Initialized Video2Knowledge project structure.
- Added project memory documents.
- Added standard-library Mock CLI pipeline.
- Added Markdown template and local file export.
- Added unit tests for the Mock MVP.

## 2026-07-05

- Added platform adapter interface for URL/local source classification.
- Added transcript strategy result metadata for the future subtitle fallback order.
- Kept the CLI command and all provider behavior Mock-only.

## 2026-07-05

- Added explicit metadata and transcript provider interfaces.
- Added non-Mock provider placeholders for `yt-dlp` and transcript fallback.
- Added CLI provider flags while keeping Mock providers as the default.

## 2026-07-05

- Added `app.pipeline` to own import orchestration.
- Added platform capabilities for provider planning.
- Added stable metadata fields for the upcoming real metadata stage.
- Kept all provider behavior Mock-only.

## 2026-07-05

- Updated development workflow guidance in existing project documents.
- Updated roadmap to version-based milestones from `v0.1.x` through `v1.0`.
- Updated project snapshot to `v0.2.0 Architecture Stable`.
- Recorded the provider, pipeline, and CLI responsibility principle.

## 2026-07-05

- Added YouTube metadata-only provider implementation using `yt-dlp` API boundaries.
- Added metadata mapping tests with mocked `yt_dlp`.
- Declared `yt-dlp` dependency without installing it.
- Kept transcript, summary, Markdown, and export paths Mock/local.

## 2026-07-06

- Added YouTube official subtitle provider for VTT/WebVTT tracks.
- Added minimum WebVTT parser coverage for headers, cue ids, metadata blocks, cue settings, multiline text, tags, and entities.
- Added transcript provider error handling in the CLI.
- Kept automatic captions, transcript API fallback, Whisper, and LLM work out of this stage.

## 2026-07-06

- Added sanitized error handling for official subtitle VTT text fetch failures.
- Covered HTTP 429, HTTP 403, network failures, timeouts, and unknown request failures in tests.
- Recorded that TED metadata screening found official `zh-CN` VTT subtitles, while live VTT fetching was blocked by YouTube HTTP 429 in the current environment.

## 2026-07-08

- Verified YouTube official `zh-CN` VTT smoke test on the TED video `https://www.youtube.com/watch?v=iG9CE55wbtY`.
- Generated structured Markdown from official subtitles.
- Confirmed no video, audio, subtitle, thumbnail, or other media artifacts were written to the project directory.
- Marked `v0.4.x Official Transcript` ready for the `v0.4.0` tag.

## 2026-07-08

- Added transcript fallback error taxonomy for missing official subtitles, unsupported subtitle formats, platform access failures, and network access failures.
- Added Whisper fallback eligibility policy without downloading audio or running Whisper.
- Kept HTTP 429, HTTP 403, timeout, and network failures from triggering fallback.

## 2026-07-08

- Added a deterministic Mock local Whisper backend.
- Updated `real-fallback` to return official subtitles when available and use Mock Whisper only for fallback-eligible subtitle absence or unsupported subtitle formats.
- Preserved stop behavior for platform access, network access, and generic transcript provider failures.
- Kept audio acquisition, ffmpeg processing, and real Whisper execution out of this stage.

## 2026-07-09

- Added Mock audio acquisition and Mock audio normalization boundaries.
- Routed fallback-eligible `real-fallback` cases through Mock audio processing before Mock Whisper.
- Kept `attempted_providers` focused on transcript providers without adding audio or normalizer ids.
- Kept real audio download, ffmpeg execution, cache handling, CLI flags, and real Whisper execution out of this stage.

## 2026-07-09

- Added `.gitignore` guardrails for runtime cache and media artifacts under `output/` and `cache/`.
- Documented explicit confirmation requirements for audio acquisition, media download, and keeping audio cache.
- Documented signed URL, cookie, token, auth header, and sensitive query parameter redaction rules.
- Kept runtime behavior unchanged.

## 2026-07-09

- Added an ffmpeg audio normalizer boundary for existing local audio files.
- Standardized the target normalized audio contract as 16 kHz mono PCM WAV.
- Added mocked subprocess tests for ffmpeg missing, non-zero exit, timeout, missing input, existing output, missing output, command construction, and sanitized errors.
- Kept `real-fallback` on the Mock audio normalizer path.

## 2026-07-09

- Verified local ffmpeg normalization smoke test using `FfmpegAudioNormalizer`.
- Confirmed 16 kHz mono PCM WAV output with `ffprobe`.
- No media artifacts were committed.

## 2026-07-11

- Added a YouTube-only `YtDlpAudioProvider` boundary using the yt-dlp Python API.
- Required explicit download permission and disabled playlists, subtitle and thumbnail writes, configuration files, and ffmpeg postprocessing.
- Added mocked yt-dlp tests for permission, platform, workspace, success, timeout, output containment, and sanitized failures.
- Kept `real-fallback`, pipeline, CLI, cache retention, and workspace cleanup unchanged.
