# PROJECT_STATUS

## 2026-07-05

Status: Stage 1 initialization in progress.

Current goal:

- Establish the Video2Knowledge project structure.
- Implement a standard-library Mock MVP pipeline.
- Validate the CLI and unit tests locally.

Current implementation:

- No real API integrations.
- No external Python dependencies.
- Mock pipeline only.

Known constraints:

- `output/` is generated runtime data and should not be committed.
- Real video, transcript, Whisper, LLM, Notion, Feishu, MCP, and browser extension work is deferred.

## 2026-07-05

Status: Stage 2 interface groundwork started.

Changes:

- Added a platform adapter boundary for URL/local source classification.
- Added transcript result metadata for future fallback strategy.
- Kept all providers Mock-only.
- Added explicit non-Mock provider placeholders that fail with clear not-implemented errors.

Validation target:

- Unit tests must still pass.
- Existing Mock CLI command must remain compatible.

## 2026-07-05

Status: Architecture correction stage in progress.

Changes:

- Move business orchestration out of CLI and into `app.pipeline`.
- Add platform capabilities before real YouTube metadata work.
- Keep all providers Mock-only or explicitly not implemented.

Validation target:

- CLI remains compatible.
- Mock pipeline still writes Markdown.
- Unit tests pass.

## 2026-07-05

Status: Documentation synchronization stage in progress.

Changes:

- Record the development workflow in existing project memory documents.
- Update roadmap to version-based milestones.
- Update snapshot to `v0.2.0 Architecture Stable`.
- Keep `CODEX_WORKFLOW.md` out of the document set to avoid workflow duplication.

Validation target:

- Only Markdown documents are changed.
- No product code changes.

## 2026-07-05

Status: `v0.3.x Real Metadata` implementation in progress.

Changes:

- Implement YouTube metadata-only provider through the `yt-dlp` Python API.
- Keep transcript, summary, Markdown, and export on the existing Mock/local path.
- Declare `yt-dlp` as a dependency without installing it in this stage.

Validation target:

- Unit tests use mocked `yt_dlp` and do not access the network.
- Mock CLI regression still passes.
- Live installation and YouTube smoke test remain separate confirmation steps.

## 2026-07-06

Status: `v0.4.x Official Transcript` implementation in progress.

Changes:

- Add YouTube official subtitle provider for VTT/WebVTT tracks only.
- Read official subtitle tracks from `yt-dlp` metadata `raw_metadata["subtitles"]`.
- Keep automatic captions, transcript API fallback, Whisper, and LLMs out of this stage.
- Keep transcript provider attempts stable with `yt_dlp_official_subtitles`.

Validation target:

- Unit tests mock subtitle fetching and do not access YouTube.
- Mock CLI regression still passes.
- Live official subtitle smoke test remains a separate confirmation step.

## 2026-07-06

Status: `v0.4.x Official Transcript` error boundary fix in progress.

Findings:

- TED video metadata-only screening found official subtitles with a `zh-CN` VTT/WebVTT track.
- Full official subtitle smoke test reached the VTT text request step but received YouTube HTTP 429.
- Browser access to YouTube also showed HTTP 429, so this is treated as current access environment or platform rate limiting.
- This does not mean the selected video lacks official subtitles.

Changes:

- Wrap official subtitle VTT text fetch failures in `TranscriptProviderError`.
- Keep errors sanitized so subtitle URLs, signatures, tokens, cookies, and temporary credentials are not exposed.

Validation target:

- CLI must print a concise `Error: official subtitle VTT fetch failed: ...` message without traceback.
- Real VTT parsing smoke test remains pending until the network environment is no longer rate limited.

## 2026-07-08

Status: `v0.4.x Official Transcript` live smoke test passed.

Validation:

- URL: `https://www.youtube.com/watch?v=iG9CE55wbtY`
- Selected subtitle: official `zh-CN` `vtt`
- Provider: `yt_dlp_official_subtitles`
- Attempted providers: `["yt_dlp_official_subtitles"]`
- Output: Markdown only
- Generated Markdown: `output\markdown\do-schools-kill-creativity-sir-ken-robinson-ted.md`
- No video, audio, subtitle, thumbnail, or other media artifacts were found in the project directory.
- Unit tests passed: `Ran 30 tests ... OK`

Next target:

- Prepare `v0.4.0` tag.
- Plan `v0.5.x Whisper Fallback`, starting with fallback policy and error taxonomy.

## 2026-07-08

Status: `v0.5.0a Fallback Policy and Error Taxonomy` implementation in progress.

Changes:

- Add transcript error classes for fallback-eligible and access-failure cases.
- Define Whisper fallback eligibility policy.
- Keep `real-fallback` as a policy validator only; it does not download audio or run Whisper in this stage.
- Preserve official subtitle behavior and automatic captions boundary.

Policy:

- Missing official subtitles can enter future Whisper fallback.
- Official subtitles without VTT/WebVTT can enter future Whisper fallback.
- Platform access failures such as HTTP 429 and HTTP 403 must stop.
- Network access failures such as timeout and network request failure must stop.
- Metadata contract errors must stop.

Validation target:

- Unit tests cover eligibility and non-eligibility cases without network access.
- Mock CLI regression still passes.

## 2026-07-08

Status: `v0.5.0b Mock Whisper Fallback Pipeline` implementation in progress.

Changes:

- Add a deterministic Mock local Whisper backend.
- Make `real-fallback` return official subtitles when available.
- Make `real-fallback` enter Mock Whisper only for missing official subtitles or unsupported official subtitle formats.
- Keep platform access failures, network failures, and generic transcript failures from entering fallback.
- Keep audio acquisition, ffmpeg processing, and real Whisper execution out of this stage.

Validation target:

- Unit tests cover official success, eligible fallback, non-eligible failures, stable attempted providers, and Mock Whisper output.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0c1 Mock Audio Processing Boundary` implementation in progress.

Changes:

- Add Mock audio acquisition boundary.
- Add Mock audio normalization boundary.
- Route eligible `real-fallback` cases through Mock audio and Mock normalizer before Mock Whisper.
- Keep official subtitle success, platform access failures, network failures, and generic transcript failures from triggering audio processing.
- Keep real audio download, ffmpeg execution, cache handling, CLI flags, and real Whisper execution out of this stage.

Validation target:

- Unit tests cover mock audio and normalizer calls without network or media files.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0c2 Cache/Temp Safety Policy` implementation in progress.

Changes:

- Add Git ignore guardrails for runtime cache and media artifacts under `output/` and `cache/`.
- Record that audio acquisition, media download, and keeping audio cache require explicit user confirmation per stage.
- Record that signed URLs, cookies, tokens, auth headers, and sensitive query parameters must not enter logs, Markdown, raw metadata, transcript results, or error messages.
- Keep runtime behavior unchanged.

Validation target:

- Only documentation and `.gitignore` are changed.
- Unit tests and Mock CLI regression still pass.

## 2026-07-09

Status: `v0.5.0d ffmpeg Normalizer Boundary` implementation in progress.

Changes:

- Add a real ffmpeg audio normalizer boundary for existing local audio files.
- Normalize toward 16 kHz mono PCM WAV and return `NormalizedAudio`.
- Keep `real-fallback` on the existing Mock audio normalizer path.
- Keep YouTube access, real audio download, Whisper, Transcript API fallback, LLM, CLI flags, and pipeline changes out of this stage.

Validation target:

- Unit tests mock `shutil.which` and `subprocess.run`; no real ffmpeg execution is required.
- Mock CLI regression still passes.

## 2026-07-09

Status: `v0.5.0d2 Local ffmpeg Smoke Test` passed.

Validation:

- ffmpeg path: `D:\yt-dlp\ffmpeg.exe`
- ffprobe path: `D:\yt-dlp\ffprobe.exe`
- Input: local short audio file `F:\05_Music\test\20260709_205744.m4a`
- Output: ignored runtime artifact `output\cache\audio\20260709_205744-16k-mono.wav`
- Normalized audio: `wav`, mono, `16000 Hz`, `pcm_s16le`
- `NormalizedAudio`: `provider=ffmpeg_audio_normalizer`, `format=wav`, `sample_rate=16000`, `channels=1`, `temporary=True`
- `ffprobe` confirmed `codec_name=pcm_s16le`, `sample_rate=16000`, and `channels=1`.
- No YouTube access, media download, Whisper, Transcript API, or LLM execution occurred.
- No tracked file changes were produced by the smoke test; the generated WAV remains under ignored `output/cache/audio/`.

