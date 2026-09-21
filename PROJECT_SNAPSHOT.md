# PROJECT_SNAPSHOT

## Snapshot Date

2026-09-19

## Current Version

v0.4.0

Official Transcript

## Project

Video2Knowledge is a Local First video-to-knowledge pipeline that converts supported video or audio sources into structured Markdown knowledge notes.

## Current Stage

The latest tagged release is `v0.4.0 Official Transcript`. Development is currently in `v0.5.x Whisper Fallback`, with policy, Mock fallback, audio boundaries, cache safety, local ffmpeg normalization, workspace cleanup, the faster-whisper backend boundary, standalone CPU transcription, non-CLI local-file-to-ASR integration, and provider input/error boundary hardening plus its reviewed remediation, authority-normalization follow-up, provider boundary finalization, and provider boundary closure validated offline.

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
- AudioWorkspace cleanup boundary for registered temporary audio artifacts.
- FasterWhisperBackend boundary for existing normalized audio with lazy optional dependency loading, sanitized errors, and mocked segment mapping tests.
- Standalone faster-whisper CPU smoke test on Windows and Python 3.13.7 using the small model, CPU `int8`, and an existing normalized WAV.
- Optional `asr` dependency set pinned to the validated `faster-whisper==1.2.1` runtime.
- Mocked local-file ASR orchestration with strict local metadata, user-owned
  source-artifact validation, private normalized-output ownership, and cleanup.
- Separately approved real local-file-to-ASR integration smoke test on Windows:
  user-owned AAC M4A -> private workspace -> real ffmpeg normalization ->
  faster-whisper small model on CPU `int8` -> `TranscriptResult`, with source
  SHA-256 preserved and temporary output cleaned.
- Provider input and error boundary hardening: exact platform hostname
  matching, sanitized yt-dlp metadata failures, minimal `raw_metadata`,
  HTTPS-only subtitle URL and redirect validation, 16 MiB bounded subtitle
  response reads, and stable charset/error sanitization, all proven by fully
  offline unit tests.
- Reviewed remediation of that hardening: bounded and closed redirect
  response handling for 301/302/303/307/308, legacy numeric IPv4 fail-closed
  rejection for initial and redirect URLs, exact-host-only `youtu.be` with
  reserved platform id collision mapped to `unknown`, string-only minimal
  subtitle metadata values without shared references, and a module-private
  quiet logger injected into yt-dlp so raw provider output cannot reach
  process streams.
- Authority normalization remediation of the reviewed validator gap: the
  validated host is the one the HTTP request layer resolves (authority percent
  encoding rejected, trailing root dot dropped, IDNA to ASCII required to
  succeed), applied identically to initial URLs and redirect targets, plus an
  HTTP error lifecycle that closes the response without reading it. Evidenced
  only by fully offline tests; DNS rebinding remains out of scope.
- Provider boundary finalization of the reviewed remainder: the reserved
  `localhost` namespace is rejected after IDNA normalization and trailing-dot
  removal, an authority containing an ASCII control character or DEL fails
  closed instead of leaking a raw `ValueError`, redirect targets are validated
  as the effective absolute target the request layer resolves them into (so
  safe relative and scheme-relative redirects work again while unsafe ones stay
  rejected), and a redirect target that cannot be quoted, encoded, or resolved
  maps to the stable `unsafe URL` error instead of a raw `UnicodeError`. Still
  offline evidence only; DNS rebinding and resolver-level TOCTOU remain outside
  the guarantee.
- Provider boundary closure of that finalization's remainder: the raw,
  unstripped input is checked for ASCII control characters and DEL before any
  parsing — so tab, CR, and LF can no longer hide a host from an
  authority-level rule that `urlparse` had already stripped them out of — for
  the initial URL and the raw redirect `Location` alike, and redirect cleanup
  is best-effort so an ordinary `close()` failure can no longer replace the
  stable `unsafe URL`/`response too large` errors, a parent-opener failure, a
  successful redirect result, or a propagating `KeyboardInterrupt`/`SystemExit`
  (which still propagate, and whose close text still never reaches a public
  error or traceback). Offline evidence only, on the same terms as above.
- Tags:
  - `v0.1.0`: provider boundaries baseline.
  - `v0.2.0`: architecture stable baseline.
  - `v0.3.0`: YouTube metadata-only baseline.
  - `v0.4.0`: YouTube official transcript baseline.

## Not Yet Implemented

