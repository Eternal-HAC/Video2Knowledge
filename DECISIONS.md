# DECISIONS

## 2026-07-05

Decision:
Use a Mock-only first stage before integrating real video, transcript, Whisper, LLM, and export providers.

Reason:
The project needs a stable end-to-end pipeline and module boundary before external integrations add operational complexity.

Alternatives:
Start directly with yt-dlp, youtube-transcript-api, faster-whisper, and LLM provider integrations.

Impact:
The first stage can be validated locally without network installs or API credentials.

Follow-up Review:
Revisit when the Mock CLI, Markdown output, and tests are stable.

## 2026-07-05

Decision:
Keep generated knowledge notes as structured Markdown with YAML Frontmatter.

Reason:
Markdown is portable, Git-friendly, Obsidian-friendly, and suitable for later Notion or Feishu export.

Alternatives:
Store data first in a database or a proprietary note format.

Impact:
The core output contract is easy to inspect and test.

Follow-up Review:
Revisit if batch processing requires a richer intermediate data format.

## 2026-07-05

Decision:
Use only Python standard library in the Mock MVP.

Reason:
The current stage must avoid network installation and real external dependencies.

Alternatives:
Use Typer, Jinja2, PyYAML, and Pydantic immediately.

Impact:
The initial implementation is simpler but has a minimal template renderer and manual YAML output.

Follow-up Review:
Revisit when real provider integrations are introduced.

## 2026-07-05

Decision:
Use `app/` as the Stage 1 source directory.

Reason:
The user-provided initialization checklist names files such as `app/cli.py`, and the Mock MVP benefits from a simple, direct structure while the project shape is still early.

Alternatives:
Start immediately with a packaging-oriented `src/video2knowledge/` layout.

Impact:
The initial code is easy to inspect and run with `python -m app.cli`, but the package layout may need revision before distribution.

Follow-up Review:
If Video2Knowledge needs formal packaging or publishing, evaluate migrating to `src/video2knowledge/`.

## 2026-07-05

Decision:
Introduce platform and transcript provider boundaries before real integrations.

Reason:
The next stage needs a stable place to plug in YouTube, local files, subtitle APIs, and Whisper without mixing provider-specific code into the CLI.

Alternatives:
Call real provider libraries directly from the CLI when each feature is added.

Impact:
The CLI remains stable while implementation modules can be replaced incrementally.

Follow-up Review:
Revisit after the first real YouTube metadata and subtitle implementation is added.

## 2026-07-05

Decision:
Expose provider selection flags before implementing real providers.

Reason:
The CLI can keep a stable shape while non-Mock providers fail clearly instead of silently pretending to work.

Alternatives:
Hide provider selection until real integrations are complete.

Impact:
Users and tests can see the planned replacement points, but only `mock` is valid for successful runs right now.

Follow-up Review:
Remove or revise placeholder behavior when `yt-dlp` metadata and the transcript fallback chain are implemented.

## 2026-07-05

Decision:
Add a pipeline layer and platform capabilities before implementing YouTube metadata.

Reason:
Real provider integration should not make the CLI own business orchestration or platform-specific branching.

Alternatives:
Start `yt-dlp` integration directly inside the existing CLI flow.

Impact:
The CLI remains thin, provider replacement points stay centralized, and platform support can grow without immediate large rewrites.

Follow-up Review:
Revisit when YouTube metadata is implemented and the first real provider behavior is known.

## 2026-07-05

Decision:
Delay splitting transcript fallback into separate real providers.

Reason:
The current stage is still Mock-only. Official subtitles, transcript API, and Whisper will have different inputs and failure modes that should be modeled when they are implemented.

Alternatives:
Create `OfficialSubtitleProvider`, `TranscriptApiProvider`, and `WhisperProvider` immediately.

Impact:
The transcript abstraction stays lightweight now, while the architecture document records the planned split.

Follow-up Review:
Split the providers during the real subtitle stage.

## 2026-07-05

Decision:
Keep real providers stateless and data-only; keep business orchestration in the pipeline and CLI lightweight.

Reason:
As provider count grows, business logic can easily scatter across metadata, transcript, Whisper, LLM, and export modules. Providers should fetch data and return typed results. The pipeline should decide how those results move through the workflow.

Alternatives:
Allow each provider to perform downstream behavior such as writing Markdown, calling LLMs, fetching unrelated data, or exporting notes.

Impact:
Provider implementations stay easier to test and replace. CLI stays focused on user input and output. Pipeline remains the single place for business flow.

Follow-up Review:
Revisit when the first real provider, YouTube metadata, is implemented.

## 2026-07-05

Decision:
Implement `v0.3.x Real Metadata` as YouTube metadata only through `yt-dlp`, with no media download or transcript work.

Reason:
The first real provider should prove the metadata boundary and mapping before adding subtitles, Whisper, LLM, or export complexity.

Alternatives:
Use `yt-dlp` to download media, fetch subtitles, and populate multiple pipeline stages at once.

Impact:
The project gains its first real data capability while preserving the stage rule: one stage, one problem.

Follow-up Review:
After user-approved installation and live smoke testing, decide whether to tag `v0.3.0`.

## 2026-07-06

Decision:
Implement `v0.4.x Official Transcript` as YouTube official VTT/WebVTT subtitles only.

Reason:
Official subtitles are the next reliable data source after metadata. Keeping this stage VTT/WebVTT-only avoids mixing transcript API fallback, automatic captions, Whisper, or format conversion into the first real transcript provider.

Alternatives:
Use automatic captions when official subtitles are missing, add `youtube-transcript-api`, parse json3/SRT/TTML/XML, or call Whisper in the same stage.

Impact:
The provider has a narrow contract: read official subtitle tracks from `yt-dlp` metadata, choose a supported VTT/WebVTT track, parse it into `TranscriptSegment`, and fail clearly when official VTT subtitles are unavailable.

Follow-up Review:
After local tests pass, run a user-approved live YouTube official subtitle smoke test before tagging `v0.4.0`.

## 2026-07-06

Decision:
Sanitize official subtitle VTT fetch failures before they reach the CLI.

