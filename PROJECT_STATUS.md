# PROJECT_STATUS

## 2026-07-05

Status: Stage 1 initialization in progress.

Current goal:

- Establish the Video2Knowledge project structure.
- Implement a standard-library Mock MVP pipeline.
- Validate the CLI and unit tests locally.

Current implementation:

- No real API integrations.
- No external Python dependencies.
- Mock pipeline only.

Known constraints:

- `output/` is generated runtime data and should not be committed.
- Real video, transcript, Whisper, LLM, Notion, Feishu, MCP, and browser extension work is deferred.

## 2026-07-05

Status: Stage 2 interface groundwork started.

Changes:

- Added a platform adapter boundary for URL/local source classification.
- Added transcript result metadata for future fallback strategy.
- Kept all providers Mock-only.
- Added explicit non-Mock provider placeholders that fail with clear not-implemented errors.

Validation target:

- Unit tests must still pass.
- Existing Mock CLI command must remain compatible.

## 2026-07-05

Status: Architecture correction stage in progress.

Changes:

- Move business orchestration out of CLI and into `app.pipeline`.
- Add platform capabilities before real YouTube metadata work.
- Keep all providers Mock-only or explicitly not implemented.

Validation target:

- CLI remains compatible.
- Mock pipeline still writes Markdown.
- Unit tests pass.

## 2026-07-05

Status: Documentation synchronization stage in progress.

Changes:

- Record the development workflow in existing project memory documents.
- Update roadmap to version-based milestones.
- Update snapshot to `v0.2.0 Architecture Stable`.
- Keep `CODEX_WORKFLOW.md` out of the document set to avoid workflow duplication.

Validation target:

- Only Markdown documents are changed.
- No product code changes.

## 2026-07-05

Status: `v0.3.x Real Metadata` implementation in progress.

Changes:

- Implement YouTube metadata-only provider through the `yt-dlp` Python API.
- Keep transcript, summary, Markdown, and export on the existing Mock/local path.
- Declare `yt-dlp` as a dependency without installing it in this stage.

Validation target:

- Unit tests use mocked `yt_dlp` and do not access the network.
- Mock CLI regression still passes.
- Live installation and YouTube smoke test remain separate confirmation steps.

## 2026-07-06

Status: `v0.4.x Official Transcript` implementation in progress.

Changes:

- Add YouTube official subtitle provider for VTT/WebVTT tracks only.
- Read official subtitle tracks from `yt-dlp` metadata `raw_metadata["subtitles"]`.
- Keep automatic captions, transcript API fallback, Whisper, and LLMs out of this stage.
- Keep transcript provider attempts stable with `yt_dlp_official_subtitles`.

Validation target:

- Unit tests mock subtitle fetching and do not access YouTube.
- Mock CLI regression still passes.
- Live official subtitle smoke test remains a separate confirmation step.

## 2026-07-06

Status: `v0.4.x Official Transcript` error boundary fix in progress.

Findings:

- TED video metadata-only screening found official subtitles with a `zh-CN` VTT/WebVTT track.
- Full official subtitle smoke test reached the VTT text request step but received YouTube HTTP 429.
- Browser access to YouTube also showed HTTP 429, so this is treated as current access environment or platform rate limiting.
- This does not mean the selected video lacks official subtitles.

Changes:

- Wrap official subtitle VTT text fetch failures in `TranscriptProviderError`.
- Keep errors sanitized so subtitle URLs, signatures, tokens, cookies, and temporary credentials are not exposed.

Validation target:

- CLI must print a concise `Error: official subtitle VTT fetch failed: ...` message without traceback.
- Real VTT parsing smoke test remains pending until the network environment is no longer rate limited.

## 2026-07-08

Status: `v0.4.x Official Transcript` live smoke test passed.

Validation:

- URL: `https://www.youtube.com/watch?v=iG9CE55wbtY`
- Selected subtitle: official `zh-CN` `vtt`
- Provider: `yt_dlp_official_subtitles`
- Attempted providers: `["yt_dlp_official_subtitles"]`
- Output: Markdown only
- Generated Markdown: `output\markdown\do-schools-kill-creativity-sir-ken-robinson-ted.md`
- No video, audio, subtitle, thumbnail, or other media artifacts were found in the project directory.
- Unit tests passed: `Ran 30 tests ... OK`

