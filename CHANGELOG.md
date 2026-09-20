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

## 2026-09-20

- Added the independent `transcribe-local` CLI subcommand:
  `python -m app.cli transcribe-local <path> [--model small] [--device cpu]
  [--compute-type int8] [--language CODE] [--ffmpeg-path EXECUTABLE]
  [--allow-model-download] [--format text|json]`. The existing `import-url`
  command, its flags, and its output are unchanged.
- The CLI parses arguments, requires a `local_file`/`local` classification from
  the existing `resolve_video_source`, builds neutral local `VideoMetadata`
  privately without `get_mock_metadata`, constructs the dependencies, and calls
  the existing `app.pipeline.transcribe_local_media`. Local-file validation
  stays in `LocalFileAudioProvider`; no pipeline, audio, model, error,
  transcript, packaging, or dependency file was modified.
- The neutral metadata is exactly `title=Path(path).stem` with the `Local media`
  fallback for an empty stem, `platform="local"`, `source_url=path`, empty
  `author`/`published_at`/`duration`/`language`, `tags=[]`,
  `status="local_input"`, and `raw_metadata=None`.
- Model loading is offline by default: `FasterWhisperBackend` gained
  `local_files_only: bool = False` and the CLI passes
  `local_files_only=not allow_model_download`. `--allow-model-download` is the
  only switch that permits a model download, so no environment or configuration
  input can silently widen the policy. The default `False` keeps every earlier
  direct caller behaviorally compatible; the `WhisperModel` call itself now
  always passes the keyword explicitly, so callers or stubs that asserted the
  exact keyword set see one added argument rather than byte-identical
  arguments. The constructor still imports nothing, loads no model, and touches
  no file or network.
- Closed the tokenizer fallback in the offline path. In faster-whisper 1.2.1 a
  `local_files_only=True` `WhisperModel` only constrains the model-snapshot
  download: when the resolved snapshot has no `tokenizer.json`, the library
  calls `tokenizers.Tokenizer.from_pretrained`, which reaches Hugging Face Hub
  despite the flag. With `local_files_only=True` the backend now resolves the
  model before constructing `WhisperModel` — an existing local model directory
  is used as-is, otherwise `download_model(model_size, local_files_only=True)`
  returns an existing cached snapshot or fails closed — and requires a regular
  `tokenizer.json` inside the resolved directory. The resolved local directory
  is passed to `WhisperModel` with `local_files_only=True` still set. A missing
  tokenizer, an unresolvable model, and any other resolution failure are all
  sanitized to `local transcription failed` before `WhisperModel` is
  constructed. No environment variable, monkey patch, or new dependency is
  used, and `local_files_only=False` keeps the previous direct behavior with no
  pre-resolution and no tokenizer check.
- Input classification now maps a `ValueError` raised by `resolve_video_source`
  — for example a malformed IPv6 URL that `urlparse` cannot parse — to the same
  stable `local media file path required` error with exit code 1 instead of a
  traceback. Only that classification step converts it; `KeyboardInterrupt` and
  `SystemExit` are not intercepted, and a later `ValueError` still propagates.
- `--ffmpeg-path` is validated as an existing regular file and injected through
  `normalizer_factory` as
  `FfmpegAudioNormalizer(output_dir=workspace_path, ffmpeg_path=override)`, so
  normalized output still lands in the private workspace and keeps the existing
  cleanup lifecycle. An omitted flag keeps the existing PATH discovery
  untouched, and validation errors never echo the supplied path and reuse the
  boundary's existing `ffmpeg not found` wording rather than adding a second
  message for the same failure.
- Default text stdout is `Provider:`, `Attempted providers:`, then
  `[start --> end] text` lines; `--format json` prints exactly `provider`,
  `attempted_providers`, and `segments[{start, end, text}]` with
  `ensure_ascii=False`. Output contains only `TranscriptResult` fields, and the
  command writes no transcript file, no Markdown, and no export.
- Failures in `AudioAcquisitionError`, `AudioProcessingError` /
  `FfmpegNotFoundError`, and `LocalTranscriptionError` print one stable
  sanitized `Error: <message>` line to stderr and return exit code 1, without
  causes, paths, or tracebacks. In the default offline mode an exact
  `local transcription failed` failure prints exactly two lines with one final
  newline:

  ```text
  Error: local transcription failed
  Hint: offline model loading is enabled; use an existing cached model, a local model directory, or explicitly pass --allow-model-download.
  ```

  The hint is a separate `Hint:` line, not a parenthetical suffix on the
  `Error:` line. An explicit `--allow-model-download` or any other message
  prints no hint. `KeyboardInterrupt` and `SystemExit` propagate unchanged.
- Added 41 fully mocked tests in `tests/test_local_asr_cli.py`, including
  malformed-URL classification, the shared `ffmpeg not found` message, and the
  local model directory pass-through, plus offline model-resolution,
  tokenizer-guard, and pass-through tests in `tests/test_whisper_backend.py`
  (`python -m unittest tests.test_local_asr_cli`: 41 OK;
  `python -m unittest tests.test_whisper_backend`: 31 OK; full suite: 257
  executed, 256 passed, 1 pre-existing Windows symlink skip).
- No real ffmpeg, faster-whisper, model download, provider call, or network
  access was performed, and no real `transcribe-local` CLI smoke test has been
  run: this stage is mocked-test evidence only. Default pipeline,
  `real-fallback`, YouTube audio acquisition, retained cache, model-cache
  lifecycle, detected language, LLM extraction, Markdown, and export behavior
  are unchanged.
