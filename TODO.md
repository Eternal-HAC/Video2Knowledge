# TODO

## Current Stage

- [x] Create project documentation skeleton.
- [x] Create Mock pipeline modules.
- [x] Create Markdown template.
- [x] Add unit tests for Mock flow.
- [x] Add platform adapter interface while keeping Mock metadata.
- [x] Define real provider placeholders with explicit not-implemented errors.
- [x] Add pipeline layer so CLI does not own business orchestration.
- [x] Add platform capabilities model before real provider integration.
- [x] Tag architecture stable baseline as `v0.2.0`.
- [x] Plan `v0.3.x Real Metadata`.
- [x] Implement YouTube metadata-only provider behind `yt-dlp`.
- [x] Install `yt-dlp` after user confirmation.
- [x] Run live YouTube metadata-only smoke test after user confirmation.
- [x] Tag real metadata baseline as `v0.3.0`.
- [x] Plan `v0.4.x Official Transcript`.
- [x] Add YouTube official VTT/WebVTT subtitle acquisition.
- [x] Add sanitized error boundary for official VTT text fetch failures.
- [ ] Re-run live YouTube official subtitle smoke test after HTTP 429 rate limit clears.
- [ ] Add transcript API fallback.
- [ ] Add local Whisper fallback.
- [ ] Add configurable LLM summarizer.
- [ ] Add Obsidian import workflow.

## Deferred

- Notion export.
- Feishu export.
- MCP server.
- Browser extension.
- Batch import.
- Prompt template management.
