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

v0.4.0

## Current Development Stage

Official Transcript verified.

The current milestone is `v0.5.x Whisper Fallback`.

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
- YouTube official subtitle provider for VTT/WebVTT tracks.
- Verified YouTube official `zh-CN` VTT smoke test on a public TED video.

Not implemented yet:

- Real video download.
- Automatic captions.
- Transcript API fallback.
- Whisper or faster-whisper transcription.
- LLM calls.
- External knowledge base sync such as Notion or Feishu.
- MCP server.
- Browser extension.

## Run the Mock CLI

```powershell
python -m app.cli import-url "https://example.com/watch?v=mock" --output-dir output/markdown
```

The command writes a Markdown file under `output/markdown/`.

Provider flags exist to make the future replacement points explicit:

```powershell
python -m app.cli import-url "https://example.com/watch?v=mock" --metadata-provider mock --transcript-provider mock
```

Mock providers remain the default local path. Real provider work is currently limited to YouTube metadata-only extraction and YouTube official VTT/WebVTT subtitles.

The CLI delegates the business flow to `app.pipeline`. The pipeline owns:

```text
source -> metadata -> transcript -> summary -> markdown -> export
```

This keeps real provider code out of the CLI as metadata and transcript providers are added.

Real YouTube metadata is exposed through:

```powershell
python -m app.cli import-url "https://www.youtube.com/watch?v=VIDEO_ID" --metadata-provider yt-dlp --transcript-provider mock
```

This provider is metadata-only. It must not download video, audio, subtitles, or thumbnails.

YouTube official subtitles are exposed through:

```powershell
python -m app.cli import-url "https://www.youtube.com/watch?v=VIDEO_ID" --metadata-provider yt-dlp --transcript-provider official-subtitles
```

This provider only uses official VTT/WebVTT subtitle tracks from `yt-dlp` metadata. It does not use automatic captions, Transcript API fallback, Whisper, or LLMs. A live smoke test has verified official `zh-CN` VTT subtitles on a public TED video.

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
