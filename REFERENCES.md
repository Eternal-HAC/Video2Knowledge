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

## Audio and ASR Pipeline

### kangarooking-skills/video-downloader

Repository:

https://github.com/kangarooking/kangarooking-skills/tree/main/video-downloader

Useful reference for:

- ffmpeg availability check.
- audio extraction / normalization command structure.
- local Whisper CLI or cloud ASR backend selection.
- transcript.txt / raw ASR JSON output artifact design.
- clear ASR backend behavior such as auto / none / whisper / cloud provider.

Do not copy directly:

- Do not turn Video2Knowledge into a video downloader.
- Do not copy its platform download behavior.
- Do not use cookies, login sessions, or authenticated access without explicit user confirmation.
- Do not add automatic media download to v0.5.x without a separate stage and user confirmation.
- Keep Video2Knowledge's main output as structured Markdown, not source-material folders.

Relationship to Video2Knowledge:

- It is an upstream material acquisition / ASR reference.
- Video2Knowledge should borrow only the audio-processing boundary and ASR backend design ideas.
- Video2Knowledge should preserve its current staged architecture: official subtitles first, then explicit audio acquisition, then local Whisper fallback, then structured Markdown.

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