Reason:
Live validation can fail because of environment or platform rate limits such as YouTube HTTP 429. These failures should be reported clearly without leaking subtitle URLs, signatures, tokens, cookies, or temporary credentials.

Alternatives:
Expose raw urllib exceptions, retry automatically, use cookies or login state, or fall back to automatic captions.

Impact:
The provider keeps the same official VTT/WebVTT-only boundary while CLI errors remain concise and safe. Live VTT parsing validation can be retried later when rate limiting clears.

Follow-up Review:
Re-run the official subtitle smoke test only after user confirmation and a recovered network environment.

## 2026-07-08

Decision:
Keep Video2Knowledge's primary output as structured Markdown knowledge notes. Treat cangjie-skill-style method-card or skill-pack generation as a future optional advanced export.

Reason:
cangjie-skill is a useful downstream reference for turning long-form content into executable AI Skills, but Video2Knowledge still needs to stabilize acquisition, transcript, Whisper fallback, and base LLM extraction first. Skill-pack generation would mix a downstream product layer into the current provider and transcript stages.

Alternatives:
Add skill-pack output directly to `v0.4.x`, `v0.5.x`, or the first LLM extraction stage.

Impact:
The project keeps a clear staged architecture: source acquisition and transcript first, structured Markdown as the durable local artifact, knowledge extraction next, and optional skill-pack or method-card export only after the base pipeline is reliable.

Follow-up Review:
Revisit during or after `v0.6.x Knowledge Extraction`, after Whisper fallback and basic LLM extraction are stable.

## 2026-07-08

Decision:
Only missing official subtitles and unsupported official subtitle formats are eligible for future Whisper fallback.

Reason:
Platform and network access failures are not evidence that a video lacks subtitles. Falling back to audio download when YouTube returns HTTP 429, HTTP 403, timeout, or network errors would blur provider errors with content absence and could trigger unintended media downloads.

Alternatives:
Treat every official subtitle failure as a reason to run Whisper, or keep all transcript failures under a single generic `TranscriptProviderError`.

Impact:
`v0.5.0a` defines `NoOfficialSubtitleError`, `UnsupportedSubtitleFormatError`, `PlatformAccessError`, and `NetworkAccessError`. `real-fallback` can validate the policy but still does not download audio or run Whisper.

Follow-up Review:
Use this policy in `v0.5.0b` when adding the mock Whisper fallback pipeline.

## 2026-07-08

Decision:
Use a deterministic Mock local Whisper backend before adding audio acquisition, ffmpeg, or real Whisper execution.

Reason:
The fallback orchestration should be validated separately from media download, local processing dependencies, model installation, and transcription runtime behavior.

Alternatives:
Connect `real-fallback` directly to audio download and faster-whisper after the fallback policy stage.

Impact:
`real-fallback` can now prove the official-subtitles-to-Whisper control flow while remaining fully local, deterministic, and dependency-free. Audio acquisition and real transcription remain separate stages.

Follow-up Review:
Use the stable Mock fallback path when designing the audio acquisition and ffmpeg boundary.

## 2026-07-09

Decision:
Add Mock audio acquisition and Mock audio normalization boundaries before implementing cache handling, real audio download, or ffmpeg execution.

Reason:
The fallback chain should prove where audio acquisition and normalization belong without introducing media files, filesystem cleanup, ffmpeg availability checks, or network behavior.

Alternatives:
Add real `yt-dlp` audio download and ffmpeg normalization directly after the Mock Whisper fallback stage.

Impact:
`real-fallback` now has a visible audio processing boundary while preserving the existing transcript-level `attempted_providers` contract. The project can test fallback orchestration without creating media artifacts.

Follow-up Review:
Define cache/temp handling and explicit audio download confirmation before any real media acquisition is implemented.

## 2026-07-09

Decision:
Restrict runtime cache and media artifact ignore rules to `output/` and `cache/`, and require explicit confirmation for audio acquisition, media download, and keeping audio cache.

Reason:
The project needs guardrails before real media work, but global media extension ignores would make it easy to accidentally exclude legitimate future fixtures or documentation assets.

Alternatives:
Ignore every media extension globally, or defer cache and media artifact policy until real audio download is implemented.

Impact:
Future runtime media outputs are protected from accidental commits while source assets outside runtime directories can still be intentionally tracked. Real audio acquisition remains opt-in and must not leak signed URLs, cookies, tokens, auth headers, or sensitive query parameters.

Follow-up Review:
Use this policy when adding the real audio acquisition boundary and future `--allow-audio-download` / `--keep-audio-cache` behavior.

## 2026-07-09

Decision:
Add a real ffmpeg audio normalizer boundary before wiring ffmpeg into the default transcript fallback path.

Reason:
ffmpeg command construction, output overwrite safety, timeout handling, and sanitized error mapping should be validated separately from audio download and Whisper transcription.

Alternatives:
Wire ffmpeg directly into `real-fallback`, or wait to implement ffmpeg until the faster-whisper stage.

Impact:
The project can normalize existing local audio files through a tested boundary while `real-fallback` remains deterministic and Mock-only by default.

Follow-up Review:
Run a separate user-confirmed local ffmpeg smoke test before using the boundary with real audio.

## 2026-07-11

Decision:
Define Video2Knowledge as a Local First video-to-knowledge pipeline and make the `v1.0` product boundary a complete path from a supported YouTube URL or local media file to structured Markdown.

Reason:
The product should be judged by whether it creates durable local knowledge artifacts, not by whether it resembles a downloader, standalone transcription script, or generic chat summarizer. A useful `v1.0` nevertheless requires the supporting capabilities that complete that knowledge workflow: necessary and explicitly permitted media acquisition, ffmpeg normalization, local ASR fallback, LLM knowledge extraction, and local or Obsidian-friendly export.

Alternatives:
Exclude media acquisition, local ASR, or LLM extraction from `v1.0`; position the product as a downloader, Whisper wrapper, or generic summary tool; or include browser, mobile, multi-platform ingestion, cloud sync, and skill generation in the first production milestone.

