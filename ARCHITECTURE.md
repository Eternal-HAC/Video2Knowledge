# ARCHITECTURE

## Overview

Video2Knowledge is a Local First video-to-knowledge pipeline with replaceable provider modules. Its primary output is structured Markdown for local PKM systems such as Obsidian.

```text
Supported URL / local video or audio
-> platform adapter
-> downloader / metadata resolver
-> subtitle acquisition
-> explicitly permitted audio acquisition when needed
-> ffmpeg normalization
-> local ASR fallback
-> LLM knowledge extraction
-> Markdown writer
-> local exporter
```

The standard user workflow begins with a supported URL or local media file. It must not require manual video download as a normal prerequisite.

## v1.0 Pipeline Contract

The `v1.0` processing priority is:

```text
metadata
-> official subtitles
-> another explicitly supported transcript source
-> audio acquisition only when needed and explicitly permitted
-> ffmpeg normalization
-> local ASR
-> LLM knowledge extraction
-> structured Markdown export
```

The acquisition boundary exists to support knowledge processing, not to turn the product into a general-purpose downloader. Local ASR exists as a fallback, not as a standalone transcription product. LLM providers own extraction calls, while the pipeline owns orchestration and structured Markdown remains the durable output.

## Stage 1 Mock Flow

```text
example URL
-> Mock metadata
-> Mock transcript
-> Mock summary
-> Markdown template renderer
-> local Markdown file
```

## Interface Groundwork

The project started with replaceable boundaries and now has real YouTube metadata, official subtitle, and local ffmpeg normalization implementations alongside Mock defaults:

```text
raw input
-> platform adapter
-> platform capabilities
-> metadata provider
-> transcript provider strategy
-> summarizer
-> Markdown writer
-> local exporter
```

- `platform_adapter` classifies URL and local file inputs and infers platform labels through exact hostname matching, not domain substring matching.
- `platform_adapter` exposes platform capabilities for provider planning.
- `pipeline` owns the import business flow so CLI stays thin.
- `pipeline` also exposes a non-CLI local-file ASR orchestration boundary that
  composes injected audio, normalization, workspace, and Whisper components.
- `downloader` exposes Mock metadata and real YouTube metadata-only extraction,
  sanitizes extraction failures to a stable public error, and keeps only the
  minimal subtitle mapping the official subtitle provider needs in
  `raw_metadata`.
- `transcript` provides Mock transcripts, official YouTube VTT/WebVTT subtitles,
  fallback eligibility policy, and Mock Whisper fallback orchestration. Subtitle
  URLs (including redirect targets) are validated against the hostname the
  request layer would use, and initial, redirect, and final response reads are
  bounded and closed before any network callable runs.
- `audio` provides Mock audio boundaries and a real ffmpeg normalizer for existing local files.
- `whisper` provides the deterministic Mock local backend and a lazy optional
  `FasterWhisperBackend` boundary for existing normalized audio.
- The CLI remains compatible with `python -m app.cli import-url ...`.

Implemented provider boundaries have narrow responsibilities:

- Metadata provider: `yt-dlp` for YouTube metadata only.
- Transcript provider: `official-subtitles` for YouTube official VTT/WebVTT subtitles only.
- Transcript strategy: `real-fallback` for official subtitles followed only by eligible Mock local fallback.
- Audio normalizer: `ffmpeg_audio_normalizer` for existing local audio files, not wired into the default fallback chain.

Real audio acquisition is not validated. Standalone faster-whisper CPU and
non-CLI local-file-to-ASR integration smoke tests have passed, but the real
backend remains disconnected from the default import pipeline and
`real-fallback`. Transcript API fallback and LLM knowledge extraction are not
implemented.

## Design Principles

- Local First.
- CLI first, GUI later.
- Keep modules decoupled.
- Providers fetch data only and stay stateless.
- Pipeline owns business orchestration.
- CLI stays lightweight.
- Prefer mature external infrastructure for media processing later.
- Put project value in knowledge extraction and durable output.
- Keep provider APIs replaceable.
- Prefer official subtitles before acquiring media.
- Require explicit permission before media acquisition or retained media cache.
- Keep browser and mobile clients as optional capture or reading surfaces around the local core.
- Do not claim support for arbitrary websites or all video platforms.

