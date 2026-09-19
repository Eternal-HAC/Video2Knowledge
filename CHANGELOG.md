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

## 2026-07-11

- Added `AudioWorkspace` for registered temporary audio artifact cleanup.
- Added context-exit cleanup, reverse registration order, stable cleanup errors, and protection for local or workspace-external files.
- Kept cache retention, yt-dlp execution, ffmpeg execution, Whisper, CLI, pipeline, and fallback integration out of the stage.

## 2026-07-12

- Added `FasterWhisperBackend` for mapping existing normalized audio through the optional faster-whisper Python API.
- Added input-first validation, lazy dependency loading, stable sanitized local transcription errors, timestamp formatting, and empty-result handling.
- Added mocked tests for dependency absence, model configuration, path forwarding, segment mapping, failure sanitization, input preservation, and Mock backend regression.
- Kept dependency installation, model download, live ASR, pipeline integration, fallback integration, retained cache, and live audio acquisition out of this stage.

## 2026-07-12

- Sanitized `FasterWhisperBackend` dependency initialization and runtime failures without exposing underlying exception chains in default tracebacks.
- Preserved the distinct missing-dependency error and propagation of control-flow exceptions.
- Added mocked coverage for immediate and lazy failures, segment access, timestamp conversion and boundaries, input gates, and traceback redaction.
- Kept empty or filtered output mapped to `local transcription produced no segments`; pure-silence semantics remain for a future approved live validation or fallback integration stage.

## 2026-07-12

- Validated a standalone faster-whisper CPU smoke test on Windows with Python 3.13.7, faster-whisper 1.2.1, the small model, and CPU `int8` execution.
- Confirmed one non-empty `TranscriptResult` segment with stable provider ids while preserving the input audio and tracked worktree.
- Added the optional `asr` packaging extra pinned to `faster-whisper==1.2.1`; base installation remains free of the local ASR dependency set.
- Documented that model files are acquired and cached separately, the first-run timing is not a stable benchmark, and pipeline, `real-fallback`, live audio acquisition, and retained cache remain incomplete.

## 2026-07-12

- Added a non-CLI local-file-to-ASR orchestration boundary in `app.pipeline` using `LocalFileAudioProvider`, `AudioWorkspace`, an injected normalizer, and an injected Whisper backend.
- Required normalized artifacts to pass workspace ownership checks before transcription and preserved the backend `TranscriptResult` unchanged.
- Added narrowly scoped best-effort cleanup for partial ffmpeg output after timeout, startup failure, or non-zero exit.
- Added mocked integration and lifecycle coverage without running real ffmpeg, faster-whisper, user media, or network access.
- Kept CLI, default pipeline, `real-fallback`, YouTube acquisition, retained cache, and model-cache management unchanged.

## 2026-07-12

- Enforced local metadata and user-owned non-temporary source artifacts at the non-CLI local ASR orchestration boundary.
- Rejected temporary/network-style provider artifacts before workspace creation or normalization.
- Added limited provisional ownership for the exact normalized workspace object returned before registration, with non-recursive best-effort cleanup on registration failure.
- Preserved user inputs, external paths, symlink targets, unknown workspace content, business errors, and control-flow exceptions under cleanup failure.
- Added mocked lifecycle and SHA-256 input-protection coverage without running real ffmpeg, faster-whisper, network, or model operations.

## 2026-07-17

- Recorded a separately approved real non-CLI local-file-to-ASR integration smoke test through `transcribe_local_media`, real ffmpeg normalization, and faster-whisper small on CPU `int8` using an existing offline model cache.
- Confirmed the user-owned AAC source remained unchanged, the temporary normalized WAV and private workspace were cleaned, and the call returned one `TranscriptResult` segment.
- Kept CLI local ASR, default-pipeline and `real-fallback` real-ASR integration, YouTube live audio acquisition, retained cache, model-cache policy, and LLM knowledge extraction out of scope.

## 2026-09-18

- Hardened provider input and error boundaries: exact platform hostname matching, sanitized yt-dlp metadata failures without underlying text or cause, and minimal `raw_metadata` limited to `provider` plus per-track `url`/`ext`/`protocol`/`format`.
- Added offline subtitle URL validation (HTTPS-only, no userinfo, port empty or `443`, restricted literal IPs rejected via `ipaddress`) for both initial URLs and redirect targets, plus 16 MiB bounded subtitle response reads.
- Mapped unknown charsets and decode failures to stable sanitized transcript errors and removed underlying exception causes from all public subtitle fetch errors while preserving `KeyboardInterrupt` and `SystemExit`.
- Added 36 fully offline security regression tests in `tests/test_provider_security.py`; full suite passes 156 tests with one pre-existing platform-dependent skip.
- Kept CLI command surface, fallback eligibility, provider ids, and dependencies unchanged; tightened the offline URL, redirect, response, and decoding boundaries without running live network validation.

