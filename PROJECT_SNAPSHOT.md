# PROJECT_SNAPSHOT

## Snapshot Date

2026-07-08

## Current Version

v0.4.0

Official Transcript

## Project

Video2Knowledge is a Local First AI/PKM tool that converts videos into structured Markdown knowledge notes.

## Current Stage

Official transcript baseline completed. The next implementation stage is `v0.5.x Whisper Fallback`.

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
- Live official `zh-CN` VTT smoke test passed on a public TED video.
- Transcript fallback eligibility policy and error taxonomy for the upcoming Whisper fallback.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.
  - `v0.3.0`: YouTube metadata-only baseline.
  - `v0.4.0`: YouTube official transcript baseline.

## Not Yet Implemented

- Transcript API fallback.
- Whisper/faster-whisper execution.
- Audio acquisition and ffmpeg processing.
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
- Only missing official subtitles and unsupported official subtitle formats are eligible for future Whisper fallback.
- Platform and network access failures must stop and must not trigger Whisper fallback.

## Next Steps

1. Review and commit `v0.5.0a Fallback Policy and Error Taxonomy`.
2. Plan `v0.5.0b Mock Whisper Fallback Pipeline`.
3. Keep audio download, ffmpeg, faster-whisper, Transcript API fallback, LLM, and export work out of `v0.5.0a`.

## Live Validation Notes

- Metadata-only screening found a TED video with official subtitles and a `zh-CN` VTT/WebVTT track.
- After the HTTP 429 condition cleared, the full official subtitle smoke test passed.
- Test URL: `https://www.youtube.com/watch?v=iG9CE55wbtY`
- Provider: `yt_dlp_official_subtitles`
- Attempted providers: `["yt_dlp_official_subtitles"]`
- Output was Markdown only; no video, audio, subtitle, thumbnail, or other media artifacts were found.

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
