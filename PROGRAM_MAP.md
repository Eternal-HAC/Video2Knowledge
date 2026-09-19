# PROGRAM_MAP

## Runtime Entry

- `app/cli.py`: command-line entrypoint for the Mock import flow.
- `app/pipeline.py`: business pipeline for source resolution, metadata, transcript, summary, Markdown rendering, and export. Also contains the non-CLI, local-only `transcribe_local_media` orchestration boundary. It requires a user-owned non-temporary source artifact, gives limited provisional ownership to the exact normalized workspace output before registration, and never connects temporary/network acquisition to the default import flow.

## Pipeline Modules

- `app/platform_adapter.py`: classifies URL or local file inputs with exact hostname matching (no domain substring matching), treats `youtu.be` as exact-host only, maps reserved platform id collisions to the safe `unknown` label, infers a platform label, and exposes platform capabilities.
- `app/downloader.py`: metadata provider boundary with Mock implementation and YouTube `yt-dlp` metadata-only implementation. Does not download media. Extraction failures surface only as the stable `yt-dlp metadata extraction failed` error, yt-dlp diagnostics go to a module-private quiet logger instead of process streams, and `raw_metadata` keeps only the minimal string-valued `provider`/`subtitles` mapping the official subtitle provider needs.
- `app/transcript.py`: transcript provider boundary with Mock implementation, YouTube official VTT/WebVTT subtitles, fallback eligibility policy, and real fallback orchestration through Mock audio processing into the Mock Whisper backend. Rejects ASCII control characters and DEL in the raw, unstripped input before any parsing — initial URL and redirect `Location` alike, so tab, CR, and LF cannot be stripped out from under the check — and validates subtitle URLs (including redirect targets) against HTTPS/userinfo/port/literal-IP rules after normalizing the authority to the hostname the HTTP request layer would use: authority percent encoding is rejected rather than decoded, trailing DNS root dots are dropped, Unicode hosts must survive an IDNA to ASCII conversion, control characters in the authority fail closed, and the reserved `localhost` namespace is rejected. Rejects legacy numeric IPv4 forms offline and fails closed on numeric-looking hosts before any network callable. Resolves a redirect `Location` into the effective absolute target the request layer would use — quoting it with latin-1 and joining it against the source request URL — and validates that resolved target before reading the redirect body or calling the parent opener, mapping quote, encoding, and resolution failures to the stable `unsafe URL` error. Bounds initial, redirect, and final subtitle response reads to 16 MiB, closes the redirect response on every redirect path with a best-effort, idempotent cleanup that cannot replace a stable error, a parent-opener failure, a successful redirect result, or a propagating `KeyboardInterrupt`/`SystemExit`, closes an HTTP status error response without reading it, and maps charset and read failures to stable sanitized errors. Does not use automatic captions, transcript API fallback, real audio acquisition, or real Whisper execution.
- `app/errors.py`: shared project exceptions for explicit metadata failures, transcript failures, platform access failures, network access failures, fallback-eligible subtitle absence/format cases, audio processing, and sanitized local transcription failures.
- `app/audio.py`: audio acquisition and normalization boundaries. Includes Mock audio processing, `LocalFileAudioProvider`, a YouTube-only `YtDlpAudioProvider`, `AudioWorkspace` for registered temporary artifact cleanup, and an ffmpeg normalizer boundary for existing local audio files. Failed ffmpeg calls best-effort remove only their newly calculated partial output. These boundaries are not wired into fallback; workspace does not manage cache retention.
- `app/whisper.py`: deterministic Mock local Whisper backend plus `FasterWhisperBackend` for lazily loading the optional dependency and mapping an existing `NormalizedAudio` into `TranscriptResult`. The real backend is not wired into pipeline or fallback orchestration.
- `app/summarizer.py`: returns Mock knowledge extraction output. Does not call LLMs.
- `app/markdown_writer.py`: renders structured Markdown from metadata, transcript, and summary.
- `app/exporter/obsidian.py`: writes Markdown to a local directory.

## Configuration and Templates

- `config/settings.example.yaml`: example local configuration.
- `templates/video_note.md.j2`: Markdown note template.

## Tests

- `tests/`: unit tests for the Mock flow, CLI behavior, provider boundaries, audio lifecycle, mocked faster-whisper behavior, and mocked local-file-to-ASR orchestration.