## v0.3.x Real Metadata

`yt-dlp` is used only for metadata extraction:

```text
YouTube URL
-> yt-dlp extract_info(download=False)
-> sanitized metadata
-> VideoMetadata
-> Mock transcript
-> Mock summary
-> Markdown
```

This stage does not download media, fetch subtitles, run Whisper, call LLMs, or export to external systems. `raw_metadata` keeps only the minimal provider/subtitle mapping described under `v0.5.x Provider Input and Error Boundary Hardening`; it is not rendered into Markdown frontmatter or body content.

## Provider Direction

- `yt-dlp` is implemented for YouTube metadata-only extraction.
- Official YouTube VTT/WebVTT acquisition is implemented.
- `ffmpeg` normalization is implemented for existing local audio files.
- Future explicitly permitted audio acquisition remains separate from the current default pipeline.
- `youtube-transcript-api` for transcript fallback.
- `faster-whisper` for local transcription.
- OpenAI-compatible, Anthropic, or Gemini APIs for LLM summarization.

Transcript API fallback and LLM providers remain unimplemented. The real
faster-whisper backend and the non-CLI local-file orchestration are implemented
and have passed separate CPU smoke tests, but neither is selected by the default
import pipeline or `real-fallback`.

## v0.4.x Official Transcript

Official subtitles are acquired from `VideoMetadata.raw_metadata["subtitles"]`, which is populated by the `yt-dlp` metadata provider:

```text
YouTube URL
-> yt-dlp metadata
-> official subtitles from raw_metadata
-> VTT/WebVTT track selection
-> VTT parser
-> TranscriptResult
-> Mock summary
-> Markdown
```

This stage is intentionally VTT/WebVTT-only. It does not use `automatic_captions`, transcript API fallback, Whisper, LLMs, or subtitle file output. `attempted_providers` records only the stable provider id `yt_dlp_official_subtitles`.

## v0.5.0a Fallback Policy

The first Whisper fallback stage defines only error taxonomy and fallback eligibility:

```text
official-subtitles
-> NoOfficialSubtitleError / UnsupportedSubtitleFormatError
-> eligible for future Whisper fallback
```

Platform or network access failures do not mean subtitles are missing:

```text
HTTP 429 / HTTP 403 / timeout / network request failed
-> PlatformAccessError or NetworkAccessError
-> stop, do not enter Whisper fallback
```

`real-fallback` validates this policy and returns official subtitles when available. If fallback is eligible, it enters deterministic Mock audio processing boundaries before the Mock local Whisper backend:

```text
official-subtitles
-> NoOfficialSubtitleError / UnsupportedSubtitleFormatError
-> mock_audio_provider
-> mock_ffmpeg_normalizer
-> local_whisper_mock
-> TranscriptResult
```

The Mock audio provider and normalizer do not read local media, write audio files, download audio, check ffmpeg, or run ffmpeg. The Mock Whisper backend still does not call Whisper. Real audio acquisition, ffmpeg processing, and faster-whisper integration remain future stages.

## v0.5.0c2 Cache/Temp Safety Policy

Real audio acquisition remains disabled. Future audio download and audio cache retention require explicit user confirmation per stage. Runtime media artifacts belong only under `output/` or `cache/` paths and are ignored by Git.

Signed media URLs, cookies, tokens, auth headers, and sensitive query parameters must not be written to logs, Markdown, `TranscriptResult`, error messages, or disk. The hardened `v0.5.x` metadata boundary keeps at most the minimal signed subtitle URL inside the in-memory `raw_metadata` mapping that the official subtitle provider consumes; it never reaches Markdown, logs, or errors. Future audio and ffmpeg errors should report stable categories such as `audio download failed`, `audio processing failed`, or `ffmpeg not found` without exposing credentials or signed URLs.