Next target:

- Continue planning the next explicit audio or Whisper integration stage without changing the default `real-fallback` Mock behavior.

## 2026-07-11

Status: Project documentation aligned with the current `v0.5.x Whisper Fallback` implementation.

Current implementation:

- Latest tagged release remains `v0.4.0 Official Transcript`.
- `v0.5.x` fallback policy, Mock Whisper fallback, Mock audio boundaries, cache safety policy, and ffmpeg normalizer boundary are complete.
- The local ffmpeg smoke test passed and verified 16 kHz mono `pcm_s16le` WAV output.
- The default `real-fallback` path still uses Mock audio normalization and Mock Whisper.

Not implemented:

- Real audio acquisition.
- Real ffmpeg processing in the default fallback chain.
- Real Whisper or faster-whisper execution.
- Transcript API fallback.
- LLM knowledge extraction.
- Automated Obsidian import/update behavior or external knowledge-base synchronization.

Next target:

- Plan the real audio acquisition boundary as a separate, explicitly permitted stage before integrating real local ASR.

## 2026-07-11

Status: `v0.5.2a YouTube Audio Acquisition Provider Boundary` implementation complete.

Changes:

- Added `YtDlpAudioProvider` using the yt-dlp Python API for a single YouTube audio-only artifact.
- Download permission defaults to disabled and is checked before loading or invoking yt-dlp.
- Disabled playlist, subtitle, automatic subtitle, thumbnail, configuration-file, and postprocessor behavior.
- Returned artifacts are temporary and must remain inside the supplied or system temporary destination directory.
- Kept `real-fallback`, pipeline, CLI, ffmpeg execution, Whisper, cache retention, and workspace cleanup unchanged.

Validation target:

- Unit tests mock yt-dlp and do not access the network or download media.
- Mock CLI regression remains unchanged.

## 2026-07-11

Status: `v0.5.2b AudioWorkspace` implementation complete.

Changes:

- Added a private temporary workspace context manager for registered `temporary=True` audio artifacts.
- Cleanup removes registered files in reverse order and only removes an empty workspace directory.
- Cleanup runs after business errors without masking the original error.
- User-owned local files, workspace-external files, directories, missing files, cache retention, and fallback integration remain outside the workspace cleanup scope.

Validation target:

- Unit tests use temporary test files only and do not access the network, yt-dlp, ffmpeg, or Whisper.
- Mock CLI regression remains unchanged.

## 2026-07-12

Status: `YtDlpAudioProvider` workspace validation ordering fix complete.

Changes:

- Validate a supplied workspace before importing the optional yt-dlp dependency.
- Keep invalid workspace errors stable regardless of whether yt-dlp is installed.
- Clarify the historical and current `AudioWorkspace` status in architecture documentation.

Validation target:

- Targeted provider tests and the full standard test suite pass without installing yt-dlp or accessing the network.

## 2026-07-12

Status: `v0.5.3a FasterWhisperBackend Boundary` implementation complete.

Changes:

- Added `FasterWhisperBackend` for existing `NormalizedAudio` inputs.
- Validate the input file before lazily importing the optional faster-whisper dependency.
- Map ordered faster-whisper segments into `TranscriptSegment` timestamps and text.
- Keep model construction, transcription, and lazy segment iteration behind stable sanitized local transcription errors.
- Preserve the Mock backend and keep the real backend disconnected from pipeline and `real-fallback` orchestration.

Validation:

- Mocked faster-whisper tests only; no dependency installation, model download, network access, ffmpeg, yt-dlp, or real ASR execution.
- Targeted Whisper tests passed: 15 tests.
- Full unit tests passed: 85 tests.
- Mock CLI regression passed with the existing Mock providers.

Remaining boundaries:

- faster-whisper is not installed and no model has been downloaded.
- Live local transcription is not validated.
- The current transcript result contract cannot represent detected language.
- Retained cache and live audio acquisition remain incomplete.
- Push of the existing local commit range is temporarily deferred by the current HTTPS/TLS environment; this is not a Video2Knowledge product defect.

## 2026-07-12

Status: `FasterWhisperBackend` exception sanitization fix complete.

Changes:

- Map non-`ImportError` dependency initialization failures to the stable `local transcription failed` error.
- Suppress underlying exception chains for dependency import, model construction, transcription, lazy iteration, segment access, and timestamp conversion failures.
- Preserve `KeyboardInterrupt`, `SystemExit`, and other control-flow exceptions outside the `Exception` hierarchy.
- Add mocked traceback sanitization, input gate, control-flow, and timestamp boundary coverage without installing or importing real faster-whisper.

Validation:

- Targeted Whisper tests passed: 25 tests.
- Full unit tests passed: 95 tests.
- Mock CLI regression passed with the existing Mock providers.

Remaining boundaries:

- Empty or fully filtered segment output remains `local transcription produced no segments`; a future approved live smoke test or fallback integration stage must validate the product semantics for pure-silence audio.
- faster-whisper installation, model acquisition, live transcription, pipeline integration, and `real-fallback` integration remain incomplete.

## 2026-07-12

Status: `v0.5.3b Faster-Whisper CPU Smoke Test` passed and `v0.5.3c` optional dependency adoption complete.

Validated environment:

- Windows with Python 3.13.7.
- `faster-whisper 1.2.1`, `ctranslate2 4.8.1`, `av 18.0.0`, and `huggingface-hub 1.23.0`.
- `Systran/faster-whisper-small`, CPU, `int8`, and `language=None`.
- Existing 5.482688-second 16 kHz mono PCM WAV input.

Result:

- Backend end-to-end time was 39.169 seconds and included first model acquisition, loading, and transcription; it is not a stable benchmark.
- Returned one non-empty segment from `00:00:00.000` to `00:00:05.000`.
- Provider and attempted providers were both `faster_whisper`.
- Input audio hash and tracked Git worktree were unchanged.
- No GPU, CUDA, VAD, batch mode, pipeline integration, or accuracy evaluation was used.
- Model cache was approximately 463.70 MiB. Windows symlink degradation did not block execution but may increase disk use.

Packaging:

- Added the optional `asr` extra with `faster-whisper==1.2.1`.
- Base installation still installs only the existing core dependencies.
- Model files are not packaged; acquisition and caching remain separate first-use or preparation behavior.
- The smoke-test cache location remains experimental and is not a formal product cache policy.

Validation:

- Full unit tests passed: 95 tests on the project-standard Python 3.13.7 interpreter.
- Mock CLI regression passed with the existing Mock providers.
- Editable `.[asr]` pip dry-run recognized `faster-whisper==1.2.1` and the already installed validated runtime without planning dependency uninstall or downgrade.

Remaining boundaries:

- `FasterWhisperBackend` is not connected to pipeline or `real-fallback`.
- Formal local-file-to-real-ASR orchestration is not implemented.
- Live YouTube audio acquisition and retained audio cache remain incomplete.
- `TranscriptResult` has no detected-language field.
- Pure-silence semantics and exact half-millisecond timestamp rounding are not formal product contracts.
- GPU/CUDA and formal model-cache location, lifecycle, and cleanup remain unvalidated or undesigned.

## 2026-07-12

Status: `v0.5.4a Local File ASR Orchestration` implementation complete.

Changes:

- Added `transcribe_local_media` in `app.pipeline` for composing a local file provider, private audio workspace, normalizer, and caller-supplied Whisper backend.
- Keep the user-owned source artifact outside workspace ownership and require normalized output registration before transcription.
- Return the backend `TranscriptResult` unchanged so audio and normalizer ids do not enter transcript provider history.
- Add best-effort cleanup for only the newly calculated ffmpeg output after timeout, startup `OSError`, or non-zero exit.
- Preserve stable acquisition, processing, transcription, and cleanup errors without adding an orchestration-level exception.

Validation:

- Mocked orchestration tests use temporary placeholder files only and do not run real ffmpeg, faster-whisper, or network access.
- Targeted local ASR orchestration tests passed: 16 tests.
- Full unit tests passed: 111 tests.
- Existing Mock CLI regression passed.

Remaining boundaries:

- The orchestration is not exposed by CLI and is not connected to `real-fallback` or the default import pipeline.
- A complete real local-file-to-ASR integration smoke test has not run.
- YouTube live audio acquisition, retained audio cache, and formal model-cache management remain incomplete.
- Detected-language, pure-silence, and exact timestamp-rounding contracts remain unchanged and unresolved.