## 2026-09-19

- Remediated independently reviewed gaps in the provider boundary hardening, guided by `LONG_TASK.md`.
- Redirect handling: the standard library's unbounded redirect-body drain is replaced by a bounded read of at most `MAX_SUBTITLE_RESPONSE_BYTES + 1`, oversized redirect bodies map to the stable `response too large` error, the current response is closed on safe, unsafe, oversized, and parent-opener-failure paths, and 301/302/303/307/308 share one policy. Redirect rejection errors never expose the `Location` URL, query, userinfo, headers, or body.
- Subtitle URL validation now rejects legacy numeric IPv4 forms that the operating system would resolve as loopback or private (`127.1`, `127.0.1`, `2130706433`, `0177.0.0.1`, `0x7f000001`), fails closed on numeric-looking hosts that cannot be proven safe, and keeps the identical validator for initial URLs and redirect targets. DNS hostnames and public IPv4/IPv6 literals remain usable; DNS rebinding remains out of scope.
- Platform classification now treats `youtu.be` as exact-host only (no `*.youtu.be` subdomain gains YouTube capabilities) and maps unknown hostnames that collide with reserved platform ids (for example `https://youtube/x` or `https://user@youtube/x`) to the safe `unknown` label with no provider capabilities.
- Minimal subtitle metadata now copies only string values for the `url`/`ext`/`protocol`/`format` allowlist, drops nested dict/list or other mutable values, and never shares references with provider-owned objects.
- The yt-dlp metadata provider now injects a module-private quiet logger through `ydl_opts["logger"]` so raw yt-dlp errors, signed URLs, tokens, cookies, local paths, and stderr output cannot reach stdout/stderr before the sanitized exception is raised.
- Added 14 fully offline regression tests exercising the real redirect handler dispatch (not only validator helpers); `tests/test_provider_security.py` now covers 50 tests and the full suite passes with one pre-existing platform-dependent skip.
- No live network, yt-dlp, subtitle fetch, ffmpeg, Whisper, or media processing was run; all evidence is mocked or offline probes.

## 2026-09-19

- Remediated the independently reviewed authority-normalization gap in the
  subtitle URL validator: the validated value is now the hostname the HTTP
  request layer would use, not the raw `urlparse` result.
- Authority percent encoding is rejected instead of decoded (encoded and
  decoded forms can disagree about host and port), while percent encoding in
  the path and query of signed subtitle URLs keeps working. Trailing DNS root
  dots are removed before validation, and the host must survive an explicit
  IDNA to ASCII conversion that fails closed on full-width digits, Unicode
  label separators, and otherwise unencodable hosts.
- Initial URLs and redirect targets share the one validator. The redirect
  handler validates the raw `Location` before the standard library quotes it
  with latin-1: a raw target that is already an unsafe absolute URL, or that
  is not an absolute HTTPS URL at all, is rejected before the parent opener is
  reached and before its body is read. (Relative and scheme-relative targets
  were rejected too, which the follow-up entry below corrects, and a
  non-latin-1 absolute target still failed as a raw `UnicodeError`.)
- The HTTP status error path now closes its own response without reading the
  error body, preserves the HTTP status code, and swallows a failing close so
  it cannot replace the stable platform error; `KeyboardInterrupt` and
  `SystemExit` still propagate unchanged.
- Added 14 fully offline regression tests; `tests/test_provider_security.py`
  covers 64 tests and the full suite passes 184 tests with one pre-existing
  platform-dependent skip. No live network, yt-dlp, subtitle fetch, ffmpeg,
  Whisper, or media processing was run, and DNS rebinding remains outside the
  current capability.

## 2026-09-19

- Closed the four remaining findings in the independently reviewed provider
  boundary, keeping every earlier change in place.
- The reserved `localhost` namespace is now rejected after IDNA normalization
  and trailing-dot removal: `localhost`, `localhost.`, `*.localhost`, and the
  full-width or upper-case spellings that normalize onto them no longer reach
  the opener, for initial URLs and for every redirect target alike.