Impact:
`v1.0` includes clean YouTube URL input, local video/audio input, metadata, official subtitles first, explicitly permitted audio acquisition when needed, ffmpeg normalization, local Whisper/faster-whisper fallback, `TranscriptResult`, replaceable LLM knowledge extraction, structured Markdown, and local or Obsidian-friendly export. It excludes all-platform support, full Bilibili support, arbitrary-web ingestion, browser and mobile applications, authenticated course capture, DRM circumvention, cookie/session ingestion by default, skill generation, SaaS accounts, billing, and cloud synchronization.

Follow-up Review:
Review the boundary at the end of `v0.6.x Knowledge Extraction` before finalizing the remaining `v1.0` export and production-readiness work.

## 2026-07-11

Decision:
Keep basic URL intake in `v1.0`, and defer broad platform normalization, browser capture, and mobile processing to later versions.

Reason:
The current pipeline needs a reliable clean YouTube URL path, not a generic ingestion framework. Share-text parsing, tracking cleanup, short-link handling, multi-platform recognition, browser capture, and mobile processing add separate product, security, and platform concerns.

Alternatives:
Add full URL normalization and browser or mobile capture during `v0.5.x`, or require users to manually download every video before import.

Impact:
`v1.0` performs minimum validation for clean YouTube URLs and accepts local media directly. `v1.x` may add share-text extraction, tracking cleanup, position-parameter preservation, Chinese and mobile link handling, Bilibili adapters, and an authorized browser capture layer. Mobile remains an input and reading surface first, while ffmpeg, ASR, and knowledge processing run primarily on a PC or local service.

Follow-up Review:
Revisit after the core `v1.0` pipeline is stable and platform expansion becomes an explicit stage.

## 2026-07-11

Decision:
Describe cost boundaries by processing stage and support replaceable user-controlled LLM providers without promising universally zero-cost operation.

Reason:
Metadata, subtitles, ffmpeg, local ASR, and LLM extraction have different resource profiles. Local execution can avoid cloud LLM tokens but still consumes compute, storage, time, networking, and potentially third-party services.

Alternatives:
Treat every stage as an LLM cost, promise all-local operation is always free, or bind the product to one hosted LLM provider.

Impact:
Metadata, subtitle acquisition, and ffmpeg do not consume LLM tokens. Local Whisper/faster-whisper consumes local resources. Token cost begins primarily at knowledge extraction. The provider boundary can support user-provided API keys and future local or open-source models, while product documentation avoids absolute cost claims.

Follow-up Review:
Specify concrete provider configuration and cost visibility during `v0.6.x Knowledge Extraction`.

## 2026-07-11

Decision:
Keep `AudioProvider.acquire(metadata)` and `AudioArtifact.temporary` unchanged while adding `LocalFileAudioProvider`.

Reason:
The current metadata contract already carries the local input path through `source_url`, and the local provider only needs to validate and expose that user-owned file. Introducing an acquisition request object, lifecycle enum, workspace manager, or permission-specific exception before any network download exists would add abstractions without current behavior to support them.

Alternatives:
Introduce `AudioAcquisitionRequest`, replace `temporary` with a lifecycle enum, or build cache and cleanup orchestration during the local file boundary stage.

Impact:
`LocalFileAudioProvider` returns an `AudioArtifact` with provider id `local_file_audio` and `temporary=False`. It never copies, modifies, deletes, decodes, or cleans up the source file. Files without extensions use `format="unknown"`. The existing Mock audio path and default `real-fallback` behavior remain unchanged.

Follow-up Review:
Re-evaluate the request and lifecycle models when a real `yt_dlp_audio` provider introduces temporary downloads and explicitly retained cache.

## 2026-07-11

Decision:
Document `yt_dlp_audio` as a future explicitly permitted provider without adding a placeholder implementation.

Reason:
A placeholder class would not validate real download behavior and could imply that network acquisition is available. Permission gating, temporary workspace ownership, cleanup, cache retention, and sanitized yt-dlp failures should be designed against the actual implementation stage.

Alternatives:
Add a provider class that always raises not implemented, or implement yt-dlp audio download in `v0.5.0e`.

Impact:
This stage remains local-only. Future network acquisition must default to disabled, require explicit user permission, create temporary artifacts by default, require separate confirmation to retain cache, and avoid exposing signed URLs, cookies, tokens, auth headers, sensitive query parameters, or raw yt-dlp errors.

Follow-up Review:
Implement and review these requirements in the separate network audio acquisition stage.

## 2026-07-11

Decision:
Define the future `yt_dlp_audio` contract before implementing network-backed audio acquisition.

Reason:
Real acquisition introduces explicit user permission, temporary workspace ownership, cache retention, cleanup on failure, and credential-bearing provider errors. These rules must be stable before any download behavior is added or connected to `real-fallback`.

Alternatives:
Implement yt-dlp audio download first and derive lifecycle rules from the implementation, or add download permission directly to the CLI and pipeline in the same stage.

Impact:
The future provider keeps the existing `AudioProvider.acquire(metadata) -> AudioArtifact` contract. Provider configuration supplies `allow_audio_download`, `keep_cache`, workspace location, and timeout. Download permission defaults to false and is checked before network or filesystem side effects. Temporary acquisition returns `temporary=True`; separately approved retained cache returns `temporary=False`.

Follow-up Review:
Validate the contract with mocked backend tests before any user-approved live download test.

## 2026-07-11

Decision:
Assign cleanup ownership to a future `AudioWorkspace`, not to `AudioArtifact`, individual downstream providers, or user-owned local files.

Reason:
Acquisition, normalization, and transcription can fail independently. A single workspace owner can clean temporary artifacts reliably in a `finally` path without giving data objects destructive behavior or allowing one provider to delete another provider's external input.

Alternatives:
Add a `cleanup()` method to `AudioArtifact`, let each provider clean files opportunistically, or retain every downloaded and normalized artifact.

Impact:
The workspace cleans only files it created. `LocalFileAudioProvider` artifacts are never deleted. Default downloads and normalized outputs are temporary; cache retention requires separate explicit confirmation. Cleanup failures must remain sanitized and must not replace the original processing error.

Follow-up Review:
Implement `AudioWorkspace` together with the real acquisition provider so cleanup behavior is covered by success and failure tests.

## 2026-07-11

Decision:
Keep future network audio acquisition behind the existing transcript fallback eligibility policy and strict error sanitization.

