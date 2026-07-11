# PROJECT_SNAPSHOT

## Snapshot Date

2026-07-11

## Current Version

v0.4.0

Official Transcript

## Project

Video2Knowledge is a Local First video-to-knowledge pipeline that converts supported video or audio sources into structured Markdown knowledge notes.

## Current Stage

The latest tagged release is `v0.4.0 Official Transcript`. Development is currently in `v0.5.x Whisper Fallback`, with policy, Mock fallback, audio boundaries, cache safety, and local ffmpeg normalization validated.

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
- Mock Whisper fallback pipeline for eligible official subtitle failures.
- Mock audio acquisition and normalization boundaries for the fallback path.
- Cache/temp safety policy for future audio acquisition.
- ffmpeg audio normalizer boundary for existing local audio files.
- User-confirmed local ffmpeg smoke test with `ffprobe` validation of 16 kHz mono `pcm_s16le` WAV output.
- YouTube-only `YtDlpAudioProvider` boundary with explicit permission, audio-only yt-dlp Python API options, and mocked backend tests.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.
  - `v0.3.0`: YouTube metadata-only baseline.
  - `v0.4.0`: YouTube official transcript baseline.

## Not Yet Implemented

- Transcript API fallback.
- User-confirmed live audio acquisition.
- AudioWorkspace cleanup and retained-cache behavior.
- ffmpeg integration into the default fallback path.
- Real Whisper/faster-whisper execution.
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
- Only missing official subtitles and unsupported official subtitle formats are eligible for Whisper fallback.
- Platform and network access failures must stop and must not trigger Whisper fallback.
- `real-fallback` currently uses only Mock audio processing and Mock local Whisper; it does not download audio or run real Whisper.
- `real-fallback` eligible cases pass through Mock audio and Mock normalizer boundaries only; they do not read or write media files.
- Audio acquisition, media download, and keeping audio cache require explicit user confirmation per stage.
- Signed URLs, cookies, tokens, auth headers, and sensitive query parameters must not be written to logs, Markdown, raw metadata, transcript results, or error messages.
- The ffmpeg normalizer boundary is available for existing local audio files but is not used by `real-fallback` by default.
- `YtDlpAudioProvider` is YouTube-only, defaults to disabled, produces temporary audio artifacts, and is not connected to `real-fallback`.

## Next Steps

1. Add AudioWorkspace cleanup ownership and separately approved cache retention.
2. Keep the existing default `real-fallback` Mock-only until a separate integration stage is approved.
3. Add real Whisper or faster-whisper only after acquisition and cleanup behavior are stable.
4. Keep Transcript API fallback, LLM extraction, and export expansion in separate stages.

## Live Validation Notes

- Metadata-only screening found a TED video with official subtitles and a `zh-CN` VTT/WebVTT track.
- After the HTTP 429 condition cleared, the full official subtitle smoke test passed.
- Test URL: `https://www.youtube.com/watch?v=iG9CE55wbtY`
- Provider: `yt_dlp_official_subtitles`
- Attempted providers: `["yt_dlp_official_subtitles"]`
- Output was Markdown only; no video, audio, subtitle, thumbnail, or other media artifacts were found.
- Local ffmpeg validation used an existing user-approved audio file and produced an ignored runtime WAV artifact under `output/cache/audio/`.
- `ffprobe` confirmed `pcm_s16le`, `16000 Hz`, and one audio channel.

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
