# REFERENCES

## Video Processing

### VideoLingo

Useful reference for complete media processing pipelines, including download, WhisperX-style processing, task management, and recovery ideas.

Do not fork or copy directly.

## Markdown Output

### Youtube-fetcher-to-markdown

Useful reference for YAML Frontmatter, metadata organization, chapters, Markdown templates, and duplicate handling.

## Obsidian

### Obsidian-yt-video-summarizer

Useful reference for Obsidian integration, prompts, and multi-model support.

## Download Management

### Pinchflat

Useful reference for download queue design, configuration, and state management.

## Future Technical References

- yt-dlp.
- ffmpeg.
- faster-whisper.
- youtube-transcript-api.
- Jinja2.
- Pydantic.
- PyYAML.
- Rich.
- OpenAI-compatible APIs.
- Anthropic API.
- Gemini API.

## Downstream Knowledge Distillation

### cangjie-skill

Repository:

https://github.com/kangarooking/cangjie-skill

Useful reference for downstream knowledge distillation after Video2Knowledge has produced reliable structured Markdown notes.

Positioning:

- Distills books, long-video transcripts, podcasts, courses, interviews, long articles, and datasets into executable AI Skills.
- It is not a simple summary or review tool.
- It is closer to a future downstream knowledge distillation layer for Video2Knowledge than to the video acquisition, metadata, or transcript layer.

Ideas worth studying later:

- RIA-TV++ pipeline for turning long-form source material into reusable method units.
- Triple verification: cross-domain support, predictive power, and uniqueness.
- RIA++ structure: original source, interpretation, case, future trigger scenario, execution steps, and boundaries.
- Zettelkasten-style links between distilled units.
- `test-prompts.json` pressure tests for callable knowledge units.
- `PIPELINE_STATE.md` for resumable long-running distillation.
- `rejected/` audit trail for discarded candidate units.

Do not copy directly:

- Do not turn Video2Knowledge into a skill generator in the current stages.
- Do not add skill-pack output to `v0.4.x` or `v0.5.x`.
- Do not mix Whisper, transcript acquisition, LLM extraction, and skill generation in one stage.
- Do not copy cangjie-skill code or templates; use it only as a design reference.
