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

## Current Stage

This repository is in the first Mock MVP stage.

Implemented now:

- CLI skeleton.
- Mock metadata generation.
- Mock transcript generation.
- Mock summary generation.
- Structured Markdown output.
- Local file export for Obsidian-compatible Markdown.

Not implemented in this stage:

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
