# PROJECT_SNAPSHOT

## Snapshot Date

2026-07-05

## Current Version

v0.2.0

Architecture Stable

## Project

Video2Knowledge is a Local First AI/PKM tool that converts videos into structured Markdown knowledge notes.

## Current Stage

Architecture stable baseline completed. The current implementation stage is `v0.3.x Real Metadata`.

## Completed

- Project bootstrap and memory documents.
- Standard-library Mock CLI.
- Mock metadata, transcript, summary, Markdown, and local export pipeline.
- Platform adapter for URL and local source classification.
- Provider boundaries with explicit not-implemented errors for non-Mock providers.
- Import pipeline layer that owns business orchestration.
- Platform capabilities model.
- YouTube metadata-only provider implementation prepared behind `yt-dlp`.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.

## Not Yet Implemented

- Installed `yt-dlp` runtime dependency.
- Live YouTube metadata smoke test.
- Official transcript acquisition.
- Transcript API fallback.
- Whisper/faster-whisper.
- LLM providers.
- Obsidian automation.
- Notion export.
- Feishu export.
- MCP server.
- Browser extension.

## Current Architecture Rules

- CLI parses arguments and calls the pipeline.
- Pipeline owns business orchestration.
- Providers fetch data only and remain stateless.
- Markdown remains the primary local output.
- Do not combine metadata, transcript, Whisper, LLM, and export work in one stage.

## Next Steps

1. Confirm whether to install `yt-dlp`.
2. After installation and local tests pass, confirm whether to run a public YouTube metadata-only smoke test.
3. Keep downloading, transcript, Whisper, LLM, and export work out of `v0.3.x`.

## Must Read Files for Continuation

- `README.md`
- `PRD.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `TODO.md`
- `DECISIONS.md`
- `PROGRAM_MAP.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