Next target:

- Prepare `v0.4.0` tag.
- Plan `v0.5.x Whisper Fallback`, starting with fallback policy and error taxonomy.

## 2026-07-08

Status: `v0.5.0a Fallback Policy and Error Taxonomy` implementation in progress.

Changes:

- Add transcript error classes for fallback-eligible and access-failure cases.
- Define Whisper fallback eligibility policy.
- Keep `real-fallback` as a policy validator only; it does not download audio or run Whisper in this stage.
- Preserve official subtitle behavior and automatic captions boundary.

Policy:

- Missing official subtitles can enter future Whisper fallback.
- Official subtitles without VTT/WebVTT can enter future Whisper fallback.
- Platform access failures such as HTTP 429 and HTTP 403 must stop.
- Network access failures such as timeout and network request failure must stop.
- Metadata contract errors must stop.

Validation target:

- Unit tests cover eligibility and non-eligibility cases without network access.
- Mock CLI regression still passes.

## 2026-07-08

Status: `v0.5.0b Mock Whisper Fallback Pipeline` implementation in progress.

Changes:

- Add a deterministic Mock local Whisper backend.
- Make `real-fallback` return official subtitles when available.
- Make `real-fallback` enter Mock Whisper only for missing official subtitles or unsupported official subtitle formats.
- Keep platform access failures, network failures, and generic transcript failures from entering fallback.
- Keep audio acquisition, ffmpeg processing, and real Whisper execution out of this stage.

Validation target:

- Unit tests cover official success, eligible fallback, non-eligible failures, stable attempted providers, and Mock Whisper output.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0c1 Mock Audio Processing Boundary` implementation in progress.

Changes:

- Add Mock audio acquisition boundary.
- Add Mock audio normalization boundary.
- Route eligible `real-fallback` cases through Mock audio and Mock normalizer before Mock Whisper.
- Keep official subtitle success, platform access failures, network failures, and generic transcript failures from triggering audio processing.
- Keep real audio download, ffmpeg execution, cache handling, CLI flags, and real Whisper execution out of this stage.

Validation target:

- Unit tests cover mock audio and normalizer calls without network or media files.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0c2 Cache/Temp Safety Policy` implementation in progress.

Changes:

- Add Git ignore guardrails for runtime cache and media artifacts under `output/` and `cache/`.
- Record that audio acquisition, media download, and keeping audio cache require explicit user confirmation per stage.
- Record that signed URLs, cookies, tokens, auth headers, and sensitive query parameters must not enter logs, Markdown, raw metadata, transcript results, or error messages.
- Keep runtime behavior unchanged.

Validation target:

- Only documentation and `.gitignore` are changed.
- Unit tests and Mock CLI regression still pass.

## 2026-07-09

Status: `v0.5.0d ffmpeg Normalizer Boundary` implementation in progress.

Changes:

- Add a real ffmpeg audio normalizer boundary for existing local audio files.
- Normalize toward 16 kHz mono PCM WAV and return `NormalizedAudio`.
- Keep `real-fallback` on the existing Mock audio normalizer path.
- Keep YouTube access, real audio download, Whisper, Transcript API fallback, LLM, CLI flags, and pipeline changes out of this stage.

Validation target:

