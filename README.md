# Video2Knowledge

Video2Knowledge is a Local First AI/PKM tool that turns video sources into structured Markdown notes.

The project goal is not to build another video downloader or a generic AI summary tool. The goal is to create a complete knowledge processing pipeline:

```text
video URL / local video
-> transcript acquisition
-> optional local transcription
-> knowledge extraction
-> structured Markdown
-> Obsidian first, other exports later
```

## Current Version

v0.2.0

## Current Development Stage

Architecture Stable.

The current milestone is `v0.3.x Real Metadata`.

Implemented now:

- CLI skeleton.
- Mock metadata generation.
- Mock transcript generation.
- Mock summary generation.
- Structured Markdown output.
- Local file export for Obsidian-compatible Markdown.
- Import pipeline layer.
- Platform capabilities.
- Provider boundaries with explicit not-implemented errors.
- Real YouTube metadata provider boundary using `yt-dlp` metadata-only mode.

Not implemented yet:

- Real video download.
- Real subtitle fetching.
- Whisper or faster-whisper transcription.
- LLM calls.
- Notion API.
- Feishu API.
- MCP server.
- Browser extension.
- Any real external API integration.

## Run the Mock CLI

```powershell
python -m app.cli import-url "https://example.com/watch?v=mock" --output-dir output/markdown
```

The command writes a Markdown file under `output/markdown/`.

Provider flags exist to make the future replacement points explicit:

```powershell
python -m app.cli import-url "https://example.com/watch?v=mock" --metadata-provider mock --transcript-provider mock
```

Only `mock` providers are implemented. Non-Mock provider names are placeholders and fail with explicit not-implemented errors.

The CLI delegates the business flow to `app.pipeline`. The pipeline owns:

```text
source -> metadata -> transcript -> summary -> markdown -> export
```

This keeps real provider code out of the CLI when YouTube metadata work starts.

Real YouTube metadata is exposed through:

```powershell
python -m app.cli import-url "https://www.youtube.com/watch?v=VIDEO_ID" --metadata-provider yt-dlp --transcript-provider mock
```

This provider is metadata-only. It must not download video, audio, subtitles, or thumbnails. Installing `yt-dlp` and running a live YouTube smoke test are separate confirmation steps.

## Run Tests

```powershell
python -m unittest discover -s tests
```

## First MVP Output Shape

The generated note contains YAML Frontmatter and these sections:

- 一句话摘要
- 核心观点
- 知识点
- 技术术语
- 可执行事项
- 原始转录（带时间戳）

## Repository

GitHub repository:

https://github.com/Eternal-HAC/Video2Knowledge
