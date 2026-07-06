# PROJECT_SNAPSHOT

## Snapshot Date

2026-07-06

## Current Version

v0.3.0

Real Metadata

## Project

Video2Knowledge is a Local First AI/PKM tool that converts videos into structured Markdown knowledge notes.

## Current Stage

Real metadata baseline completed. The current implementation stage is `v0.4.x Official Transcript`.

## Completed

- Project bootstrap and memory documents.
- Standard-library Mock CLI.
- Mock metadata, transcript, summary, Markdown, and local export pipeline.
- Platform adapter for URL and local source classification.
- Provider boundaries with explicit not-implemented errors for non-Mock providers.
- Import pipeline layer that owns business orchestration.
- Platform capabilities model.
- YouTube metadata-only provider implemented and validated behind `yt-dlp`.
- YouTube official subtitle provider for VTT/WebVTT tracks.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.
  - `v0.3.0`: YouTube metadata-only baseline.

## Not Yet Implemented

- Successful live YouTube official subtitle VTT parsing smoke test.
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
- Official subtitle provider uses only official VTT/WebVTT tracks and never automatic captions.

## Next Steps

1. Review the `v0.4.x Official Transcript` implementation.
2. Re-run a public YouTube official subtitle smoke test after the current YouTube HTTP 429 rate limit clears.
3. Keep transcript API fallback, Whisper, LLM, and export work out of `v0.4.x`.

## Live Validation Notes

- Metadata-only screening found a TED video with official subtitles and a `zh-CN` VTT/WebVTT track.
- The full official subtitle smoke test was blocked when the VTT text request returned HTTP 429.
- Browser access to YouTube also showed HTTP 429, so the failure is treated as access environment or platform rate limiting.
- This is not equivalent to the video lacking official subtitles.
- VTT parsing against live YouTube subtitles still needs confirmation after the network environment recovers.

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
