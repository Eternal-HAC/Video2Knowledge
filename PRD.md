# PRD: Video2Knowledge

## Product Positioning

Video2Knowledge is a Local First AI tool for personal knowledge management. It converts video sources into structured Markdown notes that can be stored, searched, versioned, and later synced to knowledge systems.

## Target Users

- Personal knowledge management users.
- Obsidian users.
- Developers and researchers who collect knowledge from videos.
- Users who prefer local files over cloud-first workflows.

## Pain Points

- Video knowledge is hard to search, quote, and reuse.
- Existing AI video summary tools often stop at a short summary instead of a durable knowledge artifact.
- Downloading, transcription, summarization, and note formatting are usually disconnected.
- Cloud-first tools can make local ownership, Git history, and long-term portability harder.

## MVP

The first real MVP should support:

- YouTube URL input.
- Local video input.
- Official subtitles first.
- Transcript API fallback.
- Local Whisper fallback only when subtitles are unavailable.
- LLM-based cleaning, segmentation, summarization, concepts, action items, and tags.
- Structured Markdown output with valid YAML Frontmatter.
- Obsidian-friendly local storage.

## Current Mock MVP

The current stage implements only:

- Example URL input.
- Mock metadata.
- Mock transcript.
- Mock summary.
- Structured Markdown output.

## Success Criteria

- A single CLI command can run the end-to-end Mock pipeline.
- Generated Markdown is deterministic enough for tests.
- The module boundaries allow replacing Mock implementations with real integrations later.
- Project memory documents make the current state recoverable.

## Explicitly Out of Scope for Stage 1

- Browser extension.
- MCP server.
- Notion API.
- Feishu API.
- Docker cluster.
- Web backend.
- User system.
- Cloud database.
- Video translation.
- Dubbing.
- TTS.
- Real downloading.
- Real subtitle fetching.
- Whisper/faster-whisper execution.
- LLM calls.