Reason:
HTTP 429, HTTP 403, network failures, generic transcript failures, and metadata contract errors do not prove that subtitles are unavailable and must not trigger media download. yt-dlp may also expose signed URLs, credentials, query parameters, temporary paths, commands, or stderr through raw exceptions.

Alternatives:
Download audio after every subtitle failure, expose raw yt-dlp errors for debugging, or reuse signed URLs from metadata.

Impact:
Only an eligible missing-subtitle or unsupported-format result plus explicit download permission may enter future `yt_dlp_audio`. Errors use stable categories and never expose full commands, signed URLs, cookies, tokens, auth headers, query parameters, temporary credentials, temporary paths, raw yt-dlp exceptions, or stderr.

Follow-up Review:
Preserve these boundaries when real acquisition is integrated with ffmpeg and local Whisper in separate stages.

## 2026-07-11

Decision:
Implement a limited YouTube-only `YtDlpAudioProvider` before workspace lifecycle, cache retention, or fallback integration.

Reason:
The provider boundary needs real Python API option construction and sanitized error mapping, but a provider cannot safely determine when downstream normalization or transcription has finished using its returned artifact. Combining download behavior with cleanup ownership would make the first implementation stage too broad.

Alternatives:
Implement `AudioWorkspace` and retained cache in the same commit, expose yt-dlp as a generic all-platform provider, or connect acquisition directly to `real-fallback`.

Impact:
`YtDlpAudioProvider` supports only YouTube metadata and requires `allow_audio_download=True` before loading yt-dlp or invoking its backend. It requests one audio-only artifact through the yt-dlp Python API, disables playlists, subtitle and thumbnail writes, configuration files, and postprocessors, and returns `AudioArtifact(provider="yt_dlp_audio", temporary=True)`. The optional workspace is a caller-provided destination, not a lifecycle owner. Tests mock yt-dlp; no live network download is part of this stage.

Follow-up Review:
Add `AudioWorkspace` cleanup ownership and separately approved cache retention before integrating acquisition with ffmpeg, Whisper, or `real-fallback`.

## 2026-07-11

Decision:
Give `AudioWorkspace` ownership of only registered temporary artifacts in a private temporary directory.

Reason:
Temporary acquisition and normalization files need deterministic cleanup, while user-owned local files and unknown files must never be removed incidentally. A small context manager provides this ownership boundary without adding pipeline orchestration, cache retention, or lifecycle enums.

Alternatives:
Let each provider delete its own output, use recursive workspace deletion, add cleanup methods to data artifacts, or defer cleanup until full fallback integration.

Impact:
`AudioWorkspace` creates a unique temporary directory, accepts only existing regular files with `temporary=True` inside that directory, and removes registered files in reverse order before removing the empty directory. It suppresses cleanup failure when a business exception is already active; otherwise it raises a stable `AudioProcessingError`. `LocalFileAudioProvider` artifacts cannot be registered or deleted.

Follow-up Review:
Integrate the workspace with explicitly selected acquisition and normalization only in a separate stage, then design separately approved cache retention.

## 2026-07-12

Decision:
Limit `transcribe_local_media` to user-owned local source artifacts and give orchestration provisional ownership only of the exact normalized object returned inside its private workspace before registration.

Reason:
Temporary acquisition artifacts cannot safely outlive their acquisition owner, while a normalized object rejected during registration is not yet tracked by `AudioWorkspace`. Without an explicit boundary, local orchestration can leak downloaded source artifacts or unregistered workspace output.

Alternatives:
Allow arbitrary providers, recursively delete the workspace after registration failure, or leave every rejected normalized object for test or caller cleanup.

Impact:
The local entry point rejects non-local metadata and any source artifact that is temporary, missing, or not a regular file. On registration failure it best-effort cleans only the exact returned in-workspace file or empty directory. It does not scan, recurse, follow symlinks to external targets, remove unknown files, or claim output a normalizer created but did not return. Registration, business, and control-flow errors remain primary over cleanup failures.

Follow-up Review:
Validate the boundary with a separately approved real local-file-to-ASR integration smoke test before exposing it through CLI or `real-fallback`.

## 2026-07-12

Decision:
Implement `FasterWhisperBackend` as a lazy optional boundary over existing `NormalizedAudio` without connecting it to the pipeline or `real-fallback`.

Reason:
The project needs to validate input ordering, optional dependency loading, model arguments, segment mapping, and sanitized failures independently from dependency installation, model download, media acquisition, ffmpeg orchestration, and live ASR cost.

Alternatives:
Install and execute faster-whisper immediately, construct the model during backend initialization, or integrate the backend directly into `real-fallback` in the same stage.

Impact:
Backend construction has no file, model, network, or import side effects. Transcription validates the normalized audio file before importing faster-whisper, returns only the stable `faster_whisper` transcript provider id, and sanitizes model and iteration failures. The current result contract has no language field, so configured language is forwarded to faster-whisper while detected language remains outside the returned result.

Follow-up Review:
Review the transcript language contract before or during real fallback integration, and require separate approval for dependency installation, model acquisition, and live transcription validation.

## 2026-07-12

Decision:
Expose local ASR dependencies through an optional `asr` extra and pin `faster-whisper==1.2.1` at the current stage.

Reason:
Official subtitle and base Mock workflows do not need the heavier local ASR runtime or model resources. Version 1.2.1 is the only faster-whisper version currently validated end to end on Windows with Python 3.13.7, CTranslate2 4.8.1, PyAV 18.0.0, and the real small model. The project is still early enough that reproducibility is more valuable than an unvalidated broad version range.

Alternatives:
Add faster-whisper to base dependencies, use an unpinned or ranged ASR dependency, or package model files and cache policy with the Python dependency.

Impact:
Base installation remains lightweight, while `.[asr]` installs the validated Python runtime combination. Model files remain separate first-use or explicit preparation artifacts and are not part of repository packaging. A broader version range requires a later compatibility validation stage.

Follow-up Review:
Re-evaluate the exact pin after newer faster-whisper versions are tested, and design formal model acquisition and cache lifecycle separately from dependency packaging.

## 2026-09-18