- An authority containing an ASCII control character or DEL now fails closed.
  IDNA's ASCII fast path passes such labels through without nameprep, so
  `https://example.com\x00.evil/sub.vtt` previously reached
  `socket.inet_aton`, whose raw `ValueError("embedded null character")` escaped
  the validator and replaced the stable error. `_ip_literal_address` now maps
  the expected `ValueError` and `OSError` to a safe validation failure, the
  validator fails closed on any unexpected parse failure, and
  `KeyboardInterrupt`/`SystemExit` still propagate unchanged.
- Redirect targets are validated as the effective absolute target: the raw
  `Location` is parsed, given a `/` path when authority-only, re-serialized,
  percent-encoded with latin-1, and `urljoin`-ed against the source request URL
  exactly as `urllib.request` does, and the resolved target is what the safety
  rules judge. Safe relative (`/next.vtt`, `../next.vtt`, `?sig=abc`) and
  scheme-relative (`//cdn.example.com/next.vtt`) redirects from an HTTPS source
  are accepted again, while `//127.0.0.1/next.vtt`, `//localhost/next.vtt`,
  encoded authorities, `http`/`file`/`ftp`/`data` targets, userinfo, and
  non-`443` ports stay rejected. `redirect_request` keeps its second
  validation of the absolute target.
- A redirect target that cannot be quoted, encoded, or resolved now maps to
  `official subtitle VTT fetch failed: unsafe URL` inside the handler instead
  of raising a raw `UnicodeError`; rejected redirects call no parent opener,
  read no body, and close the response.
- Added 12 fully offline regression tests (76 in `tests/test_provider_security.py`,
  196 in the full suite with one pre-existing platform-dependent skip), all
  driven through `fetch_text` or the real `http_error_30x` dispatch. No live
  network, DNS lookup, yt-dlp, subtitle fetch, ffmpeg, Whisper, or media
  processing was run. This is not a complete SSRF defense: DNS rebinding and
  resolver-level time-of-check/time-of-use differences remain outside the
  current capability.

## 2026-09-19

- Closed the two runtime findings and the documentation number left by the
  finalization review, keeping every earlier change in place.
- Raw control characters now fail closed before any parsing. `urlparse` removes
  tab, CR, and LF from the whole URL before it splits the authority off, so the
  authority-level control-character rule added above never saw those three and
  `https://exa\tmple.com/sub.vtt`, `https://exa\rmple.com/sub.vtt`, and
  `https://exa\nmple.com/sub.vtt` all reached the mocked opener. A raw-value
  check now runs first, on the unstripped initial URL and on the unstripped
  redirect `Location`, and refuses any ASCII control character or DEL anywhere
  — authority, path, or query — with the stable
  `official subtitle VTT fetch failed: unsafe URL`. No opener call, no redirect
  body read, no parent opener call, and a closed response on every redirect
  code (301/302/303/307/308); legal percent encoding in the path and query is
  unaffected.
- Redirect cleanup is now best-effort, so it can no longer replace the outcome
  it runs alongside. `finally: bounded_body.close()` let an ordinary `close()`
  failure replace a propagating `TranscriptProviderError` (both the stable
  `unsafe URL` and `response too large` cases) and any error the parent opener
  raised (`URLError`, `PlatformAccessError`, `NetworkAccessError`), discard a
  successful redirect result, and mask `KeyboardInterrupt`/`SystemExit`. One
  module-internal helper now swallows ordinary close failures at the redirect
  cleanup site, inside `_BoundedRedirectBody.close`, and on the HTTP status
  error path, so both close policies are literally the same policy. The cleanup
  is idempotent — the standard library closes a successfully followed redirect
  response itself, so a repeated close that fails creates no new public failure
  — `KeyboardInterrupt`/`SystemExit` raised by `close()` still propagate
  unchanged, and close text never reaches a public error or a traceback.
- Added 10 fully offline regression tests (86 in `tests/test_provider_security.py`,
  206 executed in the full suite: 205 passed, 1 skipped), all driven through
  `fetch_text` or the real `http_error_30x` dispatch, with the red phase
  recorded first — `Ran 86 tests` / `FAILED (failures=53, errors=21)` from eight
  methods (seven of the ten new ones plus the rewritten whitespace-tolerance
  test). The two new methods that passed before the fix guard it against
  becoming over-broad, i.e. against catching `BaseException` around cleanup. No
  live network, DNS lookup, yt-dlp, subtitle fetch, ffmpeg, Whisper, or media
  processing was run. This is still not a complete SSRF defense: DNS rebinding
  and resolver-level time-of-check/time-of-use differences remain outside the
  current capability.
