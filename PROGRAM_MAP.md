# PROGRAM_MAP

## Runtime Entry

- `app/cli.py`: command-line entrypoint for the Mock import flow.
- `app/pipeline.py`: business pipeline for source resolution, metadata, transcript, summary, Markdown rendering, and export.

## Pipeline Modules

- `app/platform_adapter.py`: classifies URL or local file inputs, infers a platform label, and exposes platform capabilities.
- `app/downloader.py`: metadata provider boundary with Mock implementation and YouTube `yt-dlp` metadata-only implementation. Does not download media.
- `app/transcript.py`: transcript provider boundary with Mock implementation, YouTube official VTT/WebVTT subtitles, fallback eligibility policy, and real fallback orchestration through Mock audio processing into the Mock Whisper backend. Does not use automatic captions, transcript API fallback, real audio acquisition, or real Whisper execution.
- `app/errors.py`: shared project exceptions for explicit metadata failures, transcript failures, platform access failures, network access failures, and fallback-eligible subtitle absence/format cases.
- `app/audio.py`: Mock audio acquisition and normalization boundaries for fallback orchestration. Does not read media, write audio files, check ffmpeg, or run ffmpeg.
- `app/whisper.py`: Mock local Whisper backend boundary for validating fallback orchestration. Does not read media or run Whisper.
- `app/summarizer.py`: returns Mock knowledge extraction output. Does not call LLMs.
- `app/markdown_writer.py`: renders structured Markdown from metadata, transcript, and summary.
- `app/exporter/obsidian.py`: writes Markdown to a local directory.

## Configuration and Templates

- `config/settings.example.yaml`: example local configuration.
- `templates/video_note.md.j2`: Markdown note template.

## Tests

- `tests/`: unit tests for Mock flow and CLI behavior.