Decision:
Constrain every provider-supplied subtitle URL (including redirect targets) to
an offline trust policy before any network callable: HTTPS-only, required
hostname, no userinfo, port empty or `443`, and literal IPs rejected when
loopback, private, link-local, multicast, reserved, or unspecified. Responses
are bounded to 16 MiB, and charset, decode, URL, size, and network failures
surface only as stable sanitized public errors without underlying exception
causes.

Reason:

Provider metadata and subtitle URLs arrive from third parties (yt-dlp) and may
carry signed credentials, while redirect and response handling historically
trusted whatever the server returned. Future audio acquisition, transcript API
fallback, and any additional fetch boundary will face the same classes of
input, so the trust rules must be fixed now rather than renegotiated per
provider.

Alternatives:

Validate only the initial URL and trust default redirect handling, rely on
Content-Length alone for size limits, keep `errors="replace"` decoding, or
continue embedding underlying exceptions in public errors for debuggability.

Impact:

`app/transcript.fetch_text` validates initial and redirect URLs with the same
validator, reads at most `MAX_SUBTITLE_RESPONSE_BYTES + 1` bytes, and maps
failures to stable categories (`unsafe URL`, `response too large`,
`unsupported or invalid subtitle encoding`, HTTP status, timeout, network
failure). `app.platform_adapter` classifies hosts exactly, and
`app.downloader` keeps only minimal subtitle metadata and a single stable
extraction error. DNS hostnames pass without resolution, so DNS rebinding is
not claimed to be prevented; future fetch boundaries must reuse or tighten
this policy instead of bypassing it.

Follow-up Review:
Revisit when transcript API fallback or real audio acquisition is approved, or
if a future provider legitimately requires a scheme, port, or metadata field
outside this policy.

## 2026-09-19

### Provider Boundary Remediation Decisions

Decision:
Close the independently reviewed gaps in the `v0.5.x` provider input and
error boundary hardening before any further stage: redirect response handling
must be bounded and closed, legacy numeric IPv4 literals must fail closed,
`youtu.be` matches its exact host only, reserved platform ids can never be
granted through hostname collision, minimal subtitle metadata accepts string
values only, and yt-dlp must never write raw output to process streams before
the sanitized error boundary.

Rationale:

The standard library redirect dispatch drains redirect bodies with an
unbounded `fp.read()` and leaves responses unclosed on rejected targets, which
voids the 16 MiB subtitle bound and leaks connections. Host validators that
only understand modern IP literals accept legacy numeric IPv4 forms the
operating system resolves as loopback. Hostname-derived platform labels can
collide with reserved provider ids, and allowlist key filtering alone still
passes nested mutable provider objects by reference. yt-dlp writes diagnostics
directly to stderr unless a logger is injected, so exception-chain cleanup
alone cannot sanitize output that was already printed.

Alternatives:

Trust the standard library redirect drain, resolve hosts through DNS to
classify them, keep reference-based allowlist copying for debuggability, or
allow reserved-id hostnames to keep their label and gate only on exact
capability checks. Each alternative either breaks the offline requirement or
reopens a demonstrated bypass.

Impact:

`app/transcript` overrides `http_error_30x` (301/302/303/307/308) to read
redirect bodies through the same 16 MiB cap, maps oversized redirect bodies
to the stable `response too large` error, and closes the current response on
safe, unsafe, oversized, and parent-opener-failure paths. The URL validator
recognizes legacy numeric IPv4 forms via `socket.inet_aton` without DNS,
applies the same loopback/private/link-local/multicast/reserved/unspecified
rejection rules, and fails closed on numeric-looking hosts that cannot be
proven safe; the same validator covers initial URLs and redirect targets.
`app/platform_adapter` treats `youtu.be` as exact-host only and maps reserved
platform id collisions to the safe `unknown` label. `app/downloader` copies
only string allowlist values into fresh containers and injects a
module-private quiet logger through `ydl_opts["logger"]`. All evidence is
offline; DNS rebinding remains out of scope and no live provider validation
was performed.

Follow-up Review:
Revisit when transcript API fallback or real audio acquisition is approved,
or if `socket.inet_aton` legacy parsing diverges on a new supported platform.

## 2026-09-19

### Request Authority Normalization Decision

Decision:
The subtitle URL validator validates the hostname the HTTP request layer would
actually use, not the raw `urlparse` result. The authority is normalized
offline before any IP or hostname rule runs: percent encoding inside the
authority is rejected instead of decoded, trailing DNS root dots are removed,
and the host must survive an explicit IDNA to ASCII conversion that fails
closed. The same validator covers initial URLs and every redirect target, and
the HTTP error path closes its own response without reading it.

Rationale:

`urllib.request.Request` applies `unquote()` to the raw authority, so
`https://127%2e0%2e0%2e1/sub.vtt` reached the socket layer as `127.0.0.1`
while `urlparse(...).hostname` still reported the encoded string and passed
the previous checks. Platform resolvers additionally drop a trailing root dot
and apply IDNA, so `https://127.0.0.1./`, `https://127.1./`, and the
full-width/ideographic forms (`１２７.０.０.１`, `127。0。0。1`) reached loopback
on this platform while the validator accepted them. The standard library also
quotes the raw `Location` with latin-1 before `redirect_request` runs, so a
non-latin-1 redirect target failed as a raw encoding error rather than the
stable rejection. Separately, the HTTP status error path converted the error
but never closed the response object it was handed.

Alternatives:

Decode the authority with `unquote()` and validate the decoded value, run the
whole URL through a canonicalization layer, resolve the host through DNS to
classify it, or keep validating `urlparse` output and rely on the request
layer to agree. Decoding accepts an authority whose decoded and literal forms
can disagree about host and port; full URL canonicalization is a broader
framework than this boundary needs; DNS resolution breaks the offline
requirement and introduces rebinding exposure.

Impact:

`app/transcript` normalizes the authority in `_normalized_request_host` before
`_is_safe_subtitle_host` applies the literal-IP, legacy-numeric, and
numeric-looking fail-closed rules. Percent encoding in the path and query
(where signed subtitle URLs carry their signature) is untouched. The redirect
handler resolves the raw `Location` into the effective absolute target before
dispatch and validates the absolute target once more, so a redirect target is
checked without a second request. The HTTP error path reads the status code
first, closes the response with a swallowed close failure, and raises the same
stable sanitized error. All evidence is offline unit tests; no live provider
validation was performed; DNS rebinding and resolver-level divergence remain
outside the current capability.