- Unit tests mock `shutil.which` and `subprocess.run`; no real ffmpeg execution is required.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0d2 Local ffmpeg Smoke Test` passed.

Validation:

- ffmpeg path: `D:\yt-dlp\ffmpeg.exe`
- ffprobe path: `D:\yt-dlp\ffprobe.exe`
- Input: local short audio file `F:\05_Music\test\20260709_205744.m4a`
- Output: ignored runtime artifact `output\cache\audio\20260709_205744-16k-mono.wav`
- Normalized audio: `wav`, mono, `16000 Hz`, `pcm_s16le`
- `NormalizedAudio`: `provider=ffmpeg_audio_normalizer`, `format=wav`, `sample_rate=16000`, `channels=1`, `temporary=True`
- `ffprobe` confirmed `codec_name=pcm_s16le`, `sample_rate=16000`, and `channels=1`.
- No YouTube access, media download, Whisper, Transcript API, or LLM execution occurred.
- No tracked file changes were produced by the smoke test; the generated WAV remains under ignored `output/cache/audio/`.

Next target:

- Continue planning the next explicit audio or Whisper integration stage without changing the default `real-fallback` Mock behavior.

## 2026-07-11

Status: Project documentation aligned with the current `v0.5.x Whisper Fallback` implementation.

Current implementation:

- Latest tagged release remains `v0.4.0 Official Transcript`.
- `v0.5.x` fallback policy, Mock Whisper fallback, Mock audio boundaries, cache safety policy, and ffmpeg normalizer boundary are complete.
- The local ffmpeg smoke test passed and verified 16 kHz mono `pcm_s16le` WAV output.
- The default `real-fallback` path still uses Mock audio normalization and Mock Whisper.

Not implemented:

- Real audio acquisition.
- Real ffmpeg processing in the default fallback chain.
- Real Whisper or faster-whisper execution.
- Transcript API fallback.
- LLM knowledge extraction.
- Automated Obsidian import/update behavior or external knowledge-base synchronization.

Next target:

- Plan the real audio acquisition boundary as a separate, explicitly permitted stage before integrating real local ASR.

## 2026-07-11

Status: `v0.5.2a YouTube Audio Acquisition Provider Boundary` implementation complete.

Changes:

- Added `YtDlpAudioProvider` using the yt-dlp Python API for a single YouTube audio-only artifact.
- Download permission defaults to disabled and is checked before loading or invoking yt-dlp.
- Disabled playlist, subtitle, automatic subtitle, thumbnail, configuration-file, and postprocessor behavior.
- Returned artifacts are temporary and must remain inside the supplied or system temporary destination directory.
- Kept `real-fallback`, pipeline, CLI, ffmpeg execution, Whisper, cache retention, and workspace cleanup unchanged.

Validation target:

- Unit tests mock yt-dlp and do not access the network or download media.
- Mock CLI regression remains unchanged.

## 2026-07-11

Status: `v0.5.2b AudioWorkspace` implementation complete.

Changes:

- Added a private temporary workspace context manager for registered `temporary=True` audio artifacts.
- Cleanup removes registered files in reverse order and only removes an empty workspace directory.
- Cleanup runs after business errors without masking the original error.
- User-owned local files, workspace-external files, directories, missing files, cache retention, and fallback integration remain outside the workspace cleanup scope.

Validation target:

- Unit tests use temporary test files only and do not access the network, yt-dlp, ffmpeg, or Whisper.
- Mock CLI regression remains unchanged.

## 2026-07-12

Status: `YtDlpAudioProvider` workspace validation ordering fix complete.

Changes:

- Validate a supplied workspace before importing the optional yt-dlp dependency.
- Keep invalid workspace errors stable regardless of whether yt-dlp is installed.
- Clarify the historical and current `AudioWorkspace` status in architecture documentation.

Validation target:

- Targeted provider tests and the full standard test suite pass without installing yt-dlp or accessing the network.

## 2026-07-12

Status: `v0.5.3a FasterWhisperBackend Boundary` implementation complete.

Changes:

- Added `FasterWhisperBackend` for existing `NormalizedAudio` inputs.
- Validate the input file before lazily importing the optional faster-whisper dependency.
- Map ordered faster-whisper segments into `TranscriptSegment` timestamps and text.
- Keep model construction, transcription, and lazy segment iteration behind stable sanitized local transcription errors.
- Preserve the Mock backend and keep the real backend disconnected from pipeline and `real-fallback` orchestration.

Validation:

- Mocked faster-whisper tests only; no dependency installation, model download, network access, ffmpeg, yt-dlp, or real ASR execution.
- Targeted Whisper tests passed: 15 tests.
- Full unit tests passed: 85 tests.
- Mock CLI regression passed with the existing Mock providers.

Remaining boundaries:

- faster-whisper is not installed and no model has been downloaded.
- Live local transcription is not validated.
- The current transcript result contract cannot represent detected language.
- Retained cache and live audio acquisition remain incomplete.
- Push of the existing local commit range is temporarily deferred by the current HTTPS/TLS environment; this is not a Video2Knowledge product defect.

## 2026-07-12

Status: `FasterWhisperBackend` exception sanitization fix complete.

Changes:

- Map non-`ImportError` dependency initialization failures to the stable `local transcription failed` error.
- Suppress underlying exception chains for dependency import, model construction, transcription, lazy iteration, segment access, and timestamp conversion failures.
- Preserve `KeyboardInterrupt`, `SystemExit`, and other control-flow exceptions outside the `Exception` hierarchy.
- Add mocked traceback sanitization, input gate, control-flow, and timestamp boundary coverage without installing or importing real faster-whisper.

Validation:

- Targeted Whisper tests passed: 25 tests.
- Full unit tests passed: 95 tests.
- Mock CLI regression passed with the existing Mock providers.

Remaining boundaries:

- Empty or fully filtered segment output remains `local transcription produced no segments`; a future approved live smoke test or fallback integration stage must validate the product semantics for pure-silence audio.
- faster-whisper installation, model acquisition, live transcription, pipeline integration, and `real-fallback` integration remain incomplete.

## 2026-07-12

Status: `v0.5.3b Faster-Whisper CPU Smoke Test` passed and `v0.5.3c` optional dependency adoption complete.

Validated environment:

- Windows with Python 3.13.7.
- `faster-whisper 1.2.1`, `ctranslate2 4.8.1`, `av 18.0.0`, and `huggingface-hub 1.23.0`.
- `Systran/faster-whisper-small`, CPU, `int8`, and `language=None`.
- Existing 5.482688-second 16 kHz mono PCM WAV input.

Result:

- Backend end-to-end time was 39.169 seconds and included first model acquisition, loading, and transcription; it is not a stable benchmark.
- Returned one non-empty segment from `00:00:00.000` to `00:00:05.000`.
- Provider and attempted providers were both `faster_whisper`.
- Input audio hash and tracked Git worktree were unchanged.
- No GPU, CUDA, VAD, batch mode, pipeline integration, or accuracy evaluation was used.
- Model cache was approximately 463.70 MiB. Windows symlink degradation did not block execution but may increase disk use.

Packaging:

- Added the optional `asr` extra with `faster-whisper==1.2.1`.
- Base installation still installs only the existing core dependencies.
- Model files are not packaged; acquisition and caching remain separate first-use or preparation behavior.
- The smoke-test cache location remains experimental and is not a formal product cache policy.

Validation:

- Full unit tests passed: 95 tests on the project-standard Python 3.13.7 interpreter.
- Mock CLI regression passed with the existing Mock providers.
- Editable `.[asr]` pip dry-run recognized `faster-whisper==1.2.1` and the already installed validated runtime without planning dependency uninstall or downgrade.

Remaining boundaries:

- `FasterWhisperBackend` is not connected to pipeline or `real-fallback`.
- Formal local-file-to-real-ASR orchestration is not implemented.
- Live YouTube audio acquisition and retained audio cache remain incomplete.
- `TranscriptResult` has no detected-language field.
- Pure-silence semantics and exact half-millisecond timestamp rounding are not formal product contracts.
- GPU/CUDA and formal model-cache location, lifecycle, and cleanup remain unvalidated or undesigned.

## 2026-07-12

Status: `v0.5.4a Local File ASR Orchestration` implementation complete.

Changes:

- Added `transcribe_local_media` in `app.pipeline` for composing a local file provider, private audio workspace, normalizer, and caller-supplied Whisper backend.
- Keep the user-owned source artifact outside workspace ownership and require normalized output registration before transcription.
- Return the backend `TranscriptResult` unchanged so audio and normalizer ids do not enter transcript provider history.
- Add best-effort cleanup for only the newly calculated ffmpeg output after timeout, startup `OSError`, or non-zero exit.
- Preserve stable acquisition, processing, transcription, and cleanup errors without adding an orchestration-level exception.

Validation:

- Mocked orchestration tests use temporary placeholder files only and do not run real ffmpeg, faster-whisper, or network access.
- Targeted local ASR orchestration tests passed: 16 tests.
- Full unit tests passed: 111 tests.
- Existing Mock CLI regression passed.

Remaining boundaries:

- The orchestration is not exposed by CLI and is not connected to `real-fallback` or the default import pipeline.
- A complete real local-file-to-ASR integration smoke test has not run.
- YouTube live audio acquisition, retained audio cache, and formal model-cache management remain incomplete.
- Detected-language, pure-silence, and exact timestamp-rounding contracts remain unchanged and unresolved.

## 2026-07-12

Status: Local-file ASR ownership boundary fix complete.

Changes:

- Enforce local metadata before provider or workspace creation.
- Require provider output to be an existing regular user-owned `temporary=False` artifact.
- Reject temporary and network-style acquisition artifacts before normalization.
- Give orchestration limited provisional ownership of the exact normalized workspace output and clean only that object when registration fails.
- Preserve external paths, symlink targets, non-empty directories, unknown files, registration errors, business errors, and control-flow exceptions according to the existing ownership boundary.

Validation:

- Local ASR orchestration tests passed: 25 tests, with one filesystem symlink-escape test skipped because symlink creation is unavailable in the current Windows environment; deterministic source-symlink rejection and workspace-external escape tests passed.
- Mocked ffmpeg tests passed: 9 tests.
- Full unit tests passed: 120 tests, with the same one filesystem symlink-escape test skipped.
- No real ffmpeg, faster-whisper, model, media download, or network operation was used.

Remaining boundaries:

- The orchestration remains absent from CLI and `real-fallback`.
- A separately approved real local-file-to-ASR integration smoke test remains pending.

## 2026-07-17

Status: Real non-CLI local-file-to-ASR integration smoke test passed.

Validation:

- On Windows with Python 3.13.7, a user-owned AAC M4A input (48 kHz, stereo,
  about 5.51 seconds) entered the formal `transcribe_local_media()` path.
- The default `LocalFileAudioProvider`, private `AudioWorkspace`, real
  `FfmpegAudioNormalizer`, and `FasterWhisperBackend` with
  `Systran/faster-whisper-small`, CPU `int8`, and `language=None` returned a
  `TranscriptResult` with provider and attempted providers both set to
  `faster_whisper` and one segment from `00:00:00.000` to `00:00:05.000`.
- The source SHA-256 was unchanged. The normalized temporary 16 kHz mono WAV
  existed during Whisper execution and the normalized artifact and workspace
  were removed on return.
- The observed 9.217-second elapsed time used an existing offline model cache
  on one short sample; it is neither a stable benchmark nor an accuracy result.
- Project-standard validation passed. The current suite runs 120 tests, with
  one platform-dependent symlink test skipped when Windows cannot create it.

Remaining boundaries:

- No supported CLI local-ASR entry point exists; installing `.[asr]` does not
  enable one.
- The default import pipeline and `real-fallback` remain Mock-only for audio and
  ASR. The smoke test does not validate YouTube live audio acquisition or a
  YouTube no-subtitle-to-Whisper fallback.
- Retained cache, detected-language contract, pure-silence semantics,
  half-millisecond timestamp rules, GPU/CUDA, VAD, batch mode, formal model
  cache lifecycle, and LLM knowledge extraction remain incomplete.

## 2026-09-18

Status: `v0.5.x Provider Input and Error Boundary Hardening` implementation
complete.

Changes:

- Replaced platform domain substring matching with exact hostname matching
  (`urlparse(...).hostname`, lowercase, trailing-dot stripping, userinfo and
  empty-host rejection). Suffix-confusion hosts such as `notyoutube.com` and
  `youtube.com.evil.test` are no longer misclassified as YouTube.
- Mapped yt-dlp metadata extraction failures to the stable
  `yt-dlp metadata extraction failed` error without underlying exception text
  or cause. Missing-dependency and metadata shape errors remain separate.
- Minimized `VideoMetadata.raw_metadata` to
  `{"provider": "yt-dlp", "subtitles": {...}}` with a per-track allowlist of
  `url`, `ext`, `protocol`, and `format`.
- Added offline subtitle URL validation (HTTPS-only, hostname required, no
  userinfo, port empty or `443`, restricted literal IPs rejected via
  `ipaddress`) before any network callable, and applied the same validation to
  redirect targets through a custom `HTTPRedirectHandler`.
- Bounded subtitle response reads to 16 MiB (`MAX_SUBTITLE_RESPONSE_BYTES`)
  with pre-read `Content-Length` rejection and `limit + 1` body reads.
- Mapped unknown charsets, charset lookup failures, and decode failures to a
  stable encoding error, removed underlying exception causes from all public
  subtitle fetch errors, and preserved `KeyboardInterrupt` and `SystemExit`.

Validation:

- New offline security regression suite passed: 36 tests in
  `tests/test_provider_security.py`.
- Full unit tests passed: 156 tests, with the same one pre-existing Windows
  symlink-escape test skipped because symlink creation is unavailable in this
  environment.
- Mock CLI regression passed with the default Mock providers.
- No network access, real YouTube, real yt-dlp, real subtitle fetch, real
  ffmpeg, real faster-whisper, media download, or dependency change occurred.

Remaining boundaries:

- CLI command surface, fallback eligibility, provider ids, and
  `attempted_providers` behavior are unchanged.
- Local ASR CLI, default `real-fallback` real ASR, YouTube live audio
  acquisition, retained cache, model cache policy, YAML Frontmatter
  hardening, template packaging/path hardening, exporter overwrite policy,
  and LLM extraction remain incomplete.

## 2026-09-19

Status: `v0.5.x Provider Boundary Remediation and Acceptance` implementation
complete, pending independent re-review.

Changes:

- Replaced the standard library's unbounded redirect-body drain with a
  bounded read of at most `MAX_SUBTITLE_RESPONSE_BYTES + 1` in a custom
  `http_error_30x` override; 301, 302, 303, 307, and 308 share one policy.
  Oversized redirect bodies map to the stable `response too large` error, the
  current response is closed on safe, unsafe, oversized, and
  parent-opener-failure paths, and redirect rejection errors never expose the
  `Location` URL, query, userinfo, headers, or body.
- Extended the subtitle URL validator with offline legacy numeric IPv4
  recognition (`socket.inet_aton`) so forms such as `127.1`, `2130706433`,
  and `0x7f000001` are rejected under the same loopback/private rules;
  numeric-looking hosts that cannot be proven safe fail closed. The identical
  validator covers initial URLs and redirect targets.
- Made `youtu.be` exact-host only so no `*.youtu.be` subdomain gains YouTube
  capabilities, and mapped unknown hostnames colliding with reserved platform
  ids (for example `https://youtube/x` or `https://user@youtube/x`) to the
  safe `unknown` label with no provider capabilities.
