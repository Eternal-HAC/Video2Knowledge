# ROADMAP

## Version Roadmap

### v0.1.x Project Bootstrap

Status: Completed at `v0.1.0`.

- Project structure.
- Project memory documents.
- Mock CLI pipeline.
- Platform adapter mock pipeline.
- Provider boundaries.

### v0.2.x Architecture Stable

Status: Completed at `v0.2.0`.

- Import pipeline layer.
- Platform capabilities.
- Thin CLI.
- Provider and pipeline responsibility split.

### v0.3.x Real Metadata

Status: Completed at `v0.3.0`.

- Plan first.
- Implement real YouTube metadata only.
- Convert YouTube URL to `VideoMetadata`.
- Do not download media.
- Do not fetch transcript.
- Do not run Whisper.
- Do not call LLMs.
- Do not export to knowledge systems.

### v0.4.x Official Transcript

- Status: Completed at `v0.4.0`.
- Add YouTube official transcript acquisition.
- Support only official VTT/WebVTT subtitle tracks.
- Do not use automatic captions.
- Keep transcript providers focused on data retrieval.
- Do not add Whisper fallback in the same stage.

### v0.5.x Whisper Fallback

- [x] Define fallback policy and error taxonomy.
- [x] Add a Mock Whisper fallback pipeline before real media work.
- [x] Add Mock audio acquisition and normalization boundaries before real media work.
- [x] Add cache/temp safety policy before real media work.
- [x] Add ffmpeg normalization boundary before real Whisper work.
- [x] Validate the ffmpeg normalizer with a user-confirmed local smoke test.
- [x] Add a local file audio provider boundary without copying user media.
- [ ] Add an explicitly permitted network audio acquisition provider.
- [ ] Wire real ffmpeg normalization into an explicitly selected fallback path.
- [ ] Add local Whisper or faster-whisper transcription behind the stable audio and transcript boundaries.
- Keep local transcription separate from metadata and LLM work.
- Require explicit future confirmation before audio acquisition or dependency installation.

### v0.6.x Knowledge Extraction

- Add configurable LLM summarization and extraction.
- Keep provider calls behind clear boundaries.
- Study optional method-card or skill-pack export inspired by cangjie-skill after base extraction is stable.
- Keep structured Markdown notes as the primary output contract.

### v0.7.x Obsidian Export

- Improve Obsidian local export workflow.
- Add duplicate handling and note update behavior.

### v0.8.x Notion / Feishu

- Add optional Notion and Feishu export paths.
- Keep local Markdown as the primary source of truth.

### v0.9.x MCP

- Add an MCP server exposing a local import command such as `Import_video_to_knowledge_base(url)`.

### v1.0 Production Ready MVP

- Accept clean YouTube URLs and local video or audio files.
- Extract metadata and prefer official subtitles.
- Acquire necessary audio only when subtitles are unavailable and the user explicitly permits it.
- Normalize audio through ffmpeg and use local Whisper or faster-whisper as the ASR fallback.
- Produce a stable `TranscriptResult`.
- Run LLM knowledge extraction through a replaceable provider boundary using a user-provided API key where applicable.
- Generate structured Markdown and export to a local folder or Obsidian-friendly destination.
- Reliably validate metadata, transcript, ASR, extraction, and export paths.

Out of scope for `v1.0`:

- All-platform support and full Bilibili support.
- Generic arbitrary-web ingestion.
- Browser extension and mobile application.
- Authenticated course capture, DRM circumvention, or cookie/session ingestion by default.
- Skill generator.
- SaaS account, billing, and cloud synchronization.

### v1.x Platform and Capture Expansion

- Extract URLs from complete share text.
- Identify multiple platforms and add Bilibili or other adapters.
- Clean tracking parameters while preserving meaningful video-position parameters.
- Support Chinese share copy, short links, and mobile links.
- Explore a browser capture layer that submits authorized URLs, page metadata, and tasks to the local service.
- Treat mobile as a link collection, task submission, and reading surface rather than the primary ffmpeg or ASR runtime.
- Keep authentication, DRM, and content-rights boundaries explicit.

### Future Knowledge Distillation

- Explore optional method-card or skill-pack export after the core `v1.0` pipeline and base knowledge extraction are stable.
- Keep skill generation downstream from structured Markdown and outside the `v1.0` scope.
