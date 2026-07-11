# PRD: Video2Knowledge

## Product Positioning

Video2Knowledge is a Local First video-to-knowledge pipeline.

It converts supported video or audio sources into structured Markdown knowledge notes for local personal knowledge management systems, with Obsidian as the primary target. The durable product artifact is a portable, inspectable, and versionable knowledge note rather than a downloaded media collection or a transient chat summary.

Video2Knowledge is not positioned as a general-purpose video downloader, but `v1.0` requires the media acquisition capabilities necessary to serve knowledge processing when subtitles are unavailable and the user explicitly permits acquisition.

Video2Knowledge is not positioned as a standalone Whisper script, but `v1.0` requires a local ASR fallback.

Video2Knowledge is not positioned as a generic AI video summarizer, but `v1.0` requires LLM-based knowledge extraction and structured Markdown generation.

Skill generation is not part of `v1.0`. Method-card or skill-pack generation is a possible downstream knowledge distillation direction after the core pipeline is stable.

## Target Users

- Personal knowledge management users.
- Obsidian users.
- Developers and researchers who collect knowledge from videos.
- Users who prefer local files and replaceable providers over cloud-first workflows.

## Pain Points

- Video knowledge is hard to search, quote, connect, and reuse.
- Existing AI video summary tools often stop at a short summary instead of producing a durable knowledge artifact.
- Metadata, subtitle acquisition, transcription, knowledge extraction, and note formatting are usually disconnected.
- Requiring users to manually download media creates unnecessary friction and exposes implementation details.
- Cloud-first tools can make local ownership, Git history, provider replacement, and long-term portability harder.

## v1.0 User Experience

The user should normally need only to:

- Paste a supported video URL; or
- Provide a local video or audio file.

The standard workflow must not require the user to manually download a video. The system should process the source in this order:

1. Metadata extraction.
2. Official subtitles.
3. Another explicitly supported transcript source.
4. Audio acquisition only when needed and explicitly permitted.
5. ffmpeg audio normalization.
6. Local ASR.
7. LLM knowledge extraction.
8. Structured Markdown export.

## v1.0 In Scope

- YouTube URL input.
- Local video and audio file input.
- Metadata extraction.
- Official subtitles first.
- Necessary audio acquisition when subtitles are unavailable and the user explicitly permits it.
- ffmpeg audio normalization.
- Local Whisper or faster-whisper transcription fallback.
- A stable `TranscriptResult` contract.
- LLM knowledge extraction.
- Structured Markdown generation with valid YAML Frontmatter.
- Local folder or Obsidian-friendly export.
- User-provided LLM API keys and a replaceable LLM provider boundary.

## v1.0 Out of Scope

- All-platform support.
- Full Bilibili support.
- Generic arbitrary-web ingestion.
- Browser extension.
- Authenticated course capture.
- Mobile application.
- DRM circumvention.
- Cookie- or session-based ingestion by default.
- Skill generator.
- SaaS accounts and billing.
- Cloud synchronization.

## URL Intake Scope

### v1.0 Basic URL Input

- Accept a clean YouTube URL.
- Perform minimum input validation.
- Preserve only the behavior needed by the `v1.0` pipeline.

### v1.x and Future Platform Expansion

- Extract URLs from complete share text.
- Identify multiple platforms.
- Remove tracking parameters.
- Preserve video-position parameters where meaningful.
- Support Chinese share copy, short links, and mobile links.
- Add Bilibili and additional platform adapters.

Complete multi-platform URL normalization is not part of the current `v0.5.x` work.

## Browser Extension and Capture Layer

A browser extension is a post-`v1.0` capture surface, not a replacement for the local core pipeline. Future exploration may include:

- Sending URLs, page metadata, and import tasks to a local service.
- Assisting capture for content the user is logged in to and authorized to process.
- Researching an audio-capture fallback where lawful and technically appropriate.

The capture layer must not bypass authentication, circumvent DRM, copy or transmit content the user is not authorized to process, or move core processing out of the local pipeline.

## Mobile Positioning

Mobile is an input and reading surface first, not the primary processing runtime.

The mobile experience should prioritize:

- Collecting links.
- Submitting processing tasks.
- Reading generated knowledge notes.

ffmpeg, Whisper, and the main knowledge-processing workload should run on a PC or local service.

## Cost and Token Boundaries

- Metadata extraction does not require LLM tokens.
- Subtitle acquisition does not require LLM tokens.
- ffmpeg processing does not require LLM tokens.
- Local Whisper or faster-whisper does not require cloud LLM tokens, but it consumes local compute, storage, and time.
- LLM token cost begins primarily at the knowledge extraction stage.
- The product can support user-provided API keys.
- Future versions may support local models or a fully open-source provider path.
- The project must not promise universally zero-cost operation because networking, compute, hosting, model downloads, or third-party APIs can still have costs.

## v1.0 Success Criteria

- A supported YouTube URL or local media file can enter one coherent pipeline.
- Official subtitles are preferred over media acquisition and local ASR.
- Media acquisition never occurs without an explicit permission boundary.
- Local ASR can produce a stable `TranscriptResult` when eligible fallback is required.
- Knowledge extraction produces useful, structured Markdown rather than only a short summary.
- The resulting note is portable, inspectable, and suitable for local folder or Obsidian use.
- Provider boundaries allow metadata, transcript, ASR, and LLM implementations to be replaced independently.

## Current Development Boundary

The current `v0.5.x` milestone is building the local Whisper fallback prerequisites in small stages. It does not expand into multi-platform URL normalization, browser capture, mobile processing, skill generation, or the `v0.6.x` LLM knowledge extraction implementation.