Follow-up Review:
Revisit when transcript API fallback or real audio acquisition is approved, or
if a supported platform resolves an authority differently from IDNA.

### Reserved Namespace, Control Character, and Redirect Resolution Decision

Decision:
Three gaps left in the request-authority normalization above are closed in the
same validator, and the redirect rule is restated as a resolution rule.

1. The reserved `localhost` namespace is rejected after IDNA normalization and
   trailing-dot removal: `localhost`, `localhost.`, every `*.localhost`
   subdomain, and every full-width, upper-case, or port-qualified spelling that
   normalizes onto them.
2. An authority that contains an ASCII control character or DEL fails closed,
   and `_ip_literal_address` converts the `ValueError` and `OSError` that
   `socket.inet_aton` can raise into "not a usable numeric form" instead of
   letting them escape.
3. A redirect is validated as the effective absolute target: the raw
   `Location` is parsed, given a `/` path when it is authority-only,
   re-serialized, percent-encoded with latin-1, and `urljoin`-ed against the
   URL of the request being redirected — exactly what `urllib.request` does —
   and that resolved target is what the safety rules judge. `redirect_request`
   keeps a second validation of the absolute target the standard library
   itself computed.
4. A quote, encoding, or resolution failure during that step is converted
   inside the handler into `TranscriptProviderError("official subtitle VTT
   fetch failed: unsafe URL")` with `from None`. No raw `UnicodeError` crosses
   the handler.

Rationale:

`localhost` is not an IP literal, so the literal rules never saw it, yet the
whole namespace resolves to loopback without any lookup of ours; the full-width
and upper-case spellings normalize onto the same name. IDNA's ASCII fast path
returns already-ASCII labels without running nameprep, so
`https://example.com\x00.evil/sub.vtt` survived normalization intact and
`socket.inet_aton` raised `ValueError("embedded null character")` from inside
the validator, which sits outside the `fetch_text` conversion block and so
reached the caller as a raw exception. Validating the raw `Location` as if it
were an absolute URL rejected legal relative and scheme-relative redirects
(`/next.vtt`, `../next.vtt`, `?sig=abc`, `//cdn.example.com/next.vtt`) that
resolve to a safe public HTTPS target, and non-latin-1 targets failed as a raw
`UnicodeEncodeError` rather than the documented stable error.

Alternatives:

Resolve `localhost` through DNS, keep a hard-coded name list per platform, or
treat it as a special case only in the resolver. Resolve the redirect target by
calling the standard library's own handler and intercepting the result. Keep
raising the raw `UnicodeError` and document that instead of the stable error.
DNS resolution breaks the offline requirement and reintroduces rebinding;
intercepting the handler would run the dispatch that must not run for a
rejected target; the existing contract, tests, and documentation all already
published the stable `unsafe URL` error, so the raw exception was the outlier.

Impact:

`app/transcript` adds `_has_control_characters` and `_is_localhost_namespace`
checks to the normalization and host gates, `_ip_literal_address` catches
`(OSError, ValueError)`, `_is_safe_subtitle_url` fails closed on any unexpected
parse failure, and `_effective_redirect_target` mirrors the request layer's
resolution before `http_error_30x` validates it. Rejected redirects still call
no parent opener, read no body, and close the response. All evidence is offline
unit tests through `fetch_text` and the real `http_error_30x` dispatch; no live
provider validation was performed, DNS rebinding and resolver-level time-of-
check/time-of-use differences remain outside the current capability, and this
is not a complete SSRF defense.

Follow-up Review:
Revisit if a supported platform resolves the `localhost` namespace differently,
or if control characters ever become legal in an authority.

### Raw Input Check and Redirect Cleanup Precedence Decision

Decision:
The control-character rule above is applied to the raw input rather than only to
the parsed authority, and redirect-response cleanup is made best-effort.

1. The unstripped initial URL and the unstripped raw redirect `Location` are
   checked for ASCII control characters and DEL before any `urlparse`, `quote`,
   or `urljoin` runs. A hit fails closed with the stable
   `official subtitle VTT fetch failed: unsafe URL`. Percent encoding in the
   path and query remains legal and unaffected.
2. Redirect cleanup goes through one module-internal best-effort close helper,
   used by the `http_error_30x` `finally`, by `_BoundedRedirectBody.close`, and
   by the HTTP status error path. An ordinary exception from `close()` is
   swallowed so it cannot replace a propagating stable error, a parent-opener
   failure, a successful redirect result, or a control-flow exception, and the
   close text never reaches a public error or a traceback. `KeyboardInterrupt`
   and `SystemExit` from `close()` still propagate unchanged.

Rationale:

`urlparse` removes tab, CR, and LF from the whole URL before it splits the
authority off, so the previous authority-level rule never saw those three and
`https://exa\tmple.com/sub.vtt`, `https://exa\rmple.com/sub.vtt`, and
`https://exa\nmple.com/sub.vtt` reached the request layer as `example.com`. The
check therefore has to run on the unstripped string, exactly as the NUL and DEL
cases already had to. Separately, `finally: bounded_body.close()` gave an
ordinary close failure the power to replace the exception — or the return value
— it was running alongside: the stable `unsafe URL` and `response too large`
errors, a `URLError` raised by the parent opener, a successful redirect result,
and `KeyboardInterrupt`/`SystemExit` all became `RuntimeError: raw close
failure`. Cleanup is not an outcome, so it must not be able to become one.

Alternatives:

Keep the authority-level rule and document the tab/CR/LF tolerance as accepted
behaviour, or strip those characters before validating. Keep `finally: close()`
and accept that a failing close overrides the outcome, or catch `BaseException`
around it. Documenting the tolerance contradicts the fail-closed contract the
tests and documents already publish; stripping would reproduce `urlparse`'s own
silent rewrite, which is the behaviour that hides the smuggling vector.
Catching `BaseException` would swallow `KeyboardInterrupt` and `SystemExit`,
which the contract requires to propagate unchanged.

Impact:

`app/transcript` adds `_raw_url_is_usable` and calls it from
`_is_safe_subtitle_url` and from `http_error_302` before the raw `Location` is
resolved, and replaces `_close_error_response` with `_close_response_quietly`
so the redirect and HTTP-error close policies are literally the same policy.
Rejected raw values still call no opener, read no redirect body, call no parent
opener, and close the response. All evidence is offline unit tests through
`fetch_text` and the real `http_error_30x` dispatch; no live provider validation
was performed, DNS rebinding and resolver-level time-of-check/time-of-use
differences remain outside the current capability, and this is not a complete
SSRF defense.

Follow-up Review:
Revisit if a provider ever legitimately returns a `Location` containing a raw
control character, or if the bounded redirect body gains a caller that depends
on a failing close being visible.

## 2026-09-20

### Explicit Local ASR CLI Decisions

Decision:
The local ASR capability is exposed as an independent `transcribe-local`
subcommand with a thin CLI, an offline-by-default model policy, and
stdout-only rendering.

1. `python -m app.cli transcribe-local <path>` is a new subcommand next to
   `import-url`. It accepts `--model` (default `small`), `--device` (default
   `cpu`), `--compute-type` (default `int8`), `--language` (unset),
   `--ffmpeg-path`, `--allow-model-download`, and `--format text|json`
   (default `text`). It does not add, remove, or reorder any `import-url`
   argument.
2. The CLI keeps only CLI responsibilities: parse arguments, classify the input
   with the existing `resolve_video_source` and require `local_file`/`local`,
   build neutral local `VideoMetadata` privately without `get_mock_metadata`,
   construct `FasterWhisperBackend` and the normalizer factory, call the
   existing `app.pipeline.transcribe_local_media`, and render the returned
   `TranscriptResult`. Business orchestration and local-source validation stay
   in the pipeline and in `LocalFileAudioProvider`.
3. The neutral local `VideoMetadata` uses `title=Path(path).stem` with the
   fallback `"Local media"` when the stem is empty, `platform="local"`,
   `source_url=path`, neutral empty `author`/`published_at`/`duration`/
   `language`, `tags=[]`, `status="local_input"`, and `raw_metadata=None`.
   `local_input` names the input surface this record belongs to instead of
   reusing the `local_file` source-type value.
4. `FasterWhisperBackend` gains `local_files_only: bool = False`, passed
   straight to `WhisperModel`. The CLI passes
   `local_files_only=not allow_model_download`, so offline model loading is the
   default and `--allow-model-download` is the only switch that permits a
   download.
5. `local_files_only=True` is enforced as a two-step boundary, not a single
   library flag. The flag only constrains the model-snapshot `download_model`
   call; when the resolved snapshot has no `tokenizer.json`, faster-whisper
   1.2.1 falls back to `tokenizers.Tokenizer.from_pretrained`, which ignores the
   flag and reaches the Hub. So `transcribe` resolves the model to a local
   directory before constructing `WhisperModel`: an existing local directory is
   used as-is, otherwise `download_model(model_size, local_files_only=True)`
   returns an existing cached snapshot or fails closed, and the resolved
   directory must contain a regular `tokenizer.json`. The resolved local
   directory is what is passed to `WhisperModel`, still with
   `local_files_only=True`. Every resolution failure — missing tokenizer,
   unresolvable model, or any other error — is sanitized to
   `local transcription failed` and happens before `WhisperModel` is
   constructed. `local_files_only=False` passes the model reference through
   unchanged with no pre-resolution and no tokenizer check.
6. Input classification wraps `resolve_video_source` and converts a
   `ValueError` raised there (a malformed IPv6 URL such as `http://[::1`, which
   `urlparse` cannot parse) into the same stable
   `local media file path required` error. `KeyboardInterrupt` and
   `SystemExit` are not intercepted, and only this classification step
   converts `ValueError`.
7. `--ffmpeg-path` is validated by the CLI as an existing regular file and is
   injected through `normalizer_factory` as
   `FfmpegAudioNormalizer(output_dir=workspace_path, ffmpeg_path=override)`.
   When the flag is absent the override is `None` and the normalizer keeps its
   existing PATH discovery. The failure message is the boundary's existing
   `ffmpeg not found`, not a new CLI-specific wording for the same condition.
8. Default stdout is `Provider:`, `Attempted providers:`, then
   `[start --> end] text` per segment. `--format json` prints exactly
   `provider`, `attempted_providers`, and `segments[{start, end, text}]` with
   `ensure_ascii=False`. Neither rendering writes a transcript file, Markdown,
   or an export, and neither calls the import pipeline or the Markdown
   exporter.
9. The command catches only `AudioAcquisitionError`, `AudioProcessingError` /
   `FfmpegNotFoundError`, and `LocalTranscriptionError`. Those print one
   `Error: <stable message>` line to stderr and return exit code 1. When the
   default offline mode produces exactly `local transcription failed`, stderr
   becomes exactly two lines with one final newline:

   ```text
   Error: local transcription failed
   Hint: offline model loading is enabled; use an existing cached model, a local model directory, or explicitly pass --allow-model-download.
   ```

   The hint is a separate `Hint:` line, not a parenthetical suffix on the
   `Error:` line. `KeyboardInterrupt`, `SystemExit`, and any exception outside
   those three categories propagate unchanged.

Rationale:

The local ASR capability was already implemented and validated as a local-file
orchestration boundary; the missing piece was a supported way to reach it
without letting a CLI grow its own copy of the pipeline. Calling
`transcribe_local_media` keeps one implementation of workspace ownership,
normalization, cleanup, and provider validation, so the CLI cannot drift from
the validated behavior. A separate subcommand keeps the default Mock import
flow and `real-fallback` untouched: `import-url` behavior, provider ids, and
`attempted_providers` are unchanged, and this command does not connect real
local ASR to the import pipeline. Neutral metadata built in the CLI keeps Mock
titles, authors, and transcript data out of the local ASR path while preserving the
`platform == "local"` and `source_url` contract the provider boundary already
requires.