- Transcript API fallback.
- User-confirmed live audio acquisition.
- Retained-cache behavior.
- ffmpeg integration into the default fallback path.
- Pipeline and `real-fallback` integration of the validated faster-whisper backend.
- YAML Frontmatter hardening.
- Template packaging and resource-path hardening.
- Exporter collision and overwrite policy.
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
- Signed URLs, cookies, tokens, auth headers, and sensitive query parameters must not be written to logs, Markdown, transcript results, error messages, or disk. The only `raw_metadata` exception is the minimal in-memory signed subtitle URL required by the official subtitle provider; it is never rendered or logged.
- The ffmpeg normalizer boundary is available for existing local audio files but is not used by `real-fallback` by default.
- `YtDlpAudioProvider` is YouTube-only, defaults to disabled, produces temporary audio artifacts, and is not connected to `real-fallback`.
- AudioWorkspace removes only registered temporary files in its private directory; it does not delete local user files or unknown workspace content.
- `FasterWhisperBackend` validates local normalized audio before importing its optional dependency, does not expose local paths or raw runtime failures, and is not connected to `real-fallback`.
- Base installation does not include faster-whisper. The optional `asr` extra installs the pinned Python dependency but not model files; model cache policy remains separate and unresolved.
- `transcribe_local_media` accepts only local metadata and an existing regular
  `temporary=False` user-owned source artifact; temporary or network acquisition
  providers cannot enter this boundary.
- Before workspace registration, orchestration owns only the exact normalized
  object returned inside that workspace. Registration failure triggers only
  non-recursive exact-object cleanup and never removes external, symlink-target,
  user-owned, or unknown content.
- Platform classification uses exact hostname matching; suffix-confusion hosts
  and userinfo URLs are never recognized as supported platforms. `youtu.be`
  matches its exact host only, and unknown hostnames colliding with reserved
  platform ids map to `unknown` with no provider capabilities.
- yt-dlp metadata extraction failures surface only as the stable
  `yt-dlp metadata extraction failed` error without underlying text or cause;
  a module-private quiet logger receives yt-dlp diagnostics so raw provider
  output never reaches stdout/stderr.
- `raw_metadata` keeps only `{"provider": "yt-dlp", "subtitles": {...}}` with a
  per-track `url`/`ext`/`protocol`/`format` allowlist of string values only;
  signed subtitle URLs stay in memory only and never reach Markdown, logs, or
  public errors.
- Subtitle fetching validates the initial URL and every redirect target
  against the hostname the HTTP request layer would actually use (HTTPS-only,
  no userinfo, port empty or `443`, the reserved `localhost` namespace and its
  subdomains rejected, ASCII control characters and DEL anywhere in the raw
  input failing closed before any parsing, authority percent encoding rejected
  instead of decoded, trailing DNS root dots dropped, Unicode hosts required to
  survive an explicit IDNA to ASCII conversion, restricted literal IPs rejected
  via `ipaddress`, legacy numeric IPv4 forms recognized offline and rejected,
  numeric-looking unprovable hosts failing closed) and bounds initial,
  redirect, and final response reads to 16 MiB while closing the current
  response on every redirect path. The redirect handler checks the raw
  `Location` for control characters first, then resolves it into the effective
  absolute target exactly as the request layer does — quoting it with latin-1
  and joining it against the source request URL — and validates that resolved
  target before the body is read or the parent opener is called; a target that
  cannot be quoted, encoded, or resolved is rejected with the same stable
  `unsafe URL` error instead of a raw `UnicodeError`. Redirect cleanup is
  best-effort and idempotent, so a failing `close()` cannot replace a stable
  error, a parent-opener failure, a successful redirect result, or a
  control-flow exception, and its text never reaches a public error or a
  traceback. An HTTP status error closes its own response without reading
  the error body, preserves the HTTP status code, and lets a failing close pass
  without replacing the stable error.
- Unknown charsets and decode failures map to stable sanitized transcript
  errors; public subtitle fetch errors never retain an underlying exception
  cause; `KeyboardInterrupt` and `SystemExit` propagate unchanged.
- All of the above is evidenced by fully offline unit tests. No live network,
  provider, or media validation backs this section, and DNS rebinding plus
  resolver-level differences remain outside the current capability.

## Next Steps

1. Add separately approved audio cache retention.
2. Keep the existing default `real-fallback` Mock-only until a separate integration stage is approved.
3. Keep local-file ASR orchestration disconnected from `real-fallback` until a separate integration stage is approved.
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
- A standalone faster-whisper CPU smoke test returned one non-empty segment for an existing 5.482688-second normalized WAV. The first 39.169-second end-to-end run included model acquisition and loading and is not a stable benchmark.
- A separate non-CLI local-file integration smoke test used a user-owned
  5.51-second AAC M4A at 48 kHz stereo. Real ffmpeg created a temporary 16 kHz
  mono WAV in the private workspace; faster-whisper small on CPU `int8` returned
  one segment from `00:00:00.000` to `00:00:05.000`. The source SHA-256 was
  unchanged, and the normalized file and workspace were removed after return.
  The observed 9.217-second elapsed time used an existing offline model cache
  and is not a benchmark or accuracy evaluation.

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