## v0.5.0d ffmpeg Normalizer Boundary

The real ffmpeg normalizer boundary supports only existing local audio files:

```text
local audio file
-> ffmpeg
-> 16 kHz mono PCM WAV
-> NormalizedAudio
```

This boundary is not wired into `real-fallback` by default. The fallback path still uses `MockAudioNormalizer`. The ffmpeg boundary does not download audio, run Whisper, access YouTube, use Transcript API fallback, or call LLMs. A separate user-confirmed local smoke test verified 16 kHz mono PCM WAV output.

## v0.5.0e Local File Audio Provider Boundary

`LocalFileAudioProvider` exposes a user-owned local file through the existing
`AudioProvider -> AudioArtifact` contract:

```text
local VideoMetadata
-> LocalFileAudioProvider
-> AudioArtifact(temporary=False)
```

The provider validates only that the metadata describes a local source and that
the source path exists as a file. It does not copy, modify, delete, inspect, or
decode the file. Missing extensions use `format="unknown"` so codec detection
remains an ffmpeg responsibility.

The existing `AudioProvider.acquire(metadata)` interface and
`AudioArtifact.temporary` flag remain sufficient for this stage. User-owned
local files are never temporary and must not be cleaned up by the pipeline.
At this historical stage, lifecycle enums and an `AudioWorkspace` context
manager were deferred. `AudioWorkspace` was subsequently implemented in
`v0.5.2b`; lifecycle enums and retained-cache behavior remain deferred.

A future provider id `yt_dlp_audio` is reserved conceptually for explicitly
permitted media acquisition. It is not implemented in this stage. Future
download behavior must default to disabled, use temporary artifacts by default,
require separate confirmation to retain cache, and never expose signed URLs,
cookies, tokens, auth headers, query parameters, or raw yt-dlp errors.

## v0.5.2a YouTube Audio Acquisition Provider Boundary

The future `yt_dlp_audio` provider will continue to implement the existing
`AudioProvider.acquire(metadata) -> AudioArtifact` contract. Provider-specific
runtime policy will be supplied through constructor configuration rather than
changing the shared protocol:

```text
YtDlpAudioProvider(
    workspace_dir=None,
    allow_audio_download=False,
    timeout_seconds=600,
)
```

`YtDlpAudioProvider` now implements this limited boundary through the yt-dlp
Python API. It supports only `metadata.platform == "youtube"`; it does not
claim general yt-dlp platform support. Download permission defaults to false
and is checked before importing yt-dlp or invoking its backend.

The provider requests one `bestaudio` stream with playlists, subtitles,
automatic subtitles, thumbnails, yt-dlp configuration files, and postprocessors
disabled. It returns a temporary `AudioArtifact` only after confirming that the
reported file exists inside the supplied workspace. It does not run ffmpeg,
Whisper, or cleanup logic. Its optional workspace argument is only a destination
directory; the provider does not own cleanup. `AudioWorkspace`, added in the
subsequent `v0.5.2b` stage, owns cleanup only for registered temporary artifacts.

When no workspace is supplied, the provider creates a unique directory under
the system temporary location and still returns `AudioArtifact(temporary=True)`.
No cache-retention behavior exists in this stage. A future retained cache belongs under
`output/cache/audio/<source_id>/`, requires separate explicit confirmation,
must not overwrite an existing artifact, and must not use a video title as an
unsanitized filename.

`AudioWorkspace` owns only registered `temporary=True` artifacts inside its
private temporary directory. It cleans registered files in reverse order and
then removes the empty workspace directory on context exit, including after a
business error. It never deletes user-owned artifacts returned by
`LocalFileAudioProvider`, does not recursively delete unknown files, and does
not hide a business error when cleanup also fails. Cache retention remains
outside this stage.

Future `real-fallback` integration remains outside this stage:

```text
eligible official subtitle failure
-> explicit audio permission gate
-> yt_dlp_audio
-> FfmpegAudioNormalizer
-> real local Whisper backend
-> TranscriptResult
-> workspace cleanup
```

