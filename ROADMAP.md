# ROADMAP

## Stage 1: Mock MVP

- Create project structure.
- Create project memory documents.
- Implement CLI skeleton.
- Define module interfaces.
- Generate structured Markdown from Mock data.
- Validate locally with tests and CLI run.

## Stage 2: Real Local Pipeline

- Add platform adapter interface.
- Support YouTube metadata and official subtitles.
- Add transcript API fallback.
- Add local video input path handling.
- Add local Whisper fallback.
- Add configurable Markdown and prompt templates.
- Add Obsidian import workflow.

## Stage 3: Export and Batch Workflows

- Add Notion export.
- Add Feishu export.
- Add batch import.
- Add Git-friendly duplicate detection and update behavior.

## Stage 4: MCP Server

- Add an MCP server exposing an import command such as `Import_video_to_knowledge_base(url)`.
- Keep processing in the local service.

## Stage 5: Browser Extension

- Add import buttons on supported video platforms.
- Extension sends URL only.
- Local service performs processing.