- Restricted minimal subtitle metadata to string values only for the
  `url`/`ext`/`protocol`/`format` allowlist, dropping nested dict/list values
  and any shared references with provider-owned objects.
- Injected a module-private quiet logger through `ydl_opts["logger"]` so raw
  yt-dlp output cannot reach stdout/stderr before the sanitized extraction
  error.

Validation:

- `tests/test_provider_security.py` grew from 36 to 50 fully offline tests,
  including real redirect handler dispatch coverage.
- Full unit test suite passes with one pre-existing Windows symlink-escape
  skip; Mock CLI regression passed; `compileall` passed.
- No network access, real YouTube, real yt-dlp, real subtitle fetch, real
  ffmpeg, real faster-whisper, media download, or dependency change occurred.

Remaining boundaries:

- DNS rebinding remains out of scope and unresolved.
- Real network provider behavior remains unverified; all evidence is mocked
  or offline probes.
- CLI command surface, fallback eligibility, provider ids, and
  `attempted_providers` behavior are unchanged.

## 2026-09-19 Provider Authority Normalization Remediation

An independent review rejected the previous completion claim because the
subtitle URL validator inspected `urlparse(...).hostname` while the HTTP
request layer normalizes the authority further. The gap was reproduced
offline, fixed, and covered by new offline tests.