Platform access, network access, generic transcript, and metadata contract
errors remain ineligible for audio acquisition. Provider errors must use stable
sanitized categories and must not expose full commands, signed media URLs,
query parameters, cookies, tokens, auth headers, temporary credentials,
temporary paths, raw yt-dlp exceptions, or stderr.

## Current v0.5.x State

Completed:

- Fallback eligibility and error taxonomy.
- Mock Whisper fallback orchestration.
- Mock audio acquisition and normalization boundaries.
- Runtime cache and media artifact safety policy.
- Real ffmpeg normalizer boundary for existing local audio.
- Local ffmpeg and ffprobe smoke test.
- Local file audio provider boundary for user-owned files.
- YouTube-only `yt_dlp_audio` provider boundary with mocked backend tests.
- AudioWorkspace lifecycle boundary for registered temporary artifacts.
- `FasterWhisperBackend` boundary with lazy optional dependency loading,
  sanitized errors, and mocked segment mapping tests.
- Standalone faster-whisper CPU smoke test using the pinned `asr` dependency
  combination and an existing normalized WAV input.
- Real non-CLI local-file-to-ASR integration smoke test through
  `transcribe_local_media`, real ffmpeg normalization, and the faster-whisper
  backend on CPU.

Not implemented:

- A user-confirmed live audio acquisition test.
- Retained audio cache.
- Selection of real ffmpeg normalization in `real-fallback`.
- Pipeline and `real-fallback` integration of the validated faster-whisper
  backend.
- Transcript API fallback.
- LLM knowledge extraction.

## v0.5.3a FasterWhisperBackend Boundary

`FasterWhisperBackend` accepts an existing `NormalizedAudio` and maps
faster-whisper output into the stable transcript contract:

```text
NormalizedAudio
-> validate existing local file
-> lazy import faster_whisper
-> construct WhisperModel
-> transcribe
-> TranscriptSegment list
-> TranscriptResult(provider="faster_whisper")
```

Construction only stores `model_size`, `device`, `compute_type`, and optional
`language`; it does not import faster-whisper, load a model, inspect files, or
access the network. Input existence and file checks run before the optional
dependency import. Missing dependency and runtime failures use stable sanitized
errors without local paths, cache paths, raw exceptions, or tracebacks.

The boundary preserves segment order and maps second offsets to
`HH:MM:SS.mmm`. Its transcript provider list contains only `faster_whisper`, not
audio acquisition or normalizer ids. The current `TranscriptResult` contract
has no language field, so the configured language is passed to faster-whisper
but detected language cannot yet be represented in the returned result.

The boundary stage used mocked unit tests only. A subsequent standalone CPU
smoke test validated `faster-whisper 1.2.1`, `ctranslate2 4.8.1`, and `av 18.0.0`
on Windows with Python 3.13.7, the `Systran/faster-whisper-small` model,
`device="cpu"`, `compute_type="int8"`, and `language=None`. It transcribed an
existing 5.482688-second 16 kHz mono PCM WAV into one non-empty segment from
`00:00:00.000` to `00:00:05.000`, with provider and attempted providers both
correctly set to `faster_whisper`.

The 39.169-second first end-to-end measurement included model acquisition,
loading, and transcription and is not a stable performance benchmark. The
model cache was approximately 463.70 MiB; Windows symlink degradation did not
prevent execution but may increase disk use. The experimental cache location
is not a product cache policy. The test did not use GPU, CUDA, VAD, batch mode,
pipeline orchestration, or accuracy evaluation. Input audio content and the
tracked worktree remained unchanged.

The `asr` packaging extra pins the validated faster-whisper version but does
not package model files. Model acquisition remains a separate first-use or
explicit preparation action. The backend is still not selected by the pipeline
or `real-fallback`; retained cache and live YouTube audio acquisition also
remain incomplete.

## v0.5.4a Local File ASR Orchestration

`transcribe_local_media` in `app.pipeline` composes the existing boundaries for
one user-owned local file without changing the default import pipeline:

```text
local VideoMetadata
-> LocalFileAudioProvider
-> AudioArtifact(temporary=False)
-> private AudioWorkspace
-> FfmpegAudioNormalizer
-> NormalizedAudio(temporary=True)
-> workspace registration
-> injected WhisperBackend
-> TranscriptResult
-> workspace cleanup
```

The Whisper backend is always supplied by the caller. The audio provider may
be injected and otherwise defaults to `LocalFileAudioProvider`. A normalizer
factory may be injected; the default constructs `FfmpegAudioNormalizer` only
after entering the workspace and directs its output into the private directory.
The orchestration does not read CLI, environment, YAML, or global configuration.

The original user file is never registered with the workspace and is not
copied, modified, moved, or deleted. A normalized artifact must pass the
existing temporary, regular-file, existence, and workspace-containment checks
before transcription. Registered normalized output is removed on successful
return, transcription failure, or control-flow exit. Ffmpeg timeout, startup
failure, and non-zero exit also make a best-effort non-recursive removal of
only the newly calculated output path, without masking the processing error.

The entry point accepts only `metadata.platform == "local"`. Its provider must
return an existing regular user-owned `AudioArtifact(temporary=False)`;
temporary acquisition providers, including `YtDlpAudioProvider`, are outside
this orchestration boundary. After normalization returns, the orchestration has
limited provisional ownership of only that exact returned workspace object.
If registration fails, it best-effort removes only that exact in-workspace file
or empty directory, never scans recursively, never follows a symlink to an
external target, and never deletes workspace-external or unknown content. The
original registration error remains primary if provisional cleanup also fails.

An injected normalizer must write only into the supplied workspace, return the
one `temporary=True` artifact created by the call, clean its own partial output
before raising when possible, and avoid unknown side files. Orchestration cannot
safely claim files that a failing normalizer did not return.

Mocked integration tests and a separately approved real local-file integration
smoke test have validated this stage. The real smoke test used a user-owned AAC
M4A input on Windows with Python 3.13.7, the default `LocalFileAudioProvider`,
a private `AudioWorkspace`, real `FfmpegAudioNormalizer`, and
`FasterWhisperBackend("Systran/faster-whisper-small", device="cpu",
compute_type="int8", language=None)`. It produced one `TranscriptResult`
segment while preserving the source SHA-256; the temporary 16 kHz mono WAV and
workspace existed for transcription and were removed afterwards. Its observed
elapsed time on this short cached-model sample is not a benchmark or accuracy
result.

The orchestration remains non-CLI and is not selected by the default import
pipeline or `real-fallback`. It does not validate YouTube audio acquisition,
retained audio cache, detected language, pure-silence semantics, timestamp
rounding policy, GPU/CUDA, VAD, batch mode, or model-cache management.

## v0.5.x Provider Input and Error Boundary Hardening

The real provider input surface is hardened before any live audio, ASR, or
LLM integration. Each statement below is covered by fully offline unit tests in
`tests/test_provider_security.py`. No live network, real provider, or media
validation has been performed for this section, and it does not claim complete
SSRF protection: DNS rebinding and resolver-level differences remain outside
its scope.

- Platform classification uses `urlparse(...).hostname` with exact
  `host == domain or host.endswith("." + domain)` matching. Hostnames are
  lowercased and stripped of trailing dots; userinfo URLs and empty hostnames
  are never recognized as supported platforms. Suffix-confusion hosts such as
  `notyoutube.com` or `youtube.com.evil.test` no longer match YouTube.
  `youtu.be` additionally matches its exact host only: no `*.youtu.be`
  subdomain receives YouTube capabilities, while real subdomains of
  `youtube.com` and the other registered domains remain supported. An unknown
  hostname that collides with a reserved platform id (for example
  `https://youtube/x` or `https://user@youtube/x`) maps to the safe `unknown`
  label so it can never obtain provider capabilities; ordinary unknown hosts
  keep their normalized hostname label.
