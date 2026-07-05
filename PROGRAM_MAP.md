# PROGRAM_MAP

## Runtime Entry

- `app/cli.py`: command-line entrypoint for the Mock import flow.
- `app/pipeline.py`: business pipeline for source resolution, metadata, transcript, summary, Markdown rendering, and export.

## Pipeline Modules

- `app/platform_adapter.py`: classifies URL or local file inputs, infers a platform label, and exposes platform capabilities.
- `app/downloader.py`: metadata provider boundary with Mock implementation and `yt-dlp` placeholder. Does not download media.
- `app/transcript.py`: transcript provider boundary with Mock implementation and real fallback placeholder. Does not fetch subtitles.
- `app/errors.py`: shared project exceptions for explicit provider boundary failures.
- `app/whisper.py`: placeholder for future local transcription. Does not run Whisper.
- `app/summarizer.py`: returns Mock knowledge extraction output. Does not call LLMs.
- `app/markdown_writer.py`: renders structured Markdown from metadata, transcript, and summary.
- `app/exporter/obsidian.py`: writes Markdown to a local directory.

## Configuration and Templates

- `config/settings.example.yaml`: example local configuration.
- `templates/video_note.md.j2`: Markdown note template.

## Tests

- `tests/`: unit tests for Mock flow and CLI behavior.
