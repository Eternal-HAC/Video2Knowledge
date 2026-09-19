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
- [x] Run live YouTube official subtitle smoke test after HTTP 429 rate limit clears.
- [x] Plan `v0.5.x Whisper Fallback`.
- [x] Define fallback policy and error taxonomy for Whisper fallback.
- [x] Add mock Whisper fallback pipeline.
- [x] Add mock audio acquisition and normalizer boundary.
- [x] Add cache/temp handling and explicit audio download confirmation policy.
- [x] Add ffmpeg audio normalizer boundary.
- [x] Add local ffmpeg smoke test after explicit confirmation.
- [x] Add YouTube-only yt-dlp audio acquisition provider boundary with mocked tests.
- [x] Add AudioWorkspace cleanup for registered temporary audio artifacts.
- [ ] Add separately approved audio cache retention.
- [ ] Run a separately confirmed live audio acquisition smoke test.
- [x] Add mocked faster-whisper backend boundary.
- [x] Install faster-whisper and obtain the small model after explicit approval.
- [x] Run a separately confirmed standalone faster-whisper CPU transcription test.
- [x] Declare faster-whisper as the optional `asr` dependency set.
- [x] Add mocked local-file-to-ASR orchestration.
- [x] Run a separately approved real local-file-to-ASR integration smoke test.
- [x] Harden provider input and error boundaries (exact host classification,
      sanitized yt-dlp metadata failures, minimal `raw_metadata`, HTTPS
      subtitle URL and redirect validation, bounded response reads, stable
      charset/error sanitization).
- [x] Remediate reviewed provider boundary gaps (bounded and closed redirect
      responses for 301/302/303/307/308, legacy numeric IPv4 fail-closed
      rejection, exact-host-only `youtu.be` with reserved platform id
      collision mapped to `unknown`, string-only minimal metadata values, and
      a module-private quiet logger for yt-dlp output), proven by fully
      offline tests.
- [x] Remediate the reviewed authority-normalization gap (validate the
      hostname the HTTP request layer resolves: authority percent encoding
      rejected, trailing DNS root dot dropped, IDNA to ASCII required to
      succeed, one validator for initial URLs and redirect targets, and an HTTP
      error path that closes its response without reading it), proven by fully
      offline tests.
- [x] Finalize the provider boundary (reject the reserved `localhost`
      namespace after IDNA normalization and trailing-dot removal, fail closed
      on ASCII control characters and DEL in the authority without leaking a
      raw `ValueError`, validate a redirect `Location` as the effective
      absolute target the request layer resolves it into so safe relative and
      scheme-relative redirects work again, and map quote/encoding/resolution
      failures to the stable `unsafe URL` error), proven by fully offline
      tests. DNS rebinding and resolver-level TOCTOU remain out of scope.
- [x] Close the provider boundary (reject ASCII control characters and DEL in
      the raw unstripped input before any parsing, for the initial URL and the
      raw redirect `Location` alike, so tab/CR/LF can no longer hide a host
      from an authority-level rule; and make redirect-response cleanup
      best-effort and idempotent so a failing `close()` cannot replace a stable
      error, a parent-opener failure, a successful redirect result, or a
      propagating `KeyboardInterrupt`/`SystemExit`), proven by fully offline
      tests. DNS rebinding and resolver-level TOCTOU remain out of scope.
- [ ] Add explicit local ASR CLI entry point (parameter surface to be locked
      by Architecture & Product first).
- [ ] Add transcript API fallback.
- [ ] Add local Whisper fallback.
- [ ] Add YAML Frontmatter hardening.
- [ ] Add template packaging and resource-path hardening.
- [ ] Add exporter collision and overwrite policy.
- [ ] Add configurable LLM summarizer.
- [ ] Add Obsidian import workflow.

## Deferred

- Notion export.
- Feishu export.
- MCP server.
- Browser extension.
- Batch import.
- Prompt template management.
- Study cangjie-skill-style method-card or skill-pack export after Whisper fallback and base LLM extraction are stable.