- `YtDlpMetadataProvider` maps every extraction failure to the stable
  `yt-dlp metadata extraction failed` error without the underlying exception
  text or cause. The missing-dependency error and metadata shape validation
  errors remain separate and stable. yt-dlp runs with a module-private quiet
  logger injected through `ydl_opts["logger"]`, so raw yt-dlp errors, signed
  URLs, tokens, cookies, local paths, and stderr output cannot reach
  stdout/stderr before the sanitized exception is raised.
- `VideoMetadata.raw_metadata` no longer stores the full sanitized yt-dlp
  info. It keeps only `{"provider": "yt-dlp", "subtitles": {...}}`, where each
  track retains at most `url`, `ext`, `protocol`, and `format`, and only when
  the value is a plain string. Non-string, nested dict/list, or other mutable
  values are dropped, so the output never shares references with provider-owned
  objects. This field-and-type boundary removes separate headers, cookies,
  fragments, paths, and arbitrary provider fields; it does not inspect the
  contents of an allowed string field.
  `YtDlpOfficialSubtitleProvider` consumes this minimal structure unchanged.
- Subtitle fetching validates the initial URL before any network call: the
  scheme must be `https`, a hostname must exist, userinfo is rejected, and the
  port must be empty or `443`. The validated value is the hostname the HTTP
  request layer would actually use, not the raw `urlparse` result:
  `urllib.request.Request` percent-decodes the authority before the host
  reaches the socket layer, platform resolvers drop a trailing DNS root dot,
  and IDNA maps full-width digits and Unicode label separators onto ASCII.
  Any percent encoding inside the authority is therefore rejected instead of
  decoded — encoded and decoded forms can disagree about host and port — while
  percent encoding in the path and query (where signed subtitle URLs carry
  their signature) stays usable. The raw URL is checked before anything parses
  it: any ASCII control character or DEL — tab, CR, LF, NUL, DEL, and the rest
  — fails closed rather than being tolerated. That check has to run on the
  unstripped string, because `urlparse` removes tab, CR, and LF from the whole
  URL before it splits the authority off, so a per-authority check would never
  see those three and the request layer would still contact the host they were
  hiding inside; an embedded NUL additionally makes `socket.inet_aton` raise a
  raw `ValueError`. The same rule is applied again to the parsed authority and
  to the IDNA-normalized host, where IDNA's ASCII fast path would otherwise
  pass such labels through without nameprep and reach the resolver unchanged.
  The remaining checks run on the IDNA ASCII host with trailing
  root dots removed: the reserved `localhost` namespace (`localhost`,
  `localhost.`, `*.localhost`, and every full-width or upper-case spelling that
  normalizes onto them) is rejected, and so are loopback, private, link-local,
  multicast, reserved, and unspecified literals through `ipaddress`. Legacy
  numeric IPv4 forms that the operating system would resolve as loopback or
  private (`127.1`, `127.0.1`, `2130706433`, `0177.0.0.1`, `0x7f000001`) are
  recognized offline via `socket.inet_aton` and rejected under the same rules,
  and numeric-looking hosts that cannot be proven safe fail closed. A hostname
  that cannot be safely encoded is rejected. The validator is total: an
  unexpected parsing failure yields the same rejection instead of a raw
  exception, and `KeyboardInterrupt` and `SystemExit` still propagate.
  Ordinary DNS hostnames, public IPv4/IPv6 literals, and a trailing root dot on
  a real name pass without extra resolution; DNS rebinding is not claimed to be
  prevented in this stage.
