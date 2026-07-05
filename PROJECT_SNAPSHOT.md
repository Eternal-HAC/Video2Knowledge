# PROJECT_SNAPSHOT

## Snapshot Date

2026-07-05

## Current Version

v0.2.0

Architecture Stable

## Project

Video2Knowledge is a Local First AI/PKM tool that converts videos into structured Markdown knowledge notes.

## Current Stage

Architecture stable baseline completed. The next stage is `v0.3.x Real Metadata`.

## Completed

- Project bootstrap and memory documents.
- Standard-library Mock CLI.
- Mock metadata, transcript, summary, Markdown, and local export pipeline.
- Platform adapter for URL and local source classification.
- Provider boundaries with explicit not-implemented errors for non-Mock providers.
- Import pipeline layer that owns business orchestration.
- Platform capabilities model.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.

## Not Yet Implemented

- Real metadata provider.
- Real YouTube metadata via `yt-dlp`.
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

1. Plan `v0.3.x Real Metadata`.
2. Implement real YouTube metadata only after the plan is confirmed.
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