What changed:

- The validator now validates the hostname the request layer would actually
  use. `_normalized_request_host` rejects any percent encoding inside the
  authority instead of decoding it, drops trailing DNS root dots, and
  requires the host to survive an explicit IDNA to ASCII conversion, failing
  closed when it cannot. Percent encoding in the path and query (where signed
  subtitle URLs carry their signature) is unaffected.
- The literal-IP, legacy numeric IPv4, and numeric-looking fail-closed rules
  now run on that normalized host, so `https://127%2e0%2e0%2e1/`,
  `https://%31%32%37.0.0.1/`, `https://127.0.0.1./`, `https://127.1./`,
  `https://2130706433./`, `https://127。0。0。1/`, and `https://１２７.０.０.１/`
  are all rejected before any network callable, while ordinary DNS hostnames,
  public IPv4/IPv6 literals, and a trailing root dot on a real name still work.
- Initial URLs and redirect targets share the one validator. The redirect
  handler also validates the raw `Location` before the standard library
  quotes it with latin-1, so a raw target that is already an unsafe absolute
  URL, or that is not an absolute HTTPS URL at all, is rejected before the
  parent opener is reached and before its body is read. This holds for 301,
  302, 303, 307, and 308. (Relative targets were over-rejected and a
  non-latin-1 absolute target still failed as a raw `UnicodeError`; both are
  corrected in the entry below.)