Offline-by-default model loading is a privacy and reproducibility decision
before it is a convenience decision. A model name can silently reach Hugging
Face Hub on first use, so the safe direction is inverted: the command cannot
download a model unless the user asks for it in that invocation, and nothing in
the environment or configuration can widen the policy. Keeping the backend
parameter defaulted to `False` keeps earlier direct callers behaviorally
compatible, so the new flag is additive at the behavior level. It is not
byte-for-byte compatible at the `WhisperModel` call: the constructor now always
passes `local_files_only` explicitly, so a caller or stub that asserted the
exact keyword set of that call observes one added keyword.

Passing the library flag was not sufficient for that promise, which is why the
tokenizer guard exists. `local_files_only` is implemented by faster-whisper as
an argument to the snapshot `download_model` call only; the tokenizer is loaded
separately and its `from_pretrained` fallback has no offline argument at all. A
resolved snapshot that happens to lack `tokenizer.json` — an interrupted
download, a partially pruned cache, a hand-copied model directory — would
therefore make an "offline" command reach the Hub. Verifying the tokenizer file
locally before `WhisperModel` is constructed keeps the offline claim honest at
the cost of one directory check, and resolving the model to a concrete local
directory first is what makes that check possible. Failing closed with the same
sanitized message, rather than a tokenizer-specific error, keeps the error
surface unchanged and avoids leaking cache paths or model ids.

`resolve_video_source` treats its argument as user input, and `urlparse` raises
`ValueError` for input it cannot parse at all. That is a classification outcome,
not a programming error, so converting it at the single classification call site
keeps malformed input on the same stable error path as every other rejected
input. Converting `ValueError` more broadly, or catching `Exception`, would
swallow real defects and would risk the control-flow contract that keeps
`KeyboardInterrupt` and `SystemExit` propagating.

Reusing the ffmpeg boundary's existing `ffmpeg not found` message keeps one
wording for one condition. A CLI-specific variant would give users two strings
for the same failure and would make error-matching consumers depend on which
layer reported it.

Rendering only `TranscriptResult` fields, and only to stdout, keeps this stage
from inventing a second durable output contract next to the Markdown note, and
creates no transcript or Markdown artifact beyond the private workspace the
existing orchestration owns and cleans. When `--allow-model-download` is used,
faster-whisper may still write to its external model cache; that cache is not
owned or cleaned by `AudioWorkspace`.

Alternatives:

Reuse `import-url` with new provider values. Rejected: it would mix local ASR
into the import pipeline, require `real-fallback` and real-audio decisions in
the same stage, and put the `--output-dir`/Markdown contract in front of a
result that must not be written to a transcript file.

Let `FasterWhisperBackend` read an environment variable or configuration for
the model policy, or default `local_files_only=True` in the backend itself.
Rejected: the first hides a network permission in ambient state the user did
not set for this call, and the second silently changes behavior for callers
that already rely on the current default.

Set `HF_HUB_OFFLINE`, invoke `huggingface_hub` directly, or monkey-patch
`Tokenizer.from_pretrained` to force the tokenizer local. Rejected: ambient
environment state is exactly what the flag-driven policy avoids, a direct Hub
call would add a dependency on one of faster-whisper's transitive packages, and
patching a library internal would break on any upgrade. Resolving the model
directory and checking for `tokenizer.json` uses only the public top-level
`download_model`/`WhisperModel` surface and adds no dependency.

Reject a missing tokenizer with a distinct message such as
`local tokenizer not found`. Rejected: it would add a second wording next to the
existing single offline failure message and would distinguish cache states that
the command's contract deliberately keeps indistinguishable.

Convert every `ValueError` in the command, or catch `Exception` around
classification. Rejected: only the classification call treats `ValueError` as
user input, and broadening it would convert programming errors into misleading
stable output while endangering the `KeyboardInterrupt`/`SystemExit` contract.

Have the CLI construct `AudioWorkspace`, the normalizer, and the provider
itself instead of calling `transcribe_local_media`. Rejected: it duplicates the
validated lifecycle, ownership checks, and cleanup rules, and any later fix to
them would have to be made twice.

Write a transcript file next to the input, into `output/`, or as a
side-by-side `.txt`/`.json`. Rejected: this stage has no approved transcript
artifact contract, no naming or collision policy, and no retention policy, so
writing files would create generated output the project has not decided how to
own.

Catch `Exception` in the command so every failure becomes a stable error line.
Rejected: it would convert programming errors into a misleading "stable" error,
and it risks the control-flow requirement, which needs
`KeyboardInterrupt`/`SystemExit` to keep propagating.

Impact:

`app/cli.py` gains the subcommand, the `run_transcribe_local` dependency
builder, the classification wrapper, the private neutral-metadata builder, the
ffmpeg-path validation helper, the two renderings, and the command error
handling. `app/whisper.py` gains the `local_files_only` parameter, passes it to
`WhisperModel`, and resolves an offline model reference to a local directory
whose `tokenizer.json` must exist. `app/pipeline.py`, `app/audio.py`,
`app/models.py`, `app/errors.py`, `app/transcript.py`, packaging, and
dependencies are unchanged. `tests/test_local_asr_cli.py` adds 41 fully mocked
tests and `tests/test_whisper_backend.py` adds offline resolution,
tokenizer-guard, and pass-through coverage; the full suite passes 257 tests with
one pre-existing platform-dependent skip.

All evidence for this stage is mocked unit tests and offline CLI probes that
never reach ffmpeg, faster-whisper, a model download, a provider, or the
network. The offline resolution path is proven against a stub `faster_whisper`
module, not against a real cache or a real `download_model` call, and no real
model was loaded. No real `transcribe-local` CLI smoke test has been run, so the
command's real end-to-end behavior is unverified. Real fallback, YouTube audio
acquisition, retained cache, model-cache lifecycle, detected language, LLM
extraction, Markdown, and export behavior are unchanged, and
`TranscriptResult` still has no language field.

Follow-up Review:
Revisit when a real `transcribe-local` CLI smoke test is approved, when a real
cached snapshot and a real `download_model(local_files_only=True)` call can be
exercised without network access, when a transcript artifact or naming contract
is approved, when model-cache location and lifecycle become a product policy,
when detected language or silence semantics need a result field, or when a real
ffmpeg/faster-whisper path is wired into `real-fallback`.
