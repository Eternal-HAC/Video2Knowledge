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
