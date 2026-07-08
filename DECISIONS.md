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