- The HTTP status error path reads the status code, closes the error response
  without reading the body, and swallows a failing close so it cannot replace
  the stable `official subtitle VTT fetch failed: HTTP Error <status>` error.
  No URL, header, body, or underlying exception is exposed, and
  `KeyboardInterrupt` and `SystemExit` still propagate unchanged.

Validation:

- `tests/test_provider_security.py` grew from 50 to 64 fully offline tests.
- Full unit test suite: 184 tests executed, 183 passed, and one pre-existing
  Windows symlink-escape test was skipped; Mock CLI regression passed; `compileall` passed;
  `git diff --check` passed.
- No network access, real YouTube, real yt-dlp, real subtitle fetch, real
  ffmpeg, real faster-whisper, media download, or dependency change occurred.

Remaining boundaries:

- DNS rebinding and resolver-level differences remain out of scope.
- Real network provider behavior remains unverified; every statement above is
  backed by offline tests only, and this is not a complete SSRF defense.
- CLI command surface, fallback eligibility, provider ids, and
  `attempted_providers` behavior are unchanged.

## 2026-09-19 Provider Boundary Finalization

An independent review rejected the previous completion claim again, leaving
four findings in the same boundary. All four were reproduced offline first,
then fixed, with every earlier change kept in place.

What changed:

- The reserved `localhost` namespace is rejected after IDNA normalization and
  trailing-dot removal, for initial URLs and redirect targets alike:
  `https://localhost/`, `https://localhost./`, `https://x.localhost/`,
  `https://a.b.localhost/`, and the full-width (`ｌｏｃａｌｈｏｓｔ`) and
  upper-case spellings that normalize onto them no longer reach the opener.
  Names that merely contain the label (`localhost.example.com`,
  `notlocalhost.example.com`) still work.