- A custom `HTTPRedirectHandler` applies the same validator to every redirect
  target before the redirected request is constructed, and before the redirect
  body is read or the parent opener is called. The raw `Location` is checked
  first, before anything parses it: a tab, CR, LF, NUL, DEL, or any other ASCII
  control character in it is refused outright — the same unstripped-string rule
  the initial URL gets. Only then is it resolved exactly the way
  `urllib.request` does — parse, give an authority-only target a `/` path,
  re-serialize, percent-encode with latin-1, then `urljoin` against the URL of
  the request being redirected — and that effective absolute target is what the
  safety rules judge.
  Relative (`/next.vtt`, `../next.vtt`, `?sig=abc`) and scheme-relative
  (`//cdn.example.com/next.vtt`) targets are therefore accepted when they
  resolve to a safe public HTTPS URL, and refused when they resolve to
  loopback, the `localhost` namespace, an encoded authority, userinfo, a
  non-`443` port, or a non-HTTPS scheme. A target that cannot be quoted,
  encoded, or resolved at all is refused with the same stable `unsafe URL`
  error instead of a raw `UnicodeError`. `redirect_request` validates the
  absolute target the standard library itself computed once more, so both
  layers agree. The handler also overrides the standard `http_error_30x`
  dispatch (301, 302, 303, 307, and 308 share one policy): the redirect
  response body is read with the same 16 MiB cap instead of the standard
  library's unbounded drain, an oversized redirect body maps to the stable
  `response too large` error, the current response is closed on safe, unsafe,
  oversized, and parent-opener-failure paths, and rejection errors never expose
  the `Location` URL, query, userinfo, headers, or body. A rejected redirect
  never reaches the parent opener and its body is never read.
- Redirect cleanup is best-effort so it can never replace the outcome it runs
  alongside: a `close()` raising an ordinary exception is swallowed rather than
  allowed to replace the stable `unsafe URL` or `response too large` error, the
  platform, network, or `URLError` failure raised by the parent opener, a
  successful redirect result, or a propagating `KeyboardInterrupt`/
  `SystemExit`. The standard library closes a successfully followed redirect
  response itself, so the cleanup is also idempotent: a repeated close that
  fails does not invent a new public failure, and the underlying close text
  never reaches a public error or a traceback. `KeyboardInterrupt` and
  `SystemExit` raised by `close()` still propagate unchanged.
- An HTTP status error closes its own response and never reads or exposes the
  error body. A failing `close()` is swallowed under the same best-effort
  cleanup policy as the redirect path, so it cannot replace the stable
  `official subtitle VTT fetch failed: HTTP Error <status>` error, the HTTP
  status code is preserved, no URL, header, body, or underlying exception is
  exposed, and `KeyboardInterrupt` and `SystemExit` still propagate unchanged.
- Subtitle responses are read with a 16 MiB module-level limit
  (`MAX_SUBTITLE_RESPONSE_BYTES`). An oversized `Content-Length` is rejected
  before the body is read, and the body read itself is bounded to
  `limit + 1` bytes, so a missing or lying `Content-Length` cannot bypass the
  limit. Initial, redirect, and final responses are all covered by this bound.
- Charset handling supports UTF-8 and any legal response charset. Unknown
  charsets, charset lookup failures, and decode failures map to the stable
  `official subtitle VTT fetch failed: unsupported or invalid subtitle
  encoding` error. Unsafe URLs, oversized responses, HTTP status codes,
  timeouts, and network failures keep their existing stable public categories,
  and none of them retain an underlying exception cause. `KeyboardInterrupt`
  and `SystemExit` propagate unchanged.

## URL Intake Boundaries

`v1.0` accepts clean YouTube URLs with minimum validation needed by the current pipeline. Full share-text parsing, tracking-parameter cleanup, short-link expansion, mobile-link handling, video-position preservation, and multi-platform normalization belong to `v1.x` platform expansion. They must not be folded into the current `v0.5.x` audio and ASR work.

## Future Capture and Mobile Surfaces

A future browser extension may submit URLs, page metadata, and tasks to a local service. It may assist content capture only where the user is authenticated and authorized. It must not bypass authentication, circumvent DRM, or replace the local processing core.

Mobile is an input and reading surface first. Link collection, task submission, and note reading may run on mobile, while ffmpeg, local ASR, and knowledge extraction remain primarily on a PC or local service.

## Cost Boundaries

Metadata, subtitle acquisition, and ffmpeg do not consume LLM tokens. Local Whisper or faster-whisper consumes local compute, storage, and time rather than cloud LLM tokens. Token cost begins primarily at LLM knowledge extraction. Replaceable providers should support user-provided API keys and may later support local models, but the architecture does not promise zero-cost operation.
