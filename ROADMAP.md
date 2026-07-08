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

- Start with fallback policy and error taxonomy.
- Add a Mock Whisper fallback pipeline before real media work.
- Add Mock audio acquisition and normalization boundaries before real media work.
- Add local Whisper fallback only after transcript acquisition is stable.
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

- Stable local pipeline from supported source to structured Markdown.
- Reliable validation for metadata, transcript, extraction, and export paths.