- An authority containing an ASCII control character or DEL fails closed.
  Before the fix, `https://example.com\x00.evil/sub.vtt` passed IDNA's ASCII
  fast path unchanged and `socket.inet_aton` raised
  `ValueError("embedded null character")` from inside the validator, which
  runs outside the `fetch_text` conversion block. `_ip_literal_address` now
  maps the expected `ValueError` and `OSError` to a safe validation failure,
  the validator fails closed on any unexpected parse failure, and
  `KeyboardInterrupt`/`SystemExit` still propagate unchanged. (The rule as
  written here applied to the *parsed* authority only, which left raw tab, CR,
  and LF in the URL string itself; the section below closes that gap.)
- Redirect targets are validated as the effective absolute target: the raw
  `Location` is parsed, given a `/` path when authority-only, re-serialized,
  percent-encoded with latin-1, and `urljoin`-ed against the source request
  URL exactly as `urllib.request` does. Safe relative (`/next.vtt`,
  `../next.vtt`, `next.vtt`, `?sig=abc`) and scheme-relative
  (`//cdn.example.com/next.vtt`, `//8.8.8.8/next.vtt`) redirects from an HTTPS
  source are accepted again, while `//127.0.0.1/next.vtt`,
  `//127.1/next.vtt`, `//localhost/next.vtt`, `//x.localhost/next.vtt`,
  encoded authorities, `http`/`file`/`ftp`/`data` targets, userinfo, and
  non-`443` ports stay rejected. `redirect_request` keeps its second
  validation of the absolute target.
- A redirect target that cannot be quoted, encoded, or resolved now maps to
  `official subtitle VTT fetch failed: unsafe URL` inside the handler instead
  of raising a raw `UnicodeError`. Rejected redirects call no parent opener,
  read no body, and close the response; safe ones still perform the bounded
  16 MiB redirect read and call the parent exactly once.

Validation:

- `tests/test_provider_security.py` grew from 64 to 76 fully offline tests,
  all driven through `fetch_text` or the real `http_error_30x` dispatch.
- Full unit test suite: 196 tests executed, 195 passed, and one pre-existing
  Windows symlink-escape test was skipped; Mock CLI regression passed; `compileall` passed;
  `git diff --check` passed.
- No network access, DNS lookup, real YouTube, real yt-dlp, real subtitle
  fetch, real ffmpeg, real faster-whisper, media download, or dependency
  change occurred.

Remaining boundaries:

- DNS rebinding and resolver-level time-of-check/time-of-use differences remain
  out of scope, and this is not a complete SSRF defense.
- Real network provider behavior remains unverified; every statement above is
  backed by offline tests only.
- CLI command surface, fallback eligibility, provider ids, and
  `attempted_providers` behavior are unchanged.

## 2026-09-19 Provider Boundary Closure

An independent review rejected the Finalization completion claim as well,
leaving two runtime findings and one documentation number. Both findings were
reproduced offline first, then fixed, with every earlier change kept in place.

What changed:

- Raw control characters now fail closed *before* any parsing, for the initial
  URL and for the raw redirect `Location` alike. `urlparse` removes tab, CR,
  and LF from the whole URL before it splits the authority off, so the
  authority-level rule added by the previous round never saw those three:
  `https://exa\tmple.com/sub.vtt` and its CR and LF variants all reached the
  mocked opener. Any ASCII control character or DEL anywhere in the raw string
  — authority, path, or query — is now refused with the stable
  `official subtitle VTT fetch failed: unsafe URL`, without calling the
  opener, reading a redirect body, or calling the parent opener. Legal percent
  encoding in the path and query is untouched.
- Redirect cleanup is now best-effort. The `finally: bounded_body.close()` in
  the redirect handler let an ordinary `close()` failure replace whatever it
  ran alongside: the stable `unsafe URL` and `response too large` errors, a
  `URLError`/platform/network failure from the parent opener, a successful
  redirect result, and a propagating `KeyboardInterrupt`/`SystemExit`. One
  module-internal helper now swallows ordinary close failures at the redirect
  cleanup site, inside `_BoundedRedirectBody.close`, and on the HTTP status
  error path, so the HTTPError and redirect policies are literally the same
  policy. Cleanup is idempotent because the standard library closes a
  successfully followed redirect response itself; `KeyboardInterrupt` and
  `SystemExit` raised by `close()` still propagate unchanged, and close text
  never reaches a public error or a traceback.

Validation:

- `tests/test_provider_security.py` grew from 76 to 86 fully offline tests, all
  driven through `fetch_text` or the real `http_error_30x` dispatch.
- Red phase recorded before any runtime edit: `Ran 86 tests` /
  `FAILED (failures=53, errors=21)` from eight methods — seven of the ten new
  ones plus the rewritten whitespace-tolerance test. The two new methods that
  passed before the fix guard it against catching `BaseException` around
  cleanup.
- Full unit test suite: 206 tests executed, 205 passed, 1 skipped (the
  pre-existing Windows symlink-escape case); Mock CLI regression passed;
  `compileall` passed; `git diff --check` passed.
- No network access, DNS lookup, real YouTube, real yt-dlp, real subtitle
  fetch, real ffmpeg, real faster-whisper, media download, or dependency
  change occurred.

Remaining boundaries:

- DNS rebinding and resolver-level time-of-check/time-of-use differences remain
  out of scope, and this is not a complete SSRF defense.
- Real network provider behavior remains unverified; every statement above is
  backed by offline tests only.
- CLI command surface, fallback eligibility, provider ids, and
  `attempted_providers` behavior are unchanged.
